"""
Event mapping functions for transforming external API data into Event models.

Maps data from GDELT, ReliefWeb, FRED, UN Comtrade, and World Bank into
the unified Event model structure.
"""
import logging
from datetime import datetime
from datetime import timezone as dt_timezone
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
    - seendate: When GDELT first saw this article (ISO 8601: YYYYMMDDTHHmmssZ)
    - socialimage: Social media preview image
    - domain: Domain name
    - language: Language code
    - sourcecountry: Source country code

    Args:
        gdelt_record: GDELT article record dict

    Returns:
        Event instance (not saved to database)
    """
    # Parse GDELT seendate format: 20251106T070000Z (ISO 8601)
    seendate_str = gdelt_record.get('seendate', '')
    try:
        if seendate_str:
            # GDELT uses ISO 8601 basic format: YYYYMMDDTHHmmssZ
            timestamp = datetime.strptime(seendate_str, '%Y%m%dT%H%M%SZ')
            timestamp = timezone.make_aware(timestamp, dt_timezone.utc)
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
                timestamp = timezone.make_aware(timestamp, dt_timezone.utc)
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


def map_fred_to_event(observation: Dict[str, Any], series_config: Dict[str, Any]) -> Event:
    """
    Map FRED (Federal Reserve Economic Data) observation to Event model.

    Args:
        observation: FRED observation dict with {
            'series_id': str,
            'date': datetime,
            'value': float,
            'previous_value': float (optional),
        }
        series_config: Series configuration from fred_series.py with {
            'name': str,
            'units': str,
            'frequency': str,
            'category': str,
            etc.
        }

    Returns:
        Event instance (not saved to database)
    """
    # Parse observation date
    obs_date = observation.get('date')
    if isinstance(obs_date, str):
        obs_date = date_parser.parse(obs_date)
    if timezone.is_naive(obs_date):
        obs_date = timezone.make_aware(obs_date, dt_timezone.utc)

    # Build title with series name and current value
    series_name = series_config.get('name', observation['series_id'])
    value = observation['value']
    units = series_config.get('units', '')

    # Format value based on units
    if units == 'percent':
        title = f"{series_name}: {value:.2f}%"
    elif units in ['USD/barrel', 'USD', 'USD millions']:
        title = f"{series_name}: ${value:,.2f}"
    else:
        title = f"{series_name}: {value:,.2f} {units}"

    # Calculate change if previous value available
    previous_value = observation.get('previous_value')
    change_pct = None
    if previous_value is not None and previous_value != 0:
        change_pct = ((value - previous_value) / previous_value) * 100

    # Build content JSON
    content = {
        'series_id': observation['series_id'],
        'value': value,
        'units': units,
        'frequency': series_config.get('frequency'),
        'category': series_config.get('category'),
        'description': series_config.get('description'),
        'previous_value': previous_value,
        'change_pct': change_pct,
        'raw_observation': observation,
    }

    # Create Event instance
    event = Event(
        source='FRED',
        event_type='ECONOMIC',
        timestamp=obs_date,
        title=title[:500],  # Limit to model max length
        content=content,
        sentiment=None,  # Economic indicators don't have sentiment
        risk_score=None,  # Computed in Phase 4
        entities=[],  # No entities for economic data
    )

    return event


def map_comtrade_to_event(trade_record: Dict[str, Any], commodity_info: Dict[str, Any]) -> Event:
    """
    Map UN Comtrade trade data to Event model.

    Comtrade API structure (simplified):
    - period: Time period (YYYYMM)
    - reporterCode: Reporter country ISO3 (VEN)
    - partnerCode: Partner country ISO3
    - cmdCode: Commodity HS code
    - flowCode: M (imports) or X (exports)
    - primaryValue: Trade value in USD
    - netWeight: Weight in kg
    - quantityUnit: Quantity unit

    Args:
        trade_record: Comtrade trade flow dict
        commodity_info: Commodity metadata from comtrade_config.py

    Returns:
        Event instance (not saved to database)
    """
    # Extract trade flow details
    period = str(trade_record.get('period', ''))
    partner = trade_record.get('partnerCode', 'Unknown')
    commodity_code = str(trade_record.get('cmdCode', ''))
    flow_code = trade_record.get('flowCode', 'M')
    flow_type = 'Imports' if flow_code == 'M' else 'Exports'

    # Trade values
    trade_value = float(trade_record.get('primaryValue', 0))  # USD
    quantity = trade_record.get('netWeight')  # kg

    # Parse period to datetime (YYYYMM format)
    try:
        if len(period) == 6:  # YYYYMM
            year = int(period[:4])
            month = int(period[4:6])
            # Use last day of month as timestamp
            from calendar import monthrange
            last_day = monthrange(year, month)[1]
            timestamp = datetime(year, month, last_day)
        else:  # YYYY format
            year = int(period)
            timestamp = datetime(year, 12, 31)  # End of year
        timestamp = timezone.make_aware(timestamp, dt_timezone.utc)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse Comtrade period: {period}")
        timestamp = timezone.now()

    # Build title
    commodity_name = commodity_info.get('name', f'Commodity {commodity_code}')
    if trade_value >= 1_000_000_000:  # Billions
        value_str = f"${trade_value/1_000_000_000:.2f}B"
    elif trade_value >= 1_000_000:  # Millions
        value_str = f"${trade_value/1_000_000:.1f}M"
    else:
        value_str = f"${trade_value:,.0f}"

    title = f"{commodity_name}: {flow_type} {value_str}"

    # Build content JSON
    content = {
        'period': period,
        'commodity_code': commodity_code,
        'commodity_name': commodity_name,
        'commodity_category': commodity_info.get('category'),
        'partner_country': partner,
        'flow_type': flow_type.lower(),
        'trade_value_usd': trade_value,
        'quantity_kg': quantity,
        'raw_comtrade': trade_record,
    }

    # Create Event instance
    event = Event(
        source='COMTRADE',
        event_type='TRADE',
        timestamp=timestamp,
        title=title[:500],
        content=content,
        sentiment=None,
        risk_score=None,  # Computed in Phase 4
        entities=[],
    )

    return event


def map_worldbank_to_event(indicator_data: Dict[str, Any], indicator_info: Dict[str, Any]) -> Event:
    """
    Map World Bank indicator data to Event model.

    Args:
        indicator_data: dict with {'year': int, 'value': float, 'indicator_id': str}
        indicator_info: Indicator metadata from worldbank_config.py

    Returns:
        Event instance (not saved to database)
    """
    # Extract indicator details
    indicator_id = indicator_data.get('indicator_id', '')
    year = indicator_data.get('year')
    value = indicator_data.get('value')

    # Get indicator metadata
    indicator_name = indicator_info.get('name', indicator_id)
    category = indicator_info.get('category', 'development')
    units = indicator_info.get('units', '')

    # Create timestamp (end of year)
    try:
        timestamp = datetime(year, 12, 31)
        timestamp = timezone.make_aware(timestamp, dt_timezone.utc)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse year: {year}")
        timestamp = timezone.now()

    # Format value for title
    if units == 'percent':
        value_str = f"{value:.2f}%"
    elif units == 'current USD':
        if value >= 1_000_000_000:  # Billions
            value_str = f"${value/1_000_000_000:.2f}B"
        elif value >= 1_000_000:  # Millions
            value_str = f"${value/1_000_000:.1f}M"
        else:
            value_str = f"${value:,.0f}"
    elif units == 'people':
        if value >= 1_000_000:  # Millions
            value_str = f"{value/1_000_000:.2f}M"
        else:
            value_str = f"{value:,.0f}"
    else:
        value_str = f"{value:,.2f}"

    title = f"{indicator_name}: {value_str} ({year})"

    # Build content JSON
    content = {
        'indicator_id': indicator_id,
        'indicator_name': indicator_name,
        'category': category,
        'year': year,
        'value': value,
        'units': units,
        'description': indicator_info.get('description'),
    }

    # Create Event instance
    event = Event(
        source='WORLD_BANK',
        event_type='DEVELOPMENT_INDICATOR',
        timestamp=timestamp,
        title=title[:500],
        content=content,
        sentiment=None,
        risk_score=None,  # Computed in Phase 4
        entities=[],
    )

    return event
