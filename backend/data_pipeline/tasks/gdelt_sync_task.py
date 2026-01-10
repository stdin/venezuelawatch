"""
GDELT BigQuery sync task - replace DOC API polling with native BigQuery queries.

Syncs Venezuela-related events from gdelt-bq.gdeltv2 to our events table.
Runs every 15 minutes to match GDELT update frequency.
"""
import logging
import uuid
from typing import Dict, Any
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import pytz

from data_pipeline.tasks.base import BaseIngestionTask
from api.services.gdelt_bigquery_service import gdelt_bigquery_service
from api.services.gdelt_gkg_service import gdelt_gkg_service
from api.bigquery_models import Event as BigQueryEvent
from api.services.bigquery_service import bigquery_service

logger = logging.getLogger(__name__)


def get_intelligence_task():
    """Lazy import to avoid circular dependency."""
    from data_pipeline.tasks.intelligence_tasks import analyze_event_intelligence
    return analyze_event_intelligence


@shared_task(base=BaseIngestionTask, bind=True)
def sync_gdelt_events(self, lookback_minutes: int = 15) -> Dict[str, Any]:
    """
    Sync Venezuela events from GDELT native BigQuery to our dataset.

    Replaces custom DOC API polling with direct BigQuery federation.

    Args:
        lookback_minutes: How many minutes to look back (default: 15)

    Returns:
        {
            'events_created': int,
            'events_skipped': int,
            'events_fetched': int
        }
    """
    logger.info(f"Starting GDELT BigQuery sync (lookback: {lookback_minutes} minutes)")

    # Time range for query
    end_time = timezone.now()
    start_time = end_time - timedelta(minutes=lookback_minutes)

    try:
        # Fetch Venezuela events from GDELT native BigQuery
        gdelt_events = gdelt_bigquery_service.get_venezuela_events(
            start_time=start_time,
            end_time=end_time,
            limit=1000  # Higher than DOC API limit of 250
        )

        logger.info(f"Fetched {len(gdelt_events)} events from GDELT BigQuery")

        # Enrich events with GKG data (themes, entities, sentiment)
        events_with_gkg = 0
        events_without_gkg = 0

        for gdelt_event in gdelt_events:
            source_url = gdelt_event.get('SOURCEURL')
            if source_url:
                try:
                    # Parse event date for partition filtering
                    date_str = str(gdelt_event['DATEADDED'])
                    event_date = timezone.datetime.strptime(date_str[:8], '%Y%m%d').replace(tzinfo=pytz.UTC)

                    # Fetch GKG record by DocumentIdentifier (= SOURCEURL)
                    gkg_record = gdelt_gkg_service.get_gkg_by_document_id(
                        document_id=source_url,
                        partition_date=event_date
                    )

                    if gkg_record:
                        gdelt_event['gkg_raw'] = gkg_record
                        events_with_gkg += 1
                    else:
                        events_without_gkg += 1

                except Exception as e:
                    logger.warning(f"Failed to fetch GKG for {source_url[:50]}: {e}")
                    events_without_gkg += 1
            else:
                events_without_gkg += 1

        logger.info(f"GKG enrichment: {events_with_gkg} with GKG data, {events_without_gkg} without")

        events_created = 0
        events_skipped = 0
        bigquery_events = []

        for gdelt_event in gdelt_events:
            # Check for duplicates using GLOBALEVENTID
            try:
                existing_query = f"""
                    SELECT COUNT(*) as count
                    FROM `{bigquery_service.project_id}.{bigquery_service.dataset_id}.events`
                    WHERE id = @event_id
                """
                from google.cloud import bigquery
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter('event_id', 'STRING', str(gdelt_event['GLOBALEVENTID']))
                    ]
                )
                results = bigquery_service.client.query(existing_query, job_config=job_config).result()
                row = list(results)[0]
                if row.count > 0:
                    logger.debug(f"Skipping duplicate GDELT event: {gdelt_event['GLOBALEVENTID']}")
                    events_skipped += 1
                    continue
            except Exception as e:
                logger.error(f"Failed to check for duplicate: {e}")
                # Continue with insert
                pass

            # Map GDELT event to our BigQuery schema
            try:
                # Parse GDELT date format (YYYYMMDDHHMMSS)
                date_str = str(gdelt_event['DATEADDED'])
                event_date = timezone.datetime.strptime(date_str[:8], '%Y%m%d').replace(tzinfo=pytz.UTC)

                # Generate title from actors and event code
                title = f"{gdelt_event.get('Actor1Name', 'Unknown')} - {gdelt_event.get('Actor2Name', 'Event')} ({gdelt_event.get('EventCode', '')})"

                # Map QuadClass to event_type
                quad_class = gdelt_event.get('QuadClass')
                event_type_map = {
                    1: 'political',  # Verbal Cooperation
                    2: 'political',  # Material Cooperation
                    3: 'political',  # Verbal Conflict
                    4: 'political'   # Material Conflict
                }
                event_type = event_type_map.get(quad_class, 'other')

                # Create BigQueryEvent
                bq_event = BigQueryEvent(
                    id=str(gdelt_event['GLOBALEVENTID']),  # Use GDELT ID
                    source_url=gdelt_event.get('SOURCEURL', ''),
                    mentioned_at=event_date,
                    created_at=timezone.now(),
                    title=title[:500],  # Truncate if needed
                    content=f"GDELT Event: {gdelt_event.get('EventCode', '')} - Tone: {gdelt_event.get('AvgTone', 0)}",
                    source_name='GDELT',
                    event_type=event_type,
                    location=gdelt_event.get('ActionGeo_FullName', 'Venezuela'),
                    risk_score=None,  # Computed by LLM
                    severity=None,    # Computed by LLM
                    metadata={
                        'goldstein_scale': gdelt_event.get('GoldsteinScale'),
                        'avg_tone': gdelt_event.get('AvgTone'),
                        'num_mentions': gdelt_event.get('NumMentions'),
                        'num_sources': gdelt_event.get('NumSources'),
                        'num_articles': gdelt_event.get('NumArticles'),
                        'quad_class': quad_class,
                        'actor1_code': gdelt_event.get('Actor1Code'),
                        'actor1_name': gdelt_event.get('Actor1Name'),
                        'actor2_code': gdelt_event.get('Actor2Code'),
                        'actor2_name': gdelt_event.get('Actor2Name'),
                        'event_code': gdelt_event.get('EventCode'),
                        'action_geo_lat': gdelt_event.get('ActionGeo_Lat'),
                        'action_geo_long': gdelt_event.get('ActionGeo_Long'),

                        # Religion & Ethnicity
                        'actor1_religion1_code': gdelt_event.get('Actor1Religion1Code'),
                        'actor1_religion2_code': gdelt_event.get('Actor1Religion2Code'),
                        'actor2_religion1_code': gdelt_event.get('Actor2Religion1Code'),
                        'actor2_religion2_code': gdelt_event.get('Actor2Religion2Code'),
                        'actor1_ethnic_code': gdelt_event.get('Actor1EthnicCode'),
                        'actor2_ethnic_code': gdelt_event.get('Actor2EthnicCode'),

                        # Enhanced Actor Classification
                        'actor1_known_group_code': gdelt_event.get('Actor1KnownGroupCode'),
                        'actor1_type2_code': gdelt_event.get('Actor1Type2Code'),
                        'actor2_known_group_code': gdelt_event.get('Actor2KnownGroupCode'),
                        'actor2_type3_code': gdelt_event.get('Actor2Type3Code'),

                        # Geographic Precision
                        'actor1_geo_adm1': gdelt_event.get('Actor1Geo_ADM1Code'),
                        'actor1_geo_adm2': gdelt_event.get('Actor1Geo_ADM2Code'),
                        'actor1_geo_feature_id': gdelt_event.get('Actor1Geo_FeatureID'),
                        'actor2_geo_adm1': gdelt_event.get('Actor2Geo_ADM1Code'),
                        'actor2_geo_adm2': gdelt_event.get('Actor2Geo_ADM2Code'),
                        'actor2_geo_feature_id': gdelt_event.get('Actor2Geo_FeatureID'),
                        'action_geo_adm1': gdelt_event.get('ActionGeo_ADM1Code'),
                        'action_geo_adm2': gdelt_event.get('ActionGeo_ADM2Code'),
                        'action_geo_feature_id': gdelt_event.get('ActionGeo_FeatureID'),

                        # GKG enrichment data (raw strings, will parse in next plan)
                        'gkg_data': gdelt_event.get('gkg_raw') if 'gkg_raw' in gdelt_event else None,
                    }
                )

                bigquery_events.append(bq_event)
                events_created += 1

            except Exception as e:
                logger.error(f"Failed to map GDELT event: {e}", exc_info=True)
                events_skipped += 1

        # Batch insert to BigQuery
        if bigquery_events:
            try:
                bigquery_service.insert_events(bigquery_events)
                logger.info(f"Inserted {len(bigquery_events)} events to BigQuery")

                # Dispatch LLM analysis for each event
                analyze_task = get_intelligence_task()
                for event in bigquery_events:
                    analyze_task.delay(event.id, model='fast')
                    logger.debug(f"Dispatched LLM analysis for GDELT event {event.id}")

            except Exception as e:
                logger.error(f"Failed to insert events to BigQuery: {e}", exc_info=True)
                raise

        result = {
            'events_created': events_created,
            'events_skipped': events_skipped,
            'events_fetched': len(gdelt_events)
        }

        logger.info(
            f"GDELT sync complete: {events_created} created, {events_skipped} skipped"
        )

        return result

    except Exception as e:
        logger.error(f"GDELT sync failed: {e}", exc_info=True)
        raise


# Deprecated: Old DOC API ingestion task
# from data_pipeline.tasks.gdelt_tasks import ingest_gdelt_events
# Use sync_gdelt_events instead
