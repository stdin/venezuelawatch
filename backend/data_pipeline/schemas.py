"""
API schemas for data pipeline endpoints.

Pydantic/Ninja schemas for request/response validation.
"""
from ninja import Schema
from typing import List, Optional
from datetime import datetime


class SanctionsMatchSchema(Schema):
    """Schema for sanctions match data in event responses."""
    entity_name: str
    entity_type: str
    sanctions_list: str
    match_score: float


class RiskIntelligenceEventSchema(Schema):
    """
    Response schema for risk intelligence events.

    Includes risk scores, severity, sanctions matches, and key metadata
    for dashboard filtering and visualization.
    """
    id: str
    source: str
    event_type: str
    timestamp: datetime
    title: str
    summary: Optional[str]
    risk_score: Optional[float]
    severity: Optional[str]
    urgency: Optional[str]
    sentiment: Optional[float]
    themes: List[str]
    sanctions_matches: List[SanctionsMatchSchema]
    entities: dict  # {people: [], organizations: [], locations: []}


class EventFilterParams(Schema):
    """
    Query parameters for filtering risk intelligence events.

    Supports filtering by severity, risk score range, sanctions,
    event type, source, and time range.
    """
    severity: Optional[str] = None  # e.g., "SEV1_CRITICAL,SEV2_HIGH"
    min_risk_score: Optional[float] = None
    max_risk_score: Optional[float] = None
    has_sanctions: Optional[bool] = None
    event_type: Optional[str] = None
    source: Optional[str] = None
    days_back: int = 30
    limit: int = 100
    offset: int = 0


# ========================================================================
# Entity API Schemas
# ========================================================================

class EntitySchema(Schema):
    """
    Basic entity info for leaderboard.

    Used in trending entity lists with minimal data for performance.
    """
    id: str
    canonical_name: str
    entity_type: str  # PERSON, ORGANIZATION, GOVERNMENT, LOCATION
    mention_count: int
    first_seen: datetime
    last_seen: datetime
    trending_score: Optional[float] = None  # From Redis, may be null
    trending_rank: Optional[int] = None  # 1-indexed rank


class EntityProfileSchema(Schema):
    """
    Detailed entity profile.

    Extends EntitySchema with additional metadata for profile view.
    """
    id: str
    canonical_name: str
    entity_type: str
    mention_count: int
    first_seen: datetime
    last_seen: datetime
    trending_score: Optional[float] = None
    trending_rank: Optional[int] = None
    # Additional profile fields
    aliases: List[str]
    metadata: Optional[dict] = None
    sanctions_status: bool  # True if any sanctions matches
    risk_score: Optional[float] = None  # Avg risk from events
    recent_events: List[dict]  # Last 5 events mentioning entity


class EntityMentionSchema(Schema):
    """
    Entity mention details for timeline.

    Links entity to specific event with mention metadata.
    """
    id: str
    raw_name: str
    match_score: float
    relevance: Optional[float] = None
    mentioned_at: datetime
    event_summary: dict  # {id, title, source, event_type, risk_score, severity, timestamp}


class EntityTimelineResponse(Schema):
    """
    Timeline aggregation response.

    Shows entity's mention history over time.
    """
    entity_id: str
    canonical_name: str
    total_mentions: int
    mentions: List[EntityMentionSchema]
    time_range: dict  # {start: datetime, end: datetime}
