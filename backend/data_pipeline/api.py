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

from data_pipeline.tasks.gdelt_sync_task import sync_gdelt_events
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
        result = sync_gdelt_events.delay(lookback_minutes=payload.lookback_minutes)

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

    Now queries BigQuery for time-series event data instead of PostgreSQL.

    Filters:
    - severity: Comma-separated SEV levels (e.g., "SEV1_CRITICAL,SEV2_HIGH")
    - min_risk_score, max_risk_score: Risk score range (0-100)
    - has_sanctions: Boolean - only events with sanctions matches
    - event_type, source: Filter by type/source
    - days_back: Lookback period (default 30 days)

    Sorting: By risk_score DESC, timestamp DESC
    """
    from api.services.bigquery_service import bigquery_service

    # Calculate date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=filters.days_back)

    # Query BigQuery for events
    # Note: BigQuery filters handle severity, risk_score, event_type
    # has_sanctions filter requires separate PostgreSQL query (sanctions not in BigQuery yet)
    bq_events = bigquery_service.get_recent_events(
        start_date=start_date,
        end_date=end_date,
        event_type=filters.event_type if filters.event_type else None,
        severity=filters.severity if filters.severity and ',' not in filters.severity else None,
        min_risk_score=filters.min_risk_score,
        max_risk_score=filters.max_risk_score,
        limit=filters.limit + filters.offset  # Fetch enough for pagination
    )

    # Handle comma-separated severity levels (BigQuery filter only handles single value)
    if filters.severity and ',' in filters.severity:
        severity_levels = set(filters.severity.split(','))
        bq_events = [e for e in bq_events if e.get('severity') in severity_levels]

    # Handle source filter
    if filters.source:
        bq_events = [e for e in bq_events if e.get('source_name') == filters.source]

    # Handle has_sanctions filter (query PostgreSQL for sanctions matches)
    if filters.has_sanctions:
        # Get event IDs that have sanctions matches from PostgreSQL
        sanctioned_event_ids = set(
            SanctionsMatch.objects.values_list('event_id', flat=True).distinct()
        )
        # Convert to strings for comparison
        sanctioned_event_ids = {str(eid) for eid in sanctioned_event_ids}
        bq_events = [e for e in bq_events if e.get('id') in sanctioned_event_ids]

    # Apply pagination
    bq_events = bq_events[filters.offset:filters.offset + filters.limit]

    # Convert to response schema
    results = []
    for event in bq_events:
        event_id = event.get('id')

        # Extract entities from metadata (was llm_analysis in PostgreSQL)
        entities = {"people": [], "organizations": [], "locations": []}
        metadata = event.get('metadata')
        if metadata and isinstance(metadata, dict) and 'entities' in metadata:
            entities = metadata['entities']

        # Fetch sanctions matches from PostgreSQL (if any)
        sanctions = []
        if filters.has_sanctions or event_id:
            sanctions_matches = SanctionsMatch.objects.filter(event_id=event_id)
            sanctions = [
                SanctionsMatchSchema(
                    entity_name=match.entity_name,
                    entity_type=match.entity_type,
                    sanctions_list=match.sanctions_list,
                    match_score=match.match_score
                )
                for match in sanctions_matches
            ]

        results.append(RiskIntelligenceEventSchema(
            id=str(event_id),
            source=event.get('source_name', ''),
            event_type=event.get('event_type', ''),
            timestamp=event.get('mentioned_at'),
            title=event.get('title', ''),
            summary=event.get('content', ''),  # BigQuery uses 'content', PostgreSQL used 'summary'
            risk_score=event.get('risk_score'),
            severity=event.get('severity'),
            urgency=metadata.get('urgency') if metadata else None,
            sentiment=metadata.get('sentiment') if metadata else None,
            themes=metadata.get('themes', []) if metadata else [],
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

    Now uses BigQuery for trending calculations instead of Redis.

    Metrics:
    - mentions: Most mentioned entities (time-decayed score with 7-day half-life)
    - risk: Highest risk entities (avg risk_score from events)
    - sanctions: Recently sanctioned entities

    Returns:
        List of entities ordered by selected metric
    """
    from api.services.bigquery_service import bigquery_service

    # Get trending entities from BigQuery
    trending = bigquery_service.get_entity_trending(metric=metric, limit=limit)

    # Bulk fetch Entity objects from PostgreSQL
    entity_ids = [item['entity_id'] for item in trending]
    entities = Entity.objects.filter(id__in=entity_ids)
    entity_map = {str(e.id): e for e in entities}

    # Convert to EntitySchema format (add trending_score and rank)
    results = []
    for idx, entity_data in enumerate(trending, start=1):
        entity_id = entity_data['entity_id']

        # Get Entity object
        entity = entity_map.get(entity_id)
        if not entity:
            logger.warning(f"Entity {entity_id} not found in PostgreSQL")
            continue

        # Filter by entity_type if provided
        if entity_type and entity.entity_type != entity_type:
            continue

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

    return results


