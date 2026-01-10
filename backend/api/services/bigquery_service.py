"""
BigQuery service layer for VenezuelaWatch time-series data.

Provides methods for inserting and querying time-series data in BigQuery.
Uses google-cloud-bigquery client library with parameterized queries for security.
"""

from google.cloud import bigquery
from django.conf import settings
from typing import List, Optional
from datetime import datetime
from api.bigquery_models import Event, EntityMention, FREDIndicator, UNComtrade, WorldBank


class BigQueryService:
    """Service for interacting with BigQuery time-series data."""

    def __init__(self):
        """Initialize BigQuery client with Django settings."""
        self.project_id = settings.GCP_PROJECT_ID
        self.dataset_id = settings.BIGQUERY_DATASET
        self.client = bigquery.Client(project=self.project_id)

    # Insert methods
    def insert_events(self, events: List[Event]) -> None:
        """Insert events using streaming insert."""
        if not events:
            return

        table_id = f"{self.project_id}.{self.dataset_id}.events"
        rows = [event.to_bigquery_row() for event in events]
        errors = self.client.insert_rows_json(table_id, rows)

        if errors:
            raise Exception(f"BigQuery insert errors: {errors}")

    def insert_entity_mentions(self, mentions: List[EntityMention]) -> None:
        """Insert entity mentions using streaming insert."""
        if not mentions:
            return

        table_id = f"{self.project_id}.{self.dataset_id}.entity_mentions"
        rows = [mention.to_bigquery_row() for mention in mentions]
        errors = self.client.insert_rows_json(table_id, rows)

        if errors:
            raise Exception(f"BigQuery insert errors: {errors}")

    def insert_fred_indicators(self, indicators: List[FREDIndicator]) -> None:
        """Insert FRED economic indicators using streaming insert."""
        if not indicators:
            return

        table_id = f"{self.project_id}.{self.dataset_id}.fred_indicators"
        rows = [ind.to_bigquery_row() for ind in indicators]
        errors = self.client.insert_rows_json(table_id, rows)

        if errors:
            raise Exception(f"BigQuery insert errors: {errors}")

    def insert_un_comtrade(self, records: List[UNComtrade]) -> None:
        """Insert UN Comtrade trade records using streaming insert."""
        if not records:
            return

        table_id = f"{self.project_id}.{self.dataset_id}.un_comtrade"
        rows = [rec.to_bigquery_row() for rec in records]
        errors = self.client.insert_rows_json(table_id, rows)

        if errors:
            raise Exception(f"BigQuery insert errors: {errors}")

    def insert_world_bank(self, indicators: List[WorldBank]) -> None:
        """Insert World Bank development indicators using streaming insert."""
        if not indicators:
            return

        table_id = f"{self.project_id}.{self.dataset_id}.world_bank"
        rows = [ind.to_bigquery_row() for ind in indicators]
        errors = self.client.insert_rows_json(table_id, rows)

        if errors:
            raise Exception(f"BigQuery insert errors: {errors}")

    # Query methods
    def get_recent_events(
        self,
        start_date: datetime,
        end_date: datetime,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        min_risk_score: Optional[float] = None,
        max_risk_score: Optional[float] = None,
        limit: int = 100
    ) -> List[dict]:
        """
        Get recent events with optional filtering.

        Args:
            start_date: Start of time range
            end_date: End of time range
            event_type: Filter by event type (optional)
            severity: Filter by severity level (SEV1-SEV5, optional)
            min_risk_score: Minimum risk score (0-100, optional)
            max_risk_score: Maximum risk score (0-100, optional)
            limit: Maximum number of results

        Returns:
            List of event dicts
        """
        query = f"""
            SELECT *
            FROM `{self.project_id}.{self.dataset_id}.events`
            WHERE mentioned_at BETWEEN @start_date AND @end_date
        """

        params = [
            bigquery.ScalarQueryParameter('start_date', 'TIMESTAMP', start_date),
            bigquery.ScalarQueryParameter('end_date', 'TIMESTAMP', end_date),
        ]

        if event_type:
            query += " AND event_type = @event_type"
            params.append(bigquery.ScalarQueryParameter('event_type', 'STRING', event_type))

        if severity:
            query += " AND severity = @severity"
            params.append(bigquery.ScalarQueryParameter('severity', 'STRING', severity))

        if min_risk_score is not None:
            query += " AND risk_score >= @min_risk_score"
            params.append(bigquery.ScalarQueryParameter('min_risk_score', 'FLOAT64', min_risk_score))

        if max_risk_score is not None:
            query += " AND risk_score <= @max_risk_score"
            params.append(bigquery.ScalarQueryParameter('max_risk_score', 'FLOAT64', max_risk_score))

        query += " ORDER BY mentioned_at DESC LIMIT @limit"
        params.append(bigquery.ScalarQueryParameter('limit', 'INT64', limit))

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        results = self.client.query(query, job_config=job_config).result()

        return [dict(row) for row in results]

    def get_event_by_id(self, event_id: str) -> Optional[dict]:
        """
        Get single event by ID.

        Args:
            event_id: Event ID (UUID string)

        Returns:
            Event dict or None if not found
        """
        query = f"""
            SELECT *
            FROM `{self.project_id}.{self.dataset_id}.events`
            WHERE id = @event_id
            LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('event_id', 'STRING', event_id)
            ]
        )

        results = self.client.query(query, job_config=job_config).result()
        row = next(results, None)

        return dict(row) if row else None

    def get_entity_trending(
        self,
        metric: str = 'mentions',
        limit: int = 20
    ) -> List[dict]:
        """
        Get trending entities using exponential time-decay.
        7-day half-life (168 hours) for time-decay calculation.

        Args:
            metric: 'mentions', 'risk', or 'sanctions'
            limit: Number of top entities to return
        """
        if metric == 'mentions':
            # Time-decay weighted mention count
            query = f"""
                SELECT
                    entity_id,
                    SUM(EXP(-(TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), mentioned_at, HOUR) / 168.0) * LN(2))) as score
                FROM `{self.project_id}.{self.dataset_id}.entity_mentions`
                WHERE mentioned_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
                GROUP BY entity_id
                ORDER BY score DESC
                LIMIT @limit
            """
        elif metric == 'risk':
            # Average risk score of events mentioning entity
            query = f"""
                SELECT
                    em.entity_id,
                    AVG(e.risk_score) as score
                FROM `{self.project_id}.{self.dataset_id}.entity_mentions` em
                JOIN `{self.project_id}.{self.dataset_id}.events` e ON em.event_id = e.id
                WHERE em.mentioned_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
                GROUP BY em.entity_id
                ORDER BY score DESC
                LIMIT @limit
            """
        elif metric == 'sanctions':
            # Count of sanctioned events mentioning entity
            query = f"""
                SELECT
                    em.entity_id,
                    COUNT(*) as score
                FROM `{self.project_id}.{self.dataset_id}.entity_mentions` em
                JOIN `{self.project_id}.{self.dataset_id}.events` e ON em.event_id = e.id
                WHERE em.mentioned_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
                AND e.event_type = 'sanctions'
                GROUP BY em.entity_id
                ORDER BY score DESC
                LIMIT @limit
            """
        else:
            raise ValueError(f"Invalid metric: {metric}. Must be 'mentions', 'risk', or 'sanctions'")

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('limit', 'INT64', limit)
            ]
        )

        results = self.client.query(query, job_config=job_config).result()
        return [{'entity_id': row.entity_id, 'score': float(row.score)} for row in results]

    def get_risk_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        bucket_size: str = 'DAY'
    ) -> List[dict]:
        """
        Get risk trends over time with time-bucket aggregation.

        Args:
            start_date: Start of time range
            end_date: End of time range
            bucket_size: 'DAY', 'WEEK', or 'MONTH'
        """
        if bucket_size == 'DAY':
            trunc_format = 'DAY'
        elif bucket_size == 'WEEK':
            trunc_format = 'WEEK'
        elif bucket_size == 'MONTH':
            trunc_format = 'MONTH'
        else:
            raise ValueError(f"Invalid bucket_size: {bucket_size}. Must be 'DAY', 'WEEK', or 'MONTH'")

        query = f"""
            SELECT
                TIMESTAMP_TRUNC(mentioned_at, {trunc_format}) as time_bucket,
                AVG(risk_score) as avg_risk_score,
                MAX(risk_score) as max_risk_score,
                COUNT(*) as event_count
            FROM `{self.project_id}.{self.dataset_id}.events`
            WHERE mentioned_at BETWEEN @start_date AND @end_date
            AND risk_score IS NOT NULL
            GROUP BY time_bucket
            ORDER BY time_bucket ASC
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('start_date', 'TIMESTAMP', start_date),
                bigquery.ScalarQueryParameter('end_date', 'TIMESTAMP', end_date)
            ]
        )

        results = self.client.query(query, job_config=job_config).result()
        return [dict(row) for row in results]

    def get_entity_events(
        self,
        entity_id: str,
        limit: int = 50,
        days: int = 90
    ) -> List[dict]:
        """
        Get recent events mentioning an entity.

        Args:
            entity_id: Entity ID (UUID string)
            limit: Maximum number of events to return
            days: Lookback period in days

        Returns:
            List of event dicts
        """
        query = f"""
            SELECT e.*
            FROM `{self.project_id}.{self.dataset_id}.events` e
            JOIN `{self.project_id}.{self.dataset_id}.entity_mentions` em ON e.id = em.event_id
            WHERE em.entity_id = @entity_id
            AND em.mentioned_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days DAY)
            ORDER BY e.mentioned_at DESC
            LIMIT @limit
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('entity_id', 'STRING', entity_id),
                bigquery.ScalarQueryParameter('days', 'INT64', days),
                bigquery.ScalarQueryParameter('limit', 'INT64', limit)
            ]
        )

        results = self.client.query(query, job_config=job_config).result()
        return [dict(row) for row in results]

    def search_events(
        self,
        query: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 20
    ) -> List[dict]:
        """
        Search events by text query (LIKE search on title and content).

        Args:
            query: Search query string
            start_date: Start of time range
            end_date: End of time range
            limit: Maximum number of results

        Returns:
            List of matching event dicts
        """
        bq_query = f"""
            SELECT *
            FROM `{self.project_id}.{self.dataset_id}.events`
            WHERE (title LIKE @query OR content LIKE @query)
            AND mentioned_at BETWEEN @start_date AND @end_date
            ORDER BY mentioned_at DESC
            LIMIT @limit
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('query', 'STRING', f'%{query}%'),
                bigquery.ScalarQueryParameter('start_date', 'TIMESTAMP', start_date),
                bigquery.ScalarQueryParameter('end_date', 'TIMESTAMP', end_date),
                bigquery.ScalarQueryParameter('limit', 'INT64', limit)
            ]
        )

        results = self.client.query(bq_query, job_config=job_config).result()
        return [dict(row) for row in results]

    def get_entity_stats(self, entity_id: str, days: int = 90) -> dict:
        """
        Get aggregated stats for entity profile.

        Args:
            entity_id: Entity ID (UUID string)
            days: Lookback period in days

        Returns:
            Dict with aggregated statistics
        """
        query = f"""
            SELECT
                COUNT(DISTINCT em.event_id) as total_mentions,
                COUNT(DISTINCT CASE WHEN e.event_type = 'sanctions' THEN e.id END) as sanctions_count,
                AVG(e.risk_score) as avg_risk_score,
                MAX(e.risk_score) as max_risk_score
            FROM `{self.project_id}.{self.dataset_id}.entity_mentions` em
            JOIN `{self.project_id}.{self.dataset_id}.events` e ON em.event_id = e.id
            WHERE em.entity_id = @entity_id
            AND em.mentioned_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days DAY)
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('entity_id', 'STRING', entity_id),
                bigquery.ScalarQueryParameter('days', 'INT64', days)
            ]
        )

        results = self.client.query(query, job_config=job_config).result()
        row = next(results, None)

        if row:
            return {
                'total_mentions': row.total_mentions or 0,
                'sanctions_count': row.sanctions_count or 0,
                'avg_risk_score': float(row.avg_risk_score) if row.avg_risk_score else 0.0,
                'max_risk_score': float(row.max_risk_score) if row.max_risk_score else 0.0
            }
        return {'total_mentions': 0, 'sanctions_count': 0, 'avg_risk_score': 0.0, 'max_risk_score': 0.0}


# Singleton instance for convenient importing
bigquery_service = BigQueryService()
