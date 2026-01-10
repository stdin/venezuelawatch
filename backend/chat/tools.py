"""
Anthropic tool definitions for VenezuelaWatch data access.

Provides 4 tools for Claude to query events, entities, and risk data:
1. search_events - Query events by filters
2. get_entity_profile - Get detailed entity information
3. get_trending_entities - List trending entities by metric
4. analyze_risk_trends - Get risk score trends over time
"""
import logging
from datetime import timedelta
from typing import List, Dict, Any, Optional
from django.utils import timezone

from core.models import Entity, SanctionsMatch

logger = logging.getLogger(__name__)


# Anthropic tool definitions (used in Claude API calls)
TOOLS = [
    {
        "name": "search_events",
        "description": "Search for VenezuelaWatch events by date range, risk threshold, source, or other filters. Returns events with titles, summaries, risk scores, and metadata.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_from": {
                    "type": "string",
                    "description": "Start date in ISO format (YYYY-MM-DD). Defaults to 30 days ago.",
                },
                "date_to": {
                    "type": "string",
                    "description": "End date in ISO format (YYYY-MM-DD). Defaults to now.",
                },
                "risk_threshold": {
                    "type": "number",
                    "description": "Minimum risk score (0-100). Only return events with risk_score >= this value.",
                },
                "source": {
                    "type": "string",
                    "description": "Filter by data source (GDELT, RELIEFWEB, FRED, UN_COMTRADE, WORLD_BANK).",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return. Defaults to 20.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_entity_profile",
        "description": "Get detailed profile for a specific entity (person, organization, government). Returns entity type, mention count, average risk score, sanctions status, and recent events.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_name": {
                    "type": "string",
                    "description": "Name of the entity to look up (e.g., 'Nicolas Maduro', 'PDVSA', 'Chevron')",
                },
            },
            "required": ["entity_name"],
        },
    },
    {
        "name": "get_trending_entities",
        "description": "Get list of trending entities ranked by mentions, risk score, or sanctions. Returns entities with trending scores and metadata.",
        "input_schema": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": ["mentions", "risk", "sanctions"],
                    "description": "Metric to rank by: mentions (most mentioned), risk (highest risk score), or sanctions (recently sanctioned)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return. Defaults to 20.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "analyze_risk_trends",
        "description": "Analyze risk score trends over time. Returns time-series data showing average risk scores by day for specified period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_back": {
                    "type": "integer",
                    "description": "Number of days to analyze. Defaults to 30.",
                },
                "event_types": {
                    "type": "string",
                    "description": "Comma-separated list of event types to filter by (POLITICAL, ECONOMIC, TRADE, etc.)",
                },
            },
            "required": [],
        },
    },
]


