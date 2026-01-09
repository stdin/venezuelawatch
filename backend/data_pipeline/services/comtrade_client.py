"""
UN Comtrade API client wrapper.

Provides access to international trade statistics with Secret Manager integration
for API key management and rate limiting.
"""
import logging
import os
from typing import Optional
import pandas as pd
import comtradeapicall

from data_pipeline.services.secrets import SecretManagerClient

logger = logging.getLogger(__name__)


class ComtradeClient:
    """
    Wrapper for UN Comtrade API with Secret Manager integration.

    Retrieves optional API key from Secret Manager (or environment variable)
    and provides convenience methods for fetching Venezuela trade data.

    Note: API key is optional but recommended (500 req/day with key vs 100/day without)
    """

    _api_key: Optional[str] = None
    _initialized: bool = False

    def __init__(self):
        """
        Initialize Comtrade client with optional API key from Secret Manager.

        API key is cached to avoid repeated Secret Manager calls.
        Falls back to no auth if key not available (100 req/day limit).
        """
        if not ComtradeClient._initialized:
            # Try to get API key from Secret Manager or environment
            try:
                secret_client = SecretManagerClient()
                ComtradeClient._api_key = secret_client.get_secret('api-comtrade-key')
                logger.info("Comtrade API key retrieved from Secret Manager")
            except ValueError as e:
                # API key is optional - continue without authentication
                logger.warning(f"No Comtrade API key found (operating with 100 req/day limit): {e}")
                logger.info("Register at https://comtradeplus.un.org/ to get an API key (500 req/day)")
                ComtradeClient._api_key = None

            ComtradeClient._initialized = True
            logger.info("Comtrade client initialized successfully")

        self.api_key = ComtradeClient._api_key

    def get_trade_data(
        self,
        reporter: str = 'VEN',
        period: Optional[str] = None,
        commodity: str = 'TOTAL',
        flow_code: str = 'M',  # M=imports, X=exports
        partner: str = 'all',
    ) -> pd.DataFrame:
        """
        Fetch trade data for Venezuela from UN Comtrade.

        Args:
            reporter: ISO3 country code (default: 'VEN' for Venezuela)
            period: Time period in format YYYY or YYYYMM (e.g., '2023', '202312')
                    If None, fetches most recent available
            commodity: HS commodity code (e.g., '2709' for crude oil) or 'TOTAL'
            flow_code: 'M' for imports, 'X' for exports
            partner: Partner country ISO3 code or 'all'

        Returns:
            pandas DataFrame with trade data columns:
            - period, reporterCode, partnerCode, cmdCode
            - flowCode, primaryValue, netWeight, quantityUnit
        """
        try:
            # Comtradeapicall library uses different method based on parameters
            # Note: Library API may vary by version, using basic approach

            # Build request parameters
            params = {
                'r': reporter,  # Reporter country
                'p': partner,   # Partner country
                'ps': period if period else 'recent',  # Period
                'px': commodity,  # Commodity code (px = HS classification)
                'rg': flow_code,  # Flow code (M=import, X=export)
            }

            # Add API key if available
            if self.api_key:
                params['token'] = self.api_key

            # Fetch data using comtradeapicall
            # The library's previewFinalData function returns a DataFrame
            df = comtradeapicall.previewFinalData(**params)

            if df is None or len(df) == 0:
                logger.warning(f"No trade data found for {reporter}, period={period}, commodity={commodity}")
                return pd.DataFrame()

            logger.info(f"Fetched {len(df)} trade records for {reporter} (period={period}, commodity={commodity})")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch Comtrade trade data: {e}", exc_info=True)
            raise

    def get_imports(
        self,
        period: Optional[str] = None,
        commodity: str = 'TOTAL',
        partner: str = 'all',
    ) -> pd.DataFrame:
        """
        Fetch Venezuela import data.

        Convenience method for get_trade_data with flow_code='M'.

        Args:
            period: Time period (YYYY or YYYYMM)
            commodity: HS commodity code or 'TOTAL'
            partner: Partner country ISO3 code or 'all'

        Returns:
            pandas DataFrame with import trade flows
        """
        return self.get_trade_data(
            reporter='VEN',
            period=period,
            commodity=commodity,
            flow_code='M',
            partner=partner,
        )

    def get_exports(
        self,
        period: Optional[str] = None,
        commodity: str = 'TOTAL',
        partner: str = 'all',
    ) -> pd.DataFrame:
        """
        Fetch Venezuela export data.

        Convenience method for get_trade_data with flow_code='X'.

        Args:
            period: Time period (YYYY or YYYYMM)
            commodity: HS commodity code or 'TOTAL'
            partner: Partner country ISO3 code or 'all'

        Returns:
            pandas DataFrame with export trade flows
        """
        return self.get_trade_data(
            reporter='VEN',
            period=period,
            commodity=commodity,
            flow_code='X',
            partner=partner,
        )

    def get_latest_period(self) -> Optional[str]:
        """
        Get the most recent available period in Comtrade.

        Returns:
            Period string (e.g., '202312') or None if unavailable
        """
        try:
            # Fetch a small dataset to check latest available period
            df = self.get_exports(commodity='TOTAL')
            if df is not None and len(df) > 0 and 'period' in df.columns:
                # Return the most recent period
                latest = df['period'].max()
                return str(latest)
            return None
        except Exception as e:
            logger.warning(f"Could not determine latest period: {e}")
            return None
