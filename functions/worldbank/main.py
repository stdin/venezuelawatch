"""
World Bank development indicators Cloud Function.

Fetches Venezuela development indicators from World Bank API.
HTTP trigger for Cloud Scheduler invocation (monthly).
"""
import functions_framework
import logging
from datetime import datetime
from typing import Dict, Any
from flask import Request
import wbgapi as wb
import sys
import os

# Add shared utilities to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from bigquery_client import BigQueryClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Venezuela Development Indicators
VENEZUELA_INDICATORS = {
    'NY.GDP.MKTP.CD': {
        'name': 'GDP (current USD)',
        'category': 'economic',
        'units': 'current USD',
    },
    'FP.CPI.TOTL.ZG': {
        'name': 'Inflation (CPI)',
        'category': 'economic',
        'units': 'percent',
    },
    'NY.GDP.PCAP.CD': {
        'name': 'GDP per capita',
        'category': 'economic',
        'units': 'current USD',
    },
    'SL.UEM.TOTL.ZS': {
        'name': 'Unemployment rate',
        'category': 'labor',
        'units': 'percent',
    },
    'SI.POV.NAHC': {
        'name': 'Poverty headcount ratio',
        'category': 'social',
        'units': 'percent',
    },
    'SE.XPD.TOTL.GD.ZS': {
        'name': 'Education expenditure (% GDP)',
        'category': 'social',
        'units': 'percent',
    },
    'SH.XPD.CHEX.GD.ZS': {
        'name': 'Health expenditure (% GDP)',
        'category': 'social',
        'units': 'percent',
    },
    'EG.ELC.ACCS.ZS': {
        'name': 'Electricity access (%)',
        'category': 'infrastructure',
        'units': 'percent',
    },
    'IT.NET.USER.ZS': {
        'name': 'Internet users (%)',
        'category': 'infrastructure',
        'units': 'percent',
    },
    'SP.POP.TOTL': {
        'name': 'Population total',
        'category': 'demographic',
        'units': 'people',
    },
}


@functions_framework.http
def sync_worldbank(request: Request):
    """
    HTTP Cloud Function to sync World Bank development indicators.

    Request JSON body:
        {
            "lookback_years": 2  // Optional, default: 2
        }

    Returns:
        JSON response with sync statistics
    """
    try:
        # Parse request
        request_json = request.get_json(silent=True) or {}
        lookback_years = request_json.get('lookback_years', 2)

        logger.info(f"Starting World Bank ingestion (lookback_years={lookback_years})")

        # Initialize clients
        bq_client = BigQueryClient()

        # Calculate year range
        current_year = datetime.utcnow().year
        start_year = current_year - lookback_years
        end_year = current_year

        indicators_processed = 0
        observations_created = 0
        observations_skipped = 0
        indicators_failed = 0
        worldbank_indicators = []

        # Process each indicator
        for indicator_id, indicator_config in VENEZUELA_INDICATORS.items():
            logger.info(f"Processing indicator: {indicator_config['name']} ({indicator_id})")

            try:
                # Fetch indicator data using wbgapi
                time_range = range(start_year, end_year + 1)
                result = wb.data.DataFrame(indicator_id, 'VE', time=time_range, skipBlanks=True)

                if result is None or result.empty:
                    logger.warning(f"No data available for {indicator_id}")
                    indicators_failed += 1
                    continue

                # Convert DataFrame to records
                data_points = []
                for year_col in result.columns:
                    value = result[year_col].values[0] if len(result[year_col].values) > 0 else None
                    if value is not None:
                        # Extract year from column name (e.g., 'YR2023' -> 2023)
                        year = int(year_col.replace('YR', '')) if isinstance(year_col, str) else int(year_col)
                        data_points.append({
                            'year': year,
                            'value': float(value),
                        })

                logger.info(f"Found {len(data_points)} observations for {indicator_id}")

                # Process each observation
                for data_point in data_points:
                    year = data_point['year']
                    value = data_point['value']

                    # Convert year to date (January 1st)
                    indicator_date = datetime(year=year, month=1, day=1).date()

                    # Create World Bank indicator record
                    wb_indicator = {
                        'indicator_id': indicator_id,
                        'date': indicator_date.isoformat(),
                        'value': float(value) if value is not None else None,
                        'country_code': 'VE'
                    }
                    worldbank_indicators.append(wb_indicator)
                    observations_created += 1
                    logger.debug(f"Prepared World Bank indicator: {indicator_id} {year} = {value}")

                indicators_processed += 1

            except Exception as e:
                logger.error(f"Failed to process indicator {indicator_id}: {e}", exc_info=True)
                indicators_failed += 1
                continue

        # Batch insert to BigQuery
        if worldbank_indicators:
            try:
                bq_client.insert_world_bank(worldbank_indicators)
                logger.info(f"Inserted {len(worldbank_indicators)} World Bank indicators to BigQuery")
            except Exception as e:
                logger.error(f"Failed to insert World Bank indicators: {e}", exc_info=True)
                return {
                    'error': str(e),
                    'indicators_processed': indicators_processed,
                    'observations_created': 0
                }, 500

        result = {
            'indicators_processed': indicators_processed,
            'observations_created': observations_created,
            'observations_skipped': observations_skipped,
            'indicators_failed': indicators_failed,
        }

        logger.info(
            f"World Bank ingestion complete: {indicators_processed} indicators, "
            f"{observations_created} observations, {indicators_failed} failed"
        )

        return result, 200

    except Exception as e:
        logger.error(f"World Bank ingestion failed: {e}", exc_info=True)
        return {'error': str(e)}, 500
