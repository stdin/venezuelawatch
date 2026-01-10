"""
Celery tasks for sanctions screening.

Provides daily refresh task to re-screen recent events for sanctions matches.
Ensures sanctions data stays current as new sanctions are added.

Migration: Phase 14.3 - Now reads events from BigQuery instead of PostgreSQL.
"""
import logging
from typing import Dict, Any
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from core.models import SanctionsMatch
from data_pipeline.tasks.base import BaseIngestionTask
from data_pipeline.services.sanctions_screener import SanctionsScreener
from api.services.bigquery_service import bigquery_service

logger = logging.getLogger(__name__)


@shared_task(base=BaseIngestionTask, bind=True, name='refresh_sanctions_screening')
def refresh_sanctions_screening(self, lookback_days: int = 7) -> Dict[str, Any]:
    """
    Re-screen recent events for sanctions matches.

    Reads events from BigQuery, screens for sanctions, and stores matches in PostgreSQL.
    Runs daily to catch new sanctions additions and updates.
    Only screens events with LLM entity extraction (metadata.llm_analysis populated).

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
        from google.cloud import bigquery as bq

        cutoff_date = timezone.now() - timedelta(days=lookback_days)

        # Get recent events from BigQuery with LLM analysis
        query = f"""
            SELECT id, metadata
            FROM `{bigquery_service.project_id}.{bigquery_service.dataset_id}.events`
            WHERE mentioned_at >= @cutoff_date
            AND metadata IS NOT NULL
            AND JSON_VALUE(metadata, '$.llm_analysis') IS NOT NULL
            ORDER BY mentioned_at DESC
        """

        job_config = bq.QueryJobConfig(
            query_parameters=[
                bq.ScalarQueryParameter('cutoff_date', 'TIMESTAMP', cutoff_date)
            ]
        )

        results = bigquery_service.client.query(query, job_config=job_config).result()
        event_rows = list(results)
        total_events = len(event_rows)

        logger.info(
            f"Starting sanctions screening refresh: "
            f"{total_events} events from last {lookback_days} days"
        )

        screened_count = 0
        matches_found = 0
        total_matches = 0

        for row in event_rows:
            event_id = row.id
            metadata = row.metadata if hasattr(row, 'metadata') else {}

            # Create mock event object for SanctionsScreener compatibility
            # SanctionsScreener expects event.llm_analysis field
            from types import SimpleNamespace
            mock_event = SimpleNamespace(
                id=event_id,
                llm_analysis=metadata.get('llm_analysis', {})
            )

            # Delete old sanctions matches for this event (refresh)
            # Note: SanctionsMatch stores event_id as string (BigQuery event ID)
            from django.db.models import Q
            old_matches_count = SanctionsMatch.objects.filter(
                Q(event_id=event_id) | Q(event__id=event_id)
            ).count()
            SanctionsMatch.objects.filter(
                Q(event_id=event_id) | Q(event__id=event_id)
            ).delete()

            # Re-screen event
            sanctions_score = SanctionsScreener.screen_event_entities(mock_event)

            # Count new matches
            new_matches_count = SanctionsMatch.objects.filter(
                Q(event_id=event_id) | Q(event__id=event_id)
            ).count()
            total_matches += new_matches_count

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
def screen_event_sanctions(self, event_id: str) -> Dict[str, Any]:
    """
    Screen a single event for sanctions matches.

    Reads event from BigQuery and screens for sanctions matches.
    Useful for immediate screening of new events as they are ingested.

    Args:
        event_id: ID of Event to screen (UUID string from BigQuery)

    Returns:
        Dictionary with screening results:
        {
            'event_id': str,
            'sanctions_score': float (0.0 or 1.0),
            'matches_count': int,
            'status': 'success' | 'error'
        }
    """
    try:
        # Fetch event from BigQuery
        event = bigquery_service.get_event_by_id(event_id)

        if not event:
            logger.error(f"Event {event_id} not found in BigQuery")
            return {
                'event_id': event_id,
                'sanctions_score': 0.0,
                'matches_count': 0,
                'status': 'error',
                'error': 'event_not_found'
            }

        # Check if event has LLM analysis
        metadata = event.get('metadata', {})
        llm_analysis = metadata.get('llm_analysis', {}) if metadata else {}

        if not llm_analysis or 'entities' not in llm_analysis:
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

        # Create mock event object for SanctionsScreener compatibility
        from types import SimpleNamespace
        mock_event = SimpleNamespace(
            id=event_id,
            llm_analysis=llm_analysis
        )

        # Screen event
        logger.info(f"Screening Event {event_id} for sanctions matches")
        sanctions_score = SanctionsScreener.screen_event_entities(mock_event)

        # Count matches
        from django.db.models import Q
        matches_count = SanctionsMatch.objects.filter(
            Q(event_id=event_id) | Q(event__id=event_id)
        ).count()

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

    except Exception as e:
        logger.error(f"Event {event_id} sanctions screening failed: {e}", exc_info=True)
        return {
            'event_id': event_id,
            'sanctions_score': 0.0,
            'matches_count': 0,
            'status': 'error',
            'error': str(e)
        }
