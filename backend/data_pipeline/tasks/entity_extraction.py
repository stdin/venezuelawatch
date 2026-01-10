"""
Celery tasks for entity extraction and trending updates.

**MIGRATION STATUS: Phase 18.2 - Tasks replaced by Cloud Run handlers**

These Celery tasks are DEPRECATED and will be removed in Phase 18-03.
They have been replaced by event-driven Cloud Run handlers in api/views/internal.py:
- extract_entities_from_event → /api/internal/extract-entities (Pub/Sub handler)
- backfill_entities → Batch processing via Pub/Sub publishing

The core entity extraction logic is unchanged and reused by the new handlers.

Extracts entities from BigQuery event data, normalizes using EntityService,
and updates trending scores in Redis.

Migration: Phase 14.3 - Now reads events from BigQuery instead of PostgreSQL.
"""

import logging
from typing import Dict
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from core.models import Entity, EntityMention
from data_pipeline.services.entity_service import EntityService
from data_pipeline.services.trending_service import TrendingService
from api.services.bigquery_service import bigquery_service


logger = logging.getLogger(__name__)


@shared_task
def extract_entities_from_event(event_id: str) -> Dict:
    """
    Extract and normalize entities from a single event.

    Reads event data from BigQuery and processes llm_analysis['entities'] to create/match
    Entity records, create EntityMention links, and update trending scores in Redis.

    Args:
        event_id: Event UUID to process

    Returns:
        Dict with extraction results:
        {
            'event_id': str,
            'entities_extracted': int,
            'entities_linked': int,
            'entity_names': List[str]
        }
    """
    try:
        # Load event from BigQuery
        event = bigquery_service.get_event_by_id(event_id)

        if not event:
            logger.error(f"Event {event_id} not found in BigQuery")
            return {
                'event_id': str(event_id),
                'error': 'Event not found'
            }

        # Check if event has entities to extract
        if not event.get('entities') or len(event['entities']) == 0:
            logger.warning(f"Event {event_id} has no entities to extract")
            return {
                'event_id': str(event_id),
                'entities_extracted': 0,
                'entities_linked': 0,
                'error': 'No entities in event'
            }

        # Check if LLM analysis has structured entities
        if not event.get('llm_analysis') or 'entities' not in event['llm_analysis']:
            logger.warning(f"Event {event_id} missing llm_analysis.entities - using basic extraction")
            return _extract_from_entities_array(event)

        # Extract from structured LLM analysis
        return _extract_from_llm_analysis(event)

    except Exception as e:
        logger.error(f"Error extracting entities from event {event_id}: {e}", exc_info=True)
        return {
            'event_id': str(event_id),
            'error': str(e)
        }


