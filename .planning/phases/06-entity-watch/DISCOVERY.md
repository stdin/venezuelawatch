# Phase 6: Entity Watch - Technical Discovery

**Date:** 2026-01-08
**Project:** VenezuelaWatch
**Context:** Entity tracking and leaderboard system for monitoring people, companies, and governments mentioned in events

---

## Executive Summary

This discovery document outlines the recommended technical approach for Phase 6: Entity Watch. The system will extract, normalize, and track entities (people, companies, governments) from event data, providing trending leaderboards and relationship graphs.

**Key Recommendation:** Use a **hybrid LLM + fuzzy matching** approach that leverages existing Claude analysis for entity extraction while using dedicated libraries for deduplication and normalization.

---

## Standard Stack

### 1. Entity Extraction (NER)

**RECOMMENDED: LLM-based extraction (Claude)**

**Rationale:**
- VenezuelaWatch already uses Claude 4.5 for comprehensive event analysis
- Current `LLMIntelligence.analyze_event_comprehensive()` already extracts structured entities:
  ```python
  'entities': {
      'people': [{'name': str, 'role': str, 'relevance': float}],
      'organizations': [{'name': str, 'type': str, 'relevance': float}],
      'locations': [{'name': str, 'type': str, 'relevance': float}]
  }
  ```
- LLMs outperform traditional NER (spaCy) for accuracy and contextual understanding
- Performance comparison (Sunscrapers 2024):
  - GPT-4: 9/10 accuracy
  - spaCy: 3/10 accuracy
- LLMs provide contextual information (roles, relationships) that spaCy cannot
- Multilingual support (Spanish/English/Portuguese) already working
- Zero additional API calls (already analyzing events)

**Traditional NER (NOT recommended for primary extraction):**
- **spaCy** (`en_core_web_sm`, `es_core_news_sm`) - Fast but less accurate
- **Stanza** - More accurate but slower
- **Use case:** Fallback for real-time extraction if LLM quota exceeded

**Decision:** Continue using Claude for entity extraction, extend existing schema.

### 2. Entity Normalization & Deduplication

**RECOMMENDED: RapidFuzz + Dedupe**

**Primary Tool: RapidFuzz** (Python library)
```bash
pip install rapidfuzz
```

**Key Features:**
- Fast fuzzy string matching (MIT license, no dependencies)
- 10x faster than FuzzyWuzzy
- Multiple similarity algorithms:
  - **Jaro-Winkler**: Best for name matching (favors prefix matches)
  - **WRatio**: Best for general text with preprocessing
  - **Levenshtein**: Edit distance
- Case-insensitive matching with preprocessing

**Example Code:**
```python
from rapidfuzz import fuzz, process, utils
from rapidfuzz.distance import JaroWinkler

# Name normalization example
def find_matching_entity(new_name: str, existing_names: List[str], threshold: float = 0.85) -> Optional[str]:
    """
    Find best matching entity name using Jaro-Winkler similarity.

    Args:
        new_name: Entity name to match (e.g., "Nicolás Maduro")
        existing_names: List of known entities
        threshold: Minimum similarity score (0.85 = 85% match)

    Returns:
        Best matching name or None if no match above threshold
    """
    # Use Jaro-Winkler for name matching (better for prefixes)
    result = process.extractOne(
        new_name,
        existing_names,
        scorer=JaroWinkler.similarity,
        processor=utils.default_process  # Lowercase, strip whitespace
    )

    if result and result[1] >= threshold:
        return result[0]  # Return matched name
    return None

# Examples:
candidates = ["Nicolás Maduro", "Vladimir Putin", "Joe Biden"]
find_matching_entity("N. Maduro", candidates)  # Returns "Nicolás Maduro"
find_matching_entity("President Maduro", candidates)  # Returns "Nicolás Maduro"
find_matching_entity("Maduro", candidates)  # Returns "Nicolás Maduro"
```

**Secondary Tool: Dedupe** (for complex deduplication)
```bash
pip install dedupe
```

**Use case:** Batch deduplication of large entity lists using machine learning
- Learns from human-labeled examples
- Handles complex name variations
- Scales to large databases
- **Use when:** Merging entity databases, cleaning historical data

**Decision:** Use RapidFuzz for real-time matching, Dedupe for batch cleanup.

### 3. Entity Relationship Tracking

**RECOMMENDED: PostgreSQL JSONField (current) + Optional Neo4j (future)**

**Current Phase (Phase 6):**
- Store relationships in existing `Event.relationships` JSONField:
  ```python
  relationships = [
      {'subject': 'Maduro', 'predicate': 'leads', 'object': 'Venezuela', 'confidence': 0.95}
  ]
  ```
