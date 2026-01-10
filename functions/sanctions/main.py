"""
OFAC Sanctions screening Cloud Function.

Refreshes sanctions screening for recent events.
HTTP trigger for Cloud Scheduler invocation (daily).

Note: This function reads events from BigQuery and screens for sanctions matches.
The actual sanctions matching logic is still in Django (core.models.SanctionsMatch).
This Cloud Function serves as a lightweight orchestrator that:
1. Fetches recent events from BigQuery
2. Triggers the existing Django sanctions screening endpoint via HTTP
"""
import functions_framework
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from flask import Request
import requests
import sys
import os

# Add shared utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from bigquery_client import BigQueryClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@functions_framework.http
def sync_sanctions(request: Request):
    """
    HTTP Cloud Function to refresh sanctions screening for recent events.

    Request JSON body:
        {
            "lookback_days": 7  // Optional, default: 7
        }

    Returns:
        JSON response with screening statistics

    Note: This function orchestrates sanctions screening by calling the Django
    sanctions screening endpoint for each event. The actual OFAC SDN list matching
    logic remains in the Django backend (SanctionsScreener service).
    """
    try:
        # Parse request
        request_json = request.get_json(silent=True) or {}
        lookback_days = request_json.get('lookback_days', 7)

        logger.info(f"Starting sanctions screening refresh (lookback: {lookback_days} days)")

        # Initialize BigQuery client
        bq_client = BigQueryClient()

        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

        # Get Django backend URL from environment
        django_backend_url = os.environ.get('DJANGO_BACKEND_URL')
        if not django_backend_url:
            logger.error("DJANGO_BACKEND_URL environment variable not set")
            return {
                'error': 'DJANGO_BACKEND_URL not configured',
                'screened': 0
            }, 500

        # Query recent events with LLM analysis from BigQuery
        query = f"""
            SELECT id, metadata
            FROM `{bq_client.project_id}.{bq_client.dataset_id}.events`
            WHERE mentioned_at >= @cutoff_date
            AND metadata IS NOT NULL
            AND JSON_VALUE(metadata, '$.llm_analysis') IS NOT NULL
            ORDER BY mentioned_at DESC
        """

        from google.cloud import bigquery
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('cutoff_date', 'TIMESTAMP', cutoff_date)
            ]
        )

        results = bq_client.client.query(query, job_config=job_config).result()
        event_rows = list(results)
        total_events = len(event_rows)

        logger.info(
            f"Found {total_events} events from last {lookback_days} days with LLM analysis"
        )

        screened_count = 0
        matches_found = 0
        errors_count = 0

        # Screen each event by calling Django endpoint
        for row in event_rows:
            event_id = row.id

            try:
                # Call Django sanctions screening endpoint
                # This endpoint will:
                # 1. Fetch event from BigQuery
                # 2. Run SanctionsScreener.screen_event_entities()
                # 3. Create SanctionsMatch records in PostgreSQL
                # 4. Return screening results
                response = requests.post(
                    f"{django_backend_url}/api/sanctions/screen-event/",
                    json={'event_id': event_id},
                    timeout=30
                )
                response.raise_for_status()

                result = response.json()
                screened_count += 1

                if result.get('sanctions_score', 0.0) > 0.0:
                    matches_found += 1
                    logger.info(f"Event {event_id} has sanctions matches")

                # Log progress every 100 events
                if screened_count % 100 == 0:
                    logger.info(
                        f"Sanctions screening progress: {screened_count}/{total_events} "
                        f"({matches_found} matches)"
                    )

            except requests.RequestException as e:
                logger.error(f"Failed to screen event {event_id}: {e}")
                errors_count += 1
                # Continue with next event
                continue

        result = {
            'screened': screened_count,
            'matches_found': matches_found,
            'errors': errors_count,
            'lookback_days': lookback_days,
            'status': 'success'
        }

        logger.info(
            f"Sanctions screening complete: {screened_count} events screened, "
            f"{matches_found} with matches, {errors_count} errors"
        )

        return result, 200

    except Exception as e:
        logger.error(f"Sanctions screening failed: {e}", exc_info=True)
        return {
            'error': str(e),
            'screened': 0,
            'status': 'error'
        }, 500
