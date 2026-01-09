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