- Aggregate relationships across events using Django ORM:
  ```python
  # Count mentions of entity pairs
  from django.db.models import Count, Q
  from django.contrib.postgres.aggregates import ArrayAgg

  Event.objects.filter(
      relationships__contains=[{'subject': 'Maduro'}]
  ).aggregate(
      total_mentions=Count('id'),
      related_entities=ArrayAgg('relationships')
  )
  ```

**Future Phase (If graph queries become complex):**
- **Neo4j** with `neo4j-graphrag-python` for entity-resolved knowledge graphs
- **Use when:** Need to query multi-hop relationships (e.g., "Who is connected to Maduro through PDVSA?")
- **Migration path:** Export PostgreSQL relationships to Neo4j using Cypher

**Decision:** Start with PostgreSQL JSONField, evaluate Neo4j if relationship queries become performance bottleneck.

### 4. Trending & Ranking Algorithm

**RECOMMENDED: Redis Sorted Sets + Time-decay algorithm**

**Primary Tool: Redis Sorted Sets**
```bash
# Already available in project (used for caching)
pip install redis
```

**Architecture:**
```python
import redis
from datetime import datetime, timedelta

redis_client = redis.Redis(host='localhost', port=6379, db=0)

class EntityLeaderboard:
    """Real-time entity trending leaderboard using Redis."""

    @staticmethod
    def add_entity_mention(entity_name: str, timestamp: datetime, weight: float = 1.0):
        """
        Add entity mention with time-decay scoring.

        Score = weight * recency_factor
        - Recent mentions (last 24h) get higher scores
        - Older mentions decay exponentially
        """
        # Calculate time decay (exponential decay over 7 days)
        now = datetime.utcnow()
        age_hours = (now - timestamp).total_seconds() / 3600
        recency_factor = math.exp(-age_hours / 168)  # Half-life = 7 days

        score = weight * recency_factor

        # Increment score in sorted set
        redis_client.zincrby('entity:trending', score, entity_name)

    @staticmethod
    def get_trending_entities(limit: int = 10) -> List[Tuple[str, float]]:
        """Get top N trending entities."""
        # ZREVRANGE returns highest scores first
        return redis_client.zrevrange('entity:trending', 0, limit-1, withscores=True)

    @staticmethod
    def get_entity_rank(entity_name: str) -> Optional[int]:
        """Get entity's current rank (1-indexed)."""
        rank = redis_client.zrevrank('entity:trending', entity_name)
        return rank + 1 if rank is not None else None
```

**Time-Decay Algorithm Options:**

1. **Exponential Decay** (Recommended for trending)
   ```python
   score = weight * exp(-age_hours / half_life)
   # Half-life = 7 days (168 hours)
   # Recent mentions matter more
   ```

2. **Reddit Hot Score** (For discussion-like ranking)
   ```python
   from datetime import datetime
   import math

   def reddit_hot_score(mentions: int, timestamp: datetime) -> float:
       """Reddit's hot ranking algorithm."""
       epoch = datetime(1970, 1, 1)
       seconds = (timestamp - epoch).total_seconds() - 1134028003
       order = math.log10(max(abs(mentions), 1))
       sign = 1 if mentions > 0 else -1
       return round(sign * order + seconds / 45000, 7)
   ```

3. **Hacker News Hot Score** (For velocity-based ranking)
   ```python
   def hn_hot_score(mentions: int, age_hours: float, gravity: float = 1.8) -> float:
       """Hacker News ranking algorithm."""
       return (mentions - 1) / (age_hours + 2) ** gravity
   ```

**Recommendation:** Use **exponential decay** for entity trending (simple, predictable, adjustable half-life).

**Performance:**
- Redis Sorted Sets: O(log N) for add/update/rank operations
- Handle millions of entities
- Real-time updates (no batch processing needed)

**Alternative (if Redis not available):**
- PostgreSQL with materialized views (refresh every 5-15 minutes)
- Trade-off: Less real-time, but simpler infrastructure

### 5. Database Schema Extensions

**New Model: `Entity`**

