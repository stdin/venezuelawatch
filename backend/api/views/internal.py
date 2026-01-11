"""
Internal API handlers for GCP-native processing pipeline.

These endpoints are triggered by Pub/Sub push subscriptions and Cloud Tasks.
They are NOT public - authentication is handled via OIDC tokens from GCP services.

Architecture:
- Pub/Sub push → /api/internal/process-event → enqueue Cloud Tasks
- Cloud Tasks → /api/internal/analyze-intelligence → run LLM analysis
- Pub/Sub push → /api/internal/extract-entities → process entity extraction

Replace Celery tasks with event-driven GCP-native orchestration.
"""
import json
import base64
import logging
import os
from typing import Dict, Any

from ninja import Router
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from google.cloud import tasks_v2, pubsub_v1

from data_pipeline.services.llm_intelligence import LLMIntelligence
from data_pipeline.services.entity_service import EntityService
from data_pipeline.services.trending_service import TrendingService
from api.services.bigquery_service import bigquery_service
from core.models import Entity, EntityMention

logger = logging.getLogger(__name__)

internal_router = Router()

# GCP Project configuration from environment
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID', 'venezuelawatch-staging')
GCP_LOCATION = 'us-central1'
CLOUD_RUN_URL = os.environ.get('CLOUD_RUN_URL', 'https://venezuelawatch-api-gc6im6smjq-uc.a.run.app')


@internal_router.post('/process-event')
def process_event_pubsub(request):
    """
    Pub/Sub push endpoint for event analysis triggers.

    Receives event IDs from ingestion functions, enqueues to Cloud Tasks
    for LLM intelligence analysis.

    Pub/Sub message format:
    {
        "message": {
            "data": base64("{"event_id": "abc-123"}"),
            "messageId": "...",
            "publishTime": "..."
        }
    }

    Returns:
        200: Task enqueued successfully
        400: Invalid message format
        500: Failed to enqueue task
    """
    try:
        # Parse Pub/Sub message envelope
        envelope = json.loads(request.body.decode('utf-8'))

        if 'message' not in envelope:
            logger.error("Invalid Pub/Sub message: missing 'message' field")
            return JsonResponse({'error': 'Invalid Pub/Sub message'}, status=400)

        pubsub_message = envelope['message']

        # Decode base64 data
        if 'data' not in pubsub_message:
            logger.error("Invalid Pub/Sub message: missing 'data' field")
            return JsonResponse({'error': 'Missing data field'}, status=400)

        event_data = json.loads(base64.b64decode(pubsub_message['data']))
        event_id = event_data.get('event_id')
        model = event_data.get('model', 'fast')  # LLM model tier

        if not event_id:
            logger.error("Invalid event data: missing 'event_id'")
            return JsonResponse({'error': 'Missing event_id'}, status=400)

        logger.info(f"Received event analysis trigger: event_id={event_id}, model={model}")

        # Enqueue to Cloud Tasks for LLM analysis
        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(GCP_PROJECT_ID, GCP_LOCATION, 'llm-analysis-queue')

        task = {
            'http_request': {
                'http_method': tasks_v2.HttpMethod.POST,
                'url': f'{CLOUD_RUN_URL}/api/internal/analyze-intelligence',
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'event_id': event_id, 'model': model}).encode(),
                'oidc_token': {
                    'service_account_email': f'cloudrun-tasks@{GCP_PROJECT_ID}.iam.gserviceaccount.com'
                }
            }
        }

        response = client.create_task(request={'parent': parent, 'task': task})

        logger.info(f"Enqueued intelligence analysis task: {response.name}")

        return JsonResponse({
            'status': 'enqueued',
            'event_id': event_id,
            'task_name': response.name
        }, status=200)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Failed to process event: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@internal_router.post('/analyze-intelligence')
