"""
Celery tasks for sanctions screening.

Provides daily refresh task to re-screen recent events for sanctions matches.
Ensures sanctions data stays current as new sanctions are added.
"""
import logging
from typing import Dict, Any
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from core.models import Event, SanctionsMatch
from data_pipeline.tasks.base import BaseIngestionTask
from data_pipeline.services.sanctions_screener import SanctionsScreener

logger = logging.getLogger(__name__)


@shared_task(base=BaseIngestionTask, bind=True, name='refresh_sanctions_screening')
def refresh_sanctions_screening(self, lookback_days: int = 7) -> Dict[str, Any]:
    """
    Re-screen recent events for sanctions matches.

    Runs daily to catch new sanctions additions and updates.
    Only screens events with LLM entity extraction (llm_analysis populated).

    Args:
        lookback_days: Number of days to look back (default: 7)

    Returns:
        Dictionary with screening statistics:
        {
            'screened': int (number of events screened),
            'matches_found': int (events with sanctions matches),
            'total_matches': int (total SanctionsMatch records created),
            'lookback_days': int,
            'status': 'success' | 'error'
        }
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=lookback_days)

        # Get recent events with LLM analysis (exclude those without entities)
        recent_events = Event.objects.filter(
            created_at__gte=cutoff_date
        ).exclude(
            llm_analysis__isnull=True
        )

        total_events = recent_events.count()
        logger.info(
            f"Starting sanctions screening refresh: "
            f"{total_events} events from last {lookback_days} days"
        )

        screened_count = 0
        matches_found = 0
        total_matches = 0

        for event in recent_events:
            # Delete old sanctions matches for this event (refresh)
            old_matches = SanctionsMatch.objects.filter(event=event).count()
            SanctionsMatch.objects.filter(event=event).delete()

            # Re-screen event
            sanctions_score = SanctionsScreener.screen_event_entities(event)

            # Count new matches
            new_matches = SanctionsMatch.objects.filter(event=event).count()
            total_matches += new_matches

            if sanctions_score > 0.0:
                matches_found += 1

            screened_count += 1

            # Log progress every 100 events
            if screened_count % 100 == 0:
                logger.info(
                    f"Sanctions screening progress: {screened_count}/{total_events} "
                    f"({matches_found} matches)"
                )

        logger.info(
            f"Sanctions screening refresh complete: "
            f"{screened_count} events screened, "
            f"{matches_found} events with matches, "
            f"{total_matches} total SanctionsMatch records"
        )

        return {
            'screened': screened_count,
            'matches_found': matches_found,
            'total_matches': total_matches,
            'lookback_days': lookback_days,
            'status': 'success'
        }

    except Exception as e:
        logger.error(f"Sanctions screening refresh failed: {e}", exc_info=True)
        return {
            'screened': 0,
            'matches_found': 0,
            'total_matches': 0,
            'lookback_days': lookback_days,
            'status': 'error',
            'error': str(e)
        }


@shared_task(base=BaseIngestionTask, bind=True, name='screen_event_sanctions')
def screen_event_sanctions(self, event_id: int) -> Dict[str, Any]:
    """
    Screen a single event for sanctions matches.

    Useful for immediate screening of new events as they are ingested.

    Args:
        event_id: ID of Event to screen

    Returns:
        Dictionary with screening results:
        {
            'event_id': int,
            'sanctions_score': float (0.0 or 1.0),
            'matches_count': int,
            'status': 'success' | 'error'
        }
    """
    try:
        # Fetch event
        event = Event.objects.get(id=event_id)

        # Check if event has LLM analysis
        if not event.llm_analysis or 'entities' not in event.llm_analysis:
            logger.warning(
                f"Event {event_id} has no entity data. "
                f"Run LLM analysis first before sanctions screening."
            )
            return {
                'event_id': event_id,
                'sanctions_score': 0.0,
                'matches_count': 0,
                'status': 'skipped',
                'reason': 'no_entity_data'
            }

        # Screen event
        logger.info(f"Screening Event {event_id} for sanctions matches")
        sanctions_score = SanctionsScreener.screen_event_entities(event)

        # Count matches
        matches_count = SanctionsMatch.objects.filter(event=event).count()

        logger.info(
            f"Event {event_id} sanctions screening complete: "
            f"score={sanctions_score}, matches={matches_count}"
        )

        return {
            'event_id': event_id,
            'sanctions_score': sanctions_score,
            'matches_count': matches_count,
            'status': 'success'
        }

    except Event.DoesNotExist:
        logger.error(f"Event {event_id} not found")
        return {
            'event_id': event_id,
            'sanctions_score': 0.0,
            'matches_count': 0,
            'status': 'error',
            'error': 'event_not_found'
        }

    except Exception as e:
        logger.error(f"Event {event_id} sanctions screening failed: {e}", exc_info=True)
        return {
            'event_id': event_id,
            'sanctions_score': 0.0,
            'matches_count': 0,
            'status': 'error',
            'error': str(e)
        }