```python
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex

class Entity(models.Model):
    """
    Deduplicated entity (person, company, government) extracted from events.
    Aggregates mentions across all events.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Canonical entity information
    canonical_name = models.CharField(
        max_length=200,
        unique=True,
        db_index=True,
        help_text="Normalized/deduplicated entity name"
    )
    entity_type = models.CharField(
        max_length=50,
        choices=[
            ('PERSON', 'Person'),
            ('ORGANIZATION', 'Organization'),
            ('GOVERNMENT', 'Government Agency'),
        ],
        db_index=True
    )

    # Aliases and variations
    aliases = ArrayField(
        models.CharField(max_length=200),
        default=list,
        help_text="Known name variations (e.g., ['N. Maduro', 'President Maduro'])"
    )

    # Aggregated metadata
    first_seen = models.DateTimeField(db_index=True)
    last_seen = models.DateTimeField(db_index=True)
    mention_count = models.IntegerField(default=0, db_index=True)

    # Contextual information (from LLM)
    roles = ArrayField(
        models.CharField(max_length=200),
        default=list,
        help_text="Roles mentioned in events (e.g., ['President of Venezuela', 'PSUV Leader'])"
    )

    # Trending metrics (updated by background task)
    trending_score = models.FloatField(
        default=0.0,
        db_index=True,
        help_text="Real-time trending score (from Redis)"
    )
    trending_rank = models.IntegerField(
        null=True,
        blank=True,
        help_text="Current rank in trending leaderboard"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'entities'
        ordering = ['-trending_score', '-mention_count']
        indexes = [
            models.Index(fields=['-trending_score']),
            models.Index(fields=['-mention_count']),
            GinIndex(fields=['aliases']),  # Fast array contains queries
        ]

class EntityMention(models.Model):
    """
    Individual entity mention in an event (many-to-many through table).
    Links events to deduplicated entities.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Relationships
    entity = models.ForeignKey(
        Entity,
        on_delete=models.CASCADE,
        related_name='mentions'
    )
    event = models.ForeignKey(
        'Event',
        on_delete=models.CASCADE,
        related_name='entity_mentions'
    )

    # Mention metadata
    mention_text = models.CharField(
        max_length=200,
        help_text="Exact text as it appeared in event"
    )
    relevance_score = models.FloatField(
        help_text="Relevance/confidence score from LLM (0.0-1.0)"
    )
    role_in_event = models.CharField(
        max_length=200,
        blank=True,
        help_text="Role/context in this specific event"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'entity_mentions'
        unique_together = [['entity', 'event']]
        indexes = [
            models.Index(fields=['entity', '-created_at']),
            models.Index(fields=['event']),
        ]
```

---

## Architecture Patterns

### Pattern 1: Entity Extraction Pipeline

**Flow:**
1. **Event ingestion** → LLM analysis (already happening in Phase 4-5)
2. **Extract entities** from `Event.llm_analysis['entities']`
3. **Normalize/deduplicate** using RapidFuzz
4. **Create or update** `Entity` records
5. **Create** `EntityMention` links
6. **Update trending scores** in Redis

**Implementation:**
```python
# data_pipeline/services/entity_service.py

from rapidfuzz import process, utils
from rapidfuzz.distance import JaroWinkler
from typing import List, Dict, Tuple
from core.models import Entity, EntityMention, Event

class EntityService:
    """Service for entity extraction, normalization, and tracking."""

    SIMILARITY_THRESHOLD = 0.85  # 85% match required

    @classmethod
    def process_event_entities(cls, event: Event) -> List[Entity]:
        """
        Extract and normalize entities from event's LLM analysis.

        Args:
            event: Event object with populated llm_analysis

        Returns:
            List of Entity objects (created or matched)
        """
        if not event.llm_analysis or 'entities' not in event.llm_analysis:
            return []

        entities_data = event.llm_analysis['entities']
        processed_entities = []

        # Process people
        for person in entities_data.get('people', []):
            entity = cls._normalize_and_create_entity(
                name=person['name'],
                entity_type='PERSON',
                role=person.get('role'),
                relevance=person.get('relevance', 1.0)
            )
            cls._create_mention(entity, event, person)
            processed_entities.append(entity)

        # Process organizations
        for org in entities_data.get('organizations', []):
            entity = cls._normalize_and_create_entity(
                name=org['name'],
                entity_type='ORGANIZATION',
                role=org.get('type'),
                relevance=org.get('relevance', 1.0)
            )
            cls._create_mention(entity, event, org)
            processed_entities.append(entity)

        # Update trending scores
        cls._update_trending_scores(processed_entities, event.timestamp)

        return processed_entities

    @classmethod
    def _normalize_and_create_entity(
        cls,
        name: str,
        entity_type: str,
        role: str = None,
        relevance: float = 1.0
    ) -> Entity:
        """
        Find matching entity or create new one.
        Uses fuzzy matching to deduplicate.
        """
        # Get all entities of same type
        existing_entities = Entity.objects.filter(
            entity_type=entity_type
        ).values_list('canonical_name', flat=True)

        if not existing_entities:
            # First entity of this type
            return cls._create_new_entity(name, entity_type, role)

        # Find best match using Jaro-Winkler
        match = process.extractOne(
            name,
            existing_entities,
            scorer=JaroWinkler.similarity,
            processor=utils.default_process
        )

        if match and match[1] >= cls.SIMILARITY_THRESHOLD:
            # Match found - update existing entity
            entity = Entity.objects.get(canonical_name=match[0])
            cls._update_entity_alias(entity, name, role)
            return entity
        else:
            # No match - create new entity
            return cls._create_new_entity(name, entity_type, role)

    @classmethod
    def _create_new_entity(cls, name: str, entity_type: str, role: str = None) -> Entity:
        """Create new entity record."""
        from django.utils import timezone

        entity = Entity.objects.create(
            canonical_name=name,
            entity_type=entity_type,
            first_seen=timezone.now(),
            last_seen=timezone.now(),
            mention_count=1,
            roles=[role] if role else []
        )
        return entity

    @classmethod
    def _update_entity_alias(cls, entity: Entity, alias: str, role: str = None):
        """Add alias to entity if not already present."""
        from django.utils import timezone

        if alias not in entity.aliases and alias != entity.canonical_name:
            entity.aliases.append(alias)

        if role and role not in entity.roles:
            entity.roles.append(role)

        entity.mention_count += 1
        entity.last_seen = timezone.now()
        entity.save()

    @classmethod
    def _create_mention(cls, entity: Entity, event: Event, entity_data: Dict):
        """Create EntityMention linking entity to event."""
        EntityMention.objects.get_or_create(
            entity=entity,
            event=event,
            defaults={
                'mention_text': entity_data['name'],
                'relevance_score': entity_data.get('relevance', 1.0),
                'role_in_event': entity_data.get('role', '')
            }
        )

    @classmethod
    def _update_trending_scores(cls, entities: List[Entity], timestamp):
        """Update Redis trending scores for entities."""
        from data_pipeline.services.trending_service import TrendingService

        for entity in entities:
            TrendingService.add_entity_mention(
                entity_name=entity.canonical_name,
                timestamp=timestamp,
                weight=1.0
            )
```

