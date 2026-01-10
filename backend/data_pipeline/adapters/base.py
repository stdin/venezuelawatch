"""
Abstract base class for data source adapters.

This module defines the contract all data source adapters must implement.
Adapters follow a plugin pattern: drop a file in adapters/, follow naming conventions,
and the registry will auto-discover it.

Example adapter implementation:

    from data_pipeline.adapters.base import DataSourceAdapter
    from api.bigquery_models import Event
    from datetime import datetime

    class MySourceAdapter(DataSourceAdapter):
        source_name = "mysource"
        schedule_frequency = "*/15 * * * *"  # Every 15 minutes
        default_lookback_minutes = 30

        def fetch(self, start_time, end_time, limit=100):
            # Fetch raw data from external API
            response = requests.get(f"https://api.mysource.com/events?start={start_time}")
            return response.json()

        def transform(self, raw_events):
            # Map to BigQuery Event schema
            events = []
            for raw in raw_events:
                event = Event(
                    source_url=raw['url'],
                    mentioned_at=datetime.fromisoformat(raw['date']),
                    created_at=datetime.utcnow(),
                    title=raw['headline'],
                    content=raw['body'],
                    source_name=self.source_name
                )
                events.append(event)
            return events

        def validate(self, event):
            # Validate required fields
            if not event.source_url:
                return (False, "Missing source_url")
            if not event.mentioned_at:
                return (False, "Missing mentioned_at")
            return (True, None)

Then deploy:
    1. Save as data_pipeline/adapters/mysource_adapter.py
    2. Registry auto-discovers on next import
    3. Cloud Scheduler triggers based on schedule_frequency
    4. Cloud Function calls adapter.fetch() → adapter.transform() → adapter.publish_events()
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class DataSourceAdapter(ABC):
    """
    Abstract base class for pluggable data source adapters.

    All data sources implement this interface for consistent ingestion pipeline.

    Attributes:
        source_name (str): Human-readable name (e.g., "gdelt", "reliefweb")
        schedule_frequency (str): Cron expression for Cloud Scheduler
        default_lookback_minutes (int): Default time window for incremental fetch
    """

    # Class attributes - override in implementations
    source_name: str = "undefined"
    schedule_frequency: str = "0 * * * *"  # Default: hourly
    default_lookback_minutes: int = 60

    @abstractmethod
    def fetch(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch raw data from external source.

        Args:
            start_time: Start of time window (inclusive)
            end_time: End of time window (exclusive)
            limit: Maximum number of records to fetch

        Returns:
            List of raw event dictionaries from source API

        Raises:
            Adapter-specific exceptions for API errors, rate limits, etc.

        Example:
            raw_events = adapter.fetch(
                start_time=datetime(2025, 1, 1),
                end_time=datetime(2025, 1, 2),
                limit=1000
            )
        """
        pass

    @abstractmethod
    def transform(self, raw_events: List[Dict[str, Any]]) -> List['Event']:
        """
        Transform raw events to BigQuery Event schema.

        Args:
            raw_events: List of raw event dicts from fetch()

        Returns:
            List of Event dataclass instances ready for BigQuery

        Note:
            Use api.bigquery_models.Event for return type.
            Missing fields should be set to None, not omitted.
            Metadata dict holds source-specific fields not in base schema.

        Example:
            from api.bigquery_models import Event

            def transform(self, raw_events):
                events = []
                for raw in raw_events:
                    event = Event(
                        source_url=raw['url'],
                        mentioned_at=parse_datetime(raw['date']),
                        created_at=datetime.utcnow(),
                        title=raw.get('title'),
                        content=raw.get('content'),
                        source_name=self.source_name,
                        metadata={'raw_id': raw['id']}
                    )
                    events.append(event)
                return events
        """
        pass

    @abstractmethod
    def validate(self, event: 'Event') -> Tuple[bool, Optional[str]]:
        """
        Validate a single BigQuery Event.

        Args:
            event: Event dataclass instance to validate

        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, "error description") if invalid

        Why separate from transform?
            Validation is per-event, allowing partial success.
            If 100 events are fetched and 3 fail validation, we can still
            publish the 97 valid ones rather than failing the entire batch.

        Example:
            def validate(self, event):
                if not event.source_url:
                    return (False, "Missing required field: source_url")
                if not event.mentioned_at:
                    return (False, "Missing required field: mentioned_at")
                if event.risk_score and (event.risk_score < 0 or event.risk_score > 100):
                    return (False, f"Invalid risk_score: {event.risk_score}")
                return (True, None)
        """
        pass

    def publish_events(self, events: List['Event']) -> Dict[str, int]:
        """
        Publish validated events to Pub/Sub for downstream processing.

        This is a concrete helper method - implementations don't override it.

        Args:
            events: List of validated Event instances

        Returns:
            Dict with counts: {'published': int, 'failed': int}

        Note:
            - Validates each event before publishing
            - Logs validation failures but continues with valid events
            - Publishes to 'event-ingestion' topic
            - Returns counts for observability

        Example:
            valid_events = [e for e in events if self.validate(e)[0]]
            result = self.publish_events(valid_events)
            logger.info(f"Published {result['published']}, failed {result['failed']}")
        """
        from google.cloud import pubsub_v1
        import json

        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path('venezuelawatch-447923', 'event-ingestion')

        published = 0
        failed = 0

        for event in events:
            # Validate before publishing
            is_valid, error = self.validate(event)
            if not is_valid:
                logger.warning(
                    f"Validation failed for event from {self.source_name}: {error}",
                    extra={'source_url': event.source_url}
                )
                failed += 1
                continue

            try:
                # Convert to JSON and publish
                event_data = event.to_bigquery_row()
                message_bytes = json.dumps(event_data).encode('utf-8')
                future = publisher.publish(topic_path, message_bytes)
                future.result()  # Wait for publish confirmation
                published += 1
            except Exception as e:
                logger.error(
                    f"Failed to publish event from {self.source_name}: {e}",
                    extra={'source_url': event.source_url}
                )
                failed += 1

        logger.info(
            f"{self.source_name} publish complete",
            extra={
                'published': published,
                'failed': failed,
                'total': len(events)
            }
        )

        return {'published': published, 'failed': failed}
