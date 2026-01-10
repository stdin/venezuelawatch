"""
BigQuery dataclass models for VenezuelaWatch time-series data.

These are NOT Django models - they're Python dataclasses that convert to BigQuery row format.
Use these with api.services.bigquery_service for inserting/querying BigQuery data.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any, List
import uuid


@dataclass
class Event:
    """
    Canonical event time-series record for BigQuery.

    Core model with 30+ fields from platform design:
    - Temporal: event_timestamp, ingested_at
    - Classification: category, subcategory, event_type
    - Location: country_code, admin1, admin2, latitude, longitude
    - Magnitude: magnitude_raw, magnitude_unit, magnitude_norm
    - Direction: direction (POSITIVE/NEGATIVE/NEUTRAL)
    - Tone: tone_raw, tone_norm
    - Confidence: num_sources, source_credibility, confidence
    - Actors: actor1/2 name/type
    - Commodities/sectors arrays

    Enhancement arrays (future-proof for Phase 26+):
    - themes: GKG V2Themes (2300+ categories)
    - quotations: Who-said-what tracking
    - gcam_scores: GCAM emotional dimensions
    - entity_relationships: Actor network graphs
    - related_events: Narrative lineage tracking
    """

    # Required fields
    source_url: str
    event_timestamp: datetime  # When event occurred (renamed from mentioned_at)
    created_at: datetime

    # Identity
    id: Optional[str] = None
    source: Optional[str] = None  # 'gdelt' | 'acled' | 'world_bank' | etc.
    source_event_id: Optional[str] = None

    # Temporal (additional)
    ingested_at: Optional[datetime] = None

    # Classification (10-category taxonomy)
    category: Optional[str] = None  # POLITICAL | CONFLICT | ECONOMIC | TRADE | REGULATORY | INFRASTRUCTURE | HEALTHCARE | SOCIAL | ENVIRONMENTAL | ENERGY
    subcategory: Optional[str] = None
    event_type: Optional[str] = None

    # Location
    country_code: Optional[str] = "VE"
    admin1: Optional[str] = None  # State/province
    admin2: Optional[str] = None  # City/district
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None  # Legacy field

    # Magnitude
    magnitude_raw: Optional[float] = None  # Native value (deaths, %, Goldstein, etc.)
    magnitude_unit: Optional[str] = None  # 'fatalities' | 'percent' | 'goldstein' | 'usd' | 'interest_score'
    magnitude_norm: Optional[float] = None  # 0-1 normalized

    # Sentiment/Direction
    direction: Optional[str] = None  # POSITIVE | NEGATIVE | NEUTRAL
    tone_raw: Optional[float] = None
    tone_norm: Optional[float] = None  # 0-1 normalized (1 = most negative)

    # Confidence
    num_sources: Optional[int] = None
    source_credibility: Optional[float] = None  # 0-1 source tier weight
    confidence: Optional[float] = None  # 0-1 composite confidence

    # Actors
    actor1_name: Optional[str] = None
    actor1_type: Optional[str] = None  # GOVERNMENT | MILITARY | REBEL | CIVILIAN | CORPORATE
    actor2_name: Optional[str] = None
    actor2_type: Optional[str] = None

    # Commodities/Sectors
    commodities: List[str] = field(default_factory=list)  # ['OIL', 'GOLD', etc.]
    sectors: List[str] = field(default_factory=list)  # ['ENERGY', 'MINING', etc.]

    # Legacy fields (backward compatibility)
    title: Optional[str] = None
    content: Optional[str] = None
    source_name: Optional[str] = None
    risk_score: Optional[float] = None
    severity: Optional[str] = None  # P1 | P2 | P3 | P4

    # Enhancement arrays (future-proof for Phase 26+)
    themes: List[str] = field(default_factory=list)  # GKG V2Themes
    quotations: List[Dict[str, Any]] = field(default_factory=list)  # [{speaker, text, offset}]
    gcam_scores: Optional[Dict[str, float]] = None  # {fear, anger, joy, etc.}
    entity_relationships: List[Dict[str, Any]] = field(default_factory=list)  # [{entity1_id, entity2_id, relationship_type}]
    related_events: List[Dict[str, Any]] = field(default_factory=list)  # [{event_id, relationship_type, timestamp}]

    # Metadata (source-specific payloads)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Generate UUID and validate canonical fields."""
        if self.id is None:
            self.id = str(uuid.uuid4())

        # Default ingested_at to created_at if not provided
        if self.ingested_at is None:
            self.ingested_at = self.created_at

        # Validate category
        VALID_CATEGORIES = {
            "POLITICAL", "CONFLICT", "ECONOMIC", "TRADE", "REGULATORY",
            "INFRASTRUCTURE", "HEALTHCARE", "SOCIAL", "ENVIRONMENTAL", "ENERGY"
        }
        if self.category and self.category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {self.category}. Must be one of {VALID_CATEGORIES}")

        # Validate direction
        VALID_DIRECTIONS = {"POSITIVE", "NEGATIVE", "NEUTRAL"}
        if self.direction and self.direction not in VALID_DIRECTIONS:
            raise ValueError(f"Invalid direction: {self.direction}. Must be one of {VALID_DIRECTIONS}")

        # Validate normalized fields (0-1 range)
        if self.magnitude_norm is not None and not (0 <= self.magnitude_norm <= 1):
            raise ValueError(f"magnitude_norm must be 0-1, got {self.magnitude_norm}")

        if self.tone_norm is not None and not (0 <= self.tone_norm <= 1):
            raise ValueError(f"tone_norm must be 0-1, got {self.tone_norm}")

        if self.confidence is not None and not (0 <= self.confidence <= 1):
            raise ValueError(f"confidence must be 0-1, got {self.confidence}")

        if self.source_credibility is not None and not (0 <= self.source_credibility <= 1):
            raise ValueError(f"source_credibility must be 0-1, got {self.source_credibility}")

    def to_bigquery_row(self) -> dict:
        """Convert to BigQuery insert format with all canonical fields."""
        return {
            # Identity
            'id': self.id,
            'source': self.source,
            'source_event_id': self.source_event_id,
            'source_url': self.source_url,
            'source_name': self.source_name,

            # Temporal
            'event_timestamp': self.event_timestamp.isoformat() if isinstance(self.event_timestamp, datetime) else self.event_timestamp,
            'ingested_at': self.ingested_at.isoformat() if isinstance(self.ingested_at, datetime) else self.ingested_at,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,

            # Classification
            'category': self.category,
            'subcategory': self.subcategory,
            'event_type': self.event_type,

            # Location
            'country_code': self.country_code,
            'admin1': self.admin1,
            'admin2': self.admin2,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'location': self.location,

            # Magnitude
            'magnitude_raw': self.magnitude_raw,
            'magnitude_unit': self.magnitude_unit,
            'magnitude_norm': self.magnitude_norm,

            # Direction/Tone
            'direction': self.direction,
            'tone_raw': self.tone_raw,
            'tone_norm': self.tone_norm,

            # Confidence
            'num_sources': self.num_sources,
            'source_credibility': self.source_credibility,
            'confidence': self.confidence,

            # Actors
            'actor1_name': self.actor1_name,
            'actor1_type': self.actor1_type,
            'actor2_name': self.actor2_name,
            'actor2_type': self.actor2_type,

            # Commodities/Sectors
            'commodities': self.commodities,
            'sectors': self.sectors,

            # Legacy fields
            'title': self.title,
            'content': self.content,
            'risk_score': self.risk_score,
            'severity': self.severity,

            # Enhancement arrays (Phase 26+)
            'themes': self.themes,
            'quotations': self.quotations,
            'gcam_scores': self.gcam_scores,
            'entity_relationships': self.entity_relationships,
            'related_events': self.related_events,

            # Metadata
            'metadata': self.metadata
        }


