"""
Data pipeline API endpoints for task triggering and monitoring.

Provides HTTP endpoints for Cloud Scheduler to trigger Celery tasks.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import timedelta
from ninja import Router, Schema, Query
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.db.models import Count

from data_pipeline.tasks.gdelt_tasks import ingest_gdelt_events
from data_pipeline.tasks.reliefweb_tasks import ingest_reliefweb_updates
from data_pipeline.tasks.fred_tasks import ingest_fred_series
from data_pipeline.tasks.comtrade_tasks import ingest_comtrade_trade_data
from data_pipeline.tasks.worldbank_tasks import ingest_worldbank_indicators
from data_pipeline.schemas import (
    RiskIntelligenceEventSchema,
    EventFilterParams,
    SanctionsMatchSchema,
    EntitySchema,
    EntityProfileSchema,
    EntityTimelineResponse,
    EntityMentionSchema
)
from core.models import Event, SanctionsMatch, Entity, EntityMention

logger = logging.getLogger(__name__)

router = Router()
risk_router = Router(tags=["Risk Intelligence"])


# Request/Response schemas
class GDELTTriggerRequest(Schema):
    lookback_minutes: int = 15


class ReliefWebTriggerRequest(Schema):
    lookback_days: int = 1


class FREDTriggerRequest(Schema):
    lookback_days: int = 7


class ComtradeTriggerRequest(Schema):
    lookback_months: int = 3


class WorldBankTriggerRequest(Schema):
    lookback_years: int = 2


class TaskTriggerResponse(Schema):
    status: str
    task_id: str
    task_name: str
    message: Optional[str] = None


@router.post("/trigger/gdelt", response=TaskTriggerResponse)
def trigger_gdelt_ingestion(request: HttpRequest, payload: GDELTTriggerRequest):
    """
    Trigger GDELT ingestion task.

    Called by GCP Cloud Scheduler every 15 minutes.

    Args:
        payload: Request body with lookback_minutes parameter

    Returns:
        TaskTriggerResponse with task ID and status
    """
    logger.info(f"Triggering GDELT ingestion (lookback: {payload.lookback_minutes} minutes)")

    try:
        # Dispatch Celery task asynchronously
        result = ingest_gdelt_events.delay(lookback_minutes=payload.lookback_minutes)

        return TaskTriggerResponse(
            status="dispatched",
            task_id=result.id,
            task_name="gdelt",
            message=f"GDELT ingestion task dispatched with {payload.lookback_minutes} minute lookback"
        )

    except Exception as e:
        logger.error(f"Failed to trigger GDELT ingestion: {e}", exc_info=True)
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=500
        )


@router.post("/trigger/reliefweb", response=TaskTriggerResponse)
def trigger_reliefweb_ingestion(request: HttpRequest, payload: ReliefWebTriggerRequest):
    """
    Trigger ReliefWeb ingestion task.

    Called by GCP Cloud Scheduler daily at 9 AM UTC.

    Args:
        payload: Request body with lookback_days parameter

    Returns:
        TaskTriggerResponse with task ID and status
    """
    logger.info(f"Triggering ReliefWeb ingestion (lookback: {payload.lookback_days} days)")

    try:
        # Dispatch Celery task asynchronously
        result = ingest_reliefweb_updates.delay(lookback_days=payload.lookback_days)

        return TaskTriggerResponse(
            status="dispatched",
            task_id=result.id,
            task_name="reliefweb",
            message=f"ReliefWeb ingestion task dispatched with {payload.lookback_days} day lookback"
        )

    except Exception as e:
        logger.error(f"Failed to trigger ReliefWeb ingestion: {e}", exc_info=True)
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=500
        )


@router.post("/trigger/fred", response=TaskTriggerResponse)
def trigger_fred_ingestion(request: HttpRequest, payload: FREDTriggerRequest):
    """
    Trigger FRED economic series ingestion task.

    Called by GCP Cloud Scheduler daily at 10 AM UTC.

    Args:
        payload: Request body with lookback_days parameter

    Returns:
        TaskTriggerResponse with task ID and status
    """
    logger.info(f"Triggering FRED ingestion (lookback: {payload.lookback_days} days)")

    try:
        # Dispatch Celery task asynchronously
        result = ingest_fred_series.delay(lookback_days=payload.lookback_days)

        return TaskTriggerResponse(
            status="dispatched",
            task_id=result.id,
            task_name="fred",
            message=f"FRED ingestion task dispatched with {payload.lookback_days} day lookback"
        )

    except Exception as e:
        logger.error(f"Failed to trigger FRED ingestion: {e}", exc_info=True)
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=500
        )


@router.post("/trigger/comtrade", response=TaskTriggerResponse)
def trigger_comtrade_ingestion(request: HttpRequest, payload: ComtradeTriggerRequest):
    """
    Trigger UN Comtrade trade data ingestion task.

    Called by GCP Cloud Scheduler monthly on the 1st at 2 AM UTC.

    Args:
        payload: Request body with lookback_months parameter

    Returns:
        TaskTriggerResponse with task ID and status
    """
    logger.info(f"Triggering Comtrade ingestion (lookback: {payload.lookback_months} months)")

    try:
        # Dispatch Celery task asynchronously
        result = ingest_comtrade_trade_data.delay(lookback_months=payload.lookback_months)

        return TaskTriggerResponse(
            status="dispatched",
            task_id=result.id,
            task_name="comtrade",
            message=f"Comtrade ingestion task dispatched with {payload.lookback_months} month lookback"
        )

    except Exception as e:
        logger.error(f"Failed to trigger Comtrade ingestion: {e}", exc_info=True)
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=500
        )


@router.post("/trigger/worldbank", response=TaskTriggerResponse)
def trigger_worldbank_ingestion(request: HttpRequest, payload: WorldBankTriggerRequest):
    """
    Trigger World Bank development indicators ingestion task.

    Called by GCP Cloud Scheduler quarterly on the 1st at 3 AM UTC.

    Args:
        payload: Request body with lookback_years parameter

    Returns:
        TaskTriggerResponse with task ID and status
    """
    logger.info(f"Triggering World Bank ingestion (lookback: {payload.lookback_years} years)")

    try:
        # Dispatch Celery task asynchronously
        result = ingest_worldbank_indicators.delay(lookback_years=payload.lookback_years)

        return TaskTriggerResponse(
            status="dispatched",
            task_id=result.id,
            task_name="worldbank",
            message=f"World Bank ingestion task dispatched with {payload.lookback_years} year lookback"
        )

    except Exception as e:
        logger.error(f"Failed to trigger World Bank ingestion: {e}", exc_info=True)
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=500
        )


@router.get("/health")
def health_check(request: HttpRequest):
    """
    Health check endpoint for Cloud Scheduler.

    Returns:
        Simple health status
    """
    return {"status": "healthy", "service": "data_pipeline"}


# ========================================================================
# Risk Intelligence API Endpoints
# ========================================================================

@risk_router.get("/events", response=List[RiskIntelligenceEventSchema])
def get_risk_intelligence_events(request: HttpRequest, filters: EventFilterParams = Query(...)):
    """
    Get events with risk intelligence filtering and sorting.

    Filters:
    - severity: Comma-separated SEV levels (e.g., "SEV1_CRITICAL,SEV2_HIGH")
    - min_risk_score, max_risk_score: Risk score range (0-100)
    - has_sanctions: Boolean - only events with sanctions matches
    - event_type, source: Filter by type/source
    - days_back: Lookback period (default 30 days)

    Sorting: By risk_score DESC, timestamp DESC
    """

    cutoff_date = timezone.now() - timedelta(days=filters.days_back)
    queryset = Event.objects.filter(timestamp__gte=cutoff_date)

    # Apply filters
    if filters.severity:
        severity_levels = filters.severity.split(',')
        queryset = queryset.filter(severity__in=severity_levels)

    if filters.min_risk_score is not None:
        queryset = queryset.filter(risk_score__gte=filters.min_risk_score)

    if filters.max_risk_score is not None:
        queryset = queryset.filter(risk_score__lte=filters.max_risk_score)

    if filters.has_sanctions:
        queryset = queryset.filter(sanctions_matches__isnull=False).distinct()

    if filters.event_type:
        queryset = queryset.filter(event_type=filters.event_type)

    if filters.source:
        queryset = queryset.filter(source=filters.source)

    # Sort by risk_score DESC, timestamp DESC
    queryset = queryset.order_by('-risk_score', '-timestamp')

    # Pagination
    queryset = queryset[filters.offset:filters.offset + filters.limit]

    # Prefetch sanctions matches
    queryset = queryset.prefetch_related('sanctions_matches')

    # Convert to response schema
    results = []
    for event in queryset:
        # Extract entities from llm_analysis
        entities = {"people": [], "organizations": [], "locations": []}
        if event.llm_analysis and 'entities' in event.llm_analysis:
            entities = event.llm_analysis['entities']

        # Convert sanctions matches
        sanctions = [
            SanctionsMatchSchema(
                entity_name=match.entity_name,
                entity_type=match.entity_type,
                sanctions_list=match.sanctions_list,
                match_score=match.match_score
            )
            for match in event.sanctions_matches.all()
        ]

        results.append(RiskIntelligenceEventSchema(
            id=str(event.id),
            source=event.source,
            event_type=event.event_type,
            timestamp=event.timestamp,
            title=event.title,
            summary=event.summary,
            risk_score=event.risk_score,
            severity=event.severity,
            urgency=event.urgency,
            sentiment=event.sentiment,
            themes=event.themes or [],
            sanctions_matches=sanctions,
            entities=entities
        ))

    return results


@risk_router.get("/sanctions-summary", response=dict)
def get_sanctions_summary(request: HttpRequest, days_back: int = 30):
    """
    Get summary of sanctions matches in recent events.

    Returns:
    {
        "total_events_with_sanctions": int,
        "unique_sanctioned_entities": int,
        "by_entity_type": {"person": X, "organization": Y},
        "by_sanctions_list": {"OFAC-SDN": X, "UN-1267": Y}
    }
    """
    cutoff_date = timezone.now() - timedelta(days=days_back)
    matches = SanctionsMatch.objects.filter(event__timestamp__gte=cutoff_date)

    # Aggregate by entity type
    by_entity_type = {}
    for item in matches.values('entity_type').annotate(count=Count('id')):
        by_entity_type[item['entity_type']] = item['count']

    # Aggregate by sanctions list
    by_sanctions_list = {}
    for item in matches.values('sanctions_list').annotate(count=Count('id')):
        by_sanctions_list[item['sanctions_list']] = item['count']

    return {
        "total_events_with_sanctions": matches.values('event').distinct().count(),
        "unique_sanctioned_entities": matches.values('entity_name').distinct().count(),
        "by_entity_type": by_entity_type,
        "by_sanctions_list": by_sanctions_list
    }


# ========================================================================
# Entity Watch API Endpoints
# ========================================================================

entity_router = Router(tags=["Entity Watch"])


@entity_router.get("/trending", response=List[EntitySchema])
def get_trending_entities(
    request: HttpRequest,
    metric: str = "mentions",  # mentions, risk, sanctions
    limit: int = 50,
    entity_type: Optional[str] = None  # Filter by PERSON, ORGANIZATION, etc.
):
    """
    Get trending entities leaderboard with metric toggle.

    Metrics:
    - mentions: Most mentioned entities (time-decayed score from Redis)
    - risk: Highest risk entities (avg risk_score from events)
    - sanctions: Recently sanctioned entities

    Returns:
        List of entities ordered by selected metric
    """
    from data_pipeline.services.trending_service import TrendingService

    # Get trending entities from TrendingService
    trending = TrendingService.get_trending_entities(metric=metric, limit=limit)

    # Filter by entity_type if provided
    if entity_type:
        trending = [e for e in trending if e['entity_type'] == entity_type]

    # Convert to EntitySchema format (add trending_score and rank)
    results = []
    for idx, entity_data in enumerate(trending, start=1):
        # Get Entity object to fetch all fields
        try:
            entity = Entity.objects.get(id=entity_data['entity_id'])
            results.append(EntitySchema(
                id=str(entity.id),
                canonical_name=entity.canonical_name,
                entity_type=entity.entity_type,
                mention_count=entity.mention_count,
                first_seen=entity.first_seen,
                last_seen=entity.last_seen,
                trending_score=entity_data['score'],
                trending_rank=idx
            ))
        except Entity.DoesNotExist:
            logger.warning(f"Entity {entity_data['entity_id']} not found in database")
            continue

    return results


@entity_router.get("/{entity_id}", response=EntityProfileSchema)
def get_entity_profile(request: HttpRequest, entity_id: str, include_history: bool = False):
    """
    Get detailed entity profile with sanctions status and recent events.

    Args:
        entity_id: UUID of the entity
        include_history: If True, include 30-day historical risk scores

    Returns:
        EntityProfileSchema with full profile details
    """
    from django.shortcuts import get_object_or_404
    from django.db.models import Avg

    entity = get_object_or_404(Entity, id=entity_id)

    # Check sanctions status
    sanctions_status = SanctionsMatch.objects.filter(
        event__entity_mentions__entity=entity
    ).exists()

    # Calculate avg risk score from events
    mentions = EntityMention.objects.filter(entity=entity).select_related('event')
    risk_scores = [m.event.risk_score for m in mentions if m.event.risk_score]
    avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else None

    # Get recent events (last 5)
    recent_mentions = mentions.order_by('-mentioned_at')[:5]
    recent_events = [
        {
            'id': str(m.event.id),
            'title': m.event.title,
            'source': m.event.source,
            'event_type': m.event.event_type,
            'risk_score': m.event.risk_score,
            'severity': m.event.severity,
            'timestamp': m.event.timestamp.isoformat()
        }
        for m in recent_mentions
    ]

    # Get risk history for last 30 days if requested
    risk_history = None
    if include_history:
        cutoff = timezone.now() - timedelta(days=30)
        history_mentions = EntityMention.objects.filter(
            entity=entity,
            mentioned_at__gte=cutoff
        ).select_related('event').order_by('mentioned_at')

        # Aggregate by date
        from collections import defaultdict
        daily_scores = defaultdict(list)
        for m in history_mentions:
            if m.event.risk_score is not None:
                date_str = m.mentioned_at.date().isoformat()
                daily_scores[date_str].append(m.event.risk_score)

        # Calculate daily average
        risk_history = [
            {'date': date, 'risk_score': sum(scores) / len(scores)}
            for date, scores in sorted(daily_scores.items())
        ]

    # Get trending rank from TrendingService
    from data_pipeline.services.trending_service import TrendingService
    trending_rank = TrendingService.get_entity_rank(str(entity.id))

    return EntityProfileSchema(
        id=str(entity.id),
        canonical_name=entity.canonical_name,
        entity_type=entity.entity_type,
        mention_count=entity.mention_count,
        first_seen=entity.first_seen,
        last_seen=entity.last_seen,
        trending_score=None,  # Could fetch from Redis if needed
        trending_rank=trending_rank,
        aliases=entity.aliases,
        metadata=entity.metadata,
        sanctions_status=sanctions_status,
        risk_score=avg_risk,
        recent_events=recent_events,
        risk_history=risk_history
    )


@entity_router.get("/{entity_id}/timeline", response=EntityTimelineResponse)
def get_entity_timeline(request: HttpRequest, entity_id: str, days: int = 30):
    """
    Get entity mention timeline for specified time range.

    Args:
        entity_id: UUID of the entity
        days: Lookback period in days (default 30)

    Returns:
        EntityTimelineResponse with mention history
    """
    from django.shortcuts import get_object_or_404

    entity = get_object_or_404(Entity, id=entity_id)
    cutoff = timezone.now() - timedelta(days=days)

    mentions = EntityMention.objects.filter(
        entity=entity,
        mentioned_at__gte=cutoff
    ).select_related('event').order_by('-mentioned_at')

    mention_schemas = [
        EntityMentionSchema(
            id=str(m.id),
            raw_name=m.raw_name,
            match_score=m.match_score,
            relevance=m.relevance,
            mentioned_at=m.mentioned_at,
            event_summary={
                'id': str(m.event.id),
                'title': m.event.title,
                'source': m.event.source,
                'event_type': m.event.event_type,
                'risk_score': m.event.risk_score,
                'severity': m.event.severity,
                'timestamp': m.event.timestamp.isoformat()
            }
        )
        for m in mentions
    ]

    return EntityTimelineResponse(
        entity_id=str(entity.id),
        canonical_name=entity.canonical_name,
        total_mentions=mentions.count(),
        mentions=mention_schemas,
        time_range={
            'start': cutoff.isoformat(),
            'end': timezone.now().isoformat()
        }
    )
