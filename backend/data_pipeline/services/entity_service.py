"""
Entity service for deduplication and fuzzy matching using RapidFuzz.

This service normalizes entity mentions from events using JaroWinkler
similarity to deduplicate name variations (e.g., "Nicolás Maduro" = "N. Maduro").
"""

from typing import Tuple, Optional
from django.db import transaction
from django.utils import timezone
from rapidfuzz import process, utils
from rapidfuzz.distance import JaroWinkler

from core.models import Entity, EntityMention, Event


class EntityService:
    """Service for entity extraction, normalization, and tracking."""

    SIMILARITY_THRESHOLD = 0.85  # 85% match required for deduplication

    @classmethod
    def find_or_create_entity(
        cls,
        raw_name: str,
        entity_type: str,
        metadata: dict = None
    ) -> Tuple[Entity, bool, float]:
        """
        Find matching entity using fuzzy matching or create new one.

        Args:
            raw_name: Entity name to match (e.g., "Nicolás Maduro")
            entity_type: Type of entity (PERSON, ORGANIZATION, GOVERNMENT, LOCATION)
            metadata: Optional metadata dict (roles, descriptions, etc.)

        Returns:
            Tuple of (entity, created, match_score)
            - entity: Entity object (matched or created)
            - created: True if new entity was created, False if matched
            - match_score: Fuzzy match confidence (1.0 if created, 0.0-1.0 if matched)
        """
        # Normalize input
        normalized_name = cls._normalize_name(raw_name)

        # Get all entities of same type for matching
        existing_entities = Entity.objects.filter(entity_type=entity_type)

        if not existing_entities.exists():
            # First entity of this type - create new
            entity = cls._create_new_entity(
                canonical_name=normalized_name,
                entity_type=entity_type,
                metadata=metadata
            )
            return entity, True, 1.0

        # Build search list: canonical names + all aliases
        search_candidates = {}
        for entity in existing_entities:
            search_candidates[entity.canonical_name] = entity
            for alias in entity.aliases:
                search_candidates[alias] = entity

        # Find best match using Jaro-Winkler
        match_result = process.extractOne(
            normalized_name,
            search_candidates.keys(),
            scorer=JaroWinkler.similarity,
            processor=utils.default_process
        )

        if match_result and match_result[1] >= cls.SIMILARITY_THRESHOLD:
            # Match found - return existing entity
            matched_name = match_result[0]
            match_score = match_result[1]
            entity = search_candidates[matched_name]

            # Add raw_name to aliases if not already present
            cls._update_entity_alias(entity, normalized_name, metadata)

            return entity, False, match_score
        else:
            # No match - create new entity
            entity = cls._create_new_entity(
                canonical_name=normalized_name,
                entity_type=entity_type,
                metadata=metadata
            )
            return entity, True, 1.0

    @classmethod
    @transaction.atomic
    def link_entity_to_event(
        cls,
        entity: Entity,
        event: Event,
        raw_name: str,
        match_score: float,
        relevance: float = None
    ) -> EntityMention:
        """
        Create EntityMention linking entity to event.

        Args:
            entity: Entity to link
            event: Event to link
            raw_name: Original name as extracted from event
            match_score: Fuzzy match score (0.0-1.0)
            relevance: Optional LLM relevance score

        Returns:
            EntityMention instance
        """
        # Create or get EntityMention
        mention, created = EntityMention.objects.get_or_create(
            entity=entity,
            event=event,
            raw_name=raw_name,
            defaults={
                'match_score': match_score,
                'relevance': relevance,
                'mentioned_at': event.timestamp
            }
        )

        if created:
            # Increment entity mention count and update last_seen
            entity.mention_count += 1
            entity.last_seen = timezone.now()
            entity.save(update_fields=['mention_count', 'last_seen', 'updated_at'])

        return mention

    @classmethod
    @transaction.atomic
    def batch_deduplicate_entities(
        cls,
        entity_type: str = None,
        threshold: float = 0.90
    ) -> int:
        """
        Find and merge duplicate entities using pairwise fuzzy matching.

        This is a maintenance operation for cleaning up the entity database.
        Uses higher threshold (0.90) than real-time matching to avoid false merges.

        Args:
            entity_type: Optional filter by entity type
            threshold: Minimum similarity score for merging (default 0.90)

        Returns:
            Number of entities merged
        """
        # Get entities to deduplicate
        query = Entity.objects.all()
        if entity_type:
            query = query.filter(entity_type=entity_type)

        entities = list(query.order_by('-mention_count'))
        merged_count = 0

        # Track entities to delete
        entities_to_delete = set()

        # Pairwise comparison
        for i, entity1 in enumerate(entities):
            if entity1.id in entities_to_delete:
                continue

            # Build search candidates from remaining entities
            candidates = {}
            for j in range(i + 1, len(entities)):
                entity2 = entities[j]
                if entity2.id in entities_to_delete:
                    continue

                # Check similarity
                score = JaroWinkler.similarity(
                    utils.default_process(entity1.canonical_name),
                    utils.default_process(entity2.canonical_name)
                )

                if score >= threshold:
                    # Merge entity2 into entity1
                    cls._merge_entities(entity1, entity2)
                    entities_to_delete.add(entity2.id)
                    merged_count += 1

        # Delete merged entities
        if entities_to_delete:
            Entity.objects.filter(id__in=entities_to_delete).delete()

        return merged_count

    @classmethod
    def _normalize_name(cls, name: str) -> str:
        """Normalize entity name (strip whitespace, normalize Unicode)."""
        import unicodedata
        # Normalize to NFC form (canonical composition)
        normalized = unicodedata.normalize('NFC', name)
        return normalized.strip()

    @classmethod
    def _create_new_entity(
        cls,
        canonical_name: str,
        entity_type: str,
        metadata: dict = None
    ) -> Entity:
        """Create new entity record."""
        now = timezone.now()
        entity = Entity.objects.create(
            canonical_name=canonical_name,
            entity_type=entity_type,
            aliases=[],
            mention_count=0,
            first_seen=now,
            last_seen=now,
            metadata=metadata or {}
        )
        return entity

    @classmethod
    def _update_entity_alias(
        cls,
        entity: Entity,
        alias: str,
        metadata: dict = None
    ):
        """Add alias to entity if not already present."""
        # Add to aliases if not canonical name and not already in list
        if alias != entity.canonical_name and alias not in entity.aliases:
            entity.aliases.append(alias)

        # Merge metadata if provided
        if metadata:
            if entity.metadata is None:
                entity.metadata = {}
            # Merge new metadata (simple update, can be enhanced)
            entity.metadata.update(metadata)

        entity.save(update_fields=['aliases', 'metadata', 'updated_at'])

    @classmethod
    @transaction.atomic
    def _merge_entities(cls, target: Entity, source: Entity):
        """
        Merge source entity into target entity.

        Moves all EntityMentions to target, combines aliases, sums mention_counts.
        """
        # Move all mentions from source to target
        EntityMention.objects.filter(entity=source).update(entity=target)

        # Combine aliases
        for alias in source.aliases:
            if alias not in target.aliases and alias != target.canonical_name:
                target.aliases.append(alias)

        # Add source canonical name as alias if different
        if source.canonical_name != target.canonical_name:
            if source.canonical_name not in target.aliases:
                target.aliases.append(source.canonical_name)

        # Sum mention counts
        target.mention_count += source.mention_count

        # Update timestamps
        if source.first_seen < target.first_seen:
            target.first_seen = source.first_seen
        if source.last_seen > target.last_seen:
            target.last_seen = source.last_seen

        # Merge metadata
        if source.metadata:
            if target.metadata is None:
                target.metadata = {}
            target.metadata.update(source.metadata)

        target.save()
