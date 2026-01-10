"""
BigQuery client for Cloud Functions with Application Default Credentials.

Provides reusable BigQuery client setup and insert operations for ingestion functions.
No Django dependencies - pure GCP client library.
"""
import os
import logging
from typing import List, Dict, Any
from google.cloud import bigquery

logger = logging.getLogger(__name__)


class BigQueryClient:
    """BigQuery client wrapper for Cloud Functions."""

    def __init__(self):
        """Initialize BigQuery client with ADC and environment variables."""
        self.project_id = os.environ.get('GCP_PROJECT_ID')
        self.dataset_id = os.environ.get('BIGQUERY_DATASET', 'venezuelawatch')

        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID environment variable not set")

        # Initialize client with Application Default Credentials
        self.client = bigquery.Client(project=self.project_id)
        logger.info(f"BigQuery client initialized for project: {self.project_id}")

    def insert_events(self, events: List[Dict[str, Any]]) -> None:
        """
        Insert events to BigQuery events table using streaming insert.

        Args:
            events: List of event dicts with BigQuery schema format

        Raises:
            Exception: If insert fails with errors
        """
        if not events:
            logger.warning("No events to insert")
            return

        table_id = f"{self.project_id}.{self.dataset_id}.events"
        errors = self.client.insert_rows_json(table_id, events)

        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
            raise Exception(f"Failed to insert events to BigQuery: {errors}")

        logger.info(f"Successfully inserted {len(events)} events to BigQuery")

    def insert_fred_indicators(self, indicators: List[Dict[str, Any]]) -> None:
        """
        Insert FRED indicators to BigQuery fred_indicators table.

        Args:
            indicators: List of indicator dicts with BigQuery schema format

        Raises:
            Exception: If insert fails with errors
        """
        if not indicators:
            logger.warning("No FRED indicators to insert")
            return

        table_id = f"{self.project_id}.{self.dataset_id}.fred_indicators"
        errors = self.client.insert_rows_json(table_id, indicators)

        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
            raise Exception(f"Failed to insert FRED indicators: {errors}")

        logger.info(f"Successfully inserted {len(indicators)} FRED indicators to BigQuery")

    def insert_un_comtrade(self, records: List[Dict[str, Any]]) -> None:
        """
        Insert UN Comtrade records to BigQuery un_comtrade table.

        Args:
            records: List of trade flow dicts with BigQuery schema format

        Raises:
            Exception: If insert fails with errors
        """
        if not records:
            logger.warning("No Comtrade records to insert")
            return

        table_id = f"{self.project_id}.{self.dataset_id}.un_comtrade"
        errors = self.client.insert_rows_json(table_id, records)

        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
            raise Exception(f"Failed to insert Comtrade records: {errors}")

        logger.info(f"Successfully inserted {len(records)} Comtrade records to BigQuery")

    def insert_world_bank(self, indicators: List[Dict[str, Any]]) -> None:
        """
        Insert World Bank indicators to BigQuery world_bank table.

        Args:
            indicators: List of indicator dicts with BigQuery schema format

        Raises:
            Exception: If insert fails with errors
        """
        if not indicators:
            logger.warning("No World Bank indicators to insert")
            return

        table_id = f"{self.project_id}.{self.dataset_id}.world_bank"
        errors = self.client.insert_rows_json(table_id, indicators)

        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
            raise Exception(f"Failed to insert World Bank indicators: {errors}")

        logger.info(f"Successfully inserted {len(indicators)} World Bank indicators to BigQuery")

    def check_duplicate_event(self, event_id: str) -> bool:
        """
        Check if event ID already exists in BigQuery.

        Args:
            event_id: Event ID to check

        Returns:
            True if exists, False otherwise
        """
        query = f"""
            SELECT COUNT(*) as count
            FROM `{self.project_id}.{self.dataset_id}.events`
            WHERE id = @event_id
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('event_id', 'STRING', event_id)
            ]
        )

        try:
            results = self.client.query(query, job_config=job_config).result()
            row = list(results)[0]
            return row.count > 0
        except Exception as e:
            logger.error(f"Failed to check for duplicate event: {e}")
            return False

    def check_duplicate_by_url(self, source_url: str, days: int = 30) -> bool:
        """
        Check if event with source_url exists in last N days.

        Args:
            source_url: Source URL to check
            days: Lookback period in days

        Returns:
            True if exists, False otherwise
        """
        query = f"""
            SELECT COUNT(*) as count
            FROM `{self.project_id}.{self.dataset_id}.events`
            WHERE source_url = @url
            AND mentioned_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days DAY)
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('url', 'STRING', source_url),
                bigquery.ScalarQueryParameter('days', 'INT64', days)
            ]
        )

        try:
            results = self.client.query(query, job_config=job_config).result()
            row = list(results)[0]
            return row.count > 0
        except Exception as e:
            logger.error(f"Failed to check for duplicate by URL: {e}")
            return False

    def get_previous_fred_value(self, series_id: str, date: str) -> float:
        """
        Get previous FRED indicator value for a series.

        Args:
            series_id: FRED series ID
            date: Current observation date (ISO format)

        Returns:
            Previous value or None if not found
        """
        query = f"""
            SELECT value
            FROM `{self.project_id}.{self.dataset_id}.fred_indicators`
            WHERE series_id = @series_id
            AND date < @date
            ORDER BY date DESC
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('series_id', 'STRING', series_id),
                bigquery.ScalarQueryParameter('date', 'DATE', date)
            ]
        )

        try:
            results = self.client.query(query, job_config=job_config).result()
            rows = list(results)
            return rows[0].value if rows else None
        except Exception as e:
            logger.warning(f"Failed to get previous FRED value: {e}")
            return None
