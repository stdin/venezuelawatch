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
import re
import os

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

    def _extract_and_link_entities(self, event: 'Event') -> List[str]:
        """
        Extract entity mentions from event and link to canonical entities.

        This method:
        1. Extracts potential entity mentions using capitalization patterns
        2. Resolves each mention to a canonical entity using SplinkEntityResolver
        3. Creates/updates EntityAlias records with confidence and resolution method
        4. Returns list of canonical entity IDs for storage in event metadata

        Args:
            event: BigQuery Event instance to extract entities from

        Returns:
            List of canonical entity ID strings

        Note:
            This runs at publish time (not query time) for performance.
            Entity linking happens before BigQuery insert so metadata.linked_entities
            is immediately available for multi-source queries.
        """
        from api.services.splink_resolver import SplinkEntityResolver
        from data_pipeline.models import CanonicalEntity, EntityAlias
        from django.utils import timezone

        canonical_entity_ids = []

        try:
            # Extract potential entity mentions from title and content
            # Use simple capitalized word pattern (can be enhanced later with Phase 6 patterns)
            text = f"{event.title or ''} {event.content or ''}"

            # Pattern: Find sequences of capitalized words (potential entities)
            # Examples: "PDVSA", "Nicolás Maduro", "Petróleos de Venezuela"
            capitalized_pattern = r'\b([A-Z][a-záéíóúñü]*(?:\s+[A-Z][a-záéíóúñü]*)*)\b'
            potential_entities = re.findall(capitalized_pattern, text)

            # Remove duplicates while preserving order
            seen = set()
            unique_entities = []
            for entity in potential_entities:
                entity_lower = entity.lower()
                if entity_lower not in seen and len(entity) > 1:  # Skip single letters
                    seen.add(entity_lower)
                    unique_entities.append(entity)

            # Limit to top 10 entities per event to avoid excessive processing
            unique_entities = unique_entities[:10]

            if not unique_entities:
                return []

            logger.info(
                f"Extracted {len(unique_entities)} potential entities from event {event.id}: {unique_entities}"
            )

            # Initialize Splink resolver
            resolver = SplinkEntityResolver()

            # Resolve each entity to canonical form
            for entity_name in unique_entities:
                try:
                    # Infer entity type from context (default to organization for Venezuela events)
                    # TODO: Use NER or LLM for better entity type classification
                    entity_type = 'organization'

                    # Extract country code from event if available
                    country_code = None
                    if hasattr(event, 'location'):
                        if 'Venezuela' in str(event.location):
                            country_code = 'VE'

                    # Resolve to canonical entity
                    canonical_id, confidence, method = resolver.resolve_entity(
                        entity_name=entity_name,
                        source=self.source_name,
                        entity_type=entity_type,
                        country_code=country_code
                    )

                    canonical_entity_ids.append(canonical_id)

                    # Update or create EntityAlias record
                    alias_obj, created = EntityAlias.objects.get_or_create(
                        alias=entity_name,
                        source=self.source_name,
                        defaults={
                            'canonical_entity_id': canonical_id,
                            'confidence': confidence,
                            'resolution_method': method,
                        }
                    )

                    if not created:
                        # Update existing alias
                        alias_obj.last_seen = timezone.now()
                        alias_obj.save(update_fields=['last_seen'])

                    logger.debug(
                        f"Linked entity '{entity_name}' to canonical ID {canonical_id} "
                        f"(confidence: {confidence:.3f}, method: {method})"
                    )

                except Exception as e:
                    logger.warning(
                        f"Failed to resolve entity '{entity_name}' for event {event.id}: {e}"
                    )
                    # Continue with other entities - don't fail entire event

            logger.info(
                f"Linked {len(canonical_entity_ids)} entities to event {event.id}"
            )

        except Exception as e:
            logger.error(
                f"Entity extraction failed for event {event.id}: {e}",
                exc_info=True
            )
            # Return empty list on failure - don't fail entire publish operation

        return canonical_entity_ids

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

        project_id = os.environ.get('GCP_PROJECT_ID', 'venezuelawatch-staging')
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project_id, 'event-ingestion')

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
                # Extract and link entities before publishing
                linked_entity_ids = self._extract_and_link_entities(event)
                if linked_entity_ids:
                    # Enrich event metadata with linked entities
                    if not hasattr(event, 'metadata') or event.metadata is None:
                        event.metadata = {}
                    event.metadata['linked_entities'] = linked_entity_ids
                    logger.info(
                        f"Enriched event {event.id} with {len(linked_entity_ids)} linked entities"
                    )

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
