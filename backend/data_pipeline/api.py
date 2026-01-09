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
    SanctionsMatchSchema
)
from core.models import Event, SanctionsMatch

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
