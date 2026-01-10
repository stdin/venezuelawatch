"""
FRED (Federal Reserve Economic Data) ingestion tasks.

Fetches economic indicators from FRED API with parallel series processing
and threshold-based alert generation.
"""
import logging
from datetime import datetime, timedelta, date
from datetime import timezone as dt_timezone
from typing import Dict, Any, Optional
from celery import shared_task, group
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from google.cloud import bigquery
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
from api.bigquery_models import FREDIndicator, Event as BigQueryEvent
from api.services.bigquery_service import bigquery_service

logger = logging.getLogger(__name__)


# Import intelligence task for LLM analysis
def get_intelligence_task():
    """Lazy import to avoid circular dependency."""
    from data_pipeline.tasks.intelligence_tasks import analyze_event_intelligence
    return analyze_event_intelligence


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

        # Batch collection for BigQuery
        fred_indicators = []
        threshold_alert_events = []

        # Process each observation
        for obs_date, row in df.iterrows():
            value = row['value']

            # Skip NaN values
            if value is None or (hasattr(value, '__iter__') and any(pd.isna(v) for v in value if hasattr(pd, 'isna'))) or (not hasattr(value, '__iter__') and str(value) == 'nan'):
                logger.debug(f"Skipping NaN value for {series_id} on {obs_date}")
                observations_skipped += 1
                continue

            # Convert pandas Timestamp to datetime/date
            if hasattr(obs_date, 'to_pydatetime'):
                obs_datetime = obs_date.to_pydatetime()
            else:
                obs_datetime = obs_date

            # Convert to date for fred_indicators table
            if isinstance(obs_datetime, datetime):
                obs_date_only = obs_datetime.date()
            else:
                obs_date_only = obs_datetime

            # Make timezone aware for event timestamps
            if hasattr(obs_datetime, 'tzinfo') and timezone.is_naive(obs_datetime):
                obs_datetime = timezone.make_aware(obs_datetime, dt_timezone.utc)

            # Check for duplicate in BigQuery fred_indicators
            try:
                query = f"""
                    SELECT COUNT(*) as count
                    FROM `{settings.GCP_PROJECT_ID}.{settings.BIGQUERY_DATASET}.fred_indicators`
                    WHERE series_id = @series_id
                    AND date = @date
                """
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter('series_id', 'STRING', series_id),
                        bigquery.ScalarQueryParameter('date', 'DATE', obs_date_only)
                    ]
                )
                results = bigquery_service.client.query(query, job_config=job_config).result()
                row_result = list(results)[0]
                if row_result.count > 0:
                    logger.debug(f"Skipping duplicate observation for {series_id} on {obs_date_only}")
                    observations_skipped += 1
                    continue
            except Exception as e:
                logger.error(f"Failed to check for duplicate in BigQuery: {e}")
                # Continue with insert - better to have duplicate than skip valid observation
                pass

            # Get previous observation for change calculation
            try:
                prev_query = f"""
                    SELECT value
                    FROM `{settings.GCP_PROJECT_ID}.{settings.BIGQUERY_DATASET}.fred_indicators`
                    WHERE series_id = @series_id
                    AND date < @date
                    ORDER BY date DESC
                    LIMIT 1
                """
                prev_job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter('series_id', 'STRING', series_id),
                        bigquery.ScalarQueryParameter('date', 'DATE', obs_date_only)
                    ]
                )
                prev_results = bigquery_service.client.query(prev_query, prev_job_config).result()
                prev_rows = list(prev_results)
                previous_value = prev_rows[0].value if prev_rows else None
            except Exception as e:
                logger.warning(f"Failed to get previous value from BigQuery: {e}")
                previous_value = None

            # Create FREDIndicator for BigQuery
            try:
                fred_indicator = FREDIndicator(
                    series_id=series_id,
                    date=obs_date_only,
                    value=float(value),
                    series_name=series_config.get('name'),
                    units=series_config.get('units')
                )
                fred_indicators.append(fred_indicator)
                observations_created += 1
                logger.debug(f"Prepared FRED indicator: {series_id} = {value} on {obs_date_only}")

                # Detect threshold breaches for event generation
                threshold_alerts = detect_threshold_events(
                    series_id=series_id,
                    current_value=float(value),
                    previous_value=previous_value,
                    config=series_config,
                    observation_date=obs_datetime if isinstance(obs_datetime, datetime) else datetime.combine(obs_datetime, datetime.min.time()).replace(tzinfo=dt_timezone.utc),
                )

                # Convert threshold alert Django events to BigQuery events
                for alert in threshold_alerts:
                    bq_alert = BigQueryEvent(
                        source_url=f"https://fred.stlouisfed.org/series/{series_id}",
                        mentioned_at=alert.timestamp,
                        created_at=timezone.now(),
                        title=alert.title,
                        content=alert.content.get('description', '') if isinstance(alert.content, dict) else str(alert.content),
                        source_name='FRED',
                        event_type='economic_alert',
                        location='Venezuela',
                        risk_score=None,  # Computed in Phase 4
                        severity=None,  # Computed in Phase 4
                        metadata={
                            'series_id': series_id,
                            'threshold_type': alert.content.get('threshold_type') if isinstance(alert.content, dict) else None,
                            'current_value': float(value),
                            'previous_value': previous_value,
                            'change_pct': ((float(value) - previous_value) / previous_value * 100) if previous_value else None
                        }
                    )
                    threshold_alert_events.append(bq_alert)
                    logger.info(f"Prepared threshold alert event: {bq_alert.title}")

            except Exception as e:
                logger.error(
                    f"Failed to prepare FRED indicator for {series_id} observation: {e}",
                    exc_info=True
                )
                observations_skipped += 1

        # Batch insert to BigQuery
        if fred_indicators:
            try:
                bigquery_service.insert_fred_indicators(fred_indicators)
                logger.info(f"Inserted {len(fred_indicators)} FRED indicators to BigQuery")
            except Exception as e:
                logger.error(f"Failed to insert FRED indicators to BigQuery: {e}", exc_info=True)
                raise

        # Insert threshold alert events
        if threshold_alert_events:
            try:
                bigquery_service.insert_events(threshold_alert_events)
                logger.info(f"Inserted {len(threshold_alert_events)} threshold alert events to BigQuery")

                # Dispatch LLM intelligence analysis for threshold alerts
                analyze_task = get_intelligence_task()
                for alert_event in threshold_alert_events:
                    analyze_task.delay(alert_event.id, model='standard')
                    logger.debug(f"Dispatched LLM analysis for FRED alert {alert_event.id}")

            except Exception as e:
                logger.error(f"Failed to insert threshold alert events to BigQuery: {e}", exc_info=True)
                # Don't raise - indicators are more important than alerts
                pass

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
