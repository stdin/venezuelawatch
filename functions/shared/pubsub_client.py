"""
Pub/Sub client for Cloud Functions.

Publishes event IDs to 'event-analysis' topic for LLM processing.
No Django dependencies.
"""
import os
import logging
import json
from typing import List
from google.cloud import pubsub_v1

logger = logging.getLogger(__name__)


class PubSubClient:
    """Pub/Sub client wrapper for publishing event analysis tasks."""

    def __init__(self):
        """Initialize Pub/Sub publisher client."""
        self.project_id = os.environ.get('GCP_PROJECT_ID')

        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID environment variable not set")

        self.publisher = pubsub_v1.PublisherClient()
        self.topic_name = f"projects/{self.project_id}/topics/event-analysis"

        logger.info(f"Pub/Sub client initialized for topic: {self.topic_name}")

    def publish_event_for_analysis(self, event_id: str, model: str = 'fast') -> None:
        """
        Publish event ID to Pub/Sub for LLM analysis.

        Args:
            event_id: Event ID to analyze
            model: LLM model to use ('fast' or 'standard')
        """
        message_data = {
            'event_id': event_id,
            'model': model
        }

        # Encode message as JSON bytes
        message_bytes = json.dumps(message_data).encode('utf-8')

        try:
            # Publish message
            future = self.publisher.publish(self.topic_name, message_bytes)
            message_id = future.result()

            logger.debug(f"Published event {event_id} for analysis (message_id: {message_id})")
        except Exception as e:
            logger.error(f"Failed to publish event {event_id} to Pub/Sub: {e}")
            # Don't raise - event ingestion should succeed even if Pub/Sub fails

    def publish_events_for_analysis(self, event_ids: List[str], model: str = 'fast') -> None:
        """
        Publish multiple event IDs to Pub/Sub for LLM analysis.

        Args:
            event_ids: List of event IDs to analyze
            model: LLM model to use ('fast' or 'standard')
        """
        if not event_ids:
            return

        published_count = 0
        failed_count = 0

        for event_id in event_ids:
            try:
                self.publish_event_for_analysis(event_id, model)
                published_count += 1
            except Exception as e:
                logger.error(f"Failed to publish event {event_id}: {e}")
                failed_count += 1

        logger.info(f"Published {published_count} events for analysis ({failed_count} failed)")
