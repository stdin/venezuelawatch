"""
Celery tasks for intelligence processing using LLM (Claude) for comprehensive analysis.

These tasks analyze Event instances to populate intelligence fields:
- sentiment: Sentiment score from -1 (negative) to +1 (positive)
- risk_score: Risk assessment from 0 (low) to 1 (high)
- entities: List of extracted named entities
- summary: LLM-generated concise summary
- relationships: Entity relationships graph
- themes: Thematic topics
- urgency: Urgency level (low, medium, high, immediate)
- language: Detected language code

Uses comprehensive one-shot LLM analysis for efficiency and multilingual support.
"""
import logging
from typing import Dict, Any, List, Optional
from celery import shared_task, group
from django.utils import timezone
from datetime import timedelta

from core.models import Event
from data_pipeline.tasks.base import BaseIngestionTask
from data_pipeline.services.llm_intelligence import LLMIntelligence

logger = logging.getLogger(__name__)


@shared_task(base=BaseIngestionTask, bind=True)
def analyze_event_intelligence(self, event_id: int, model: str = "fast") -> Dict[str, Any]:
    """
    Analyze a single event using comprehensive LLM intelligence.

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
        event_id: ID of Event to analyze
        model: LLM model tier ("fast", "standard", "premium")

    Returns:
        Dictionary with comprehensive analysis results:
        {
            'event_id': int,
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
        # Fetch event
        event = Event.objects.get(id=event_id)

        # Perform comprehensive LLM analysis (one API call)
        logger.info(f"Performing LLM intelligence analysis for Event {event_id}")
        analysis = LLMIntelligence.analyze_event_model(event, model=model)

        # Extract entity names for backward compatibility
        entities = []
        for person in analysis['entities'].get('people', []):
            entities.append(person['name'])
        for org in analysis['entities'].get('organizations', []):
            entities.append(org['name'])
        for loc in analysis['entities'].get('locations', []):
            entities.append(loc['name'])

        # Update event with all intelligence fields
        event.sentiment = analysis['sentiment']['score']
        event.entities = entities[:20]  # Limit to top 20 for backward compat
        event.summary = analysis['summary']['short']
        event.relationships = analysis['relationships']
        event.themes = analysis['themes']
        event.urgency = analysis['urgency']
        event.language = analysis['language']
        event.llm_analysis = analysis  # Store complete analysis

        # Calculate comprehensive multi-dimensional risk score
        # (combines LLM risk + sanctions + sentiment + urgency + supply chain)
        from data_pipeline.services.risk_scorer import RiskScorer
        comprehensive_risk = RiskScorer.calculate_comprehensive_risk(event)
        event.risk_score = comprehensive_risk

        event.save(update_fields=[
            'sentiment', 'risk_score', 'entities', 'summary',
            'relationships', 'themes', 'urgency', 'language', 'llm_analysis'
        ])

        logger.info(
            f"Event {event_id} intelligence updated: "
            f"sentiment={analysis['sentiment']['score']:.3f}, "
            f"llm_risk={analysis['risk']['score']:.3f}, "
            f"comprehensive_risk={comprehensive_risk:.2f}, "
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
            'entities': entities,
            'summary': analysis['summary']['short'],
            'themes': analysis['themes'],
            'urgency': analysis['urgency'],
            'language': analysis['language'],
            'model_used': analysis['metadata']['model_used'],
            'tokens_used': analysis['metadata']['tokens_used'],
            'status': 'success',
        }

    except Event.DoesNotExist:
        logger.error(f"Event {event_id} not found")
        return {
            'event_id': event_id,
            'status': 'error',
            'error': 'Event not found'
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
    limit: Optional[int] = None,
    reanalyze: bool = False,
) -> Dict[str, Any]:
    """
    Batch analyze multiple events.

    Dispatches individual analysis tasks for events matching filters.

    Args:
        source: Filter by event source (e.g., 'GDELT', 'RELIEFWEB')
        event_type: Filter by event type (e.g., 'NEWS', 'HUMANITARIAN')
        days_back: Only analyze events from last N days (default: 30)
        limit: Maximum number of events to process (default: no limit)
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

    # Build query
    cutoff_date = timezone.now() - timedelta(days=days_back)
    queryset = Event.objects.filter(timestamp__gte=cutoff_date)

    if source:
        queryset = queryset.filter(source=source)

    if event_type:
        queryset = queryset.filter(event_type=event_type)

    # Filter for events without intelligence (unless reanalyzing)
    if not reanalyze:
        queryset = queryset.filter(sentiment__isnull=True)

    # Apply limit
    if limit:
        queryset = queryset[:limit]

    event_ids = list(queryset.values_list('id', flat=True))
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
    logger.info(f"Updating intelligence (LLM) for source={source}, model={model}")

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

            event.save(update_fields=[
                'sentiment', 'risk_score', 'entities', 'summary',
                'relationships', 'themes', 'urgency', 'language', 'llm_analysis'
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
    Update risk scores (and all intelligence) for all events using LLM.

    Note: This now performs comprehensive LLM analysis, not just risk scoring.
    Alias for update_sentiment_scores for backward compatibility.

    Args:
        source: Filter by event source (optional)
        model: LLM model tier ("fast", "standard", "premium")

    Returns:
        Dictionary with update statistics
    """
    logger.info(f"Updating risk scores (comprehensive LLM analysis) for source={source}")
    return update_sentiment_scores(source=source, model=model)


@shared_task(base=BaseIngestionTask, bind=True)
def update_entities(self, source: Optional[str] = None, model: str = "fast") -> Dict[str, Any]:
    """
    Update entity extraction (and all intelligence) for all events using LLM.

    Note: This now performs comprehensive LLM analysis, not just entity extraction.
    Alias for update_sentiment_scores for backward compatibility.

    Args:
        source: Filter by event source (optional)
        model: LLM model tier ("fast", "standard", "premium")

    Returns:
        Dictionary with update statistics
    """
    logger.info(f"Updating entities (comprehensive LLM analysis) for source={source}")
    return update_sentiment_scores(source=source, model=model)


@shared_task(base=BaseIngestionTask, bind=True, name='batch_recalculate_risk_scores')
def batch_recalculate_risk_scores(self, lookback_days: int = 30) -> Dict[str, Any]:
    """
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
    from data_pipeline.services.risk_scorer import RiskScorer

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
