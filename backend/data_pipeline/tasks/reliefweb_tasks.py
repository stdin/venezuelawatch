"""
ReliefWeb humanitarian reports ingestion tasks.

Fetches Venezuela-related humanitarian reports from ReliefWeb API.
Updates daily to capture UN OCHA reports, NGO updates, and disaster information.
"""
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from data_pipeline.tasks.base import BaseIngestionTask
from data_pipeline.services.event_mapper import map_reliefweb_to_event
from core.models import Event

logger = logging.getLogger(__name__)


@shared_task(base=BaseIngestionTask, bind=True)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.RequestException, requests.Timeout)),
    reraise=True,
)
def ingest_reliefweb_updates(self, lookback_days: int = 1) -> Dict[str, Any]:
    """
    Ingest Venezuela humanitarian reports from ReliefWeb API.

    ReliefWeb provides UN OCHA reports, NGO updates, and disaster information.
    Rate limit: 1000 requests/day (daily polling is safe).

    API Documentation: https://apidoc.reliefweb.int/

    Args:
        lookback_days: How many days to look back (default: 1)

    Returns:
        {
            'events_created': int,
            'events_skipped': int,  # Duplicates
            'reports_fetched': int,
        }
    """
    logger.info(f"Starting ReliefWeb ingestion (lookback: {lookback_days} days)")

    # Calculate date filter
    cutoff_date = timezone.now() - timedelta(days=lookback_days)
    date_filter = cutoff_date.strftime('%Y-%m-%d')

    # ReliefWeb API v1 endpoint
    api_url = "https://api.reliefweb.int/v1/reports"

    # Query parameters
    # appname: Required identification header
    # query: Search for Venezuela (country.iso3:VEN)
    # filter: Date filter for recent reports
    # fields: Specify which fields to include
    # limit: Results per request (max 1000)
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
        'limit': 100,  # Start with 100, increase if needed
    }

    try:
        # Fetch from ReliefWeb
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        # ReliefWeb response structure: {'data': [...], 'count': N, 'totalCount': N}
        reports = data.get('data', [])
        total_count = data.get('totalCount', 0)

        logger.info(f"Fetched {len(reports)} reports from ReliefWeb (total available: {total_count})")

        events_created = 0
        events_skipped = 0

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

            # Check for duplicates by URL in content field
            existing = Event.objects.filter(
                source='RELIEFWEB',
                content__url=url
            ).exists()

            if existing:
                logger.debug(f"Skipping duplicate ReliefWeb report: {url}")
                events_skipped += 1
                continue

            # Map ReliefWeb report to Event
            try:
                event = map_reliefweb_to_event(report_wrapper)

                # Save to database
                with transaction.atomic():
                    event.save()
                    events_created += 1
                    logger.debug(f"Created ReliefWeb event: {event.title[:50]}")

            except Exception as e:
                logger.error(f"Failed to create event from ReliefWeb report: {e}", exc_info=True)
                events_skipped += 1

        result = {
            'events_created': events_created,
            'events_skipped': events_skipped,
            'reports_fetched': len(reports),
        }

        logger.info(
            f"ReliefWeb ingestion complete: {events_created} created, {events_skipped} skipped"
        )

        return result

    except requests.RequestException as e:
        logger.error(f"ReliefWeb API request failed: {e}", exc_info=True)
        # Tenacity will retry automatically (3 attempts with exponential backoff)
        raise

    except Exception as e:
        logger.error(f"ReliefWeb ingestion failed: {e}", exc_info=True)
        raise