### Pattern 2: Trending Score Calculation

**Flow:**
1. **Real-time updates** → Redis Sorted Sets (immediate)
2. **Periodic sync** → PostgreSQL `Entity.trending_score` (every 15 minutes)
3. **Leaderboard queries** → Redis (fast) or PostgreSQL (acceptable)

**Implementation:**
```python
# data_pipeline/services/trending_service.py

import redis
import math
from datetime import datetime, timedelta
from typing import List, Tuple
from django.conf import settings

class TrendingService:
    """Manages entity trending scores using Redis + time-decay."""

    REDIS_KEY = 'entity:trending'
    HALF_LIFE_HOURS = 168  # 7 days

    redis_client = redis.Redis.from_url(settings.REDIS_URL)

    @classmethod
    def add_entity_mention(cls, entity_name: str, timestamp: datetime, weight: float = 1.0):
        """
        Add entity mention with time-decay scoring.

        Args:
            entity_name: Canonical entity name
            timestamp: When entity was mentioned
            weight: Importance multiplier (default 1.0)
        """
        # Calculate time decay
        now = datetime.utcnow()
        age_hours = (now - timestamp).total_seconds() / 3600
        recency_factor = math.exp(-age_hours / cls.HALF_LIFE_HOURS)

        score = weight * recency_factor

        # Increment score in Redis
        cls.redis_client.zincrby(cls.REDIS_KEY, score, entity_name)

    @classmethod
    def get_trending_entities(cls, limit: int = 50) -> List[Tuple[str, float]]:
        """Get top N trending entities with scores."""
        results = cls.redis_client.zrevrange(
            cls.REDIS_KEY,
            0,
            limit - 1,
            withscores=True
        )
        return [(name.decode('utf-8'), score) for name, score in results]

    @classmethod
    def get_entity_rank(cls, entity_name: str) -> int:
        """Get entity's rank in trending leaderboard (1-indexed)."""
        rank = cls.redis_client.zrevrank(cls.REDIS_KEY, entity_name)
        return rank + 1 if rank is not None else None

    @classmethod
    def sync_to_database(cls):
        """
        Sync Redis trending scores to PostgreSQL.
        Run this periodically (every 15 minutes via Celery).
        """
        from core.models import Entity

        trending_data = cls.get_trending_entities(limit=1000)

        for rank, (entity_name, score) in enumerate(trending_data, start=1):
            Entity.objects.filter(canonical_name=entity_name).update(
                trending_score=score,
                trending_rank=rank
            )
```

### Pattern 3: Celery Background Tasks

**Tasks:**
1. **Extract entities from new events** (triggered after LLM analysis)
2. **Sync trending scores** (periodic, every 15 minutes)
3. **Recalculate trending scores** (daily, apply decay to all entities)

