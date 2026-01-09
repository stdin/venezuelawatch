"""
UN Comtrade trade data ingestion tasks.

Fetches Venezuela import/export data with pagination and filtering
for significant trade flows.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from celery import shared_task
from django.db import transaction
from django.utils import timezone

from data_pipeline.tasks.base import BaseIngestionTask
from data_pipeline.services.comtrade_client import ComtradeClient
from data_pipeline.services.event_mapper import map_comtrade_to_event
from data_pipeline.config.comtrade_config import (
    get_all_commodities,
    get_commodity_config,
    MIN_TRADE_VALUE_USD,
)
from core.models import Event

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

                        # Check for duplicate
                        period_str = str(row.get('period', ''))
                        partner = row.get('partnerCode', '')
                        flow_code = row.get('flowCode', 'M')

                        existing = Event.objects.filter(
                            source='COMTRADE',
                            content__period=period_str,
                            content__commodity_code=commodity_code,
                            content__partner_country=partner,
                            content__flow_type='imports' if flow_code == 'M' else 'exports'
                        ).exists()

                        if existing:
                            logger.debug(f"Skipping duplicate trade flow: {commodity_code} {period_str} {partner}")
                            trade_flows_skipped += 1
                            continue

                        # Map to Event
                        try:
                            trade_record = row.to_dict()
                            event = map_comtrade_to_event(trade_record, commodity_config)

                            # Save to database
                            with transaction.atomic():
                                event.save()
                                trade_flows_created += 1
                                total_trade_value += trade_value
                                logger.debug(f"Created trade flow event: {event.title}")

                        except Exception as e:
                            logger.error(f"Failed to create event for trade flow: {e}", exc_info=True)
                            trade_flows_skipped += 1

                except Exception as e:
                    logger.error(f"Failed to fetch {flow_type} for {commodity_code}: {e}", exc_info=True)
                    continue

            commodities_processed += 1

        except Exception as e:
            logger.error(f"Failed to process commodity {commodity_code}: {e}", exc_info=True)
            continue

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
