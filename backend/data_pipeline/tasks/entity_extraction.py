"""
Celery tasks for entity extraction and trending updates.

Extracts entities from Event.llm_analysis, normalizes using EntityService,
and updates trending scores in Redis.
"""

import logging
from typing import Dict
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from core.models import Event, Entity, EntityMention
from data_pipeline.services.entity_service import EntityService
from data_pipeline.services.trending_service import TrendingService


logger = logging.getLogger(__name__)


@shared_task
def extract_entities_from_event(event_id: str) -> Dict:
    """
    Extract and normalize entities from a single event.

    Processes Event.llm_analysis['entities'] to create/match Entity records,
    create EntityMention links, and update trending scores in Redis.

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
        # Load event
        event = Event.objects.get(id=event_id)

        # Check if event has entities to extract
        if not event.entities or len(event.entities) == 0:
            logger.warning(f"Event {event_id} has no entities to extract")
            return {
                'event_id': str(event_id),
                'entities_extracted': 0,
                'entities_linked': 0,
                'error': 'No entities in event'
            }

        # Check if LLM analysis has structured entities
        if not event.llm_analysis or 'entities' not in event.llm_analysis:
            logger.warning(f"Event {event_id} missing llm_analysis.entities - using basic extraction")
            return _extract_from_entities_array(event)

        # Extract from structured LLM analysis
        return _extract_from_llm_analysis(event)

    except Event.DoesNotExist:
        logger.error(f"Event {event_id} not found")
        return {
            'event_id': str(event_id),
            'error': 'Event not found'
        }
    except Exception as e:
        logger.error(f"Error extracting entities from event {event_id}: {e}", exc_info=True)
        return {
            'event_id': str(event_id),
            'error': str(e)
        }


@shared_task
def backfill_entities(days: int = 30, batch_size: int = 100) -> Dict:
    """
    Backfill entity extraction for existing events.

    Queues extract_entities_from_event tasks for events with entities
    from the last N days.

    Args:
        days: Number of days to backfill (default 30)
        batch_size: Number of events to process per batch (default 100)

    Returns:
        Dict with backfill stats:
        {
            'events_queued': int,
            'days': int,
            'cutoff': str (ISO timestamp)
        }
    """
    try:
        # Calculate cutoff timestamp
        cutoff = timezone.now() - timedelta(days=days)

        # Query events with entities from last N days
        events = Event.objects.filter(
            timestamp__gte=cutoff,
            entities__len__gt=0
        ).values_list('id', flat=True)

        # Queue tasks for each event
        events_queued = 0
        for event_id in events.iterator(chunk_size=batch_size):
            extract_entities_from_event.delay(str(event_id))
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
def _extract_from_llm_analysis(event: Event) -> Dict:
    """
    Extract entities from structured LLM analysis.

    LLM analysis structure:
    {
        'entities': {
            'people': [{'name': str, 'role': str, 'relevance': float}],
            'organizations': [{'name': str, 'type': str, 'relevance': float}],
            'locations': [{'name': str, 'type': str, 'relevance': float}]
        }
    }
    """
    entities_data = event.llm_analysis['entities']
    extracted_entities = []
    linked_count = 0

    # Process people
    for person in entities_data.get('people', []):
        entity, created, match_score = EntityService.find_or_create_entity(
            raw_name=person['name'],
            entity_type='PERSON',
            metadata={'role': person.get('role')}
        )

        EntityService.link_entity_to_event(
            entity=entity,
            event=event,
            raw_name=person['name'],
            match_score=match_score,
            relevance=person.get('relevance', 1.0)
        )

        # Update trending score
        TrendingService.update_entity_score(
            entity_id=str(entity.id),
            timestamp=event.timestamp,
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
            event=event,
            raw_name=org['name'],
            match_score=match_score,
            relevance=org.get('relevance', 1.0)
        )

        # Update trending score
        TrendingService.update_entity_score(
            entity_id=str(entity.id),
            timestamp=event.timestamp,
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
            event=event,
            raw_name=location['name'],
            match_score=match_score,
            relevance=location.get('relevance', 1.0)
        )

        # Update trending score
        TrendingService.update_entity_score(
            entity_id=str(entity.id),
            timestamp=event.timestamp,
            weight=location.get('relevance', 1.0)
        )

        extracted_entities.append(entity.canonical_name)
        linked_count += 1

    logger.info(f"Extracted {len(extracted_entities)} entities from event {event.id}")

    return {
        'event_id': str(event.id),
        'entities_extracted': len(extracted_entities),
        'entities_linked': linked_count,
        'entity_names': extracted_entities
    }


@transaction.atomic
def _extract_from_entities_array(event: Event) -> Dict:
    """
    Fallback extraction from Event.entities ArrayField.

    Used when llm_analysis.entities is not available.
    Infers entity types heuristically.
    """
    extracted_entities = []
    linked_count = 0

    for entity_name in event.entities:
        # Infer entity type heuristically
        entity_type = _infer_entity_type(entity_name)

        entity, created, match_score = EntityService.find_or_create_entity(
            raw_name=entity_name,
            entity_type=entity_type
        )

        EntityService.link_entity_to_event(
            entity=entity,
            event=event,
            raw_name=entity_name,
            match_score=match_score
        )

        # Update trending score
        TrendingService.update_entity_score(
            entity_id=str(entity.id),
            timestamp=event.timestamp,
            weight=1.0
        )

        extracted_entities.append(entity.canonical_name)
        linked_count += 1

    logger.info(f"Extracted {len(extracted_entities)} entities from event {event.id} (fallback mode)")

    return {
        'event_id': str(event.id),
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
