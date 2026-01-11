"""
Shared Pub/Sub publisher utility for Cloud Functions.

Provides consistent event publishing pattern for ingestion functions
to trigger downstream processing (intelligence analysis, entity extraction).

Usage:
    from shared.pubsub_publisher import publisher

    # Publish event for analysis
    publisher.publish_event_analysis(event_id='abc-123', model='fast')
"""
import os
import json
import logging
from google.cloud import pubsub_v1

logger = logging.getLogger(__name__)


class PubSubPublisher:
    """Pub/Sub publisher for event analysis triggers."""

    def __init__(self):
        """Initialize publisher with GCP project configuration."""
        self.client = pubsub_v1.PublisherClient()
        self.project_id = os.environ.get('GCP_PROJECT_ID', 'venezuelawatch-staging')

    def publish_event_analysis(self, event_id: str, model: str = 'fast') -> str:
        """
        Publish event for intelligence analysis.

        Publishes to 'event-analysis' Pub/Sub topic, which triggers:
        1. Pub/Sub push subscription to /api/internal/process-event
        2. Cloud Tasks enqueue to /api/internal/analyze-intelligence
        3. LLM intelligence analysis
        4. Pub/Sub publish to entity-extraction topic

        Args:
            event_id: BigQuery event ID (UUID string)
            model: LLM model tier ('fast', 'standard', 'premium')

        Returns:
            Message ID from Pub/Sub publish

        Raises:
            Exception: If publish fails after retries
        """
        topic_path = self.client.topic_path(self.project_id, 'event-analysis')

        message_data = json.dumps({
            'event_id': event_id,
            'model': model
        }).encode('utf-8')

        try:
            # Publish with blocking wait for confirmation
            future = self.client.publish(topic_path, message_data)
            message_id = future.result(timeout=30)  # Wait up to 30 seconds

            logger.info(f"Published event analysis trigger: event_id={event_id}, message_id={message_id}")
            return message_id

        except Exception as e:
            logger.error(f"Failed to publish event analysis trigger: {e}", exc_info=True)
            raise

    def publish_batch_events(self, event_ids: list, model: str = 'fast') -> int:
        """
        Publish multiple events for analysis in batch.

        Uses non-blocking publish with futures for better throughput.

        Args:
            event_ids: List of BigQuery event IDs
            model: LLM model tier for all events

        Returns:
            Count of successfully published messages

        Raises:
            Exception: If any publish fails
        """
        topic_path = self.client.topic_path(self.project_id, 'event-analysis')

        futures = []
        for event_id in event_ids:
            message_data = json.dumps({
                'event_id': event_id,
                'model': model
            }).encode('utf-8')

            future = self.client.publish(topic_path, message_data)
            futures.append((event_id, future))

        # Wait for all publishes to complete
        published_count = 0
        for event_id, future in futures:
            try:
                message_id = future.result(timeout=30)
                logger.debug(f"Published {event_id}: message_id={message_id}")
                published_count += 1
            except Exception as e:
                logger.error(f"Failed to publish {event_id}: {e}")
                # Continue publishing remaining events

        logger.info(f"Batch published {published_count}/{len(event_ids)} events")
        return published_count


# Singleton instance for import
publisher = PubSubPublisher()