@shared_task
def backfill_entities(days: int = 30, limit: int = 1000) -> Dict:
    """
    Backfill entity extraction for existing events from BigQuery.

    Queues extract_entities_from_event tasks for events with entities
    from the last N days.

    Args:
        days: Number of days to backfill (default 30)
        limit: Maximum number of events to process (default 1000)

    Returns:
        Dict with backfill stats:
        {
            'events_queued': int,
            'days': int,
            'cutoff': str (ISO timestamp)
        }
    """
    try:
        from google.cloud import bigquery

        # Calculate cutoff timestamp
        cutoff = timezone.now() - timedelta(days=days)

        # Query BigQuery for events with entities from last N days
        query = f"""
            SELECT id
            FROM `{bigquery_service.project_id}.{bigquery_service.dataset_id}.events`
            WHERE mentioned_at >= @cutoff
            AND ARRAY_LENGTH(entities) > 0
            ORDER BY mentioned_at DESC
            LIMIT @limit
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('cutoff', 'TIMESTAMP', cutoff),
                bigquery.ScalarQueryParameter('limit', 'INT64', limit)
            ]
        )

        results = bigquery_service.client.query(query, job_config=job_config).result()

        # Queue tasks for each event
        events_queued = 0
        for row in results:
            extract_entities_from_event.delay(row.id)
            events_queued += 1

        logger.info(f"Queued {events_queued} events for entity extraction (last {days} days)")

        return {
            'events_queued': events_queued,
            'days': days,
            'cutoff': cutoff.isoformat()
        }

    except Exception as e:
        logger.error(f"Error in backfill_entities: {e}", exc_info=True)
        return {
            'error': str(e)
        }


# Private helper functions

@transaction.atomic
def _extract_from_llm_analysis(event: dict) -> Dict:
    """
    Extract entities from structured LLM analysis in BigQuery event.

    LLM analysis structure:
    {
        'entities': {
            'people': [{'name': str, 'role': str, 'relevance': float}],
            'organizations': [{'name': str, 'type': str, 'relevance': float}],
            'locations': [{'name': str, 'type': str, 'relevance': float}]
        }
    }

    Args:
        event: Event dict from BigQuery with keys: id, llm_analysis, mentioned_at, etc.
    """
    entities_data = event['llm_analysis']['entities']
    extracted_entities = []
    linked_count = 0
    event_id = event['id']
    event_timestamp = event['mentioned_at']

    # Create mock event object for EntityService compatibility
    # EntityService needs timestamp field for trending
    from types import SimpleNamespace
    mock_event = SimpleNamespace(timestamp=event_timestamp, id=event_id)

    # Process people
    for person in entities_data.get('people', []):
        entity, created, match_score = EntityService.find_or_create_entity(
            raw_name=person['name'],
            entity_type='PERSON',
            metadata={'role': person.get('role')}
        )

        EntityService.link_entity_to_event(
            entity=entity,
            event=mock_event,
            raw_name=person['name'],
            match_score=match_score,
            relevance=person.get('relevance', 1.0),
            event_id=event_id  # Pass BigQuery event ID explicitly
        )

        # Update trending score
        TrendingService.update_entity_score(
            entity_id=str(entity.id),
            timestamp=event_timestamp,
            weight=person.get('relevance', 1.0)
        )

        extracted_entities.append(entity.canonical_name)
        linked_count += 1

    # Process organizations
    for org in entities_data.get('organizations', []):
        entity, created, match_score = EntityService.find_or_create_entity(
            raw_name=org['name'],
            entity_type='ORGANIZATION',
            metadata={'org_type': org.get('type')}
        )

        EntityService.link_entity_to_event(
            entity=entity,
            event=mock_event,
            raw_name=org['name'],
            match_score=match_score,
            relevance=org.get('relevance', 1.0),
            event_id=event_id
        )

        # Update trending score
        TrendingService.update_entity_score(
            entity_id=str(entity.id),
            timestamp=event_timestamp,
            weight=org.get('relevance', 1.0)
        )

        extracted_entities.append(entity.canonical_name)
        linked_count += 1

    # Process locations
    for location in entities_data.get('locations', []):
        entity, created, match_score = EntityService.find_or_create_entity(
            raw_name=location['name'],
            entity_type='LOCATION',
            metadata={'location_type': location.get('type')}
        )

        EntityService.link_entity_to_event(
            entity=entity,
            event=mock_event,
            raw_name=location['name'],
            match_score=match_score,
            relevance=location.get('relevance', 1.0),
            event_id=event_id
        )

        # Update trending score
        TrendingService.update_entity_score(
            entity_id=str(entity.id),
            timestamp=event_timestamp,
            weight=location.get('relevance', 1.0)
        )

        extracted_entities.append(entity.canonical_name)
        linked_count += 1

    logger.info(f"Extracted {len(extracted_entities)} entities from event {event_id}")

    return {
        'event_id': event_id,
        'entities_extracted': len(extracted_entities),
        'entities_linked': linked_count,
        'entity_names': extracted_entities
    }


@transaction.atomic
def _extract_from_entities_array(event: dict) -> Dict:
    """
    Fallback extraction from event['entities'] array.

    Used when llm_analysis.entities is not available.
    Infers entity types heuristically.

    Args:
        event: Event dict from BigQuery with keys: id, entities, mentioned_at, etc.
    """
    extracted_entities = []
    linked_count = 0
    event_id = event['id']
    event_timestamp = event['mentioned_at']

    # Create mock event object for EntityService compatibility
    from types import SimpleNamespace
    mock_event = SimpleNamespace(timestamp=event_timestamp, id=event_id)

    for entity_name in event['entities']:
        # Infer entity type heuristically
        entity_type = _infer_entity_type(entity_name)

        entity, created, match_score = EntityService.find_or_create_entity(
            raw_name=entity_name,
            entity_type=entity_type
        )

        EntityService.link_entity_to_event(
            entity=entity,
            event=mock_event,
            raw_name=entity_name,
            match_score=match_score,
            event_id=event_id
        )

        # Update trending score
        TrendingService.update_entity_score(
            entity_id=str(entity.id),
            timestamp=event_timestamp,
            weight=1.0
        )

        extracted_entities.append(entity.canonical_name)
        linked_count += 1

    logger.info(f"Extracted {len(extracted_entities)} entities from event {event_id} (fallback mode)")

    return {
        'event_id': event_id,
        'entities_extracted': len(extracted_entities),
        'entities_linked': linked_count,
        'entity_names': extracted_entities
    }


def _infer_entity_type(name: str) -> str:
    """
    Infer entity type from name heuristically.

    Rules:
    - Contains "Inc", "Corp", "Ltd", "LLC", "Government" -> ORGANIZATION
    - Single capitalized word -> PERSON
    - Contains country/city names -> LOCATION
    - Default -> ORGANIZATION
    """
    name_lower = name.lower()

    # Organization indicators
    org_indicators = ['inc', 'corp', 'ltd', 'llc', 'government', 'ministry',
                      'department', 'agency', 'authority', 'company', 'bank']
    if any(indicator in name_lower for indicator in org_indicators):
        return 'ORGANIZATION'

    # Location indicators
    location_indicators = ['venezuela', 'caracas', 'maracaibo', 'valencia']
    if any(indicator in name_lower for indicator in location_indicators):
        return 'LOCATION'

    # Single word capitalized - likely PERSON
    words = name.split()
    if len(words) == 1 and name[0].isupper():
        return 'PERSON'

    # Two capitalized words - could be person name
    if len(words) == 2 and all(w[0].isupper() for w in words):
        return 'PERSON'

    # Default to ORGANIZATION
    return 'ORGANIZATION'
