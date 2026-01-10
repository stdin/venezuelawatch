"""
DEPRECATED - DO NOT USE

**MIGRATION COMPLETE: Phase 18-03 - Celery tasks fully replaced**

These Celery tasks are DEPRECATED and scheduled for removal.
All functionality has been migrated to event-driven Cloud Run handlers in api/views/internal.py:
- analyze_event_intelligence → /api/internal/analyze-intelligence (Cloud Tasks handler)
- batch_analyze_events → Pub/Sub publishing pattern

Celery has been removed from the project. Use Cloud Run handlers instead.
The core LLM analysis logic is unchanged and reused by the new handlers.

These tasks analyze events from BigQuery to populate intelligence fields:
- sentiment: Sentiment score from -1 (negative) to +1 (positive)
- risk_score: Risk assessment from 0 (low) to 1 (high)
- entities: List of extracted named entities
- summary: LLM-generated concise summary
- relationships: Entity relationships graph
- themes: Thematic topics
- urgency: Urgency level (low, medium, high, immediate)
- language: Detected language code

Uses comprehensive one-shot LLM analysis for efficiency and multilingual support.

Migration: Phase 14.3 - Now reads events from BigQuery instead of PostgreSQL.
"""
import logging
from typing import Dict, Any, List, Optional
from celery import shared_task, group
from django.utils import timezone
from datetime import timedelta

from data_pipeline.tasks.base import BaseIngestionTask
from data_pipeline.services.llm_intelligence import LLMIntelligence
from api.services.bigquery_service import bigquery_service

logger = logging.getLogger(__name__)


