"""
GDELT Native BigQuery service for querying gdelt-bq.gdeltv2 dataset.

Provides methods for fetching Venezuela-related events from GDELT's native
BigQuery dataset with efficient partitioning and rich event data.
"""
from google.cloud import bigquery
from django.conf import settings
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class GDELTBigQueryService:
    """Service for querying GDELT native BigQuery dataset."""

    def __init__(self):
        self.client = bigquery.Client(project=settings.GCP_PROJECT_ID)
        self.gdelt_project = "gdelt-bq"
        self.gdelt_dataset = "gdeltv2"

    def get_venezuela_events(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get Venezuela-related events from GDELT native BigQuery.

        Uses events_partitioned table with:
        - _PARTITIONTIME for efficient querying
        - ActionGeo_CountryCode='VE' for Venezuela
        - Actor1CountryCode or Actor2CountryCode='VE' for Venezuelan actors

        Args:
            start_time: Start of time range
            end_time: End of time range
            limit: Max events to return

        Returns:
            List of event dicts with GDELT schema
        """
        query = f"""
            SELECT
                GLOBALEVENTID,
                SQLDATE,
                MonthYear,
                Year,
                FractionDate,
                Actor1Code,
                Actor1Name,
                Actor1CountryCode,
                Actor1Type1Code,
                Actor1Type2Code,
                Actor1KnownGroupCode,
                Actor1EthnicCode,
                Actor1Religion1Code,
                Actor1Religion2Code,
                Actor2Code,
                Actor2Name,
                Actor2CountryCode,
                Actor2Type1Code,
                Actor2Type3Code,
                Actor2KnownGroupCode,
                Actor2EthnicCode,
                Actor2Religion1Code,
                Actor2Religion2Code,
                IsRootEvent,
                EventCode,
                EventBaseCode,
                EventRootCode,
                QuadClass,
                GoldsteinScale,
                NumMentions,
                NumSources,
                NumArticles,
                AvgTone,
                Actor1Geo_Type,
                Actor1Geo_FullName,
                Actor1Geo_CountryCode,
                Actor1Geo_ADM1Code,
                Actor1Geo_ADM2Code,
                Actor1Geo_FeatureID,
                Actor1Geo_Lat,
                Actor1Geo_Long,
                Actor2Geo_Type,
                Actor2Geo_FullName,
                Actor2Geo_CountryCode,
                Actor2Geo_ADM1Code,
                Actor2Geo_ADM2Code,
                Actor2Geo_FeatureID,
                Actor2Geo_Lat,
                Actor2Geo_Long,
                ActionGeo_Type,
                ActionGeo_FullName,
                ActionGeo_CountryCode,
                ActionGeo_ADM1Code,
                ActionGeo_ADM2Code,
                ActionGeo_FeatureID,
                ActionGeo_Lat,
                ActionGeo_Long,
                DATEADDED,
                SOURCEURL
            FROM `{self.gdelt_project}.{self.gdelt_dataset}.events_partitioned`
            WHERE _PARTITIONTIME >= @start_time
            AND _PARTITIONTIME < @end_time
            AND (
                ActionGeo_CountryCode = 'VE'
                OR Actor1CountryCode = 'VE'
                OR Actor2CountryCode = 'VE'
            )
            ORDER BY DATEADDED DESC
            LIMIT @limit
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('start_time', 'TIMESTAMP', start_time),
                bigquery.ScalarQueryParameter('end_time', 'TIMESTAMP', end_time),
                bigquery.ScalarQueryParameter('limit', 'INT64', limit)
            ]
        )

        try:
            results = self.client.query(query, job_config=job_config).result()
            events = [dict(row) for row in results]
            logger.info(f"Fetched {len(events)} Venezuela events from GDELT BigQuery")
            return events
        except Exception as e:
            logger.error(f"Failed to query GDELT BigQuery: {e}", exc_info=True)
            raise

    def get_event_mentions(
        self,
        global_event_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get all mentions of a specific GDELT event.

        Args:
            global_event_id: GDELT GLOBALEVENTID
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of mention dicts with URLs, tone, etc.
        """
        query = f"""
            SELECT
                GLOBALEVENTID,
                EventTimeDate,
                MentionTimeDate,
                MentionType,
                MentionSourceName,
                MentionIdentifier,
                SentenceID,
                Actor1CharOffset,
                Actor2CharOffset,
                ActionCharOffset,
                InRawText,
                Confidence,
                MentionDocLen,
                MentionDocTone
            FROM `{self.gdelt_project}.{self.gdelt_dataset}.eventmentions_partitioned`
            WHERE _PARTITIONTIME >= @start_time
            AND _PARTITIONTIME < @end_time
            AND GLOBALEVENTID = @event_id
            ORDER BY MentionTimeDate DESC
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('start_time', 'TIMESTAMP', start_time),
                bigquery.ScalarQueryParameter('end_time', 'TIMESTAMP', end_time),
                bigquery.ScalarQueryParameter('event_id', 'STRING', global_event_id)
            ]
        )

        try:
            results = self.client.query(query, job_config=job_config).result()
            mentions = [dict(row) for row in results]
            return mentions
        except Exception as e:
            logger.error(f"Failed to query GDELT event mentions: {e}", exc_info=True)
            raise


# Singleton instance
gdelt_bigquery_service = GDELTBigQueryService()
