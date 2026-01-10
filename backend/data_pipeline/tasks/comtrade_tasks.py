"""
UN Comtrade trade data ingestion tasks.

Fetches Venezuela import/export data with pagination and filtering
for significant trade flows.
"""
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from google.cloud import bigquery

from data_pipeline.tasks.base import BaseIngestionTask
from data_pipeline.services.comtrade_client import ComtradeClient
from data_pipeline.services.event_mapper import map_comtrade_to_event
from data_pipeline.config.comtrade_config import (
    get_all_commodities,
    get_commodity_config,
    MIN_TRADE_VALUE_USD,
)
from core.models import Event
from api.bigquery_models import UNComtrade
from api.services.bigquery_service import bigquery_service

logger = logging.getLogger(__name__)


@shared_task(base=BaseIngestionTask, bind=True)
def ingest_comtrade_trade_data(
    self,
    period: Optional[str] = None,
    lookback_months: int = 3
) -> Dict[str, Any]:
    """
    Ingest Venezuela trade data from UN Comtrade.

    Fetches import and export data for tracked commodities and creates
    Events for significant trade flows (> $10M USD).

    Args:
        period: Specific period in YYYYMM format (e.g., '202312')
                If None, calculates from lookback_months
        lookback_months: Number of months to look back (default: 3)

    Returns:
        {
            'commodities_processed': int,
            'trade_flows_created': int,
            'trade_flows_skipped': int,
            'total_trade_value_usd': float,
        }
    """
    logger.info(f"Starting Comtrade ingestion (period={period}, lookback={lookback_months})")

    # Calculate period if not provided
    if period is None:
        # Comtrade has 2-3 month lag, so look back appropriately
        target_date = datetime.now() - timedelta(days=30 * (lookback_months + 2))
        period = target_date.strftime('%Y%m')

    logger.info(f"Fetching Comtrade data for period: {period}")

    # Initialize client
    client = ComtradeClient()

    # Get commodities to track
    commodity_codes = get_all_commodities()
    logger.info(f"Tracking {len(commodity_codes)} commodities")

    # Track metrics
    commodities_processed = 0
    trade_flows_created = 0
    trade_flows_skipped = 0
    total_trade_value = 0.0

    # Batch collection for BigQuery
    comtrade_records = []

    # Process each commodity
    for commodity_code in commodity_codes:
        commodity_config = get_commodity_config(commodity_code)
        if not commodity_config:
            logger.warning(f"No configuration found for commodity {commodity_code}")
            continue

        logger.info(f"Processing commodity: {commodity_config['name']} ({commodity_code})")

        try:
            # Fetch imports and exports
            for flow_type, fetch_method in [('imports', client.get_imports), ('exports', client.get_exports)]:
                logger.info(f"Fetching {flow_type} for {commodity_code}")

                try:
                    df = fetch_method(period=period, commodity=commodity_code)

                    if df is None or len(df) == 0:
                        logger.info(f"No {flow_type} data for {commodity_code} in period {period}")
                        continue

                    logger.info(f"Found {len(df)} {flow_type} records for {commodity_code}")

                    # Process each trade flow
                    for _, row in df.iterrows():
                        trade_value = float(row.get('primaryValue', 0))

                        # Filter for significant flows only
                        if trade_value < MIN_TRADE_VALUE_USD:
                            trade_flows_skipped += 1
                            continue

                        # Parse period to date
                        period_str = str(row.get('period', ''))
                        try:
                            # YYYYMM format -> first day of month
                            period_date = datetime.strptime(period_str, '%Y%m').date()
                        except ValueError:
                            logger.warning(f"Invalid period format: {period_str}")
                            trade_flows_skipped += 1
                            continue

                        partner = row.get('partnerCode', '')
                        reporter = row.get('reporterCode', 'VEN')
                        flow_code = row.get('flowCode', 'M')
                        trade_flow_type = 'imports' if flow_code == 'M' else 'exports'

                        # Check for duplicate in BigQuery
                        try:
                            query = f"""
                                SELECT COUNT(*) as count
                                FROM `{settings.GCP_PROJECT_ID}.{settings.BIGQUERY_DATASET}.un_comtrade`
                                WHERE period = @period
                                AND reporter_code = @reporter_code
                                AND commodity_code = @commodity_code
                                AND trade_flow = @trade_flow
                            """
                            job_config = bigquery.QueryJobConfig(
                                query_parameters=[
                                    bigquery.ScalarQueryParameter('period', 'DATE', period_date),
                                    bigquery.ScalarQueryParameter('reporter_code', 'STRING', reporter),
                                    bigquery.ScalarQueryParameter('commodity_code', 'STRING', commodity_code),
                                    bigquery.ScalarQueryParameter('trade_flow', 'STRING', trade_flow_type)
                                ]
                            )
                            results = bigquery_service.client.query(query, job_config=job_config).result()
                            row_result = list(results)[0]
                            if row_result.count > 0:
                                logger.debug(f"Skipping duplicate trade flow: {commodity_code} {period_str} {trade_flow_type}")
                                trade_flows_skipped += 1
                                continue
                        except Exception as e:
                            logger.error(f"Failed to check for duplicate in BigQuery: {e}")
                            # Continue with insert - better to have duplicate than skip valid record
                            pass

                        # Create UNComtrade record for BigQuery
                        try:
                            comtrade_record = UNComtrade(
                                period=period_date,
                                reporter_code=reporter,
                                commodity_code=commodity_code,
                                trade_flow=trade_flow_type,
                                value_usd=trade_value
                            )
                            comtrade_records.append(comtrade_record)
                            trade_flows_created += 1
                            total_trade_value += trade_value
                            logger.debug(f"Prepared Comtrade record: {commodity_code} {trade_flow_type} ${trade_value:,.0f}")

                        except Exception as e:
                            logger.error(f"Failed to prepare Comtrade record: {e}", exc_info=True)
                            trade_flows_skipped += 1

                except Exception as e:
                    logger.error(f"Failed to fetch {flow_type} for {commodity_code}: {e}", exc_info=True)
                    continue

            commodities_processed += 1

        except Exception as e:
            logger.error(f"Failed to process commodity {commodity_code}: {e}", exc_info=True)
            continue

    # Batch insert to BigQuery
    if comtrade_records:
        try:
            bigquery_service.insert_un_comtrade(comtrade_records)
            logger.info(f"Inserted {len(comtrade_records)} Comtrade records to BigQuery")
        except Exception as e:
            logger.error(f"Failed to insert Comtrade records to BigQuery: {e}", exc_info=True)
            raise

    result = {
        'commodities_processed': commodities_processed,
        'trade_flows_created': trade_flows_created,
        'trade_flows_skipped': trade_flows_skipped,
        'total_trade_value_usd': total_trade_value,
    }

    logger.info(
        f"Comtrade ingestion complete: {commodities_processed} commodities, "
        f"{trade_flows_created} flows created, {trade_flows_skipped} skipped, "
        f"${total_trade_value/1_000_000:.1f}M total"
    )

    return result
