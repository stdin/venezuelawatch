"""
GDELT BigQuery sync Cloud Function (standalone, no Django dependencies).

Syncs Venezuela-related events from gdelt-bq.gdeltv2.events to our events table.
HTTP trigger for Cloud Scheduler invocation (every 15 minutes).
"""
import functions_framework
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
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

# GDELT BigQuery project and dataset
GDELT_PROJECT = 'gdelt-bq'
GDELT_DATASET = 'gdeltv2'


def query_gdelt_events(start_time: datetime, end_time: datetime, limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Query GDELT BigQuery for Venezuela-related events.

    Searches for events mentioning Venezuela or Venezuelan entities.
    Returns raw event data from GDELT BigQuery.
    """
    client = bigquery.Client()

    # Query GDELT for Venezuela-related events
    # Use Actor1CountryCode or Actor2CountryCode = 'VE' for Venezuela
    query = f"""
    SELECT
        GLOBALEVENTID,
        SQLDATE,
        Actor1Code,
        Actor1Name,
        Actor2Code,
        Actor2Name,
        EventCode,
        GoldsteinScale,
        AvgTone,
        Actor1CountryCode,
        Actor2CountryCode,
        ActionGeo_CountryCode,
        ActionGeo_Lat,
        ActionGeo_Long,
        SOURCEURL
    FROM `{GDELT_PROJECT}.{GDELT_DATASET}.events`
    WHERE
        (
            Actor1CountryCode = 'VE'
            OR Actor2CountryCode = 'VE'
            OR ActionGeo_CountryCode = 'VE'
            OR LOWER(SOURCEURL) LIKE '%venezuela%'
        )
        AND SQLDATE BETWEEN @start_date AND @end_date
    ORDER BY SQLDATE DESC
    LIMIT @limit
    """

    # Convert datetime to GDELT SQLDATE format (YYYYMMDD as integer)
    start_date = int(start_time.strftime('%Y%m%d'))
    end_date = int(end_time.strftime('%Y%m%d'))

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "INT64", start_date),
            bigquery.ScalarQueryParameter("end_date", "INT64", end_date),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ]
    )

    query_job = client.query(query, job_config=job_config)
    results = query_job.result()

    events = []
    for row in results:
        events.append(dict(row.items()))

    logger.info(f"Queried GDELT: {len(events)} events found")
    return events


def transform_gdelt_to_event(gdelt_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform GDELT raw event to our BigQuery event schema.
    """
    # Generate unique event ID
    event_id = f"gdelt-{gdelt_event['GLOBALEVENTID']}"

    # Parse date (SQLDATE is YYYYMMDD integer)
    sqldate = str(gdelt_event['SQLDATE'])
    mentioned_at = datetime.strptime(sqldate, '%Y%m%d')

    # Build title from actors and event code
    actor1 = gdelt_event.get('Actor1Name') or gdelt_event.get('Actor1Code') or 'Unknown'
    actor2 = gdelt_event.get('Actor2Name') or gdelt_event.get('Actor2Code') or 'Unknown'
    event_code = gdelt_event.get('EventCode', 'Unknown')
    title = f"{actor1} - {actor2} (Event: {event_code})"

    # Build location string
    location_parts = []
    if gdelt_event.get('ActionGeo_CountryCode'):
        location_parts.append(gdelt_event['ActionGeo_CountryCode'])
    if gdelt_event.get('ActionGeo_Lat') and gdelt_event.get('ActionGeo_Long'):
        location_parts.append(f"{gdelt_event['ActionGeo_Lat']}, {gdelt_event['ActionGeo_Long']}")
    location = ' - '.join(location_parts) if location_parts else None

    # Calculate initial risk score from Goldstein Scale and Tone
    # Goldstein: -10 (very negative) to +10 (very positive)
    # Tone: -100 (negative) to +100 (positive)
    goldstein = gdelt_event.get('GoldsteinScale', 0.0)
    tone = gdelt_event.get('AvgTone', 0.0)

    # Invert scales: negative events = higher risk
    # Normalize to 0-100 scale
    goldstein_risk = max(0, min(100, ((-goldstein + 10) / 20) * 100))  # -10 to +10 → 100 to 0
    tone_risk = max(0, min(100, ((-tone + 100) / 200) * 100))  # -100 to +100 → 100 to 0

    # Average risk from both signals
    risk_score = (goldstein_risk * 0.6 + tone_risk * 0.4)  # Weight Goldstein more heavily

    # Determine severity based on risk score
    if risk_score >= 80:
        severity = 'SEV1'
    elif risk_score >= 60:
        severity = 'SEV2'
    elif risk_score >= 40:
        severity = 'SEV3'
    elif risk_score >= 20:
        severity = 'SEV4'
    else:
        severity = 'SEV5'

    # Build metadata with GDELT-specific fields
    metadata = {
        'source': 'gdelt',
        'globaleventid': str(gdelt_event['GLOBALEVENTID']),
        'event_code': event_code,
        'goldstein_scale': goldstein,
        'avg_tone': tone,
        'actor1_code': gdelt_event.get('Actor1Code'),
        'actor1_name': gdelt_event.get('Actor1Name'),
        'actor2_code': gdelt_event.get('Actor2Code'),
        'actor2_name': gdelt_event.get('Actor2Name'),
        'actor1_country': gdelt_event.get('Actor1CountryCode'),
        'actor2_country': gdelt_event.get('Actor2CountryCode'),
    }

    return {
        'id': event_id,
        'source_url': gdelt_event.get('SOURCEURL', ''),
        'mentioned_at': mentioned_at.isoformat(),
        'created_at': datetime.utcnow().isoformat(),
        'title': title,
        'content': f"GDELT Event: {actor1} and {actor2} (Code: {event_code})",
        'source_name': 'GDELT',
        'event_type': 'geopolitical',
        'location': location,
        'risk_score': risk_score,
        'severity': severity,
        'metadata': metadata
    }


@functions_framework.http
def sync_gdelt_events(request: Request):
    """
    HTTP Cloud Function to sync GDELT events.

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

        logger.info(f"Starting GDELT sync (lookback: {lookback_minutes}m)")

        # Initialize clients
        bq_client = BigQueryClient()
        pubsub_client = PubSubClient()

        # Time range for query
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=lookback_minutes)

        # Fetch raw events from GDELT BigQuery
        raw_events = query_gdelt_events(start_time, end_time, limit=1000)
        logger.info(f"Fetched {len(raw_events)} events from GDELT")

        # Transform to our schema
        valid_events = []
        event_ids_for_analysis = []
        events_skipped = 0

        for gdelt_event in raw_events:
            try:
                # Basic validation: must have required fields
                if not gdelt_event.get('GLOBALEVENTID') or not gdelt_event.get('SQLDATE'):
                    events_skipped += 1
                    continue

                # Transform to our schema
                event = transform_gdelt_to_event(gdelt_event)
                valid_events.append(event)
                event_ids_for_analysis.append(event['id'])

            except Exception as e:
                logger.warning(f"Failed to transform event: {e}")
                events_skipped += 1
                continue

        # Batch insert to BigQuery
        if valid_events:
            try:
                bq_client.insert_events(valid_events)
                logger.info(f"Inserted {len(valid_events)} events to BigQuery")

                # Publish event IDs to Pub/Sub for LLM analysis
                pubsub_client.publish_events_for_analysis(event_ids_for_analysis, model='fast')
                logger.info(f"Published {len(event_ids_for_analysis)} events for LLM analysis")

            except Exception as e:
                logger.error(f"Failed to insert events to BigQuery: {e}", exc_info=True)
                return {
                    'error': str(e),
                    'events_created': 0,
                    'events_skipped': events_skipped,
                    'events_fetched': len(raw_events)
                }, 500

        result = {
            'events_created': len(valid_events),
            'events_skipped': events_skipped,
            'events_fetched': len(raw_events)
        }

        logger.info(
            f"GDELT sync complete: {len(valid_events)} created, {events_skipped} skipped"
        )

        return result, 200

    except Exception as e:
        logger.error(f"GDELT sync failed: {e}", exc_info=True)
        return {'error': str(e)}, 500
