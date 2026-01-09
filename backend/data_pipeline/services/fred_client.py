"""
FRED (Federal Reserve Economic Data) API client wrapper.

Provides access to economic indicators with Secret Manager integration
for API key management.
"""
import logging
from typing import Optional
import pandas as pd
from fredapi import Fred

from data_pipeline.services.secrets import SecretManagerClient

logger = logging.getLogger(__name__)


class FREDClient:
    """
    Wrapper for FRED API with Secret Manager integration.

    Retrieves API key from Secret Manager (or environment variable)
    and provides convenience methods for fetching economic series data.
    """

    _instance: Optional[Fred] = None
    _api_key: Optional[str] = None

    def __init__(self):
        """
        Initialize FRED client with API key from Secret Manager.

        API key is cached to avoid repeated Secret Manager calls.
        """
        if FREDClient._instance is None:
            # Get API key from Secret Manager or environment
            try:
                secret_client = SecretManagerClient()
                FREDClient._api_key = secret_client.get_secret('api-fred-key')
                logger.info("FRED API key retrieved from Secret Manager")
            except ValueError as e:
                logger.warning(f"Failed to retrieve FRED API key from Secret Manager: {e}")
                logger.info("Make sure to set API_FRED_KEY environment variable or provision api-fred-key in Secret Manager")
                raise

            # Initialize Fred client
            FREDClient._instance = Fred(api_key=FREDClient._api_key)
            logger.info("FRED client initialized successfully")

        self.client = FREDClient._instance

    def get_series(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch economic series data from FRED.

        Args:
            series_id: FRED series identifier (e.g., 'DCOILWTICO' for WTI crude oil)
            start_date: Optional start date in 'YYYY-MM-DD' format
            end_date: Optional end date in 'YYYY-MM-DD' format

        Returns:
            pandas DataFrame with date index and series values

        Raises:
            Exception: If FRED API request fails
        """
        try:
            logger.debug(f"Fetching FRED series {series_id} (start={start_date}, end={end_date})")

            # Fetch series data
            data = self.client.get_series(
                series_id,
                observation_start=start_date,
                observation_end=end_date
            )

            # Convert Series to DataFrame for easier handling
            df = data.to_frame(name='value')
            df.index.name = 'date'

            logger.info(f"Fetched {len(df)} observations for series {series_id}")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch FRED series {series_id}: {e}", exc_info=True)
            raise

    def get_latest_observation(self, series_id: str) -> dict:
        """
        Fetch the most recent observation for a series.

        Args:
            series_id: FRED series identifier

        Returns:
            dict with {
                'series_id': str,
                'date': datetime,
                'value': float,
            }

        Raises:
            Exception: If FRED API request fails or series has no data
        """
        try:
            # Fetch last 1 observation
            data = self.client.get_series(series_id, observation_start='2020-01-01')

            if data is None or len(data) == 0:
                raise ValueError(f"No data available for series {series_id}")

            # Get latest observation
            latest_date = data.index[-1]
            latest_value = data.iloc[-1]

            result = {
                'series_id': series_id,
                'date': latest_date,
                'value': float(latest_value),
            }

            logger.info(f"Latest observation for {series_id}: {latest_value} on {latest_date}")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch latest observation for {series_id}: {e}", exc_info=True)
            raise

    def get_series_info(self, series_id: str) -> dict:
        """
        Fetch metadata about a FRED series.

        Args:
            series_id: FRED series identifier

        Returns:
            dict with series metadata (title, units, frequency, etc.)
        """
        try:
            info = self.client.get_series_info(series_id)
            return info.to_dict() if hasattr(info, 'to_dict') else dict(info)
        except Exception as e:
            logger.error(f"Failed to fetch series info for {series_id}: {e}", exc_info=True)
            raise