@dataclass
class EntityMention:
    """EntityMention time-series record for BigQuery."""

    entity_id: str
    event_id: str
    mentioned_at: datetime
    id: Optional[str] = None
    context: Optional[str] = None

    def __post_init__(self):
        """Generate UUID if id not provided."""
        if self.id is None:
            self.id = str(uuid.uuid4())

    def to_bigquery_row(self) -> dict:
        """Convert to BigQuery insert format."""
        return {
            'id': self.id,
            'entity_id': self.entity_id,
            'event_id': self.event_id,
            'mentioned_at': self.mentioned_at.isoformat() if isinstance(self.mentioned_at, datetime) else self.mentioned_at,
            'context': self.context or ''
        }


@dataclass
class FREDIndicator:
    """FRED economic indicator record for BigQuery."""

    series_id: str
    date: date
    value: Optional[float] = None
    series_name: Optional[str] = None
    units: Optional[str] = None

    def to_bigquery_row(self) -> dict:
        """Convert to BigQuery insert format."""
        return {
            'series_id': self.series_id,
            'date': self.date.isoformat() if isinstance(self.date, date) else self.date,
            'value': self.value,
            'series_name': self.series_name,
            'units': self.units
        }


@dataclass
class UNComtrade:
    """UN Comtrade trade flow record for BigQuery."""

    period: date
    reporter_code: str
    commodity_code: str
    trade_flow: str
    value_usd: Optional[float] = None

    def to_bigquery_row(self) -> dict:
        """Convert to BigQuery insert format."""
        return {
            'period': self.period.isoformat() if isinstance(self.period, date) else self.period,
            'reporter_code': self.reporter_code,
            'commodity_code': self.commodity_code,
            'trade_flow': self.trade_flow,
            'value_usd': self.value_usd
        }


@dataclass
class WorldBank:
    """World Bank development indicator record for BigQuery."""

    indicator_id: str
    date: date
    value: Optional[float] = None
    country_code: Optional[str] = None

    def to_bigquery_row(self) -> dict:
        """Convert to BigQuery insert format."""
        return {
            'indicator_id': self.indicator_id,
            'date': self.date.isoformat() if isinstance(self.date, date) else self.date,
            'value': self.value,
            'country_code': self.country_code
        }
