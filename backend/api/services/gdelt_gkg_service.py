"""
GDELT Global Knowledge Graph (GKG) BigQuery service.

Provides methods for fetching GKG enrichment data (themes, entities, sentiment)
for GDELT events via DocumentIdentifier lookup.
"""
from google.cloud import bigquery
from django.conf import settings
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class GDELTGKGService:
    """Service for querying GDELT GKG BigQuery dataset."""

    def __init__(self):
        self.client = bigquery.Client(project=settings.GCP_PROJECT_ID)
        self.gdelt_project = "gdelt-bq"
        self.gdelt_dataset = "gdeltv2"

    def get_gkg_by_document_id(
        self,
        document_id: str,
        partition_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Get GKG record for a specific document (news article).

        Queries gkg_partitioned table by DocumentIdentifier with partition filtering.
        DocumentIdentifier matches SOURCEURL from events table.

        Note: Many events won't have matching GKG records. Returns None if not found.

        Args:
            document_id: DocumentIdentifier (typically a URL)
            partition_date: Date for _PARTITIONTIME filtering (performance critical)

        Returns:
            GKG record dict with V2 fields, or None if not found
        """
        query = f"""
            SELECT
                GKGRECORDID,
                DATE,
                DocumentIdentifier,
                SourceCommonName,
                V2Themes,
                V2Persons,
                V2Organizations,
                V2Locations,
                V2Tone,
                Quotations,
                GCAM,
                AllNames
            FROM `{self.gdelt_project}.{self.gdelt_dataset}.gkg_partitioned`
            WHERE _PARTITIONTIME = @partition_date
            AND DocumentIdentifier = @document_id
            LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('partition_date', 'DATE', partition_date.date()),
                bigquery.ScalarQueryParameter('document_id', 'STRING', document_id)
            ]
        )

        try:
            results = self.client.query(query, job_config=job_config).result()
            rows = list(results)

            if not rows:
                # No GKG record found - this is normal, not an error
                return None

            gkg_record = dict(rows[0])
            logger.debug(f"Found GKG record for document: {document_id[:50]}...")
            return gkg_record

        except Exception as e:
            logger.error(f"Failed to query GKG for document {document_id[:50]}: {e}", exc_info=True)
            # Return None instead of raising - don't break sync on GKG fetch errors
            return None


# Singleton instance
gdelt_gkg_service = GDELTGKGService()
