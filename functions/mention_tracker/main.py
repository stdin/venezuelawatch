"""
Mention Tracker Cloud Function.

Tracks mention spikes for Venezuela events with daily z-score analysis.
HTTP trigger for Cloud Scheduler invocation (daily at 2 AM UTC).
"""
import functions_framework
from google.cloud import bigquery
import psycopg2
import os
from datetime import datetime, timedelta
from typing import List, Dict
import logging

from services.gdelt_mentions_service import GDELTMentionsService
from services.spike_detection_service import spike_detection_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@functions_framework.http
def mention_tracker(request):
    """
    Track mention spikes for Venezuela events.
    Triggered daily by Cloud Scheduler at 2 AM UTC.

    Returns:
        JSON response with tracking statistics
    """
    try:
        logger.info("Starting mention spike tracking")

        # Step 1: Get Venezuela event IDs from BigQuery (last 30 days)
        event_ids = get_venezuela_event_ids()
        logger.info(f"Tracking mentions for {len(event_ids)} Venezuela events")

        if not event_ids:
            logger.warning("No Venezuela events found in last 30 days")
            return {
                "status": "success",
                "events_tracked": 0,
                "spikes_detected": 0,
                "spikes_stored": 0
            }, 200

        # Step 2: Fetch mention statistics with rolling windows
        mentions_service = GDELTMentionsService()
        mention_stats = mentions_service.get_mention_stats(
            event_ids=event_ids,
            lookback_days=30
        )
        logger.info(f"Fetched mention stats for {len(mention_stats)} event-days")

        # Step 3: Detect spikes using z-score analysis
        spikes = spike_detection_service.detect_spikes(mention_stats)
        logger.info(f"Detected {len(spikes)} spikes (z >= 2.0)")

        # Step 4: Store spikes in PostgreSQL
        spike_count = 0
        if spikes:
            spike_count = store_spikes(spikes)
            logger.info(f"Stored {spike_count} new spikes")

        result = {
            "status": "success",
            "events_tracked": len(event_ids),
            "spikes_detected": len(spikes),
            "spikes_stored": spike_count
        }

        logger.info(f"Mention tracking complete: {result}")
        return result, 200

    except Exception as e:
        logger.error(f"Mention tracking failed: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}, 500


def get_venezuela_event_ids() -> List[str]:
    """Fetch Venezuela event IDs from last 30 days in BigQuery."""
    project_id = os.getenv('GCP_PROJECT_ID')
    if not project_id:
        raise ValueError("GCP_PROJECT_ID environment variable not set")

    client = bigquery.Client(project=project_id)

    query = """
        SELECT DISTINCT CAST(GLOBALEVENTID AS STRING) AS event_id
        FROM `gdelt-bq.gdeltv2.events_partitioned`
        WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        AND (
            ActionGeo_CountryCode = 'VE'
            OR Actor1CountryCode = 'VE'
            OR Actor2CountryCode = 'VE'
        )
    """

    try:
        results = client.query(query).result()
        event_ids = [row['event_id'] for row in results]
        logger.info(f"Fetched {len(event_ids)} Venezuela event IDs from BigQuery")
        return event_ids
    except Exception as e:
        logger.error(f"Failed to fetch Venezuela event IDs: {e}", exc_info=True)
        return []


def store_spikes(spikes: List[Dict]) -> int:
    """Store detected spikes in PostgreSQL using bulk INSERT with ON CONFLICT."""
    # Get database credentials from environment
    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }

    # Validate required credentials
    if not all([db_config['host'], db_config['database'], db_config['user'], db_config['password']]):
        raise ValueError("Missing required database credentials in environment variables")

    conn = psycopg2.connect(**db_config)

    try:
        cursor = conn.cursor()

        # Bulk INSERT with ON CONFLICT DO NOTHING (unique_together constraint)
        insert_query = """
            INSERT INTO data_pipeline_mentionspike
            (event_id, spike_date, mention_count, baseline_avg, baseline_stddev,
             z_score, confidence_level, detected_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (event_id, spike_date) DO NOTHING
        """

        values = [
            (
                spike['event_id'],
                spike['spike_date'],
                spike['mention_count'],
                spike['baseline_avg'],
                spike['baseline_stddev'],
                spike['z_score'],
                spike['confidence_level'],
                datetime.utcnow()
            )
            for spike in spikes
        ]

        cursor.executemany(insert_query, values)
        inserted_count = cursor.rowcount
        conn.commit()

        logger.info(f"Inserted {inserted_count} spikes to PostgreSQL (duplicates skipped)")
        return inserted_count

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to store spikes: {e}", exc_info=True)
        raise
    finally:
        conn.close()
