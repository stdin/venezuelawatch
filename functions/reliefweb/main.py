"""
ReliefWeb humanitarian reports Cloud Function.

Fetches Venezuela-related humanitarian reports from ReliefWeb API.
HTTP trigger for Cloud Scheduler invocation (daily).
"""
import functions_framework
import logging
import uuid
import requests
from datetime import datetime, timedelta
from typing import Dict, Any
from flask import Request
from dateutil import parser as date_parser
import sys
import os

# Add shared utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from bigquery_client import BigQueryClient
from pubsub_client import PubSubClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@functions_framework.http
def sync_reliefweb(request: Request):
    """
    HTTP Cloud Function to sync ReliefWeb humanitarian reports.

    Request JSON body:
        {
            "lookback_days": 1  // Optional, default: 1
        }

    Returns:
        JSON response with sync statistics
    """
    try:
        # Parse request
        request_json = request.get_json(silent=True) or {}
        lookback_days = request_json.get('lookback_days', 1)

        logger.info(f"Starting ReliefWeb ingestion (lookback: {lookback_days} days)")

        # Initialize clients
        bq_client = BigQueryClient()
        pubsub_client = PubSubClient()

        # Calculate date filter
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        date_filter = cutoff_date.strftime('%Y-%m-%d')

        # ReliefWeb API v1 endpoint
        api_url = "https://api.reliefweb.int/v1/reports"

        # Query parameters
        params = {
            'appname': 'venezuelawatch',
            'query[value]': 'country.iso3:VEN',
            'filter[field]': 'date.created',
            'filter[value][from]': date_filter,
            'fields[include][]': [
                'id',
                'title',
                'body',
                'body-html',
                'date.created',
                'country.name',
                'source.name',
                'url',
                'file.url',
            ],
            'limit': 100,
        }

        # Fetch from ReliefWeb
        logger.info("Fetching reports from ReliefWeb API")
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        # ReliefWeb response structure: {'data': [...], 'count': N, 'totalCount': N}
        reports = data.get('data', [])
        total_count = data.get('totalCount', 0)

        logger.info(f"Fetched {len(reports)} reports from ReliefWeb (total available: {total_count})")

        events_created = 0
        events_skipped = 0
        bigquery_events = []
        event_ids_for_analysis = []

        # Process each report
        for report_wrapper in reports:
            # ReliefWeb wraps each record: {'id': ..., 'fields': {...}}
            report_id = report_wrapper.get('id')
            fields = report_wrapper.get('fields', {})
            url = fields.get('url')

            if not url:
                logger.warning(f"Skipping ReliefWeb report {report_id} without URL")
                events_skipped += 1
                continue

            # Check for duplicates in BigQuery (last 30 days)
            if bq_client.check_duplicate_by_url(url, days=30):
                logger.debug(f"Skipping duplicate ReliefWeb report: {url}")
                events_skipped += 1
                continue

            # Map ReliefWeb report to BigQuery Event
            try:
                # Parse timestamp
                date_info = fields.get('date', {})
                created_str = date_info.get('created', '')
                if created_str:
                    timestamp = date_parser.parse(created_str)
                else:
                    timestamp = datetime.utcnow()

                # Extract title
                title = fields.get('title', 'Untitled ReliefWeb Report')[:500]

                # Extract body
                body = fields.get('body', '')[:1000]  # Truncate to reasonable length

                # Extract countries and sources
                countries = [c.get('name') for c in fields.get('country', []) if c.get('name')]
                location = ', '.join(countries) if countries else 'Venezuela'

                sources = [s.get('name') for s in fields.get('source', []) if s.get('name')]

                # Generate event ID
                event_id = str(uuid.uuid4())

                # Create BigQuery event
                bq_event = {
                    'id': event_id,
                    'source_url': url,
                    'mentioned_at': timestamp.isoformat(),
                    'created_at': datetime.utcnow().isoformat(),
                    'title': title,
                    'content': body,
                    'source_name': 'ReliefWeb',
                    'event_type': 'humanitarian',
                    'location': location,
                    'risk_score': None,
                    'severity': None,
                    'metadata': {
                        'url': url,
                        'body_html': fields.get('body-html'),
                        'location': location,
                        'sources': sources,
                        'report_id': report_id,
                        'files': fields.get('file', [])
                    }
                }

                bigquery_events.append(bq_event)
                event_ids_for_analysis.append(event_id)
                events_created += 1
                logger.debug(f"Prepared ReliefWeb event: {title[:50]}")

            except Exception as e:
                logger.error(f"Failed to map ReliefWeb report: {e}", exc_info=True)
                events_skipped += 1

        # Batch insert to BigQuery
        if bigquery_events:
            try:
                bq_client.insert_events(bigquery_events)
                logger.info(f"Inserted {len(bigquery_events)} ReliefWeb events to BigQuery")

                # Publish event IDs to Pub/Sub for LLM analysis
                pubsub_client.publish_events_for_analysis(event_ids_for_analysis, model='fast')
                logger.info(f"Published {len(event_ids_for_analysis)} events for LLM analysis")

            except Exception as e:
                logger.error(f"Failed to insert events to BigQuery: {e}", exc_info=True)
                return {
                    'error': str(e),
                    'events_created': 0,
                    'events_skipped': events_skipped,
                    'reports_fetched': len(reports)
                }, 500

        result = {
            'events_created': events_created,
            'events_skipped': events_skipped,
            'reports_fetched': len(reports),
        }

        logger.info(
            f"ReliefWeb ingestion complete: {events_created} created, {events_skipped} skipped"
        )

        return result, 200

    except requests.RequestException as e:
        logger.error(f"ReliefWeb API request failed: {e}", exc_info=True)
        return {'error': f'API request failed: {str(e)}'}, 500

    except Exception as e:
        logger.error(f"ReliefWeb ingestion failed: {e}", exc_info=True)
        return {'error': str(e)}, 500