**Implementation:**
```python
# data_pipeline/tasks/entity_tasks.py

from celery import shared_task
from core.models import Event, Entity
from data_pipeline.services.entity_service import EntityService
from data_pipeline.services.trending_service import TrendingService

@shared_task
def process_event_entities(event_id: str):
    """
    Extract and normalize entities from event.
    Triggered after LLM analysis completes.
    """
    try:
        event = Event.objects.get(id=event_id)
        entities = EntityService.process_event_entities(event)
        return {
            'event_id': str(event_id),
            'entities_processed': len(entities),
            'entity_names': [e.canonical_name for e in entities]
        }
    except Event.DoesNotExist:
        return {'error': 'Event not found'}

@shared_task
def sync_trending_scores():
    """
    Sync Redis trending scores to PostgreSQL.
    Run every 15 minutes via Celery Beat.
    """
    TrendingService.sync_to_database()
    return {'status': 'success', 'synced_at': datetime.utcnow().isoformat()}

@shared_task
def recalculate_trending_scores():
    """
    Recalculate all trending scores with time decay.
    Run daily at midnight via Celery Beat.
    """
    from django.utils import timezone

    # Get all entity mentions from last 30 days
    cutoff = timezone.now() - timedelta(days=30)

    # Clear Redis
    TrendingService.redis_client.delete(TrendingService.REDIS_KEY)

    # Rebuild from database
    from core.models import EntityMention

    mentions = EntityMention.objects.filter(
        created_at__gte=cutoff
    ).select_related('entity', 'event')

    for mention in mentions:
        TrendingService.add_entity_mention(
            entity_name=mention.entity.canonical_name,
            timestamp=mention.event.timestamp,
            weight=mention.relevance_score
        )

    # Sync to database
    TrendingService.sync_to_database()

    return {'status': 'success', 'mentions_processed': mentions.count()}
```

**Celery Beat Schedule:**
```python
# venezuelawatch/settings.py

CELERY_BEAT_SCHEDULE = {
    'sync-trending-scores': {
        'task': 'data_pipeline.tasks.entity_tasks.sync_trending_scores',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'recalculate-trending-scores': {
        'task': 'data_pipeline.tasks.entity_tasks.recalculate_trending_scores',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
}
```

---

## Don't Hand Roll

### 1. String Matching Algorithms

**DON'T:** Implement your own Levenshtein distance, Jaro-Winkler, or fuzzy matching.

**WHY:**
- RapidFuzz is highly optimized (10x faster than pure Python)
- Written in C++ with Python bindings
- Handles edge cases (Unicode, empty strings, etc.)
- Battle-tested in production

**USE:** `rapidfuzz` library

### 2. Trending Algorithms

**DON'T:** Build custom time-decay scoring system from scratch.

**WHY:**
- Redis Sorted Sets are O(log N) optimized
- Exponential decay is well-understood and predictable
- Existing libraries (python-trending, ranky) provide tested implementations

**USE:** Redis Sorted Sets + simple exponential decay formula

### 3. Entity Linking/Resolution

**DON'T:** Build complex entity linking system with custom graph algorithms.

**WHY:**
- Neo4j provides optimized graph traversal
- Entity resolution is a research field with existing solutions
- Dedupe library uses ML-based probabilistic matching

**USE (if needed):**
- Simple phase: RapidFuzz threshold matching
- Complex phase: Dedupe library or Neo4j entity resolution

### 4. Leaderboard Infrastructure

**DON'T:** Build custom ranking system with database triggers and materialized views.

**WHY:**
- Redis Sorted Sets are designed for this use case
- O(log N) performance vs. O(N log N) for database sorting
- Battle-tested in gaming leaderboards (millions of users)

**USE:** Redis Sorted Sets (existing infrastructure)

### 5. Batch Processing Frameworks

**DON'T:** Build custom job queue for entity processing.

**WHY:**
- Celery already integrated in VenezuelaWatch
- Handles retries, failures, scheduling
- Monitoring via Flower

**USE:** Celery (existing infrastructure)

---

## Common Pitfalls

### Pitfall 1: Over-aggressive Deduplication

**Problem:** Setting similarity threshold too low causes false matches.

**Example:**
```python
# TOO AGGRESSIVE (threshold = 0.60)
JaroWinkler.similarity("Nicolas Cage", "Nicolás Maduro")  # 0.71 - FALSE MATCH!

# SAFER (threshold = 0.85)
JaroWinkler.similarity("Nicolás Maduro", "N. Maduro")  # 0.90 - TRUE MATCH
```

**Solution:**
- Use conservative threshold (0.85+) for automatic matching
- Implement manual review for matches between 0.75-0.85
- Store match scores for auditing

### Pitfall 2: Case-Sensitive Matching

**Problem:** Missing matches due to case variations.

