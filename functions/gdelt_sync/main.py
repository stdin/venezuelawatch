"""
GDELT BigQuery sync Cloud Function.

Syncs Venezuela-related events from gdelt-bq.gdeltv2 to our events table.
HTTP trigger for Cloud Scheduler invocation (every 15 minutes).
"""
import functions_framework
import logging
import uuid
import pytz
from datetime import datetime, timedelta
from typing import Dict, Any
from flask import Request
from google.cloud import bigquery
import sys
import os

# Add shared utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from bigquery_client import BigQueryClient
from pubsub_client import PubSubClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GDELTBigQueryService:
    """Service for querying GDELT native BigQuery dataset."""

    def __init__(self):
        project_id = os.environ.get('GCP_PROJECT_ID')
        if not project_id:
            raise ValueError("GCP_PROJECT_ID environment variable not set")

        self.client = bigquery.Client(project=project_id)
        self.gdelt_project = "gdelt-bq"
        self.gdelt_dataset = "gdeltv2"

    def get_venezuela_events(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> list:
        """
        Get Venezuela-related events from GDELT native BigQuery.

        Args:
            start_time: Start of time range
            end_time: End of time range
            limit: Max events to return

        Returns:
            List of event dicts with GDELT schema
        """
        query = f"""
            SELECT
                GLOBALEVENTID,
                SQLDATE,
                Actor1Code,
                Actor1Name,
                Actor2Code,
                Actor2Name,
                EventCode,
                QuadClass,
                GoldsteinScale,
                NumMentions,
                NumSources,
                NumArticles,
                AvgTone,
                ActionGeo_FullName,
                ActionGeo_Lat,
                ActionGeo_Long,
                DATEADDED,
                SOURCEURL
            FROM `{self.gdelt_project}.{self.gdelt_dataset}.events_partitioned`
            WHERE _PARTITIONTIME >= @start_time
            AND _PARTITIONTIME < @end_time
            AND (
                ActionGeo_CountryCode = 'VE'
                OR Actor1CountryCode = 'VE'
                OR Actor2CountryCode = 'VE'
            )
            ORDER BY DATEADDED DESC
            LIMIT @limit
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('start_time', 'TIMESTAMP', start_time),
                bigquery.ScalarQueryParameter('end_time', 'TIMESTAMP', end_time),
                bigquery.ScalarQueryParameter('limit', 'INT64', limit)
            ]
        )

        try:
            results = self.client.query(query, job_config=job_config).result()
            events = [dict(row) for row in results]
            logger.info(f"Fetched {len(events)} Venezuela events from GDELT BigQuery")
            return events
        except Exception as e:
            logger.error(f"Failed to query GDELT BigQuery: {e}", exc_info=True)
            raise


@functions_framework.http
def sync_gdelt_events(request: Request):
    """
    HTTP Cloud Function to sync GDELT events from BigQuery.

    Request JSON body:
        {
            "lookback_minutes": 15  // Optional, default: 15
        }

    Returns:
        JSON response with sync statistics
    """
    try:
        # Parse request
        request_json = request.get_json(silent=True) or {}
        lookback_minutes = request_json.get('lookback_minutes', 15)

        logger.info(f"Starting GDELT BigQuery sync (lookback: {lookback_minutes} minutes)")

        # Initialize clients
        bq_client = BigQueryClient()
        pubsub_client = PubSubClient()
        gdelt_service = GDELTBigQueryService()

        # Time range for query
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=lookback_minutes)

        # Fetch Venezuela events from GDELT native BigQuery
        gdelt_events = gdelt_service.get_venezuela_events(
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )

        logger.info(f"Fetched {len(gdelt_events)} events from GDELT BigQuery")

        events_created = 0
        events_skipped = 0
        bigquery_events = []
        event_ids_for_analysis = []

        for gdelt_event in gdelt_events:
            event_id = str(gdelt_event['GLOBALEVENTID'])

            # Check for duplicates
            if bq_client.check_duplicate_event(event_id):
                logger.debug(f"Skipping duplicate GDELT event: {event_id}")
                events_skipped += 1
                continue

            # Map GDELT event to our BigQuery schema
            try:
                # Parse GDELT date format (YYYYMMDDHHMMSS)
                date_str = str(gdelt_event['DATEADDED'])
                event_date = datetime.strptime(date_str[:8], '%Y%m%d').replace(tzinfo=pytz.UTC)

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

                # Create BigQuery event
                bq_event = {
                    'id': event_id,
                    'source_url': gdelt_event.get('SOURCEURL', ''),
                    'mentioned_at': event_date.isoformat(),
                    'created_at': datetime.utcnow().isoformat(),
                    'title': title[:500],
                    'content': f"GDELT Event: {gdelt_event.get('EventCode', '')} - Tone: {gdelt_event.get('AvgTone', 0)}",
                    'source_name': 'GDELT',
                    'event_type': event_type,
                    'location': gdelt_event.get('ActionGeo_FullName', 'Venezuela'),
                    'risk_score': None,
                    'severity': None,
                    'metadata': {
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
                        'action_geo_long': gdelt_event.get('ActionGeo_Long')
                    }
                }

                bigquery_events.append(bq_event)
                event_ids_for_analysis.append(event_id)
                events_created += 1

            except Exception as e:
                logger.error(f"Failed to map GDELT event: {e}", exc_info=True)
                events_skipped += 1

        # Batch insert to BigQuery
        if bigquery_events:
            try:
                bq_client.insert_events(bigquery_events)
                logger.info(f"Inserted {len(bigquery_events)} events to BigQuery")

                # Publish event IDs to Pub/Sub for LLM analysis
                pubsub_client.publish_events_for_analysis(event_ids_for_analysis, model='fast')
                logger.info(f"Published {len(event_ids_for_analysis)} events for LLM analysis")

            except Exception as e:
                logger.error(f"Failed to insert events to BigQuery: {e}", exc_info=True)
                return {
                    'error': str(e),
                    'events_created': 0,
                    'events_skipped': events_skipped,
                    'events_fetched': len(gdelt_events)
                }, 500

        result = {
            'events_created': events_created,
            'events_skipped': events_skipped,
            'events_fetched': len(gdelt_events)
        }

        logger.info(
            f"GDELT sync complete: {events_created} created, {events_skipped} skipped"
        )

        return result, 200

    except Exception as e:
        logger.error(f"GDELT sync failed: {e}", exc_info=True)
        return {'error': str(e)}, 500
