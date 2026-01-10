"""
GDELT Mentions BigQuery service for tracking media attention to events.

Provides methods for querying the eventmentions_partitioned table (2.5B rows, 532GB)
with rolling window statistics for spike detection.

Critical performance requirement: ALL queries MUST include _PARTITIONTIME filter
to avoid full table scans of 532GB dataset.
"""
from google.cloud import bigquery
from django.conf import settings
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class GDELTMentionsService:
    """Service for querying GDELT Mentions BigQuery dataset with rolling statistics."""

    def __init__(self):
        self.client = bigquery.Client(project=settings.GCP_PROJECT_ID)
        self.gdelt_project = "gdelt-bq"
        self.gdelt_dataset = "gdeltv2"

    def get_mention_stats(
        self,
        event_ids: List[str],
        lookback_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get daily mention counts with 7-day rolling statistics for events.

        Calculates rolling average and standard deviation using window functions
        over a 7-day window EXCLUDING the current day (prevents spike from inflating
        its own baseline).

        Performance: Uses _PARTITIONTIME filter to limit scan to lookback_days
        instead of full 532GB table.

        Args:
            event_ids: List of GLOBALEVENTID strings from BigQuery events
            lookback_days: Days to look back for calculating baselines (default: 30)

        Returns:
            List of dicts with keys:
            - event_id: GLOBALEVENTID
            - mention_date: Date of mentions
            - mention_count: Number of mentions on that date
            - rolling_avg: 7-day rolling average (excluding current day)
            - rolling_stddev: 7-day rolling standard deviation (excluding current day)

            Returns only last 7 days to focus on recent spike candidates.
        """
        if not event_ids:
            return []

        query = f"""
            WITH daily_counts AS (
                SELECT
                    GLOBALEVENTID,
                    DATE(PARSE_TIMESTAMP('%Y%m%d', CAST(MentionTimeDate AS STRING))) AS mention_date,
                    COUNT(*) AS mention_count
                FROM `{self.gdelt_project}.{self.gdelt_dataset}.eventmentions_partitioned`
                WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @lookback_days DAY)
                AND GLOBALEVENTID IN UNNEST(@event_ids)
                GROUP BY GLOBALEVENTID, mention_date
            ),
            stats_calc AS (
                SELECT
                    GLOBALEVENTID,
                    mention_date,
                    mention_count,
                    AVG(mention_count) OVER (
                        PARTITION BY GLOBALEVENTID
                        ORDER BY mention_date
                        ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
                    ) AS rolling_avg,
                    STDDEV_POP(mention_count) OVER (
                        PARTITION BY GLOBALEVENTID
                        ORDER BY mention_date
                        ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
                    ) AS rolling_stddev
                FROM daily_counts
            )
            SELECT
                GLOBALEVENTID AS event_id,
                mention_date,
                mention_count,
                rolling_avg,
                rolling_stddev
            FROM stats_calc
            WHERE mention_date >= CURRENT_DATE() - 7
            ORDER BY mention_date DESC, mention_count DESC
        """

        # Convert event_ids to INT64 array (BigQuery type requirement)
        try:
            event_ids_int = [int(eid) for eid in event_ids]
        except ValueError as e:
            logger.error(f"Invalid event ID format (expected numeric): {e}")
            return []

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter('event_ids', 'INT64', event_ids_int),
                bigquery.ScalarQueryParameter('lookback_days', 'INT64', lookback_days)
            ]
        )

        try:
            results = self.client.query(query, job_config=job_config).result()
            rows = []

            for row in results:
                rows.append({
                    'event_id': str(row['event_id']),  # Convert back to string for consistency
                    'mention_date': row['mention_date'],
                    'mention_count': row['mention_count'],
                    'rolling_avg': row['rolling_avg'] if row['rolling_avg'] is not None else 0.0,
                    'rolling_stddev': row['rolling_stddev'] if row['rolling_stddev'] is not None else 0.0,
                })

            logger.info(f"Fetched mention stats for {len(event_ids)} events, got {len(rows)} daily records")
            return rows

        except Exception as e:
            logger.error(f"Failed to query mentions for {len(event_ids)} events: {e}", exc_info=True)
            # Return empty list instead of raising - don't break pipelines on mentions fetch errors
            return []


# Singleton instance
gdelt_mentions_service = GDELTMentionsService()
