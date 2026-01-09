"""
Event mapping functions for transforming external API data into Event models.

Maps data from GDELT, ReliefWeb, FRED, UN Comtrade, and World Bank into
the unified Event model structure.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from django.utils import timezone
from dateutil import parser as date_parser

from core.models import Event

logger = logging.getLogger(__name__)


def map_gdelt_to_event(gdelt_record: Dict[str, Any]) -> Event:
    """
    Map GDELT DOC API v2 article to Event model.

    GDELT DOC API provides news article mentions with:
    - url: Article URL
    - url_mobile: Mobile URL
    - title: Article title
    - seendate: When GDELT first saw this article (YYYYMMDDHHmmss format)
    - socialimage: Social media preview image
    - domain: Domain name
    - language: Language code
    - sourcecountry: Source country code

    Args:
        gdelt_record: GDELT article record dict

    Returns:
        Event instance (not saved to database)
    """
    # Parse GDELT seendate format: YYYYMMDDHHmmss
    seendate_str = gdelt_record.get('seendate', '')
    try:
        if seendate_str:
            timestamp = datetime.strptime(seendate_str, '%Y%m%d%H%M%S')
            timestamp = timezone.make_aware(timestamp, timezone.utc)
        else:
            timestamp = timezone.now()
    except (ValueError, TypeError):
        logger.warning(f"Could not parse GDELT seendate: {seendate_str}")
        timestamp = timezone.now()

    # Extract title (limit to 500 chars for model)
    title = gdelt_record.get('title', 'Untitled GDELT Article')[:500]

    # Determine event type from URL/domain patterns
    domain = gdelt_record.get('domain', '').lower()
    url = gdelt_record.get('url', '').lower()

    event_type = 'POLITICAL'  # Default
    if any(keyword in domain or keyword in url for keyword in ['reuters.com/markets', 'bloomberg.com', 'wsj.com/economy']):
        event_type = 'ECONOMIC'
    elif any(keyword in domain or keyword in url for keyword in ['trade', 'commerce', 'customs']):
        event_type = 'TRADE'
    elif any(keyword in domain or keyword in url for keyword in ['reliefweb', 'humanitarian', 'disaster', 'crisis']):
        event_type = 'DISASTER'

    # Build content JSON with all GDELT fields
    content = {
        'url': gdelt_record.get('url'),
        'url_mobile': gdelt_record.get('url_mobile'),
        'domain': gdelt_record.get('domain'),
        'language': gdelt_record.get('language'),
        'sourcecountry': gdelt_record.get('sourcecountry'),
        'socialimage': gdelt_record.get('socialimage'),
        'raw_gdelt': gdelt_record,  # Store full record for debugging
    }

    # Create Event instance
    event = Event(
        source='GDELT',
        event_type=event_type,
        timestamp=timestamp,
        title=title,
        content=content,
        sentiment=None,  # GDELT GKG has tone, but DOC API doesn't provide it directly
        risk_score=None,  # Computed in Phase 4
        entities=[],  # Extracted in Phase 6
    )

    return event


def map_reliefweb_to_event(report: Dict[str, Any]) -> Event:
    """
    Map ReliefWeb API report to Event model.

    ReliefWeb API structure:
    - id: Report ID
    - fields: {
        title: Report title
        body: Plain text body
        body-html: HTML body
        date: { created: ISO 8601 timestamp }
        country: [{ name: 'Venezuela' }]
        source: [{ name: 'OCHA' }]
        url: Canonical URL
        file: [{ url: PDF URL }]
      }

    Args:
        report: ReliefWeb report dict

    Returns:
        Event instance (not saved to database)
    """
    fields = report.get('fields', {})

    # Parse timestamp
    date_info = fields.get('date', {})
    created_str = date_info.get('created', '')
    try:
        if created_str:
            timestamp = date_parser.parse(created_str)
            if timezone.is_naive(timestamp):
                timestamp = timezone.make_aware(timestamp, timezone.utc)
        else:
            timestamp = timezone.now()
    except (ValueError, TypeError):
        logger.warning(f"Could not parse ReliefWeb date: {created_str}")
        timestamp = timezone.now()

    # Extract title
    title = fields.get('title', 'Untitled ReliefWeb Report')[:500]

    # Extract countries
    countries = [c.get('name') for c in fields.get('country', []) if c.get('name')]
    location = ', '.join(countries) if countries else 'Venezuela'

    # Extract source organizations
    sources = [s.get('name') for s in fields.get('source', []) if s.get('name')]

    # Build content JSON
    content = {
        'url': fields.get('url'),
        'body': fields.get('body'),
        'body_html': fields.get('body-html'),
        'location': location,
        'sources': sources,
        'report_id': report.get('id'),
        'files': fields.get('file', []),
        'raw_reliefweb': report,  # Store full record for debugging
    }

    # Create Event instance
    event = Event(
        source='RELIEFWEB',
        event_type='HUMANITARIAN',
        timestamp=timestamp,
        title=title,
        content=content,
        sentiment=None,  # ReliefWeb doesn't provide sentiment
        risk_score=None,  # Computed in Phase 4
        entities=[],  # Extracted in Phase 6
    )

    return event


def map_fred_to_event(observation: Dict[str, Any], series_info: Dict[str, Any]) -> Event:
    """
    Map FRED (Federal Reserve Economic Data) observation to Event model.

    Placeholder for Plan 03-03 (Daily Batch Ingestion).

    Args:
        observation: FRED observation dict
        series_info: FRED series metadata

    Returns:
        Event instance (not saved to database)
    """
    # TODO: Implement in Plan 03-03
    raise NotImplementedError("FRED mapping will be implemented in Plan 03-03")


def map_comtrade_to_event(trade_record: Dict[str, Any]) -> Event:
    """
    Map UN Comtrade trade data to Event model.

    Placeholder for Plan 03-04 (Monthly/Quarterly Ingestion).

    Args:
        trade_record: UN Comtrade record dict

    Returns:
        Event instance (not saved to database)
    """
    # TODO: Implement in Plan 03-04
    raise NotImplementedError("Comtrade mapping will be implemented in Plan 03-04")


def map_worldbank_to_event(indicator: Dict[str, Any]) -> Event:
    """
    Map World Bank indicator data to Event model.

    Placeholder for Plan 03-04 (Monthly/Quarterly Ingestion).

    Args:
        indicator: World Bank indicator dict

    Returns:
        Event instance (not saved to database)
    """
    # TODO: Implement in Plan 03-04
    raise NotImplementedError("World Bank mapping will be implemented in Plan 03-04")
