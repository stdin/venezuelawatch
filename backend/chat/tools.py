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
from django.db.models import Avg, Count
from django.db.models.functions import TruncDate

from core.models import Event, Entity, EntityMention, SanctionsMatch
from data_pipeline.services.trending_service import TrendingService

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

    Args:
        date_from: Start date (ISO format)
        date_to: End date (ISO format)
        risk_threshold: Minimum risk score (0-100)
        source: Data source filter
        limit: Max results

    Returns:
        Dict with events list
    """
    # Parse dates
    if date_from:
        cutoff_date = timezone.datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
    else:
        cutoff_date = timezone.now() - timedelta(days=30)

    if date_to:
        end_date = timezone.datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc)
    else:
        end_date = timezone.now()

    # Build query
    queryset = Event.objects.filter(timestamp__gte=cutoff_date, timestamp__lte=end_date)

    if risk_threshold is not None:
        queryset = queryset.filter(risk_score__gte=risk_threshold)

    if source:
        queryset = queryset.filter(source=source)

    # Order by risk score and timestamp
    queryset = queryset.order_by('-risk_score', '-timestamp')[:limit]

    # Serialize events
    events = []
    for event in queryset:
        events.append({
            "id": str(event.id),
            "title": event.title,
            "date": event.timestamp.isoformat(),
            "source": event.source,
            "risk_score": event.risk_score,
            "severity": event.severity,
            "summary": event.summary or event.title,
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

    Args:
        entity_name: Name of entity to look up

    Returns:
        Dict with entity profile data
    """
    # Find entity by name (fuzzy match)
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

    # Get mentions with events
    mentions = EntityMention.objects.filter(entity=entity).select_related('event')

    # Calculate avg risk score
    risk_scores = [m.event.risk_score for m in mentions if m.event.risk_score]
    avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else None

    # Check sanctions status
    is_sanctioned = SanctionsMatch.objects.filter(
        event__entity_mentions__entity=entity
    ).exists()

    # Get recent mentions (last 5)
    recent_mentions = mentions.order_by('-mentioned_at')[:5]
    recent_events = [
        {
            "title": m.event.title,
            "date": m.event.timestamp.isoformat(),
            "source": m.event.source,
            "risk_score": m.event.risk_score,
        }
        for m in recent_mentions
    ]

    return {
        "id": str(entity.id),
        "name": entity.canonical_name,
        "type": entity.entity_type,
        "mention_count": entity.mention_count,
        "avg_risk_score": avg_risk_score,
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

    Args:
        metric: Ranking metric (mentions, risk, sanctions)
        limit: Max results

    Returns:
        Dict with trending entities list
    """
    # Get trending from TrendingService
    trending = TrendingService.get_trending_entities(metric=metric, limit=limit)

    # Format results
    entities = []
    for item in trending:
        try:
            entity = Entity.objects.get(id=item['entity_id'])
            entities.append({
                "id": str(entity.id),
                "name": entity.canonical_name,
                "type": entity.entity_type,
                "trend_score": item['score'],
                "mention_count": entity.mention_count,
            })
        except Entity.DoesNotExist:
            continue

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

    Args:
        days_back: Number of days to analyze
        event_types: Comma-separated list of event types to filter

    Returns:
        Dict with time-series risk data
    """
    cutoff_date = timezone.now() - timedelta(days=days_back)
    queryset = Event.objects.filter(timestamp__gte=cutoff_date, risk_score__isnull=False)

    if event_types:
        types = [t.strip() for t in event_types.split(',')]
        queryset = queryset.filter(event_type__in=types)

    # Aggregate by day
    daily_trends = queryset.annotate(
        date=TruncDate('timestamp')
    ).values('date').annotate(
        avg_risk=Avg('risk_score'),
        event_count=Count('id')
    ).order_by('date')

    # Format results
    trends = [
        {
            "date": item['date'].isoformat(),
            "avg_risk_score": round(item['avg_risk'], 2),
            "event_count": item['event_count'],
        }
        for item in daily_trends
    ]

    return {
        "trends": trends,
        "count": len(trends),
        "date_range": {
            "from": cutoff_date.isoformat(),
            "to": timezone.now().isoformat(),
        }
    }
