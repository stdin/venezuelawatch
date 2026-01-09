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

from data_pipeline.tasks.base import BaseIngestionTask
from data_pipeline.services.event_mapper import map_gdelt_to_event
from core.models import Event

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
        for article in articles:
            url = article.get('url')
            if not url:
                logger.warning("Skipping GDELT article without URL")
                events_skipped += 1
                continue

            # Check for duplicates by URL in content field
            # Using JSONField query to check if content->>url equals the URL
            existing = Event.objects.filter(
                source='GDELT',
                content__url=url
            ).exists()

            if existing:
                logger.debug(f"Skipping duplicate GDELT article: {url}")
                events_skipped += 1
                continue

            # Map GDELT article to Event
            try:
                event = map_gdelt_to_event(article)

                # Save to database
                with transaction.atomic():
                    event.save()
                    events_created += 1
                    logger.debug(f"Created GDELT event: {event.title[:50]}")

                # Dispatch LLM intelligence analysis (async background task)
                analyze_task = get_intelligence_task()
                analyze_task.delay(event.id, model='fast')
                logger.debug(f"Dispatched LLM analysis for GDELT event {event.id}")

            except Exception as e:
                logger.error(f"Failed to create event from GDELT article: {e}", exc_info=True)
                events_skipped += 1

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