def analyze_intelligence_task(request):
    """
    Cloud Tasks handler for LLM intelligence analysis.

    Replaces Celery analyze_event_intelligence task.
    Reads event from BigQuery, runs LLM analysis, updates event with results,
    and publishes to entity-extraction Pub/Sub topic.

    Request body:
    {
        "event_id": "abc-123",
        "model": "fast" | "standard" | "premium"
    }

    Returns:
        200: Analysis completed successfully
        404: Event not found
        500: Analysis failed
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        event_id = data.get('event_id')
        model = data.get('model', 'fast')

        if not event_id:
            return JsonResponse({'error': 'Missing event_id'}, status=400)

        logger.info(f"Starting LLM intelligence analysis: event_id={event_id}, model={model}")

        # Fetch event from BigQuery
        event = bigquery_service.get_event_by_id(event_id)

        if not event:
            logger.error(f"Event {event_id} not found in BigQuery")
            return JsonResponse({'error': 'Event not found'}, status=404)

        # Create mock event object for LLMIntelligence service compatibility
        from types import SimpleNamespace
        mock_event = SimpleNamespace(
            title=event.get('title', ''),
            content=event.get('content', ''),
            source=event.get('source_name', ''),
            event_type=event.get('event_type', ''),
            timestamp=event.get('mentioned_at')
        )

        # Run LLM analysis (reuses existing service logic)
        analysis = LLMIntelligence.analyze_event_model(mock_event, model=model)

        # Extract entity names for entities field
        entities = []
        for person in analysis['entities'].get('people', []):
            entities.append(person['name'])
        for org in analysis['entities'].get('organizations', []):
            entities.append(org['name'])
        for loc in analysis['entities'].get('locations', []):
            entities.append(loc['name'])

        # Calculate comprehensive risk score
        # TODO: Adapt RiskScorer for dict-based events (currently uses Django Event model)
        comprehensive_risk = analysis['risk']['score'] * 100  # Scale 0-1 to 0-100

        # Classify severity
        # TODO: Adapt ImpactClassifier for dict-based events
        severity = 'SEV3'  # Default medium severity

        # Update event in BigQuery with analysis results
        bigquery_service.update_event_analysis(
            event_id=event_id,
            sentiment=analysis['sentiment']['score'],
            risk_score=comprehensive_risk,
            entities=entities[:20],  # Limit to top 20
            summary=analysis['summary']['short'],
            relationships=analysis['relationships'],
            themes=analysis['themes'],
            urgency=analysis['urgency'],
            language=analysis['language'],
            llm_analysis=analysis,
            severity=severity
        )

        logger.info(
            f"Event {event_id} intelligence updated: "
            f"sentiment={analysis['sentiment']['score']:.3f}, "
            f"risk_score={comprehensive_risk:.2f}, "
            f"entities={len(entities)}"
        )

        # Publish to entity-extraction topic
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(GCP_PROJECT_ID, 'entity-extraction')
        message_data = json.dumps({'event_id': event_id}).encode('utf-8')

        future = publisher.publish(topic_path, message_data)
        future.result()  # Wait for publish confirmation

        logger.info(f"Published entity extraction trigger for event {event_id}")

        return JsonResponse({
            'status': 'analyzed',
            'event_id': event_id,
            'sentiment': analysis['sentiment']['score'],
            'risk_score': comprehensive_risk,
            'entities_count': len(entities)
        }, status=200)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Failed to analyze event {event_id}: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@internal_router.post('/extract-entities')
def extract_entities_pubsub(request):
    """
    Pub/Sub handler for entity extraction.

    Replaces Celery extract_entities_from_event task.
    Processes entities from LLM analysis, creates/matches Entity records,
    creates EntityMention links, and updates trending scores in Redis.

    Pub/Sub message format:
    {
        "message": {
            "data": base64("{"event_id": "abc-123"}"),
            "messageId": "...",
            "publishTime": "..."
        }
    }

    Returns:
        200: Entities extracted successfully
        400: Invalid message format
        404: Event not found
        500: Extraction failed
    """
    try:
        # Parse Pub/Sub message envelope
        envelope = json.loads(request.body.decode('utf-8'))

        if 'message' not in envelope:
            return JsonResponse({'error': 'Invalid Pub/Sub message'}, status=400)

        pubsub_message = envelope['message']
        event_data = json.loads(base64.b64decode(pubsub_message['data']))
        event_id = event_data.get('event_id')

        if not event_id:
            return JsonResponse({'error': 'Missing event_id'}, status=400)

        logger.info(f"Starting entity extraction: event_id={event_id}")

        # Fetch event from BigQuery
        event = bigquery_service.get_event_by_id(event_id)

        if not event:
            logger.error(f"Event {event_id} not found in BigQuery")
            return JsonResponse({'error': 'Event not found'}, status=404)

        # Check if event has entities to extract
        if not event.get('entities') or len(event['entities']) == 0:
            logger.warning(f"Event {event_id} has no entities to extract")
            return JsonResponse({
                'status': 'skipped',
                'event_id': event_id,
                'reason': 'No entities in event'
            }, status=200)

        # Check if LLM analysis has structured entities
        if not event.get('llm_analysis') or 'entities' not in event['llm_analysis']:
            logger.warning(f"Event {event_id} missing structured entities in llm_analysis")
            result = _extract_from_entities_array(event)
        else:
            result = _extract_from_llm_analysis(event)

        logger.info(
            f"Entity extraction complete: event_id={event_id}, "
            f"extracted={result.get('entities_extracted', 0)}, "
            f"linked={result.get('entities_linked', 0)}"
        )

        return JsonResponse(result, status=200)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Failed to extract entities: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


# Private helper functions (reused from entity_extraction.py)

def _extract_from_llm_analysis(event: dict) -> Dict[str, Any]:
    """
    Extract entities from structured LLM analysis and GKG data.

    Processes people, organizations, and locations from:
    1. llm_analysis['entities'] (LLM-extracted, context-rich)
    2. metadata['gkg']['persons'] and ['organizations'] (GDELT-sourced, high-confidence)

    Creates/matches Entity records, creates EntityMention links, and updates trending.
    Deduplicates GKG entities against LLM entities using Jaro-Winkler fuzzy matching.

    Args:
        event: Event dict from BigQuery with llm_analysis and metadata.gkg fields

    Returns:
        Dict with extraction statistics (includes GKG vs LLM source counts)
    """
    from django.db import transaction
    from rapidfuzz import fuzz

    entities_data = event['llm_analysis']['entities']
    extracted_entities = []
    linked_count = 0
    gkg_entities_count = 0
    llm_entities_count = 0
    event_id = event['id']
    event_timestamp = event['mentioned_at']

    # Create mock event object for EntityService compatibility
    from types import SimpleNamespace
    mock_event = SimpleNamespace(timestamp=event_timestamp, id=event_id)

    # Track entity names for deduplication
    processed_names = set()

    with transaction.atomic():
        # Process LLM-extracted people
        for person in entities_data.get('people', []):
            entity, created, match_score = EntityService.find_or_create_entity(
                raw_name=person['name'],
                entity_type='PERSON',
                metadata={'role': person.get('role'), 'source': 'llm'}
            )

            EntityService.link_entity_to_event(
                entity=entity,
                event=mock_event,
                raw_name=person['name'],
                match_score=match_score,
                relevance=person.get('relevance', 1.0),
                event_id=event_id
            )

            # Update trending score
            TrendingService.update_entity_score(
                entity_id=str(entity.id),
                timestamp=event_timestamp,
                weight=person.get('relevance', 1.0)
            )

            extracted_entities.append(entity.canonical_name)
            processed_names.add(person['name'].lower())
            linked_count += 1
            llm_entities_count += 1

        # Process LLM-extracted organizations
        for org in entities_data.get('organizations', []):
            entity, created, match_score = EntityService.find_or_create_entity(
                raw_name=org['name'],
                entity_type='ORGANIZATION',
                metadata={'org_type': org.get('type'), 'source': 'llm'}
            )

            EntityService.link_entity_to_event(
                entity=entity,
                event=mock_event,
                raw_name=org['name'],
                match_score=match_score,
                relevance=org.get('relevance', 1.0),
                event_id=event_id
            )

            TrendingService.update_entity_score(
                entity_id=str(entity.id),
                timestamp=event_timestamp,
                weight=org.get('relevance', 1.0)
            )

            extracted_entities.append(entity.canonical_name)
            processed_names.add(org['name'].lower())
            linked_count += 1
            llm_entities_count += 1

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

            TrendingService.update_entity_score(
                entity_id=str(entity.id),
                timestamp=event_timestamp,
                weight=location.get('relevance', 1.0)
            )

            extracted_entities.append(entity.canonical_name)
            linked_count += 1

        # Process GKG-sourced entities (supplement LLM extraction)
        gkg_data = event.get('metadata', {}).get('gkg')
        if gkg_data:
            # Helper function for fuzzy deduplication
            def is_duplicate(name: str, threshold: float = 0.85) -> bool:
                """Check if name is duplicate using Jaro-Winkler similarity."""
                name_lower = name.lower()
                for processed in processed_names:
                    score = fuzz.jaro_winkler(name_lower, processed)
                    if score >= threshold:
                        return True
                return False

            # Process GKG persons
            for person_name in gkg_data.get('persons', []):
                if not person_name or is_duplicate(person_name):
                    continue  # Skip if duplicate or empty

                entity, created, match_score = EntityService.find_or_create_entity(
                    raw_name=person_name,
                    entity_type='PERSON',
                    metadata={'source': 'gkg'}
                )

                EntityService.link_entity_to_event(
                    entity=entity,
                    event=mock_event,
                    raw_name=person_name,
                    match_score=match_score,
                    relevance=0.8,  # GKG entities have high confidence
                    event_id=event_id
                )

                TrendingService.update_entity_score(
                    entity_id=str(entity.id),
                    timestamp=event_timestamp,
                    weight=0.8
                )

                extracted_entities.append(entity.canonical_name)
                processed_names.add(person_name.lower())
                linked_count += 1
                gkg_entities_count += 1

            # Process GKG organizations
            for org_name in gkg_data.get('organizations', []):
                if not org_name or is_duplicate(org_name):
                    continue  # Skip if duplicate or empty

                entity, created, match_score = EntityService.find_or_create_entity(
                    raw_name=org_name,
                    entity_type='ORGANIZATION',
                    metadata={'source': 'gkg'}
                )

                EntityService.link_entity_to_event(
                    entity=entity,
                    event=mock_event,
                    raw_name=org_name,
                    match_score=match_score,
                    relevance=0.8,
                    event_id=event_id
                )

                TrendingService.update_entity_score(
                    entity_id=str(entity.id),
                    timestamp=event_timestamp,
                    weight=0.8
                )

                extracted_entities.append(entity.canonical_name)
                processed_names.add(org_name.lower())
                linked_count += 1
                gkg_entities_count += 1

    logger.info(
        f"Entity extraction complete for event {event_id}: "
        f"{llm_entities_count} LLM entities, {gkg_entities_count} GKG entities"
    )

    return {
        'status': 'success',
        'event_id': event_id,
        'entities_extracted': len(extracted_entities),
        'entities_linked': linked_count,
        'entity_names': extracted_entities,
        'llm_entities': llm_entities_count,
        'gkg_entities': gkg_entities_count
    }


def _extract_from_entities_array(event: dict) -> Dict[str, Any]:
    """
    Fallback extraction from event['entities'] array.

    Used when llm_analysis.entities is not available.
    Infers entity types heuristically.

    Args:
        event: Event dict from BigQuery with entities array

    Returns:
        Dict with extraction statistics
    """
    from django.db import transaction

    extracted_entities = []
    linked_count = 0
    event_id = event['id']
    event_timestamp = event['mentioned_at']

    # Create mock event object for EntityService compatibility
    from types import SimpleNamespace
    mock_event = SimpleNamespace(timestamp=event_timestamp, id=event_id)

    with transaction.atomic():
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

            TrendingService.update_entity_score(
                entity_id=str(entity.id),
                timestamp=event_timestamp,
                weight=1.0
            )

            extracted_entities.append(entity.canonical_name)
            linked_count += 1

    return {
        'status': 'success',
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
