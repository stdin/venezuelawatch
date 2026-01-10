"""
BigQuery dataclass models for VenezuelaWatch time-series data.

These are NOT Django models - they're Python dataclasses that convert to BigQuery row format.
Use these with api.services.bigquery_service for inserting/querying BigQuery data.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any
import uuid


@dataclass
class Event:
    """Event time-series record for BigQuery."""

    source_url: str
    mentioned_at: datetime
    created_at: datetime
    id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    source_name: Optional[str] = None
    event_type: Optional[str] = None
    location: Optional[str] = None
    risk_score: Optional[float] = None
    severity: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Generate UUID if id not provided."""
        if self.id is None:
            self.id = str(uuid.uuid4())

    def to_bigquery_row(self) -> dict:
        """Convert to BigQuery insert format."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'source_url': self.source_url,
            'source_name': self.source_name,
            'event_type': self.event_type,
            'location': self.location,
            'risk_score': self.risk_score,
            'severity': self.severity,
            'mentioned_at': self.mentioned_at.isoformat() if isinstance(self.mentioned_at, datetime) else self.mentioned_at,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
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
