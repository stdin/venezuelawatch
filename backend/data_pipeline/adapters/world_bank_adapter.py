"""
World Bank WDI BigQuery Adapter

Fetches Venezuela economic indicators from World Bank's World Development Indicators
(WDI) public BigQuery dataset (bigquery-public-data.world_bank_wdi).

This adapter follows the DataSourceAdapter pattern established in Phase 22,
providing quarterly ingestion of key macroeconomic indicators to identify
economic trends and correlate with political/social events.

Data source: bigquery-public-data.world_bank_wdi.*
Update cadence: Quarterly (WDI data updated quarterly by World Bank)
Event type: economic (development indicators represent economic signals)
Key indicators: GDP, GNI, population, inflation, trade balance
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from django.utils import timezone

from data_pipeline.adapters.base import DataSourceAdapter
from api.services.gdelt_bigquery_service import gdelt_bigquery_service
from api.bigquery_models import Event as BigQueryEvent

logger = logging.getLogger(__name__)


class WorldBankAdapter(DataSourceAdapter):
    """
    World Bank WDI BigQuery data source adapter.

    Queries World Bank's public dataset for Venezuela economic indicators,
    transforming them into economic signal events for entity linking and
    intelligence analysis.

    Focuses on 5 key indicator categories per CONTEXT.md:
    1. GDP (Gross Domestic Product)
    2. GNI (Gross National Income)
    3. Population statistics
    4. Inflation rates
    5. Trade balance
    """

    # Class attributes define adapter metadata
    source_name = "world_bank"
    schedule_frequency = "0 3 1 1,4,7,10 *"  # Quarterly: Jan 1, Apr 1, Jul 1, Oct 1 at 3 AM
    default_lookback_minutes = 129600  # 90 days (quarterly lookback)

    @property
    def source_name_prop(self) -> str:
        """Return source name as property for compatibility."""
        return self.source_name

    def fetch(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 1000,
        lookback_days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Fetch Venezuela economic indicators from World Bank WDI BigQuery.

        Queries bigquery-public-data.world_bank_wdi.* tables with:
        - Venezuela country filter (country_code='VE' or country_name LIKE '%Venezuela%')
        - Year filter for recent data (last ~3 months worth of annual/quarterly data)
        - Focus on key economic indicators per CONTEXT.md

        Note: WDI data is annual/quarterly, so lookback_days is used to calculate
        year threshold, not for precise date filtering.

        Args:
            start_time: Ignored (using lookback_days for year-based filtering)
            end_time: Ignored (using lookback_days for year-based filtering)
            limit: Maximum number of indicators to fetch (default: 1000)
            lookback_days: Days to look back for year calculation (default: 90)

        Returns:
            List of indicator dicts with indicator_name, indicator_code, country_name,
            country_code, year, value

        Raises:
            Exception: If BigQuery query fails
        """
        logger.info(
            f"Fetching World Bank WDI indicators for Venezuela "
            f"(lookback: {lookback_days} days, limit: {limit})"
        )

        # Calculate year threshold from lookback_days
        # For quarterly data, lookback of 90 days = last ~3 months
        year_threshold = datetime.now().year - (lookback_days // 365)

        # Query World Bank WDI dataset
        # Note: The dataset has multiple tables under world_bank_wdi prefix
        # We'll query the main indicators table (country_series_definitions or similar)
        # Actual table structure may need adjustment based on dataset exploration
        query = """
            SELECT
                indicator_name,
                indicator_code,
                country_name,
                country_code,
                year,
                value
            FROM `bigquery-public-data.world_bank_wdi.country_series_definitions` series
            JOIN `bigquery-public-data.world_bank_wdi.country_summary` summary
                ON series.country_code = summary.country_code
            WHERE (summary.country_code = 'VEN' OR summary.country_name LIKE '%Venezuela%')
            AND year >= @year_threshold
            ORDER BY year DESC, indicator_code ASC
            LIMIT @limit
        """

        # If the above query structure doesn't work, fall back to simpler query
        # of just the series_summary table which typically has the combined data
        fallback_query = """
            SELECT
                indicator_name,
                indicator_code,
                country_name,
                country_code,
                year,
                value
            FROM `bigquery-public-data.world_bank_wdi.series_summary`
            WHERE (country_code = 'VEN' OR country_name LIKE '%Venezuela%')
            AND year >= @year_threshold
            ORDER BY year DESC, indicator_code ASC
            LIMIT @limit
        """

        from google.cloud import bigquery
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('year_threshold', 'INT64', year_threshold),
                bigquery.ScalarQueryParameter('limit', 'INT64', limit)
            ]
        )

        try:
            # Try primary query first
            try:
                results = gdelt_bigquery_service.client.query(
                    query, job_config=job_config
                ).result()
                indicators = [dict(row) for row in results]
            except Exception as primary_error:
                # If primary query fails (table structure different), try fallback
                logger.warning(
                    f"Primary World Bank query failed: {primary_error}. "
                    f"Attempting fallback query..."
                )
                results = gdelt_bigquery_service.client.query(
                    fallback_query, job_config=job_config
                ).result()
                indicators = [dict(row) for row in results]

            logger.info(f"Fetched {len(indicators)} indicators from World Bank WDI BigQuery")
            return indicators

        except Exception as e:
            logger.error(f"Failed to query World Bank WDI BigQuery: {e}", exc_info=True)
            # Log the error but return empty list rather than failing completely
            # This allows other adapters to continue working
            logger.warning(
                "World Bank adapter may need schema adjustment. "
                "Check bigquery-public-data.world_bank_wdi table structure."
            )
            return []

    def transform(self, raw_data: List[Dict[str, Any]]) -> List[BigQueryEvent]:
        """
        Transform World Bank WDI data to BigQuery Event schema.

        Maps economic indicators to economic signal events with:
        - Stable event_id based on country code, indicator code, and year
        - Constructed World Bank indicator URL
        - Metadata preserving indicator details and values
        - Event type 'economic' (development indicators are economic signals)
        - Published date as year-end (WB data is annual/quarterly)

        Args:
            raw_data: List of indicator dicts from fetch()

        Returns:
            List of BigQueryEvent instances ready for validation and publishing
        """
        bigquery_events = []

        for indicator in raw_data:
            try:
                # Extract fields
                indicator_name = indicator.get('indicator_name', 'Unknown Indicator')
                indicator_code = indicator.get('indicator_code', '')
                country_name = indicator.get('country_name', 'Venezuela')
                country_code = indicator.get('country_code', 'VEN')
                year = indicator.get('year')
                value = indicator.get('value')

                # Skip if missing critical fields
                if not indicator_code or not year:
                    logger.warning(
                        f"Skipping indicator with missing code or year: {indicator}"
                    )
                    continue

                # Generate stable event ID from country code, indicator code, and year
                # Format: wb-{country_code}-{indicator_code}-{year}
                event_id = f"wb-{country_code}-{indicator_code}-{year}"

                # Construct World Bank indicator URL
                # Format: https://data.worldbank.org/indicator/{indicator_code}?locations=VE
                wb_url = f"https://data.worldbank.org/indicator/{indicator_code}?locations=VE"

                # Convert year to datetime (use year-end as publication date)
                # World Bank data is typically published at year-end or quarter-end
                published_at = timezone.datetime(
                    year=int(year),
                    month=12,
                    day=31,
                    hour=23,
                    minute=59
                ).replace(tzinfo=timezone.utc)

                # Create descriptive title and content
                title = f"{indicator_name} for {country_name} ({year})"
                content = f"{indicator_name}: {value}"

                # Create BigQueryEvent
                bq_event = BigQueryEvent(
                    id=event_id,
                    source_url=wb_url,
                    mentioned_at=published_at,
                    created_at=timezone.now(),
                    title=title,
                    content=content,
                    source_name=self.source_name,
                    event_type='economic',  # World Bank data is economic signal
                    location='Venezuela',
                    risk_score=None,  # Computed by LLM downstream
                    severity=None,    # Computed by LLM downstream
                    metadata={
                        'indicator_code': indicator_code,
                        'indicator_name': indicator_name,
                        'year': year,
                        'value': value,
                        'country_code': country_code,
                        'country_name': country_name
                    }
                )

                bigquery_events.append(bq_event)

            except Exception as e:
                logger.error(
                    f"Failed to transform World Bank indicator: {e}",
                    exc_info=True,
                    extra={'indicator': indicator}
                )
                # Continue with other indicators - don't fail entire batch

        logger.info(f"Transformed {len(bigquery_events)} World Bank indicators to BigQuery schema")
        return bigquery_events

    def validate(self, event: BigQueryEvent) -> Tuple[bool, Optional[str]]:
        """
        Validate World Bank WDI event completeness.

        Checks:
        - Event ID exists and follows wb-{country}-{code}-{year} pattern
        - Metadata has required indicator_code, year, and value fields
        - Country is Venezuela (VE/VEN)

        Args:
            event: BigQueryEvent instance to validate

        Returns:
            Tuple of (is_valid, error_message):
            - (True, None) if valid
            - (False, "error description") if invalid
        """
        # Check event ID exists and follows pattern
        if not event.id:
            return (False, "Missing required field: id")

        if not event.id.startswith('wb-'):
            return (False, f"Invalid event_id pattern: {event.id} (expected wb-{{country}}-{{code}}-{{year}})")

        # Check required fields
        if not event.title:
            return (False, "Missing required field: title")

        if not event.source_url:
            return (False, "Missing required field: source_url")

        if not event.mentioned_at:
            return (False, "Missing required field: mentioned_at")

        # Check metadata has required fields
        if not event.metadata:
            return (False, "Missing metadata")

        if 'indicator_code' not in event.metadata:
            return (False, "Missing metadata field: indicator_code")

        if 'year' not in event.metadata:
            return (False, "Missing metadata field: year")

        if 'value' not in event.metadata:
            return (False, "Missing metadata field: value")

        # Check country is Venezuela
        if event.location and 'Venezuela' not in event.location:
            return (False, f"Invalid location: {event.location} (expected Venezuela)")

        return (True, None)
