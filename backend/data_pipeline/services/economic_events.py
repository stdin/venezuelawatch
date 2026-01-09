"""
Economic event detection for threshold-based alerts.

Analyzes FRED observations and generates alert events when economic indicators
cross configured thresholds (e.g., oil prices below $50/barrel, hyperinflation).
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from django.utils import timezone

from core.models import Event

logger = logging.getLogger(__name__)


def detect_threshold_events(
    series_id: str,
    current_value: float,
    previous_value: Optional[float],
    config: Dict[str, Any],
    observation_date: datetime
) -> List[Event]:
    """
    Detect economic threshold breaches and generate alert events.

    Args:
        series_id: FRED series identifier (e.g., 'DCOILWTICO')
        current_value: Current observation value
        previous_value: Previous observation value (for change detection)
        config: Series configuration from fred_series.py with threshold values
        observation_date: Date of the observation

    Returns:
        List of Event instances for threshold breaches (not saved to database)
    """
    alerts = []
    series_name = config.get('name', series_id)
    units = config.get('units', '')
    category = config.get('category', 'economic')

    # Check threshold_low breach
    threshold_low = config.get('threshold_low')
    if threshold_low is not None:
        # Alert if current value crosses below threshold
        current_below = current_value < threshold_low
        previous_below = previous_value is not None and previous_value < threshold_low

        # Only alert on new breaches (not already below threshold)
        if current_below and not previous_below:
            alert_event = _create_threshold_alert(
                series_id=series_id,
                series_name=series_name,
                current_value=current_value,
                previous_value=previous_value,
                threshold_value=threshold_low,
                threshold_type='low',
                units=units,
                category=category,
                observation_date=observation_date,
            )
            alerts.append(alert_event)
            logger.info(
                f"Threshold LOW breach detected: {series_name} = {current_value} "
                f"(threshold: {threshold_low})"
            )

    # Check threshold_high breach
    threshold_high = config.get('threshold_high')
    if threshold_high is not None:
        # Alert if current value crosses above threshold
        current_above = current_value > threshold_high
        previous_above = previous_value is not None and previous_value > threshold_high

        # Only alert on new breaches (not already above threshold)
        if current_above and not previous_above:
            alert_event = _create_threshold_alert(
                series_id=series_id,
                series_name=series_name,
                current_value=current_value,
                previous_value=previous_value,
                threshold_value=threshold_high,
                threshold_type='high',
                units=units,
                category=category,
                observation_date=observation_date,
            )
            alerts.append(alert_event)
            logger.info(
                f"Threshold HIGH breach detected: {series_name} = {current_value} "
                f"(threshold: {threshold_high})"
            )

    return alerts


def _create_threshold_alert(
    series_id: str,
    series_name: str,
    current_value: float,
    previous_value: Optional[float],
    threshold_value: float,
    threshold_type: str,  # 'low' or 'high'
    units: str,
    category: str,
    observation_date: datetime,
) -> Event:
    """
    Create an economic alert Event for a threshold breach.

    Args:
        series_id: FRED series identifier
        series_name: Human-readable series name
        current_value: Current observation value
        previous_value: Previous observation value
        threshold_value: Threshold that was breached
        threshold_type: 'low' or 'high'
        units: Value units (e.g., 'USD/barrel', 'percent')
        category: Series category (e.g., 'oil_prices', 'venezuela_macro')
        observation_date: Date of the observation

    Returns:
        Event instance (not saved to database)
    """
    # Format values based on units
    if units == 'percent':
        current_str = f"{current_value:.2f}%"
        threshold_str = f"{threshold_value:.2f}%"
    elif units in ['USD/barrel', 'USD', 'USD millions']:
        current_str = f"${current_value:,.2f}"
        threshold_str = f"${threshold_value:,.2f}"
    else:
        current_str = f"{current_value:,.2f} {units}"
        threshold_str = f"{threshold_value:,.2f} {units}"

    # Build alert title based on threshold type and category
    if threshold_type == 'low':
        if 'oil' in category.lower():
            title = f"ALERT: Oil prices fall below {threshold_str}"
        elif 'reserves' in category.lower():
            title = f"ALERT: Venezuela reserves drop below {threshold_str}"
        else:
            title = f"ALERT: {series_name} falls below {threshold_str}"
    else:  # 'high'
        if 'inflation' in series_name.lower():
            title = f"ALERT: Hyperinflation exceeds {threshold_str}"
        else:
            title = f"ALERT: {series_name} exceeds {threshold_str}"

    # Calculate change percentage if previous value available
    change_pct = None
    if previous_value is not None and previous_value != 0:
        change_pct = ((current_value - previous_value) / previous_value) * 100

    # Determine severity based on threshold type and category
    severity = _determine_severity(
        threshold_type=threshold_type,
        category=category,
        series_id=series_id,
    )

    # Build content JSON
    content = {
        'series_id': series_id,
        'series_name': series_name,
        'current_value': current_value,
        'previous_value': previous_value,
        'threshold_value': threshold_value,
        'threshold_type': threshold_type,
        'units': units,
        'category': category,
        'change_pct': change_pct,
        'severity': severity,
        'alert_type': 'economic_threshold',
    }

    # Make observation_date timezone aware if needed
    if timezone.is_naive(observation_date):
        observation_date = timezone.make_aware(observation_date, timezone.utc)

    # Create alert Event
    # Use current time as timestamp (when alert was detected)
    # Store observation date in content
    event = Event(
        source='FRED',
        event_type='ECONOMIC_ALERT',
        timestamp=timezone.now(),
        title=title[:500],
        content=content,
        sentiment=None,
        risk_score=None,  # Computed in Phase 4
        entities=[],
    )

    return event


def _determine_severity(
    threshold_type: str,
    category: str,
    series_id: str,
) -> str:
    """
    Determine alert severity based on threshold type and series category.

    Args:
        threshold_type: 'low' or 'high'
        category: Series category (e.g., 'oil_prices', 'venezuela_macro')
        series_id: FRED series identifier

    Returns:
        Severity level: 'critical', 'high', 'medium', or 'low'
    """
    # Critical severity for hyperinflation
    if series_id == 'FPCPITOTLZGVEN' and threshold_type == 'high':
        return 'critical'

    # High severity for oil price drops (major impact on Venezuela)
    if category == 'oil_prices' and threshold_type == 'low':
        return 'high'

    # High severity for reserve depletion
    if category == 'reserves' and threshold_type == 'low':
        return 'high'

    # Medium severity for other high thresholds
    if threshold_type == 'high':
        return 'medium'

    # Low severity for other low thresholds
    return 'low'
