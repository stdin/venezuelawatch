"""
GDELT BigQuery sync Cloud Function using GdeltAdapter.

Syncs Venezuela-related events from gdelt-bq.gdeltv2 to our events table.
HTTP trigger for Cloud Scheduler invocation (every 15 minutes).
"""
import functions_framework
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from flask import Request
import sys
import os

# Add backend code to path (for adapter access)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

# Django setup for adapter imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venezuelawatch.settings')
import django
django.setup()

from data_pipeline.adapters.gdelt_adapter import GdeltAdapter

# Add shared utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from bigquery_client import BigQueryClient
from pubsub_client import PubSubClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@functions_framework.http
def sync_gdelt_events(request: Request):
    """
    HTTP Cloud Function to sync GDELT events using GdeltAdapter.

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

        logger.info(f"Starting GDELT sync via GdeltAdapter (lookback: {lookback_minutes}m)")

        # Initialize adapter and clients
        adapter = GdeltAdapter()
        bq_client = BigQueryClient()
        pubsub_client = PubSubClient()

        # Time range for query
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=lookback_minutes)

        # Fetch raw events using adapter
        raw_events = adapter.fetch(start_time, end_time, limit=1000)
        logger.info(f"Fetched {len(raw_events)} events from GDELT")

        # Transform to BigQuery schema using adapter
        bq_events = adapter.transform(raw_events)
        logger.info(f"Transformed {len(bq_events)} events to BigQuery schema")

        # Validate and filter events
        valid_events = []
        events_skipped = 0
        event_ids_for_analysis = []

        for event in bq_events:
            is_valid, error = adapter.validate(event)
            if is_valid:
                # Convert BigQueryEvent dataclass to dict for insertion
                event_dict = {
                    'id': event.id,
                    'source_url': event.source_url,
                    'mentioned_at': event.mentioned_at.isoformat(),
                    'created_at': event.created_at.isoformat(),
                    'title': event.title,
                    'content': event.content,
                    'source_name': event.source_name,
                    'event_type': event.event_type,
                    'location': event.location,
                    'risk_score': event.risk_score,
                    'severity': event.severity,
                    'metadata': event.metadata
                }
                valid_events.append(event_dict)
                event_ids_for_analysis.append(event.id)
            else:
                logger.debug(f"Skipping event {event.id}: {error}")
                events_skipped += 1

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
