"""
FRED (Federal Reserve Economic Data) ingestion tasks.

Fetches economic indicators from FRED API with parallel series processing
and threshold-based alert generation.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from celery import shared_task, group
from django.db import transaction
from django.utils import timezone
import pandas as pd

from data_pipeline.tasks.base import BaseIngestionTask
from data_pipeline.services.fred_client import FREDClient
from data_pipeline.services.event_mapper import map_fred_to_event
from data_pipeline.services.economic_events import detect_threshold_events
from data_pipeline.config.fred_series import (
    get_all_series_ids,
    get_series_config,
)
from core.models import Event

logger = logging.getLogger(__name__)


@shared_task(base=BaseIngestionTask, bind=True)
def ingest_single_series(
    self,
    series_id: str,
    lookback_days: int = 7
) -> Dict[str, Any]:
    """
    Ingest observations for a single FRED series.

    Args:
        series_id: FRED series identifier (e.g., 'DCOILWTICO')
        lookback_days: Number of days to look back for new observations

    Returns:
        {
            'series_id': str,
            'observations_created': int,
            'observations_skipped': int,
            'status': 'success' | 'failed' | 'no_data',
            'error': str (if failed),
        }
    """
    logger.info(f"Ingesting FRED series {series_id} (lookback: {lookback_days} days)")

    # Get series configuration
    series_config = get_series_config(series_id)
    if series_config is None:
        logger.error(f"Series {series_id} not found in configuration")
        return {
            'series_id': series_id,
            'observations_created': 0,
            'observations_skipped': 0,
            'status': 'failed',
            'error': 'Series not found in configuration',
        }

    try:
        # Initialize FRED client
        fred_client = FREDClient()

        # Calculate start date
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')

        # Fetch series data
        try:
            df = fred_client.get_series(series_id, start_date=start_date)
        except Exception as e:
            # Handle discontinued or unavailable series gracefully
            if 'Bad Request' in str(e) or '400' in str(e) or 'not found' in str(e).lower():
                logger.warning(
                    f"Series {series_id} may be discontinued or unavailable: {e}"
                )
                return {
                    'series_id': series_id,
                    'observations_created': 0,
                    'observations_skipped': 0,
                    'status': 'no_data',
                    'error': f'Series unavailable: {str(e)}',
                }
            else:
                raise

        if df is None or len(df) == 0:
            logger.info(f"No new observations for series {series_id}")
            return {
                'series_id': series_id,
                'observations_created': 0,
                'observations_skipped': 0,
                'status': 'no_data',
            }

        observations_created = 0
        observations_skipped = 0

        # Process each observation
        for obs_date, row in df.iterrows():
            value = row['value']

            # Skip NaN values
            if value is None or (hasattr(value, '__iter__') and any(pd.isna(v) for v in value if hasattr(pd, 'isna'))) or (not hasattr(value, '__iter__') and str(value) == 'nan'):
                logger.debug(f"Skipping NaN value for {series_id} on {obs_date}")
                observations_skipped += 1
                continue

            # Convert pandas Timestamp to datetime
            if hasattr(obs_date, 'to_pydatetime'):
                obs_date = obs_date.to_pydatetime()

            # Make timezone aware
            if timezone.is_naive(obs_date):
                obs_date = timezone.make_aware(obs_date, timezone.utc)

            # Check for duplicate
            existing = Event.objects.filter(
                source='FRED',
                content__series_id=series_id,
                timestamp=obs_date
            ).exists()

            if existing:
                logger.debug(f"Skipping duplicate observation for {series_id} on {obs_date}")
                observations_skipped += 1
                continue

            # Get previous observation for change calculation
            previous_events = Event.objects.filter(
                source='FRED',
                content__series_id=series_id,
                timestamp__lt=obs_date
            ).order_by('-timestamp')[:1]

            previous_value = None
            if previous_events.exists():
                previous_value = previous_events.first().content.get('value')

            # Create observation dict
            observation = {
                'series_id': series_id,
                'date': obs_date,
                'value': float(value),
                'previous_value': previous_value,
            }

            # Map to Event
            try:
                event = map_fred_to_event(observation, series_config)

                # Detect threshold breaches
                threshold_alerts = detect_threshold_events(
                    series_id=series_id,
                    current_value=float(value),
                    previous_value=previous_value,
                    config=series_config,
                    observation_date=obs_date,
                )

                # Save to database (observation + any alerts)
                with transaction.atomic():
                    event.save()
                    observations_created += 1
                    logger.debug(
                        f"Created FRED event: {series_id} = {value} on {obs_date}"
                    )

                    # Save threshold alert events
                    for alert in threshold_alerts:
                        alert.save()
                        logger.info(
                            f"Created threshold alert: {alert.title}"
                        )

            except Exception as e:
                logger.error(
                    f"Failed to create event for {series_id} observation: {e}",
                    exc_info=True
                )
                observations_skipped += 1

        result = {
            'series_id': series_id,
            'observations_created': observations_created,
            'observations_skipped': observations_skipped,
            'status': 'success',
        }

        logger.info(
            f"FRED series {series_id} ingestion complete: "
            f"{observations_created} created, {observations_skipped} skipped"
        )

        return result

    except Exception as e:
        logger.error(f"FRED series {series_id} ingestion failed: {e}", exc_info=True)
        return {
            'series_id': series_id,
            'observations_created': 0,
            'observations_skipped': 0,
            'status': 'failed',
            'error': str(e),
        }


@shared_task(base=BaseIngestionTask, bind=True)
def ingest_fred_series(self, lookback_days: int = 7) -> Dict[str, Any]:
    """
    Ingest all Venezuela economic series from FRED using parallel tasks.

    Dispatches individual series tasks in parallel using Celery groups
    for efficient batch processing.

    Args:
        lookback_days: Number of days to look back for new observations

    Returns:
        {
            'series_ingested': int,  # Number of series processed
            'observations_created': int,  # Total observations created
            'observations_skipped': int,  # Total observations skipped
            'series_failed': int,  # Number of series that failed
            'series_no_data': int,  # Number of series with no data
            'results': list[dict],  # Individual series results
        }
    """
    logger.info(f"Starting FRED batch ingestion (lookback: {lookback_days} days)")

    # Get all series IDs
    series_ids = get_all_series_ids()
    logger.info(f"Ingesting {len(series_ids)} FRED series: {series_ids}")

    # Create parallel tasks using Celery group
    job = group(
        ingest_single_series.s(series_id, lookback_days)
        for series_id in series_ids
    )

    # Execute tasks in parallel
    result = job.apply_async()

    # Wait for all tasks to complete
    individual_results = result.get(timeout=300)  # 5 minute timeout

    # Aggregate results
    series_ingested = 0
    observations_created = 0
    observations_skipped = 0
    series_failed = 0
    series_no_data = 0

    for res in individual_results:
        if res['status'] == 'success':
            series_ingested += 1
            observations_created += res['observations_created']
            observations_skipped += res['observations_skipped']
        elif res['status'] == 'failed':
            series_failed += 1
        elif res['status'] == 'no_data':
            series_no_data += 1

    summary = {
        'series_ingested': series_ingested,
        'observations_created': observations_created,
        'observations_skipped': observations_skipped,
        'series_failed': series_failed,
        'series_no_data': series_no_data,
        'results': individual_results,
    }

    logger.info(
        f"FRED batch ingestion complete: {series_ingested} series, "
        f"{observations_created} observations created, {observations_skipped} skipped, "
        f"{series_failed} failed, {series_no_data} no data"
    )

    return summary