**Example:**
```python
# WRONG (case-sensitive)
"NICOLÁS MADURO" == "Nicolás Maduro"  # False

# CORRECT (preprocessing)
from rapidfuzz import utils
utils.default_process("NICOLÁS MADURO")  # "nicolás maduro"
```

**Solution:** Always use `processor=utils.default_process` in RapidFuzz calls.

### Pitfall 3: N+1 Query Problem in Entity Processing

**Problem:** Loading entities one-by-one in loop.

**Example:**
```python
# WRONG (N+1 queries)
for person in event.llm_analysis['entities']['people']:
    entity = Entity.objects.get(canonical_name=person['name'])  # Query per person!

# CORRECT (bulk fetch)
names = [p['name'] for p in event.llm_analysis['entities']['people']]
entities = Entity.objects.filter(canonical_name__in=names)  # Single query
entity_map = {e.canonical_name: e for e in entities}
```

**Solution:** Bulk fetch entities, use dictionary for lookups.

### Pitfall 4: Trending Score Staleness

**Problem:** Redis and PostgreSQL scores get out of sync.

**Example:**
```python
# Redis shows entity #1 trending
TrendingService.get_trending_entities(limit=10)  # ["Maduro", ...]

# PostgreSQL shows different ranking (out of date)
Entity.objects.order_by('-trending_score')[:10]  # Old data
```

**Solution:**
- Set up Celery Beat to sync every 15 minutes
- Use Redis as source of truth for real-time
- Use PostgreSQL for historical analysis
- Add `last_synced_at` timestamp to Entity model

### Pitfall 5: Memory Explosion with Large Alias Lists

**Problem:** ArrayField grows unbounded with every mention variation.

**Example:**
```python
# WRONG (unlimited growth)
entity.aliases.append(new_alias)  # Could grow to 1000s of aliases

# CORRECT (cap size)
MAX_ALIASES = 50
if new_alias not in entity.aliases:
    if len(entity.aliases) < MAX_ALIASES:
        entity.aliases.append(new_alias)
```

**Solution:**
- Limit alias list to top 50 most frequent variations
- Store full variation history in separate `EntityAlias` model if needed

### Pitfall 6: Unicode Normalization Issues

**Problem:** Accented characters cause false non-matches.

**Example:**
```python
# Different Unicode representations
"Nicolás" == "Nicolás"  # False! (one uses combining accent)

# NFD: Canonical Decomposition
"Nicolás" → "Nicola" + "́s"

# NFC: Canonical Composition (recommended)
"Nicolás" → "Nicolás"
```

**Solution:**
```python
import unicodedata

def normalize_name(name: str) -> str:
    """Normalize Unicode to NFC form."""
    return unicodedata.normalize('NFC', name).strip()

# Use in entity matching
normalized_name = normalize_name(person['name'])
```

### Pitfall 7: Ignoring Entity Type in Matching

**Problem:** Matching entities across different types.

**Example:**
```python
# WRONG (matches person with organization)
all_entities = Entity.objects.all()  # Mix of people, orgs, governments
find_matching_entity("Venezuela", all_entities)  # Could match person OR country!

# CORRECT (type-specific matching)
organizations = Entity.objects.filter(entity_type='ORGANIZATION')
find_matching_entity("Venezuela", organizations)
```

**Solution:** Always filter by entity_type before fuzzy matching.

### Pitfall 8: No Monitoring of LLM Entity Quality

**Problem:** LLM occasionally extracts incorrect entities, but no visibility.

**Example:**
```python
# LLM extracts "Bitcoin" as a person instead of concept
# No validation, gets added to database as PERSON entity
```

**Solution:**
- Log low-confidence entity extractions (relevance < 0.7)
- Implement admin review queue for new entities
- Track entity extraction accuracy metrics
- Add validation rules (e.g., person names should have 2+ words)

---

## Code Examples

### Example 1: Complete Entity Extraction from Event

```python
from core.models import Event, Entity, EntityMention
from data_pipeline.services.entity_service import EntityService

# After LLM analysis completes
event = Event.objects.get(id='some-uuid')

# Process all entities in event
entities = EntityService.process_event_entities(event)

# Result:
# - Entities created/updated in database
# - EntityMention records created
# - Trending scores updated in Redis

print(f"Processed {len(entities)} entities:")
for entity in entities:
    print(f"  - {entity.canonical_name} ({entity.entity_type})")
    print(f"    Mentions: {entity.mention_count}")
    print(f"    Aliases: {entity.aliases}")
```

### Example 2: Query Trending Entities

