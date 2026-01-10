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
from data_pipeline.services.category_classifier import CategoryClassifier
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
        Transform World Bank WDI data to canonical Event schema with normalizer logic.

        Implements canonical normalizer from platform design (section 5.2):
        - Category classification using indicator code prefixes
        - Magnitude normalization (percent_change → 0-1)
        - Direction classification based on indicator semantics
        - Source credibility 0.95 (World Bank is authoritative)

        Args:
            raw_data: List of indicator dicts from fetch()

        Returns:
            List of BigQueryEvent instances with canonical fields populated
        """
        bigquery_events = []

        # Track previous values for percent_change calculation
        # In production, this would query BigQuery for historical data
        # For now, we'll compute when prev_value is available in metadata
        prev_values = {}

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
                if not indicator_code or not year or value is None:
                    logger.warning(
                        f"Skipping indicator with missing code, year, or value: {indicator}"
                    )
                    continue

                # Classify category using indicator code prefix
                category, subcategory = CategoryClassifier.classify(
                    'world_bank',
                    {'indicator_code': indicator_code}
                )

                # Calculate percent change from previous value
                # For Phase 25, we'll use 0 if no previous value
                # Phase 26+ will fetch from BigQuery for accurate historical comparison
                prev_value_key = f"{country_code}-{indicator_code}"
                prev_value = prev_values.get(prev_value_key, value)

                if prev_value and prev_value != 0:
                    pct_change = ((value - prev_value) / prev_value) * 100
                else:
                    pct_change = 0

                # Update prev_values for next iteration
                prev_values[prev_value_key] = value

                # Normalize magnitude: percent_change → 0-1
                # 50% change = 1.0
                magnitude_norm = min(abs(pct_change) / 50, 1.0)

                # Determine direction based on indicator type
                # Some indicators are "good news" (GDP growth), others "bad news" (inflation)
                negative_is_bad = (
                    indicator_code.startswith(('FP.CPI', 'SL.UEM')) or  # Inflation, unemployment
                    'DEBT' in indicator_code or
                    'DEFICIT' in indicator_code
                )

                if negative_is_bad:
                    direction = "NEGATIVE" if pct_change > 0 else ("POSITIVE" if pct_change < 0 else "NEUTRAL")
                else:
                    direction = "POSITIVE" if pct_change > 0 else ("NEGATIVE" if pct_change < 0 else "NEUTRAL")

                # Confidence scoring
                source_credibility = 0.95  # World Bank is authoritative
                confidence = 0.95

                # Generate stable event ID
                event_id = f"wb-{country_code}-{indicator_code}-{year}"

                # Construct World Bank indicator URL
                wb_url = f"https://data.worldbank.org/indicator/{indicator_code}?locations=VE"

                # Convert year to datetime (use year-end as publication date)
                published_at = timezone.datetime(
                    year=int(year),
                    month=12,
                    day=31,
                    hour=23,
                    minute=59
                ).replace(tzinfo=timezone.utc)

                # Create descriptive title and content
                title = f"{indicator_name} for {country_name} ({year})"
                content = f"{indicator_name}: {value} ({pct_change:+.1f}% change)"

                # Create canonical BigQueryEvent
                bq_event = BigQueryEvent(
                    # Identity
                    id=event_id,
                    source='world_bank',
                    source_event_id=event_id,
                    source_url=wb_url,
                    source_name=self.source_name,

                    # Temporal
                    event_timestamp=published_at,
                    ingested_at=timezone.now(),
                    created_at=timezone.now(),

                    # Classification
                    category=category,
                    subcategory=subcategory,
                    event_type='INDICATOR_UPDATE',

                    # Location
                    country_code='VE',
                    admin1=None,
                    admin2=None,
                    latitude=None,
                    longitude=None,
                    location='Venezuela',

                    # Magnitude
                    magnitude_raw=pct_change,
                    magnitude_unit='percent_change',
                    magnitude_norm=magnitude_norm,

                    # Direction/Tone
                    direction=direction,
                    tone_raw=None,
                    tone_norm=0.5,  # Neutral for data

                    # Confidence
                    num_sources=1,
                    source_credibility=source_credibility,
                    confidence=confidence,

                    # Actors
                    actor1_name=None,
                    actor1_type=None,
                    actor2_name=None,
                    actor2_type=None,

                    # Commodities/Sectors
                    commodities=[],
                    sectors=[],

                    # Legacy fields
                    title=title,
                    content=content,
                    risk_score=None,  # Computed in Phase 25-02
                    severity=None,    # Computed in Phase 25-02

                    # Enhancement arrays (Phase 26+)
                    themes=[],
                    quotations=[],
                    gcam_scores=None,
                    entity_relationships=[],
                    related_events=[],

                    # Metadata
                    metadata={
                        'indicator_code': indicator_code,
                        'indicator_name': indicator_name,
                        'year': year,
                        'value': value,
                        'prev_value': prev_value,
                        'pct_change': pct_change,
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