@entity_router.get("/{entity_id}", response=EntityProfileSchema)
def get_entity_profile(request: HttpRequest, entity_id: str, include_history: bool = False):
    """
    Get detailed entity profile with sanctions status and recent events.

    Now queries BigQuery for events and mentions instead of PostgreSQL.

    Args:
        entity_id: UUID of the entity
        include_history: If True, include 30-day historical risk scores

    Returns:
        EntityProfileSchema with full profile details
    """
    from django.shortcuts import get_object_or_404
    from api.services.bigquery_service import bigquery_service

    # Get Entity object from PostgreSQL (reference data)
    entity = get_object_or_404(Entity, id=entity_id)

    # Get stats from BigQuery
    stats = bigquery_service.get_entity_stats(str(entity.id), days=90)

    # Check sanctions status from PostgreSQL (sanctions not in BigQuery yet)
    sanctions_status = SanctionsMatch.objects.filter(
        event__entity_mentions__entity=entity
    ).exists()

    # Get recent events from BigQuery (last 5)
    bq_events = bigquery_service.get_entity_events(str(entity.id), limit=5, days=90)
    recent_events = [
        {
            'id': str(event.get('id')),
            'title': event.get('title', ''),
            'source': event.get('source_name', ''),
            'event_type': event.get('event_type', ''),
            'risk_score': event.get('risk_score'),
            'severity': event.get('severity'),
            'timestamp': event.get('mentioned_at').isoformat() if event.get('mentioned_at') else None
        }
        for event in bq_events
    ]

    # Get risk history for last 30 days if requested
    risk_history = None
    if include_history:
        # Query BigQuery for historical events
        history_events = bigquery_service.get_entity_events(str(entity.id), limit=1000, days=30)

        # Aggregate by date
        from collections import defaultdict
        daily_scores = defaultdict(list)
        for event in history_events:
            risk_score = event.get('risk_score')
            mentioned_at = event.get('mentioned_at')
            if risk_score is not None and mentioned_at:
                date_str = mentioned_at.date().isoformat()
                daily_scores[date_str].append(risk_score)

        # Calculate daily average
        risk_history = [
            {'date': date, 'risk_score': sum(scores) / len(scores)}
            for date, scores in sorted(daily_scores.items())
        ]

    # Note: trending_rank removed (Redis deprecated, would need separate BigQuery query)
    # Can be added back if needed by calling get_entity_trending and finding entity position

    return EntityProfileSchema(
        id=str(entity.id),
        canonical_name=entity.canonical_name,
        entity_type=entity.entity_type,
        mention_count=entity.mention_count,
        first_seen=entity.first_seen,
        last_seen=entity.last_seen,
        trending_score=None,  # Not included in profile view
        trending_rank=None,  # Not included in profile view (Redis deprecated)
        aliases=entity.aliases,
        metadata=entity.metadata,
        sanctions_status=sanctions_status,
        risk_score=stats['avg_risk_score'],
        recent_events=recent_events,
        risk_history=risk_history
    )