```python
from data_pipeline.services.trending_service import TrendingService
from core.models import Entity

# Get top 10 trending entities (real-time from Redis)
trending = TrendingService.get_trending_entities(limit=10)

for rank, (name, score) in enumerate(trending, start=1):
    print(f"{rank}. {name} (score: {score:.2f})")

# Get entity details from database
for name, score in trending:
    entity = Entity.objects.get(canonical_name=name)
    print(f"  Type: {entity.entity_type}")
    print(f"  Mentions: {entity.mention_count}")
    print(f"  First seen: {entity.first_seen}")
```

### Example 3: Find Entity Relationships

```python
from django.db.models import Q
from core.models import Event, Entity

# Find all events mentioning "Maduro"
maduro = Entity.objects.get(canonical_name="Nicolás Maduro")
maduro_events = Event.objects.filter(
    entity_mentions__entity=maduro
).order_by('-timestamp')

# Extract co-mentioned entities (network analysis)
co_mentioned = Entity.objects.filter(
    mentions__event__in=maduro_events
).exclude(
    id=maduro.id
).annotate(
    co_mention_count=Count('mentions')
).order_by('-co_mention_count')[:10]

print(f"Entities most often mentioned with {maduro.canonical_name}:")
for entity in co_mentioned:
    print(f"  - {entity.canonical_name} ({entity.co_mention_count} times)")
```

### Example 4: Batch Deduplicate Entities

```python
from rapidfuzz import process, utils
from rapidfuzz.distance import JaroWinkler
from core.models import Entity

def find_duplicate_entities(entity_type: str, threshold: float = 0.85):
    """
    Find potential duplicate entities using fuzzy matching.
    Returns list of (entity1, entity2, similarity_score) tuples.
    """
    entities = Entity.objects.filter(entity_type=entity_type)
    names = {e.id: e.canonical_name for e in entities}

    duplicates = []

    for entity_id, name in names.items():
        # Find similar names
        matches = process.extract(
            name,
            names.values(),
            scorer=JaroWinkler.similarity,
            processor=utils.default_process,
            limit=5
        )

        for match_name, score, _ in matches:
            if score >= threshold and match_name != name:
                # Find entity with this name
                match_entity = entities.get(canonical_name=match_name)
                if match_entity.id != entity_id:
                    duplicates.append((
                        entities.get(id=entity_id),
                        match_entity,
                        score
                    ))

    return duplicates

# Usage
duplicates = find_duplicate_entities('PERSON', threshold=0.88)
for e1, e2, score in duplicates:
    print(f"Potential duplicate ({score:.2f}): {e1.canonical_name} ≈ {e2.canonical_name}")
    print(f"  Mentions: {e1.mention_count} vs {e2.mention_count}")
```

### Example 5: Entity API Endpoint

```python
# data_pipeline/api.py (DRF ViewSet)

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from core.models import Entity, EntityMention

class EntityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for entity tracking and trending.
    """
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['canonical_name', 'aliases']
    ordering_fields = ['trending_score', 'mention_count', 'last_seen']

    @action(detail=False, methods=['get'])
    def trending(self, request):
        """
        GET /api/entities/trending/?limit=50

        Returns top trending entities with real-time scores.
        """
        limit = int(request.query_params.get('limit', 50))
        entity_type = request.query_params.get('type')  # Optional filter

        from data_pipeline.services.trending_service import TrendingService

        # Get trending from Redis
        trending = TrendingService.get_trending_entities(limit=limit)

        # Get entity details from database
        names = [name for name, score in trending]
        entities = Entity.objects.filter(canonical_name__in=names)

        if entity_type:
            entities = entities.filter(entity_type=entity_type)

        # Build response
        entity_map = {e.canonical_name: e for e in entities}
        results = []

        for rank, (name, score) in enumerate(trending, start=1):
            if name in entity_map:
                entity = entity_map[name]
                results.append({
                    'rank': rank,
                    'name': entity.canonical_name,
                    'type': entity.entity_type,
                    'trending_score': score,
                    'mention_count': entity.mention_count,
                    'last_seen': entity.last_seen,
                    'roles': entity.roles
                })

        return Response({
            'trending_entities': results,
            'count': len(results)
        })

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """
        GET /api/entities/{id}/timeline/

        Returns chronological timeline of entity mentions.
        """
        entity = self.get_object()

        mentions = EntityMention.objects.filter(
            entity=entity
        ).select_related('event').order_by('-event__timestamp')[:100]

        timeline = []
        for mention in mentions:
            timeline.append({
                'timestamp': mention.event.timestamp,
                'event_title': mention.event.title,
                'event_source': mention.event.source,
                'mention_text': mention.mention_text,
                'role': mention.role_in_event,
                'relevance': mention.relevance_score
            })

        return Response({
            'entity': entity.canonical_name,
            'timeline': timeline,
            'total_mentions': entity.mention_count
        })
```

