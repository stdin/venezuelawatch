"""
UN Comtrade trade data Cloud Function.

Fetches Venezuela import/export data from UN Comtrade API.
HTTP trigger for Cloud Scheduler invocation (monthly).
"""
import functions_framework
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from flask import Request
import comtradeapicall
import sys
import os

# Add shared utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from bigquery_client import BigQueryClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Venezuela Commodity Codes
VENEZUELA_COMMODITIES = {
    '2709': {'name': 'Petroleum oils (crude)', 'category': 'energy'},
    '2710': {'name': 'Petroleum oils (refined)', 'category': 'energy'},
    '1001': {'name': 'Wheat', 'category': 'food'},
    '1005': {'name': 'Maize (corn)', 'category': 'food'},
    '0201': {'name': 'Beef (fresh/chilled)', 'category': 'food'},
    '3004': {'name': 'Medicaments', 'category': 'healthcare'},
    '8471': {'name': 'Computing machinery', 'category': 'technology'},
    '8517': {'name': 'Telephone/communication equipment', 'category': 'technology'},
    'TOTAL': {'name': 'All commodities', 'category': 'total_trade'},
}

MIN_TRADE_VALUE_USD = 10_000_000  # $10 million


def get_trade_data(
    period: str,
    commodity: str,
    flow_code: str
) -> pd.DataFrame:
    """
    Fetch trade data from UN Comtrade.

    Args:
        period: Period in YYYYMM format
        commodity: HS commodity code
        flow_code: 'M' for imports, 'X' for exports

    Returns:
        DataFrame with trade data
    """
    try:
        # Venezuela = 862 (numeric code)
        reporter_numeric = '862'
        partner_numeric = '0'  # World (all partners)

        # Call previewFinalData
        df = comtradeapicall.previewFinalData(
            typeCode='C',              # Commodities
            freqCode='M',              # Monthly
            clCode='HS',               # Harmonized System
            period=period,
            reporterCode=reporter_numeric,
            cmdCode=commodity,
            flowCode=flow_code,
            partnerCode=partner_numeric,
            partner2Code=None,
            customsCode=None,
            motCode=None,
            maxRecords=None,
        )

        return df if df is not None else pd.DataFrame()

    except Exception as e:
        logger.error(f"Failed to fetch Comtrade data: {e}", exc_info=True)
        return pd.DataFrame()


@functions_framework.http
def sync_comtrade(request: Request):
    """
    HTTP Cloud Function to sync UN Comtrade trade data.

    Request JSON body:
        {
            "lookback_months": 3  // Optional, default: 3
        }

    Returns:
        JSON response with sync statistics
    """
    try:
        # Parse request
        request_json = request.get_json(silent=True) or {}
        lookback_months = request_json.get('lookback_months', 3)

        logger.info(f"Starting Comtrade ingestion (lookback: {lookback_months} months)")

        # Initialize clients
        bq_client = BigQueryClient()

        # Calculate period (Comtrade has 2-3 month lag)
        target_date = datetime.utcnow() - timedelta(days=30 * (lookback_months + 2))
        period = target_date.strftime('%Y%m')

        logger.info(f"Fetching Comtrade data for period: {period}")

        commodities_processed = 0
        trade_flows_created = 0
        trade_flows_skipped = 0
        total_trade_value = 0.0
        comtrade_records = []

        # Process each commodity
        for commodity_code, commodity_config in VENEZUELA_COMMODITIES.items():
            logger.info(f"Processing commodity: {commodity_config['name']} ({commodity_code})")

            try:
                # Fetch imports and exports
                for flow_type, flow_code in [('imports', 'M'), ('exports', 'X')]:
                    logger.info(f"Fetching {flow_type} for {commodity_code}")

                    df = get_trade_data(period, commodity_code, flow_code)

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

                        reporter = row.get('reporterCode', 'VEN')
                        trade_flow_type = 'imports' if flow_code == 'M' else 'exports'

                        # Create Comtrade record
                        record = {
                            'period': period_date.isoformat(),
                            'reporter_code': reporter,
                            'commodity_code': commodity_code,
                            'trade_flow': trade_flow_type,
                            'value_usd': trade_value
                        }
                        comtrade_records.append(record)
                        trade_flows_created += 1
                        total_trade_value += trade_value

                commodities_processed += 1

            except Exception as e:
                logger.error(f"Failed to process commodity {commodity_code}: {e}", exc_info=True)
                continue

        # Batch insert to BigQuery
        if comtrade_records:
            try:
                bq_client.insert_un_comtrade(comtrade_records)
                logger.info(f"Inserted {len(comtrade_records)} Comtrade records to BigQuery")
            except Exception as e:
                logger.error(f"Failed to insert Comtrade records: {e}", exc_info=True)
                return {
                    'error': str(e),
                    'commodities_processed': commodities_processed,
                    'trade_flows_created': 0
                }, 500

        result = {
            'commodities_processed': commodities_processed,
            'trade_flows_created': trade_flows_created,
            'trade_flows_skipped': trade_flows_skipped,
            'total_trade_value_usd': total_trade_value,
        }

        logger.info(
            f"Comtrade ingestion complete: {commodities_processed} commodities, "
            f"{trade_flows_created} flows, ${total_trade_value/1_000_000:.1f}M total"
        )

        return result, 200

    except Exception as e:
        logger.error(f"Comtrade ingestion failed: {e}", exc_info=True)
        return {'error': str(e)}, 500
