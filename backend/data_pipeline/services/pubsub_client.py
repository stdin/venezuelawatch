"""
GCP Pub/Sub client for event-driven architecture.

Provides:
- Event publishing (ingestion → raw-events topic)
- Event subscription (raw-events → processing)
- Topic management
- Message serialization/deserialization
"""
import logging
import json
import os
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from google.cloud import pubsub_v1
from google.api_core import retry
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class PubSubClient:
    """
    GCP Pub/Sub client for VenezuelaWatch event bus.

    Topics:
    - raw-events: Raw data from external APIs
    - processed-events: After intelligence analysis
    - high-risk-events: Events with risk_score > 0.7
    - humanitarian-events: Humanitarian crisis events
    - anomaly-events: Detected anomalies
    """

    _publisher: Optional[pubsub_v1.PublisherClient] = None
    _subscriber: Optional[pubsub_v1.SubscriberClient] = None
    _initialized: bool = False

    # Topic names
    TOPIC_RAW_EVENTS = "raw-events"
    TOPIC_PROCESSED_EVENTS = "processed-events"
    TOPIC_HIGH_RISK = "high-risk-events"
    TOPIC_HUMANITARIAN = "humanitarian-events"
    TOPIC_ANOMALY = "anomaly-events"

    # Project configuration
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "venezuelawatch-staging")

    @classmethod
    def initialize(cls, credentials_path: Optional[str] = None):
        """
        Initialize Pub/Sub clients.

        Args:
            credentials_path: Path to service account JSON (optional)
        """
        if cls._initialized:
            return

        try:
            # Load credentials if provided
            credentials = None
            if credentials_path and os.path.exists(credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path
                )
                logger.info(f"Loaded service account credentials from {credentials_path}")

            # Initialize publisher
            cls._publisher = pubsub_v1.PublisherClient(credentials=credentials)
            logger.info("Pub/Sub publisher client initialized")

            # Initialize subscriber
            cls._subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
            logger.info("Pub/Sub subscriber client initialized")

            cls._initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize Pub/Sub client: {e}", exc_info=True)
            cls._initialized = False

    @classmethod
    def get_topic_path(cls, topic_name: str) -> str:
        """Get full topic path."""
        return f"projects/{cls.PROJECT_ID}/topics/{topic_name}"

    @classmethod
    def get_subscription_path(cls, subscription_name: str) -> str:
        """Get full subscription path."""
        return f"projects/{cls.PROJECT_ID}/subscriptions/{subscription_name}"

    @classmethod
    def publish_event(
        cls,
        topic_name: str,
        event_data: Dict[str, Any],
        attributes: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Publish event to Pub/Sub topic.

        Args:
            topic_name: Topic to publish to (e.g., 'raw-events')
            event_data: Event data dictionary
            attributes: Optional message attributes (metadata)

        Returns:
            Message ID

        Raises:
            Exception if publish fails
        """
        cls.initialize()

        if not cls._publisher:
            raise RuntimeError("Pub/Sub publisher not initialized")

        try:
            topic_path = cls.get_topic_path(topic_name)

            # Serialize event data to JSON bytes
            message_json = json.dumps(event_data, default=str)
            message_bytes = message_json.encode('utf-8')

            # Add default attributes
            if attributes is None:
                attributes = {}

            attributes.update({
                'source': event_data.get('source', 'unknown'),
                'event_type': event_data.get('event_type', 'unknown'),
                'timestamp': datetime.now().isoformat(),
            })

            # Publish with retry
            future = cls._publisher.publish(
                topic_path,
                message_bytes,
                **attributes
            )

            message_id = future.result(timeout=10.0)
            logger.info(f"Published message {message_id} to {topic_name}")

            return message_id

        except Exception as e:
            logger.error(f"Failed to publish to {topic_name}: {e}", exc_info=True)
            raise

    @classmethod
    def publish_raw_event(cls, event_data: Dict[str, Any]) -> str:
        """
        Publish raw event from external API.

        Args:
            event_data: Raw event data from GDELT, ReliefWeb, etc.

        Returns:
            Message ID
        """
        return cls.publish_event(
            cls.TOPIC_RAW_EVENTS,
            event_data,
            attributes={
                'ingestion_source': event_data.get('source'),
                'priority': 'normal'
            }
        )

    @classmethod
    def publish_processed_event(cls, event_data: Dict[str, Any]) -> str:
        """
        Publish event after intelligence analysis.

        Args:
            event_data: Event with sentiment, risk_score, entities populated

        Returns:
            Message ID
        """
        attributes = {
            'sentiment': str(event_data.get('sentiment', 0.0)),
            'risk_score': str(event_data.get('risk_score', 0.0)),
        }

        # Route high-risk events to dedicated topic
        if event_data.get('risk_score', 0.0) > 0.7:
            cls.publish_event(cls.TOPIC_HIGH_RISK, event_data, attributes)

        # Route humanitarian events to dedicated topic
        if event_data.get('event_type') == 'HUMANITARIAN':
            cls.publish_event(cls.TOPIC_HUMANITARIAN, event_data, attributes)

        return cls.publish_event(cls.TOPIC_PROCESSED_EVENTS, event_data, attributes)

    @classmethod
    def publish_anomaly_event(cls, anomaly_data: Dict[str, Any]) -> str:
        """
        Publish detected anomaly.

        Args:
            anomaly_data: Anomaly detection results

        Returns:
            Message ID
        """
        return cls.publish_event(
            cls.TOPIC_ANOMALY,
            anomaly_data,
            attributes={
                'anomaly_type': anomaly_data.get('type', 'unknown'),
                'severity': anomaly_data.get('severity', 'medium'),
            }
        )

    @classmethod
    def subscribe(
        cls,
        subscription_name: str,
        callback: Callable[[pubsub_v1.subscriber.message.Message], None],
        max_messages: int = 10
    ):
        """
        Subscribe to a Pub/Sub subscription and process messages.

        Args:
            subscription_name: Subscription to listen to
            callback: Function to handle each message
            max_messages: Max concurrent messages to process

        Example:
            def handle_message(message):
                data = json.loads(message.data)
                # Process event
                message.ack()

            PubSubClient.subscribe('raw-events-sub', handle_message)
        """
        cls.initialize()

        if not cls._subscriber:
            raise RuntimeError("Pub/Sub subscriber not initialized")

        try:
            subscription_path = cls.get_subscription_path(subscription_name)

            # Configure flow control
            flow_control = pubsub_v1.types.FlowControl(
                max_messages=max_messages,
            )

            # Start streaming pull
            streaming_pull_future = cls._subscriber.subscribe(
                subscription_path,
                callback=callback,
                flow_control=flow_control
            )

            logger.info(f"Listening for messages on {subscription_name}...")

            # Keep subscriber running (blocks until cancelled)
            with cls._subscriber:
                try:
                    streaming_pull_future.result()
                except KeyboardInterrupt:
                    streaming_pull_future.cancel()
                    logger.info(f"Subscriber {subscription_name} cancelled")

        except Exception as e:
            logger.error(f"Subscription {subscription_name} failed: {e}", exc_info=True)
            raise

    @classmethod
    def create_topic(cls, topic_name: str) -> str:
        """
        Create a new Pub/Sub topic.

        Args:
            topic_name: Topic name (e.g., 'raw-events')

        Returns:
            Topic path
        """
        cls.initialize()

        if not cls._publisher:
            raise RuntimeError("Pub/Sub publisher not initialized")

        try:
            topic_path = cls.get_topic_path(topic_name)
            topic = cls._publisher.create_topic(request={"name": topic_path})
            logger.info(f"Created topic: {topic.name}")
            return topic.name

        except Exception as e:
            # Topic might already exist
            if "already exists" in str(e).lower():
                logger.info(f"Topic {topic_name} already exists")
                return cls.get_topic_path(topic_name)
            else:
                logger.error(f"Failed to create topic {topic_name}: {e}")
                raise

    @classmethod
    def create_subscription(
        cls,
        topic_name: str,
        subscription_name: str,
        ack_deadline_seconds: int = 60,
        enable_message_ordering: bool = False
    ) -> str:
        """
        Create a subscription to a topic.

        Args:
            topic_name: Topic to subscribe to
            subscription_name: Name for subscription
            ack_deadline_seconds: Time to ack message before redelivery
            enable_message_ordering: Enable ordered message delivery

        Returns:
            Subscription path
        """
        cls.initialize()

        if not cls._subscriber:
            raise RuntimeError("Pub/Sub subscriber not initialized")

        try:
            topic_path = cls.get_topic_path(topic_name)
            subscription_path = cls.get_subscription_path(subscription_name)

            subscription = cls._subscriber.create_subscription(
                request={
                    "name": subscription_path,
                    "topic": topic_path,
                    "ack_deadline_seconds": ack_deadline_seconds,
                    "enable_message_ordering": enable_message_ordering,
                }
            )

            logger.info(f"Created subscription: {subscription.name}")
            return subscription.name

        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"Subscription {subscription_name} already exists")
                return cls.get_subscription_path(subscription_name)
            else:
                logger.error(f"Failed to create subscription {subscription_name}: {e}")
                raise

    @classmethod
    def setup_topics_and_subscriptions(cls):
        """
        Set up all required topics and subscriptions for VenezuelaWatch.

        Creates:
        - Topics: raw-events, processed-events, high-risk-events, humanitarian-events, anomaly-events
        - Subscriptions for each topic
        """
        cls.initialize()

        topics = [
            cls.TOPIC_RAW_EVENTS,
            cls.TOPIC_PROCESSED_EVENTS,
            cls.TOPIC_HIGH_RISK,
            cls.TOPIC_HUMANITARIAN,
            cls.TOPIC_ANOMALY,
        ]

        for topic_name in topics:
            try:
                cls.create_topic(topic_name)
                cls.create_subscription(topic_name, f"{topic_name}-sub")
            except Exception as e:
                logger.error(f"Failed to setup {topic_name}: {e}")

        logger.info("Pub/Sub infrastructure setup complete")


# Helper functions for common use cases

def publish_ingestion_event(source: str, data: Dict[str, Any]):
    """Convenience function to publish raw ingestion event."""
    event_data = {
        'source': source,
        'data': data,
        'timestamp': datetime.now().isoformat(),
    }
    return PubSubClient.publish_raw_event(event_data)


def setup_pubsub_infrastructure():
    """
    Management command helper to set up all Pub/Sub topics and subscriptions.
    """
    logger.info("Setting up Pub/Sub infrastructure...")
    PubSubClient.setup_topics_and_subscriptions()
    logger.info("Pub/Sub infrastructure ready")