# Tool execution functions
def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool function by name with given input.

    Args:
        tool_name: Name of the tool to execute
        tool_input: Tool parameters as dict

    Returns:
        Tool execution result as dict
    """
    try:
        if tool_name == "search_events":
            return search_events(**tool_input)
        elif tool_name == "get_entity_profile":
            return get_entity_profile(**tool_input)
        elif tool_name == "get_trending_entities":
            return get_trending_entities(**tool_input)
        elif tool_name == "analyze_risk_trends":
            return analyze_risk_trends(**tool_input)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
        return {"error": str(e)}


def search_events(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    risk_threshold: Optional[float] = None,
    source: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """
    Search for events by filters.

    Now queries BigQuery instead of PostgreSQL.

    Args:
        date_from: Start date (ISO format)
        date_to: End date (ISO format)
        risk_threshold: Minimum risk score (0-100)
        source: Data source filter
        limit: Max results

    Returns:
        Dict with events list
    """
    from api.services.bigquery_service import bigquery_service

    # Parse dates
    if date_from:
        cutoff_date = timezone.datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
    else:
        cutoff_date = timezone.now() - timedelta(days=30)

    if date_to:
        end_date = timezone.datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc)
    else:
        end_date = timezone.now()

    # Query BigQuery
    bq_events = bigquery_service.get_recent_events(
        start_date=cutoff_date,
        end_date=end_date,
        min_risk_score=risk_threshold,
        limit=limit
    )

    # Filter by source if specified
    if source:
        bq_events = [e for e in bq_events if e.get('source_name') == source]

    # Serialize events
    events = []
    for event in bq_events:
        events.append({
            "id": str(event.get('id')),
            "title": event.get('title', ''),
            "date": event.get('mentioned_at').isoformat() if event.get('mentioned_at') else None,
            "source": event.get('source_name', ''),
            "risk_score": event.get('risk_score'),
            "severity": event.get('severity'),
            "summary": event.get('content', ''),  # BigQuery uses 'content' field
        })

    return {
        "events": events,
        "count": len(events),
        "date_range": {
            "from": cutoff_date.isoformat(),
            "to": end_date.isoformat(),
        }
    }


def get_entity_profile(entity_name: str) -> Dict[str, Any]:
    """
    Get detailed entity profile.

    Now queries BigQuery for events instead of PostgreSQL.

    Args:
        entity_name: Name of entity to look up

    Returns:
        Dict with entity profile data
    """
    from api.services.bigquery_service import bigquery_service

    # Find entity by name (fuzzy match) - still in PostgreSQL
    # Try exact match first
    entity = Entity.objects.filter(canonical_name__iexact=entity_name).first()

    if not entity:
        # Try alias match
        entity = Entity.objects.filter(aliases__contains=[entity_name]).first()

    if not entity:
        # Try fuzzy match on canonical_name
        from rapidfuzz import process, utils
        from rapidfuzz.distance import JaroWinkler

        all_entities = Entity.objects.all()
        choices = {e.canonical_name: e for e in all_entities}
        normalized_name = utils.default_process(entity_name)

        match = process.extractOne(
            normalized_name,
            choices.keys(),
            scorer=JaroWinkler.similarity,
            processor=utils.default_process,
            score_cutoff=0.75,
        )

        if match:
            entity = choices[match[0]]

    if not entity:
        return {"error": f"Entity not found: {entity_name}"}

    # Get stats from BigQuery
    stats = bigquery_service.get_entity_stats(str(entity.id), days=90)

    # Check sanctions status from PostgreSQL
    is_sanctioned = SanctionsMatch.objects.filter(
        event__entity_mentions__entity=entity
    ).exists()

    # Get recent events from BigQuery (last 5)
    bq_events = bigquery_service.get_entity_events(str(entity.id), limit=5, days=90)
    recent_events = [
        {
            "title": event.get('title', ''),
            "date": event.get('mentioned_at').isoformat() if event.get('mentioned_at') else None,
            "source": event.get('source_name', ''),
            "risk_score": event.get('risk_score'),
        }
        for event in bq_events
    ]

    return {
        "id": str(entity.id),
        "name": entity.canonical_name,
        "type": entity.entity_type,
        "mention_count": entity.mention_count,
        "avg_risk_score": stats['avg_risk_score'],
        "is_sanctioned": is_sanctioned,
        "first_seen": entity.first_seen.isoformat() if entity.first_seen else None,
        "last_seen": entity.last_seen.isoformat() if entity.last_seen else None,
        "recent_mentions": recent_events,
    }


def get_trending_entities(
    metric: str = "mentions",
    limit: int = 20,
) -> Dict[str, Any]:
    """
    Get trending entities by metric.

    Now uses BigQuery instead of Redis/TrendingService.

    Args:
        metric: Ranking metric (mentions, risk, sanctions)
        limit: Max results

    Returns:
        Dict with trending entities list
    """
    from api.services.bigquery_service import bigquery_service

    # Get trending from BigQuery
    trending = bigquery_service.get_entity_trending(metric=metric, limit=limit)

    # Bulk fetch Entity objects from PostgreSQL
    entity_ids = [item['entity_id'] for item in trending]
    entities_map = {str(e.id): e for e in Entity.objects.filter(id__in=entity_ids)}

    # Format results
    entities = []
    for item in trending:
        entity = entities_map.get(item['entity_id'])
        if entity:
            entities.append({
                "id": str(entity.id),
                "name": entity.canonical_name,
                "type": entity.entity_type,
                "trend_score": item['score'],
                "mention_count": entity.mention_count,
            })

    return {
        "entities": entities,
        "count": len(entities),
        "metric": metric,
    }


def analyze_risk_trends(
    days_back: int = 30,
    event_types: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze risk score trends over time.

    Now queries BigQuery instead of PostgreSQL.

    Args:
        days_back: Number of days to analyze
        event_types: Comma-separated list of event types to filter

    Returns:
        Dict with time-series risk data
    """
    from api.services.bigquery_service import bigquery_service

    end_date = timezone.now()
    cutoff_date = end_date - timedelta(days=days_back)

    # Get risk trends from BigQuery
    bq_trends = bigquery_service.get_risk_trends(
        start_date=cutoff_date,
        end_date=end_date,
        bucket_size='DAY'
    )

    # Filter by event types if specified (post-filter, not in BigQuery query)
    # Note: Would need to enhance get_risk_trends() to support event_type filter
    if event_types:
        # For now, skip event_type filtering (would require BigQuery query modification)
        logger.warning(f"Event type filtering not yet supported in BigQuery risk trends")

    # Format results
    trends = [
        {
            "date": item['time_bucket'].isoformat() if hasattr(item['time_bucket'], 'isoformat') else str(item['time_bucket']),
            "avg_risk_score": round(item['avg_risk_score'], 2) if item['avg_risk_score'] else 0,
            "event_count": item['event_count'],
        }
        for item in bq_trends
    ]

    return {
        "trends": trends,
        "count": len(trends),
        "date_range": {
            "from": cutoff_date.isoformat(),
            "to": end_date.isoformat(),
        }
    }