@entity_router.get("/{entity_id}/timeline", response=EntityTimelineResponse)
def get_entity_timeline(request: HttpRequest, entity_id: str, days: int = 30):
    """
    Get entity mention timeline for specified time range.

    Now queries BigQuery for entity mentions instead of PostgreSQL.

    Args:
        entity_id: UUID of the entity
        days: Lookback period in days (default 30)

    Returns:
        EntityTimelineResponse with mention history
    """
    from django.shortcuts import get_object_or_404
    from api.services.bigquery_service import bigquery_service

    # Get Entity object from PostgreSQL (reference data)
    entity = get_object_or_404(Entity, id=entity_id)
    cutoff = timezone.now() - timedelta(days=days)

    # Get events from BigQuery
    bq_events = bigquery_service.get_entity_events(str(entity.id), limit=1000, days=days)

    # Convert to mention schemas
    # Note: BigQuery doesn't store raw_name, match_score, relevance (only in EntityMention in BigQuery)
    # For simplicity, we'll reconstruct from events
    mention_schemas = [
        EntityMentionSchema(
            id=event.get('id'),  # Use event ID as mention ID
            raw_name=entity.canonical_name,  # Approximate (actual raw_name not in events table)
            match_score=1.0,  # Not available from events table
            relevance=None,  # Not available from events table
            mentioned_at=event.get('mentioned_at'),
            event_summary={
                'id': str(event.get('id')),
                'title': event.get('title', ''),
                'source': event.get('source_name', ''),
                'event_type': event.get('event_type', ''),
                'risk_score': event.get('risk_score'),
                'severity': event.get('severity'),
                'timestamp': event.get('mentioned_at').isoformat() if event.get('mentioned_at') else None
            }
        )
        for event in bq_events
    ]

    return EntityTimelineResponse(
        entity_id=str(entity.id),
        canonical_name=entity.canonical_name,
        total_mentions=len(mention_schemas),
        mentions=mention_schemas,
        time_range={
            'start': cutoff.isoformat(),
            'end': timezone.now().isoformat()
        }
    )


@entity_router.get("/{entity_id}/sources")
def get_entity_sources(request: HttpRequest, entity_id: str):
    """
    Get all events across all sources mentioning this canonical entity.

    Returns events from multiple data sources (gdelt, google_trends, world_bank, sec_edgar)
    that mention this canonical entity, grouped by source.

    Uses metadata.linked_entities array in BigQuery to find events linked to this entity.

    Args:
        entity_id: Canonical entity UUID

    Returns:
        Dict with entity info, aliases, and events grouped by source
    """
    from django.shortcuts import get_object_or_404
    from api.services.bigquery_service import bigquery_service
    from data_pipeline.models import CanonicalEntity, EntityAlias
    from django.conf import settings

    # Validate entity exists
    entity = get_object_or_404(CanonicalEntity, id=entity_id)

    # Get all aliases for this entity
    aliases = EntityAlias.objects.filter(canonical_entity=entity)

    # Query BigQuery for events with this entity in metadata.linked_entities
    # Use JSON_EXTRACT_ARRAY and UNNEST to search JSON array
    project = settings.GCP_PROJECT_ID
    dataset = settings.BIGQUERY_DATASET

    query = f"""
    SELECT event_id, title, source, published_at, metadata, country
    FROM `{project}.{dataset}.events_partitioned`
    WHERE '{entity_id}' IN UNNEST(JSON_EXTRACT_ARRAY(metadata, '$.linked_entities'))
    ORDER BY published_at DESC
    LIMIT 100
    """

    try:
        # Execute BigQuery query
        job_config = bigquery_service.client.query(query)
        results = job_config.result()
        events = [dict(row) for row in results]
    except Exception as e:
        logger.error(f"BigQuery query failed for entity {entity_id}: {e}", exc_info=True)
        events = []

    # Group by source
    by_source = {}
    for event in events:
        source = event.get('source', 'unknown')
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(event)

    return {
        "entity": {
            "id": str(entity.id),
            "name": entity.primary_name,
            "type": entity.entity_type,
        },
        "aliases": [
            {
                "alias": a.alias,
                "source": a.source,
                "confidence": a.confidence,
                "resolution_method": a.resolution_method,
            }
            for a in aliases
        ],
        "events_by_source": by_source,
        "total_events": len(events),
    }