@shared_task(base=BaseIngestionTask, bind=True)
def analyze_event_intelligence(self, event_id: str, model: str = "fast") -> Dict[str, Any]:
    """
    Analyze a single event using comprehensive LLM intelligence.

    Reads event from BigQuery, performs LLM analysis, and updates event in BigQuery.

    Performs one-shot analysis with Claude to extract:
    1. Sentiment (score, label, confidence, reasoning)
    2. Risk assessment (score, level, factors, mitigation)
    3. Named entities (people, organizations, locations)
    4. Entity relationships
    5. Summary and key points
    6. Themes and topics
    7. Urgency level
    8. Language detection

    Args:
        event_id: ID of Event to analyze (UUID string from BigQuery)
        model: LLM model tier ("fast", "standard", "premium")

    Returns:
        Dictionary with comprehensive analysis results:
        {
            'event_id': str,
            'sentiment': float,
            'risk_score': float,
            'entities': List[str],
            'summary': str,
            'themes': List[str],
            'urgency': str,
            'language': str,
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
                'status': 'error',
                'error': 'Event not found'
            }

        # Create mock event object for LLMIntelligence compatibility
        from types import SimpleNamespace
        mock_event = SimpleNamespace(
            title=event.get('title', ''),
            content=event.get('content', ''),
            source=event.get('source_name', ''),
            event_type=event.get('event_type', ''),
            timestamp=event.get('mentioned_at')
        )

        # Perform comprehensive LLM analysis (one API call)
        logger.info(f"Performing LLM intelligence analysis for Event {event_id}")
        analysis = LLMIntelligence.analyze_event_model(mock_event, model=model)

        # Extract entity names for backward compatibility
        entities = []
        for person in analysis['entities'].get('people', []):
            entities.append(person['name'])
        for org in analysis['entities'].get('organizations', []):
            entities.append(org['name'])
        for loc in analysis['entities'].get('locations', []):
            entities.append(loc['name'])

        # Calculate comprehensive multi-dimensional risk score
        # Note: RiskScorer expects an Event model, so we'll use just the LLM risk for now
        # TODO: Adapt RiskScorer to work with dict-based events
        comprehensive_risk = analysis['risk']['score'] * 100  # Scale 0-1 to 0-100

        # Classify severity
        # Note: ImpactClassifier also expects Event model, using LLM analysis for now
        # TODO: Adapt ImpactClassifier to work with dict-based events
        severity = 'SEV3'  # Default medium severity

        # Update event in BigQuery with all intelligence fields
        bigquery_service.update_event_analysis(
            event_id=event_id,
            sentiment=analysis['sentiment']['score'],
            risk_score=comprehensive_risk,
            entities=entities[:20],  # Limit to top 20
            summary=analysis['summary']['short'],
            relationships=analysis['relationships'],
            themes=analysis['themes'],
            urgency=analysis['urgency'],
            language=analysis['language'],
            llm_analysis=analysis,
            severity=severity
        )

        logger.info(
            f"Event {event_id} intelligence updated: "
            f"sentiment={analysis['sentiment']['score']:.3f}, "
            f"llm_risk={analysis['risk']['score']:.3f}, "
            f"comprehensive_risk={comprehensive_risk:.2f}, "
            f"severity={severity}, "
            f"entities={len(entities)}, "
            f"language={analysis['language']}, "
            f"urgency={analysis['urgency']}, "
            f"model={analysis['metadata']['model_used']}"
        )

        return {
            'event_id': event_id,
            'sentiment': analysis['sentiment']['score'],
            'llm_risk': analysis['risk']['score'],
            'comprehensive_risk_score': comprehensive_risk,
            'severity': severity,
            'entities': entities,
            'summary': analysis['summary']['short'],
            'themes': analysis['themes'],
            'urgency': analysis['urgency'],
            'language': analysis['language'],
            'model_used': analysis['metadata']['model_used'],
            'tokens_used': analysis['metadata']['tokens_used'],
            'status': 'success',
        }

    except Exception as e:
        logger.error(f"Failed to analyze Event {event_id}: {e}", exc_info=True)
        return {
            'event_id': event_id,
            'status': 'error',
            'error': str(e)
        }


@shared_task(base=BaseIngestionTask, bind=True)
def batch_analyze_events(
    self,
    source: Optional[str] = None,
    event_type: Optional[str] = None,
    days_back: int = 30,
    limit: int = 100,
    reanalyze: bool = False,
) -> Dict[str, Any]:
    """
    Batch analyze multiple events from BigQuery.

    Dispatches individual analysis tasks for events matching filters.

    Args:
        source: Filter by event source (e.g., 'GDELT', 'RELIEFWEB')
        event_type: Filter by event type (e.g., 'NEWS', 'HUMANITARIAN')
        days_back: Only analyze events from last N days (default: 30)
        limit: Maximum number of events to process (default: 100)
        reanalyze: Re-analyze events that already have intelligence fields (default: False)

    Returns:
        Dictionary with batch processing results:
        {
            'total_events': int,
            'tasks_dispatched': int,
            'source': str | None,
            'event_type': str | None,
        }
    """
    logger.info(
        f"Starting batch intelligence analysis: "
        f"source={source}, event_type={event_type}, days_back={days_back}, "
        f"limit={limit}, reanalyze={reanalyze}"
    )

    # Get events from BigQuery
    cutoff_date = timezone.now() - timedelta(days=days_back)

    if reanalyze:
        # Get all events (even those with analysis)
        from google.cloud import bigquery as bq
        query = f"""
            SELECT id
            FROM `{bigquery_service.project_id}.{bigquery_service.dataset_id}.events`
            WHERE mentioned_at >= @cutoff_date
        """
        params = [bq.ScalarQueryParameter('cutoff_date', 'TIMESTAMP', cutoff_date)]

        if source:
            query += " AND source_name = @source"
            params.append(bq.ScalarQueryParameter('source', 'STRING', source))

        if event_type:
            query += " AND event_type = @event_type"
            params.append(bq.ScalarQueryParameter('event_type', 'STRING', event_type))

        query += " ORDER BY mentioned_at DESC LIMIT @limit"
        params.append(bq.ScalarQueryParameter('limit', 'INT64', limit))

        job_config = bq.QueryJobConfig(query_parameters=params)
        results = bigquery_service.client.query(query, job_config=job_config).result()
        event_ids = [row.id for row in results]
    else:
        # Get only unanalyzed events
        event_ids = bigquery_service.get_unanalyzed_events(
            cutoff_date=cutoff_date,
            source=source,
            event_type=event_type,
            limit=limit
        )

    total_events = len(event_ids)

    logger.info(f"Found {total_events} events to analyze")

    if total_events == 0:
        return {
            'total_events': 0,
            'tasks_dispatched': 0,
            'source': source,
            'event_type': event_type,
        }

    # Dispatch analysis tasks (group for parallel execution)
    job = group(
        analyze_event_intelligence.s(event_id)
        for event_id in event_ids
    )

    result = job.apply_async()

    logger.info(f"Dispatched {total_events} event analysis tasks")

    return {
        'total_events': total_events,
        'tasks_dispatched': total_events,
        'source': source,
        'event_type': event_type,
        'group_id': result.id,
    }


@shared_task(base=BaseIngestionTask, bind=True)
def update_sentiment_scores(self, source: Optional[str] = None, model: str = "fast") -> Dict[str, Any]:
    """
    **DEPRECATED:** Use batch_analyze_events instead (now queries BigQuery).

    This legacy function still queries PostgreSQL Event model.
    It will be removed in a future phase once PostgreSQL Event table is fully deprecated.

    Update intelligence (including sentiment) for all events using LLM.

    Note: This now performs comprehensive LLM analysis, not just sentiment.
    It updates sentiment, risk, entities, summary, etc. in one pass.

    Useful for:
    - Backfilling intelligence for existing events
    - Re-analyzing after LLM improvements

    Args:
        source: Filter by event source (optional)
        model: LLM model tier ("fast", "standard", "premium")

    Returns:
        Dictionary with update statistics
    """
    logger.warning(
        "update_sentiment_scores is DEPRECATED. Use batch_analyze_events for BigQuery events."
    )
    logger.info(f"Updating intelligence (LLM) for source={source}, model={model}")

    # Import here to avoid issues if Event model is removed
    from core.models import Event

    # Build query
    queryset = Event.objects.all()
    if source:
        queryset = queryset.filter(source=source)

    total_events = queryset.count()
    updated_count = 0
    error_count = 0

    logger.info(f"Processing {total_events} events")

    for event in queryset.iterator(chunk_size=100):
        try:
            # Use comprehensive LLM analysis
            analysis = LLMIntelligence.analyze_event_model(event, model=model)

            # Extract entity names
            entities = []
            for person in analysis['entities'].get('people', []):
                entities.append(person['name'])
            for org in analysis['entities'].get('organizations', []):
                entities.append(org['name'])
            for loc in analysis['entities'].get('locations', []):
                entities.append(loc['name'])

            # Update all fields
            event.sentiment = analysis['sentiment']['score']
            event.risk_score = analysis['risk']['score']
            event.entities = entities[:20]
            event.summary = analysis['summary']['short']
            event.relationships = analysis['relationships']
            event.themes = analysis['themes']
            event.urgency = analysis['urgency']
            event.language = analysis['language']
            event.llm_analysis = analysis

            # Classify severity
            from data_pipeline.services.impact_classifier import ImpactClassifier
            severity = ImpactClassifier.classify_severity(event)
            event.severity = severity

            event.save(update_fields=[
                'sentiment', 'risk_score', 'entities', 'summary',
                'relationships', 'themes', 'urgency', 'language', 'llm_analysis', 'severity'
            ])
            updated_count += 1

            if updated_count % 100 == 0:
                logger.info(f"Updated intelligence for {updated_count}/{total_events} events")

        except Exception as e:
            logger.error(f"Failed to update intelligence for Event {event.id}: {e}")
            error_count += 1

    logger.info(
        f"Intelligence update complete: {updated_count} updated, {error_count} errors"
    )

    return {
        'total_events': total_events,
        'updated': updated_count,
        'errors': error_count,
        'source': source,
        'model': model,
    }


@shared_task(base=BaseIngestionTask, bind=True)
def update_risk_scores(self, source: Optional[str] = None, model: str = "fast") -> Dict[str, Any]:
    """
    **DEPRECATED:** Use batch_analyze_events instead (now queries BigQuery).

    Update risk scores (and all intelligence) for all events using LLM.

    Note: This now performs comprehensive LLM analysis, not just risk scoring.
    Alias for update_sentiment_scores for backward compatibility.

    Args:
        source: Filter by event source (optional)
        model: LLM model tier ("fast", "standard", "premium")

    Returns:
        Dictionary with update statistics
    """
    logger.warning(
        "update_risk_scores is DEPRECATED. Use batch_analyze_events for BigQuery events."
    )
    logger.info(f"Updating risk scores (comprehensive LLM analysis) for source={source}")
    return update_sentiment_scores(source=source, model=model)


@shared_task(base=BaseIngestionTask, bind=True)
def update_entities(self, source: Optional[str] = None, model: str = "fast") -> Dict[str, Any]:
    """
    **DEPRECATED:** Use batch_analyze_events instead (now queries BigQuery).

    Update entity extraction (and all intelligence) for all events using LLM.

    Note: This now performs comprehensive LLM analysis, not just entity extraction.
    Alias for update_sentiment_scores for backward compatibility.

    Args:
        source: Filter by event source (optional)
        model: LLM model tier ("fast", "standard", "premium")

    Returns:
        Dictionary with update statistics
    """
    logger.warning(
        "update_entities is DEPRECATED. Use batch_analyze_events for BigQuery events."
    )
    logger.info(f"Updating entities (comprehensive LLM analysis) for source={source}")
    return update_sentiment_scores(source=source, model=model)


@shared_task(base=BaseIngestionTask, bind=True, name='batch_recalculate_risk_scores')
def batch_recalculate_risk_scores(self, lookback_days: int = 30) -> Dict[str, Any]:
    """
    **DEPRECATED:** PostgreSQL Event queries no longer supported.

    This task queries PostgreSQL Event model which is deprecated.
    Risk scores are now calculated during intelligence analysis and stored in BigQuery metadata.

    Recalculate risk scores for recent events using new multi-dimensional model.

    This task updates risk_score field for events that already have LLM analysis,
    applying the new RiskAggregator composite scoring (LLM risk + sanctions +
    sentiment + urgency + supply chain).

    Useful after upgrading risk scoring logic to apply new methodology to
    existing events without re-running full LLM analysis.

    Args:
        lookback_days: Recalculate for events from last N days (default: 30)

    Returns:
        Dictionary with recalculation statistics:
        {
            'total_events': int,
            'updated': int,
            'errors': int,
            'lookback_days': int,
        }
    """
    logger.warning(
        "batch_recalculate_risk_scores is DEPRECATED. "
        "Risk scores are calculated during intelligence analysis in BigQuery."
    )
    from data_pipeline.services.risk_scorer import RiskScorer
    from core.models import Event

    logger.info(f"Batch recalculating risk scores for events from last {lookback_days} days")

    cutoff_date = timezone.now() - timedelta(days=lookback_days)
    events = Event.objects.filter(
        created_at__gte=cutoff_date,
        llm_analysis__isnull=False
    )

    total_events = events.count()
    updated_count = 0
    error_count = 0

    logger.info(f"Found {total_events} events with LLM analysis to recalculate")

    for event in events.iterator(chunk_size=100):
        try:
            old_score = event.risk_score
            new_score = RiskScorer.calculate_comprehensive_risk(event)
            event.risk_score = new_score
            event.save(update_fields=['risk_score'])
            updated_count += 1

            if updated_count % 100 == 0:
                logger.info(
                    f"Recalculated {updated_count}/{total_events} events "
                    f"(avg change: {abs(new_score - old_score) if old_score else 0:.2f})"
                )

        except Exception as e:
            logger.error(f"Failed to recalculate risk for Event {event.id}: {e}")
            error_count += 1

    logger.info(
        f"Risk score recalculation complete: {updated_count} updated, {error_count} errors"
    )

    return {
        'total_events': total_events,
        'updated': updated_count,
        'errors': error_count,
        'lookback_days': lookback_days,
    }


@shared_task(base=BaseIngestionTask, bind=True, name='batch_classify_severity')
def batch_classify_severity(self, lookback_days: int = 30) -> Dict[str, Any]:
    """
    **DEPRECATED:** PostgreSQL Event queries no longer supported.

    This task queries PostgreSQL Event model which is deprecated.
    Severity is now calculated during intelligence analysis and stored in BigQuery metadata.

    Classify severity for recent events using ImpactClassifier.

    This task classifies severity (SEV1-5) for events based on NCISS-style
    weighted multi-criteria scoring (scope, duration, reversibility, economic impact).

    Useful after adding severity feature to classify existing events without
    re-running full LLM intelligence analysis.

    Args:
        lookback_days: Classify events from last N days (default: 30)

    Returns:
        Dictionary with classification statistics:
        {
            'total_events': int,
            'classified': int,
            'errors': int,
            'distribution': Dict[str, int],  # SEV level counts
            'lookback_days': int,
        }
    """
    logger.warning(
        "batch_classify_severity is DEPRECATED. "
        "Severity is calculated during intelligence analysis in BigQuery."
    )
    from collections import defaultdict
    from data_pipeline.services.impact_classifier import ImpactClassifier
    from core.models import Event

    logger.info(f"Batch classifying severity for events from last {lookback_days} days")

    cutoff_date = timezone.now() - timedelta(days=lookback_days)
    events = Event.objects.filter(
        created_at__gte=cutoff_date,
        severity__isnull=True  # Only events without severity
    )

    total_events = events.count()
    classified_count = 0
    error_count = 0
    severity_counts = defaultdict(int)

    logger.info(f"Found {total_events} events without severity classification")

    for event in events.iterator(chunk_size=100):
        try:
            severity = ImpactClassifier.classify_severity(event)
            event.severity = severity
            event.save(update_fields=['severity'])

            classified_count += 1
            severity_counts[severity] += 1

            if classified_count % 100 == 0:
                logger.info(f"Classified {classified_count}/{total_events} events")

        except Exception as e:
            logger.error(f"Failed to classify severity for Event {event.id}: {e}")
            error_count += 1

    logger.info(
        f"Severity classification complete: {classified_count} classified, {error_count} errors"
    )
    logger.info(f"Distribution: {dict(severity_counts)}")

    return {
        'total_events': total_events,
        'classified': classified_count,
        'errors': error_count,
        'distribution': dict(severity_counts),
        'lookback_days': lookback_days,
    }
