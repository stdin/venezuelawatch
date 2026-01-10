"""
GDELT (Global Database of Events, Language, and Tone) ingestion tasks.

Fetches Venezuela-related news articles from GDELT DOC API v2.0.
Updates every 15 minutes in real-time mode.
"""
import logging
import requests
from typing import Dict, Any
from celery import shared_task
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from google.cloud import bigquery

from data_pipeline.tasks.base import BaseIngestionTask
from data_pipeline.services.event_mapper import map_gdelt_to_event
from core.models import Event
from api.bigquery_models import Event as BigQueryEvent
from api.services.bigquery_service import bigquery_service

logger = logging.getLogger(__name__)


# Import intelligence task for LLM analysis
def get_intelligence_task():
    """Lazy import to avoid circular dependency."""
    from data_pipeline.tasks.intelligence_tasks import analyze_event_intelligence
    return analyze_event_intelligence


@shared_task(base=BaseIngestionTask, bind=True)
def ingest_gdelt_events(self, lookback_minutes: int = 15) -> Dict[str, Any]:
    """
    Ingest Venezuela-related events from GDELT DOC API.

    GDELT DOC API v2.0 provides near real-time news article tracking.
    Query: 'venezuela' OR 'maduro' OR 'caracas'
    Timespan: Last N minutes (default 15)

    Args:
        lookback_minutes: How many minutes to look back (default: 15)

    Returns:
        {
            'events_created': int,
            'events_skipped': int,  # Duplicates
            'articles_fetched': int,
        }
    """
    logger.info(f"Starting GDELT ingestion (lookback: {lookback_minutes} minutes)")

    # GDELT DOC API v2.0 endpoint
    # mode=artlist: Return article list (not full text)
    # format=json: JSON response
    # query: Search terms (Venezuela-related) - OR queries must be in parentheses
    # timespan: Xm for minutes, Xh for hours, Xd for days
    api_url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        'query': '(venezuela OR maduro OR caracas)',  # Parentheses required for OR queries
        'mode': 'artlist',
        'format': 'json',
        'timespan': f'{lookback_minutes}m',
        'maxrecords': 250,  # GDELT allows up to 250 per request
    }

    try:
        # Fetch from GDELT
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()

        # Log response for debugging
        logger.debug(f"GDELT API response status: {response.status_code}")
        logger.debug(f"GDELT API response text (first 500 chars): {response.text[:500]}")

        # Handle empty response
        if not response.text or response.text.strip() == '':
            logger.warning("GDELT API returned empty response - no articles found")
            return {
                'events_created': 0,
                'events_skipped': 0,
                'articles_fetched': 0,
            }

        try:
            data = response.json()
        except ValueError as e:
            logger.error(f"Failed to parse GDELT JSON response. Response text: {response.text[:1000]}")
            raise

        # GDELT response structure: {'articles': [...]}
        articles = data.get('articles', [])
        logger.info(f"Fetched {len(articles)} articles from GDELT")

        events_created = 0
        events_skipped = 0

        # Process each article
        bigquery_events = []
        for article in articles:
            url = article.get('url')
            if not url:
                logger.warning("Skipping GDELT article without URL")
                events_skipped += 1
                continue

            # Check for duplicates in BigQuery (last 7 days)
            try:
                query = f"""
                    SELECT COUNT(*) as count
                    FROM `{settings.GCP_PROJECT_ID}.{settings.BIGQUERY_DATASET}.events`
                    WHERE source_url = @url
                    AND mentioned_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
                """
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter('url', 'STRING', url)
                    ]
                )
                results = bigquery_service.client.query(query, job_config=job_config).result()
                row = list(results)[0]
                if row.count > 0:
                    logger.debug(f"Skipping duplicate GDELT article: {url}")
                    events_skipped += 1
                    continue
            except Exception as e:
                logger.error(f"Failed to check for duplicate in BigQuery: {e}")
                # Continue with insert - better to have duplicate than skip valid event
                pass

            # Map GDELT article to BigQueryEvent
            try:
                # Get Django event for mapping convenience
                django_event = map_gdelt_to_event(article)

                # Create BigQueryEvent from mapped data
                bq_event = BigQueryEvent(
                    source_url=article.get('url'),
                    mentioned_at=django_event.timestamp,
                    created_at=timezone.now(),
                    title=django_event.title,
                    content=article.get('title', ''),  # Use article title as content
                    source_name='GDELT',
                    event_type=django_event.event_type.lower() if django_event.event_type else None,
                    location='Venezuela',  # All GDELT queries are Venezuela-specific
                    risk_score=None,  # Computed in Phase 4
                    severity=None,  # Computed in Phase 4
                    metadata=django_event.content  # Store full GDELT data in metadata
                )

                bigquery_events.append(bq_event)
                events_created += 1
                logger.debug(f"Prepared GDELT event for BigQuery: {bq_event.title[:50]}")

            except Exception as e:
                logger.error(f"Failed to create BigQuery event from GDELT article: {e}", exc_info=True)
                events_skipped += 1

        # Batch insert to BigQuery
        if bigquery_events:
            try:
                bigquery_service.insert_events(bigquery_events)
                logger.info(f"Inserted {len(bigquery_events)} events to BigQuery")

                # Dispatch LLM intelligence analysis for each event (async background task)
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
            'articles_fetched': len(articles),
        }

        logger.info(
            f"GDELT ingestion complete: {events_created} created, {events_skipped} skipped"
        )

        return result

    except requests.RequestException as e:
        logger.error(f"GDELT API request failed: {e}", exc_info=True)
        # BaseIngestionTask will retry automatically
        raise

    except Exception as e:
        logger.error(f"GDELT ingestion failed: {e}", exc_info=True)
        raise
