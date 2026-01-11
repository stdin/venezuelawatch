"""
FRED economic indicators Cloud Function.

Fetches Venezuela economic indicators from FRED API.
HTTP trigger for Cloud Scheduler invocation (daily).
"""
import functions_framework
import logging
import uuid
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from flask import Request
from fredapi import Fred
import sys
import os

# Add shared utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from bigquery_client import BigQueryClient
from pubsub_client import PubSubClient
from secret_manager import SecretManagerClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Venezuela Economic Series Registry
VENEZUELA_ECONOMIC_SERIES = {
    'DCOILWTICO': {
        'name': 'WTI Crude Oil Price',
        'units': 'USD/barrel',
        'threshold_low': 50.0,
        'threshold_high': 100.0,
        'category': 'oil_prices',
    },
    'DCOILBRENTEU': {
        'name': 'Brent Crude Oil Price',
        'units': 'USD/barrel',
        'threshold_low': 55.0,
        'threshold_high': 105.0,
        'category': 'oil_prices',
    },
    'FPCPITOTLZGVEN': {
        'name': 'Venezuela CPI Inflation (YoY)',
        'units': 'percent',
        'threshold_high': 100.0,
        'category': 'venezuela_macro',
    },
    'NYGDPPCAPKDVEN': {
        'name': 'Venezuela GDP per Capita',
        'units': 'constant 2015 USD',
        'category': 'venezuela_macro',
    },
    'DEXVZUS': {
        'name': 'Venezuela Bolivar / USD Exchange Rate',
        'units': 'VEF/USD',
        'category': 'exchange_rates',
    },
    'TRESEGVEA634N': {
        'name': 'Venezuela Total Reserves',
        'units': 'USD millions',
        'threshold_low': 10000.0,
        'category': 'reserves',
    },
}


