"""
World Bank API client wrapper.

Provides access to development indicators using the wbgapi library.
No authentication required for World Bank Open Data.
"""
import logging
from typing import Optional, Dict, Any
import wbgapi as wb

logger = logging.getLogger(__name__)


class WorldBankClient:
    """
    Wrapper for World Bank Open Data API.

    No authentication required. Uses wbgapi (official World Bank library).
    """

    def __init__(self):
        """Initialize World Bank client (no auth required)."""
        logger.info("World Bank client initialized successfully")

    def get_indicator(
        self,
        indicator_id: str,
        country: str = 'VE',
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Fetch indicator data for Venezuela from World Bank.

        Args:
            indicator_id: World Bank indicator code (e.g., 'NY.GDP.MKTP.CD')
            country: ISO2 country code (default: 'VE' for Venezuela)
            start_year: Starting year (e.g., 2015)
            end_year: Ending year (e.g., 2023)

        Returns:
            dict with format:
            {
                'indicator_id': str,
                'country': str,
                'data': [{'year': int, 'value': float}, ...]
            }
        """
        try:
            # Fetch data using wbgapi
            data_points = []

            # Build time range
            time_range = range(start_year, end_year + 1) if start_year and end_year else None

            # Fetch data
            result = wb.data.DataFrame(indicator_id, country, time=time_range, skipBlanks=True)

            if result is None or result.empty:
                logger.warning(f"No data found for indicator {indicator_id} (country={country})")
                return {'indicator_id': indicator_id, 'country': country, 'data': []}

            # Convert DataFrame to list of dicts
            for year_col in result.columns:
                value = result[year_col].values[0] if len(result[year_col].values) > 0 else None
                if value is not None:
                    data_points.append({
                        'year': int(year_col.replace('YR', '')) if isinstance(year_col, str) else int(year_col),
                        'value': float(value),
                    })

            logger.info(f"Fetched {len(data_points)} observations for {indicator_id}")

            return {
                'indicator_id': indicator_id,
                'country': country,
                'data': data_points,
            }

        except Exception as e:
            logger.error(f"Failed to fetch World Bank indicator {indicator_id}: {e}", exc_info=True)
            raise

    def get_latest_value(
        self,
        indicator_id: str,
        country: str = 'VE',
    ) -> Optional[Dict[str, Any]]:
        """
        Get the most recent value for an indicator.

        Args:
            indicator_id: World Bank indicator code
            country: ISO2 country code (default: 'VE')

        Returns:
            dict with {'year': int, 'value': float} or None if no data
        """
        try:
            # Fetch recent data (last 10 years)
            data = self.get_indicator(indicator_id, country, start_year=2015, end_year=2025)

            if not data.get('data'):
                return None

            # Return most recent non-null value
            latest = max(data['data'], key=lambda x: x['year'])
            return latest

        except Exception as e:
            logger.warning(f"Could not get latest value for {indicator_id}: {e}")
            return None