---

## Performance Considerations

### Database Optimization

**Indexing Strategy:**
```python
# Entity model indexes (already in schema above)
class Entity(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['-trending_score']),      # Trending leaderboard
            models.Index(fields=['-mention_count']),       # All-time popular
            GinIndex(fields=['aliases']),                  # Fast array search
            models.Index(fields=['entity_type', '-trending_score']),  # Filtered leaderboards
        ]
```

**Query Optimization:**
```python
# Use select_related for foreign keys
EntityMention.objects.select_related('entity', 'event').all()

# Use prefetch_related for reverse foreign keys
Entity.objects.prefetch_related('mentions__event').all()

# Annotate instead of Python loops
Entity.objects.annotate(
    recent_mention_count=Count(
        'mentions',
        filter=Q(mentions__created_at__gte=last_week)
    )
).order_by('-recent_mention_count')
```

### Caching Strategy

**Multi-layer cache:**
1. **Redis Sorted Sets** → Real-time trending (TTL: infinite, manually purged)
2. **Redis Key-Value** → Entity details (TTL: 1 hour)
3. **Django query cache** → Database results (TTL: 15 minutes)

**Implementation:**
```python
from django.core.cache import cache

def get_entity_details(entity_id: str) -> Dict:
    """Get entity with caching."""
    cache_key = f"entity:{entity_id}"

    # Try cache first
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Load from database
    entity = Entity.objects.get(id=entity_id)
    result = {
        'id': str(entity.id),
        'name': entity.canonical_name,
        'type': entity.entity_type,
        'mention_count': entity.mention_count,
        'trending_score': entity.trending_score,
    }

    # Cache for 1 hour
    cache.set(cache_key, result, 3600)

    return result
```

### Scalability Limits

**Expected Volume:**
- Events: 10,000/month → 120,000/year
- Entities: ~1,000 unique (people + orgs + governments)
- Entity mentions: ~50,000/month (5 entities per event average)

**Performance Benchmarks:**
- RapidFuzz matching: ~10,000 comparisons/second
- Redis Sorted Set operations: O(log N) = ~10μs for 1M entities
- PostgreSQL GIN index: ~1ms for array contains queries

**Bottlenecks to Monitor:**
1. **Fuzzy matching**: O(N) comparisons for each new entity
   - **Solution:** Cache results, batch processing
2. **Redis memory**: Sorted sets grow unbounded
   - **Solution:** Purge entities with score < threshold monthly
3. **PostgreSQL JSONField queries**: Slow without indexes
   - **Solution:** Use GIN indexes on JSONField paths

---

## Recommended Libraries

**Required:**
```bash
# Entity matching and deduplication
rapidfuzz>=3.0.0

# Already available in project
redis>=5.0.0
celery>=5.3.0
django>=5.2.0
psycopg2-binary>=2.9.0
```

**Optional (for future enhancements):**
```bash
# Machine learning-based deduplication (if needed)
dedupe>=2.0.0

# Graph database (if relationship queries become complex)
neo4j>=5.0.0
neo4j-graphrag-python>=0.1.0

# Phonetic matching (for name variations)
jellyfish>=1.0.0  # Soundex, Metaphone algorithms
```

---

## Next Steps

1. **Phase 6.1:** Implement `Entity` and `EntityMention` models
2. **Phase 6.2:** Build `EntityService` with RapidFuzz normalization
3. **Phase 6.3:** Implement `TrendingService` with Redis Sorted Sets
4. **Phase 6.4:** Create Celery tasks for entity processing
5. **Phase 6.5:** Build API endpoints for trending entities
6. **Phase 6.6:** Frontend dashboard integration (leaderboard UI)

---

## References

- **RapidFuzz Documentation:** https://github.com/rapidfuzz/RapidFuzz
- **Dedupe Library:** https://github.com/dedupeio/dedupe
- **Redis Sorted Sets:** https://redis.io/docs/latest/develop/data-types/sorted-sets/
- **spaCy NER Comparison:** https://sunscrapers.com/blog/named-entity-recognition-comparison-spacy-chatgpt-bard-llama2/
- **Claude Structured Outputs:** https://docs.anthropic.com/en/docs/build-with-claude/structured-outputs
- **Django PostgreSQL Aggregation:** https://docs.djangoproject.com/en/5.2/ref/contrib/postgres/aggregates/
- **Trending Algorithms:** https://github.com/zhebrak/python-trending
- **Neo4j Entity Resolution:** https://neo4j.com/blog/developer/entity-resolved-knowledge-graphs/

---

**Document Version:** 1.0
**Last Updated:** 2026-01-08
**Status:** Ready for Phase Planning