def detect_threshold_breach(
    series_id: str,
    current_value: float,
    previous_value: Optional[float],
    config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Check if threshold is breached and return alert data.

    Returns:
        Alert dict if threshold breached, None otherwise
    """
    threshold_low = config.get('threshold_low')
    threshold_high = config.get('threshold_high')

    # Check low threshold
    if threshold_low is not None:
        current_below = current_value < threshold_low
        previous_below = previous_value is not None and previous_value < threshold_low

        if current_below and not previous_below:
            return {
                'threshold_type': 'low',
                'threshold_value': threshold_low,
                'breached': True
            }

    # Check high threshold
    if threshold_high is not None:
        current_above = current_value > threshold_high
        previous_above = previous_value is not None and previous_value > threshold_high

        if current_above and not previous_above:
            return {
                'threshold_type': 'high',
                'threshold_value': threshold_high,
                'breached': True
            }

    return None


@functions_framework.http
def sync_fred(request: Request):
    """
    HTTP Cloud Function to sync FRED economic indicators.

    Request JSON body:
        {
            "lookback_days": 7  // Optional, default: 7
        }

    Returns:
        JSON response with sync statistics
    """
    try:
        # Parse request
        request_json = request.get_json(silent=True) or {}
        lookback_days = request_json.get('lookback_days', 7)

        logger.info(f"Starting FRED ingestion (lookback: {lookback_days} days)")

        # Initialize clients
        bq_client = BigQueryClient()
        pubsub_client = PubSubClient()

        # Get FRED API key from Secret Manager
        secret_client = SecretManagerClient()
        fred_api_key = secret_client.get_secret('api-fred-key')

        # Initialize FRED client
        fred_client = Fred(api_key=fred_api_key)

        # Calculate start date
        start_date = (datetime.utcnow() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')

        observations_created = 0
        observations_skipped = 0
        series_processed = 0
        fred_indicators = []
        threshold_alert_events = []

        # Process each series
        for series_id, series_config in VENEZUELA_ECONOMIC_SERIES.items():
            logger.info(f"Processing FRED series: {series_id}")

            try:
                # Fetch series data
                data = fred_client.get_series(series_id, observation_start=start_date)

                if data is None or len(data) == 0:
                    logger.info(f"No new observations for series {series_id}")
                    continue

                # Convert to DataFrame
                df = data.to_frame(name='value')

                # Process each observation
                for obs_date, row in df.iterrows():
                    value = row['value']

                    # Skip NaN values
                    if pd.isna(value):
                        observations_skipped += 1
                        continue

                    # Convert to date
                    if hasattr(obs_date, 'date'):
                        obs_date_only = obs_date.date()
                    else:
                        obs_date_only = obs_date

                    # Get previous value for change calculation
                    previous_value = bq_client.get_previous_fred_value(series_id, obs_date_only.isoformat())

                    # Create FRED indicator
                    indicator = {
                        'series_id': series_id,
                        'date': obs_date_only.isoformat(),
                        'value': float(value),
                        'series_name': series_config.get('name'),
                        'units': series_config.get('units')
                    }
                    fred_indicators.append(indicator)
                    observations_created += 1

                    # Check for threshold breaches
                    threshold_alert = detect_threshold_breach(
                        series_id=series_id,
                        current_value=float(value),
                        previous_value=previous_value,
                        config=series_config
                    )

                    if threshold_alert:
                        # Create threshold alert event
                        event_id = str(uuid.uuid4())

                        # Calculate change percentage
                        change_pct = None
                        if previous_value is not None and previous_value != 0:
                            change_pct = ((float(value) - previous_value) / previous_value) * 100

                        # Build alert title
                        threshold_type = threshold_alert['threshold_type']
                        threshold_value = threshold_alert['threshold_value']
                        series_name = series_config['name']

                        if threshold_type == 'low':
                            title = f"ALERT: {series_name} falls below ${threshold_value}"
                        else:
                            title = f"ALERT: {series_name} exceeds ${threshold_value}"

                        alert_event = {
                            'id': event_id,
                            'source_url': f"https://fred.stlouisfed.org/series/{series_id}",
                            'mentioned_at': datetime.combine(obs_date_only, datetime.min.time()).isoformat(),
                            'created_at': datetime.utcnow().isoformat(),
                            'title': title,
                            'content': f"Economic threshold breach: {series_name} = {value}",
                            'source_name': 'FRED',
                            'event_type': 'economic_alert',
                            'location': 'Venezuela',
                            'risk_score': None,
                            'severity': None,
                            'metadata': {
                                'series_id': series_id,
                                'threshold_type': threshold_type,
                                'current_value': float(value),
                                'previous_value': previous_value,
                                'change_pct': change_pct,
                                'threshold_value': threshold_value
                            }
                        }
                        threshold_alert_events.append(alert_event)
                        logger.info(f"Threshold alert created: {title}")

                series_processed += 1

            except Exception as e:
                error_msg = str(e)
                if 'Bad Request' in error_msg or '400' in error_msg:
                    logger.warning(f"Series {series_id} may be discontinued: {e}")
                else:
                    logger.error(f"Failed to process series {series_id}: {e}", exc_info=True)
                continue

        # Batch insert FRED indicators to BigQuery
        if fred_indicators:
            try:
                bq_client.insert_fred_indicators(fred_indicators)
                logger.info(f"Inserted {len(fred_indicators)} FRED indicators to BigQuery")
            except Exception as e:
                logger.error(f"Failed to insert FRED indicators: {e}", exc_info=True)
                return {
                    'error': str(e),
                    'observations_created': 0,
                    'observations_skipped': observations_skipped
                }, 500

        # Insert threshold alert events
        event_ids_for_analysis = []
        if threshold_alert_events:
            try:
                bq_client.insert_events(threshold_alert_events)
                logger.info(f"Inserted {len(threshold_alert_events)} threshold alert events")

                # Publish for LLM analysis (use 'standard' model for economic alerts)
                event_ids_for_analysis = [e['id'] for e in threshold_alert_events]
                pubsub_client.publish_events_for_analysis(event_ids_for_analysis, model='standard')
                logger.info(f"Published {len(event_ids_for_analysis)} alerts for LLM analysis")

            except Exception as e:
                logger.error(f"Failed to insert threshold alerts: {e}", exc_info=True)
                # Don't fail - indicators are more important

        result = {
            'series_processed': series_processed,
            'observations_created': observations_created,
            'observations_skipped': observations_skipped,
            'threshold_alerts': len(threshold_alert_events)
        }

        logger.info(
            f"FRED ingestion complete: {series_processed} series, "
            f"{observations_created} observations, {len(threshold_alert_events)} alerts"
        )

        return result, 200

    except Exception as e:
        logger.error(f"FRED ingestion failed: {e}", exc_info=True)
        return {'error': str(e)}, 500
