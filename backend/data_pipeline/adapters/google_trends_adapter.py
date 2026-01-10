"""
Google Trends BigQuery Adapter

Fetches Venezuela-related search trends from Google's public BigQuery dataset
(bigquery-public-data.google_trends.international_top_terms).

This adapter follows the DataSourceAdapter pattern established in Phase 22,
providing daily polling of trending search terms in Venezuela to identify
emerging public interest and social signals.

Data source: bigquery-public-data.google_trends.international_top_terms
Update cadence: Daily (refresh_date updated daily)
Event type: social (search behavior represents social signals)
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from django.utils import timezone

from data_pipeline.adapters.base import DataSourceAdapter
from api.services.gdelt_bigquery_service import gdelt_bigquery_service
from api.bigquery_models import Event as BigQueryEvent

logger = logging.getLogger(__name__)


class GoogleTrendsAdapter(DataSourceAdapter):
    """
    Google Trends BigQuery data source adapter.

    Queries Google's public dataset for trending search terms in Venezuela,
    transforming them into social signal events for entity linking and
    intelligence analysis.
    """

    # Class attributes define adapter metadata
    source_name = "google_trends"
    schedule_frequency = "0 2 * * *"  # Daily at 2 AM UTC (after Google refreshes data)
    default_lookback_minutes = 1440  # 24 hours

    @property
    def source_name_prop(self) -> str:
        """Return source name as property for compatibility."""
        return self.source_name

    def fetch(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100,
        lookback_days: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Fetch trending search terms for Venezuela from Google Trends BigQuery.

        Queries bigquery-public-data.google_trends.international_top_terms with:
        - Partition filter on refresh_date for cost optimization
        - Venezuela country filter
        - Lookback window for incremental polling

        Args:
            start_time: Ignored (using lookback_days instead for date-partitioned data)
            end_time: Ignored (using lookback_days instead)
            limit: Maximum number of trends to fetch (default: 100)
            lookback_days: Number of days to look back (default: 1)

        Returns:
            List of trend dicts with term, rank, score, refresh_date, country_name, region_name

        Raises:
            Exception: If BigQuery query fails
        """
        logger.info(
            f"Fetching Google Trends for Venezuela (lookback: {lookback_days} days, limit: {limit})"
        )

        # Use partition filtering per RESEARCH.md best practices to minimize data scanned
        query = """
            SELECT
                term,
                rank,
                score,
                refresh_date,
                country_name,
                region_name
            FROM `bigquery-public-data.google_trends.international_top_terms`
            WHERE refresh_date = DATE_SUB(CURRENT_DATE(), INTERVAL @lookback_days DAY)
            AND country_name = 'Venezuela'
            ORDER BY rank ASC
            LIMIT @limit
        """

        from google.cloud import bigquery
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('lookback_days', 'INT64', lookback_days),
                bigquery.ScalarQueryParameter('limit', 'INT64', limit)
            ]
        )

        try:
            # Reuse existing BigQuery client from gdelt_bigquery_service
            results = gdelt_bigquery_service.client.query(query, job_config=job_config).result()
            trends = [dict(row) for row in results]
            logger.info(f"Fetched {len(trends)} trending terms from Google Trends BigQuery")
            return trends
        except Exception as e:
            logger.error(f"Failed to query Google Trends BigQuery: {e}", exc_info=True)
            raise

    def transform(self, raw_data: List[Dict[str, Any]]) -> List[BigQueryEvent]:
        """
        Transform Google Trends data to BigQuery Event schema.

        Maps trending search terms to social signal events with:
        - Stable event_id based on date and term
        - Constructed Google Trends URL for each term
        - Metadata preserving rank, score, geographic context
        - Event type 'social' (search behavior is social signal)

        Args:
            raw_data: List of trend dicts from fetch()

        Returns:
            List of BigQueryEvent instances ready for validation and publishing
        """
        bigquery_events = []

        for trend in raw_data:
            try:
                # Extract fields
                term = trend.get('term', '')
                rank = trend.get('rank')
                score = trend.get('score')
                refresh_date = trend.get('refresh_date')
                country_name = trend.get('country_name', 'Venezuela')
                region_name = trend.get('region_name', '')

                # Generate stable event ID from refresh_date and term
                # Format: gt-YYYY-MM-DD-normalized-term
                term_slug = term.lower().replace(' ', '-').replace('/', '-')
                event_id = f"gt-{refresh_date}-{term_slug}"

                # Construct Google Trends explore URL
                # Format: https://trends.google.com/trends/explore?q=term&geo=VE
                import urllib.parse
                term_encoded = urllib.parse.quote_plus(term)
                trends_url = f"https://trends.google.com/trends/explore?q={term_encoded}&geo=VE"

                # Convert refresh_date to datetime (midnight UTC)
                if isinstance(refresh_date, str):
                    published_at = timezone.datetime.strptime(refresh_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                else:
                    # refresh_date is already a date object
                    published_at = timezone.datetime.combine(
                        refresh_date,
                        timezone.datetime.min.time()
                    ).replace(tzinfo=timezone.utc)

                # Create descriptive content
                content = f"Search interest rank #{rank} with score {score} in Venezuela"
                if region_name:
                    content += f" (region: {region_name})"

                # Create BigQueryEvent
                bq_event = BigQueryEvent(
                    id=event_id,
                    source_url=trends_url,
                    mentioned_at=published_at,
                    created_at=timezone.now(),
                    title=term,
                    content=content,
                    source_name=self.source_name,
                    event_type='social',  # Search behavior is social signal
                    location='Venezuela',
                    risk_score=None,  # Computed by LLM downstream
                    severity=None,    # Computed by LLM downstream
                    metadata={
                        'rank': rank,
                        'score': score,
                        'country': country_name,
                        'region': region_name,
                        'refresh_date': str(refresh_date)
                    }
                )

                bigquery_events.append(bq_event)

            except Exception as e:
                logger.error(f"Failed to transform Google Trends data: {e}", exc_info=True)
                # Continue with other trends - don't fail entire batch

        logger.info(f"Transformed {len(bigquery_events)} Google Trends to BigQuery schema")
        return bigquery_events

    def validate(self, event: BigQueryEvent) -> Tuple[bool, Optional[str]]:
        """
        Validate Google Trends event completeness.

        Checks:
        - Event ID exists and follows gt-{date}-{term} pattern
        - Metadata has required rank and score fields
        - Country is Venezuela (VE)

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

        if not event.id.startswith('gt-'):
            return (False, f"Invalid event_id pattern: {event.id} (expected gt-YYYY-MM-DD-term)")

        # Check required fields
        if not event.title:
            return (False, "Missing required field: title (search term)")

        if not event.source_url:
            return (False, "Missing required field: source_url")

        if not event.mentioned_at:
            return (False, "Missing required field: mentioned_at")

        # Check metadata has required fields
        if not event.metadata:
            return (False, "Missing metadata")

        if 'rank' not in event.metadata:
            return (False, "Missing metadata field: rank")

        if 'score' not in event.metadata:
            return (False, "Missing metadata field: score")

        # Check country is Venezuela (events should be VE-specific)
        # Note: location is full name "Venezuela", metadata contains ISO code if available
        if event.location and 'Venezuela' not in event.location:
            return (False, f"Invalid location: {event.location} (expected Venezuela)")

        return (True, None)
