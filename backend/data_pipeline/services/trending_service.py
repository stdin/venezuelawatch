"""
TrendingService for Redis-based entity leaderboard with time-decay scoring.

Uses Redis Sorted Sets for O(log N) operations and exponential time-decay
with 7-day half-life for trending entity rankings.
"""

import redis
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from django.conf import settings
from django.db.models import Avg, Count, Q
from django.utils import timezone

from core.models import Entity, EntityMention


class TrendingService:
    """Real-time entity trending leaderboard using Redis Sorted Sets."""

    REDIS_KEY = 'entity:trending'
    HALF_LIFE_HOURS = 168  # 7 days = 168 hours

    # Initialize Redis client
    redis_client = redis.Redis.from_url(
        settings.CELERY_BROKER_URL,
        decode_responses=True
    )

    @classmethod
    def update_entity_score(
        cls,
        entity_id: str,
        timestamp: datetime,
        weight: float = 1.0
    ):
        """
        Update entity's trending score with time-decay.

        Args:
            entity_id: Entity UUID
            timestamp: When entity was mentioned (event timestamp)
            weight: Importance multiplier (default 1.0)

        Formula:
            score = weight * exp(-age_hours / 168)
            where 168 = 7-day half-life
        """
        # Calculate age in hours
        now = timezone.now()
        age_hours = (now - timestamp).total_seconds() / 3600

        # Apply exponential time-decay
        recency_factor = math.exp(-age_hours / cls.HALF_LIFE_HOURS)
        score = weight * recency_factor

        # Increment score in Redis Sorted Set
        cls.redis_client.zincrby(cls.REDIS_KEY, score, str(entity_id))

    @classmethod
    def get_trending_entities(
        cls,
        metric: str = 'mentions',
        limit: int = 50
    ) -> List[Dict]:
        """
        Get top trending entities by metric.

        Args:
            metric: Metric to rank by ('mentions', 'risk', 'sanctions')
            limit: Maximum number of entities to return

        Returns:
            List of dicts with entity details and scores:
            [{'entity_id': uuid, 'canonical_name': str, 'entity_type': str,
              'score': float, 'mention_count': int}]
        """
        if metric == 'mentions':
            # Use Redis trending scores
            return cls._get_trending_from_redis(limit)
        elif metric == 'risk':
            # Query by average risk score
            return cls._get_trending_by_risk(limit)
        elif metric == 'sanctions':
            # Query by sanctions matches
            return cls._get_trending_by_sanctions(limit)
        else:
            raise ValueError(f"Invalid metric: {metric}. Must be 'mentions', 'risk', or 'sanctions'")

    @classmethod
    def get_entity_rank(cls, entity_id: str) -> Optional[int]:
        """
        Get entity's rank in trending leaderboard (1-indexed).

        Args:
            entity_id: Entity UUID

        Returns:
            Rank (1 = highest) or None if not ranked
        """
        rank = cls.redis_client.zrevrank(cls.REDIS_KEY, str(entity_id))
        return rank + 1 if rank is not None else None

    @classmethod
    def sync_trending_scores(cls, days: int = 30):
        """
        Recalculate all trending scores from EntityMention records.

        Used for periodic sync (daily cron) to correct drift between
        Redis and database. Clears Redis and rebuilds from mentions.

        Args:
            days: Time window for recalculation (default 30 days)
        """
        from django.utils import timezone

        # Clear existing Redis key
        cls.redis_client.delete(cls.REDIS_KEY)

        # Calculate cutoff timestamp
        cutoff = timezone.now() - timedelta(days=days)

        # Query all mentions in time window
        mentions = EntityMention.objects.filter(
            mentioned_at__gte=cutoff
        ).select_related('entity')

        # Rebuild trending scores
        for mention in mentions:
            cls.update_entity_score(
                entity_id=str(mention.entity.id),
                timestamp=mention.mentioned_at,
                weight=mention.relevance or 1.0
            )

        return {
            'mentions_processed': mentions.count(),
            'days': days,
            'cutoff': cutoff.isoformat()
        }

    # Private helper methods

    @classmethod
    def _get_trending_from_redis(cls, limit: int) -> List[Dict]:
        """Get trending entities from Redis Sorted Set."""
        # Get top entity IDs with scores from Redis
        trending_data = cls.redis_client.zrevrange(
            cls.REDIS_KEY,
            0,
            limit - 1,
            withscores=True
        )

        if not trending_data:
            return []

        # Extract entity IDs
        entity_ids = [entity_id for entity_id, score in trending_data]

        # Bulk fetch Entity objects
        entities = Entity.objects.filter(id__in=entity_ids)
        entity_map = {str(e.id): e for e in entities}

        # Build result list maintaining Redis order
        results = []
        for entity_id, score in trending_data:
            if entity_id in entity_map:
                entity = entity_map[entity_id]
                results.append({
                    'entity_id': str(entity.id),
                    'canonical_name': entity.canonical_name,
                    'entity_type': entity.entity_type,
                    'score': score,
                    'mention_count': entity.mention_count
                })

        return results

    @classmethod
    def _get_trending_by_risk(cls, limit: int) -> List[Dict]:
        """Get entities ranked by average risk score from mentions."""
        from core.models import Event

        # Query entities with mentions, annotate with avg risk score
        entities = Entity.objects.filter(
            mention_count__gt=0
        ).prefetch_related(
            'mentions__event'
        ).annotate(
            avg_risk_score=Avg(
                'mentions__event__risk_score',
                filter=Q(mentions__event__risk_score__isnull=False)
            )
        ).filter(
            avg_risk_score__isnull=False
        ).order_by('-avg_risk_score')[:limit]

        # Build result list
        results = []
        for entity in entities:
            results.append({
                'entity_id': str(entity.id),
                'canonical_name': entity.canonical_name,
                'entity_type': entity.entity_type,
                'score': entity.avg_risk_score,
                'mention_count': entity.mention_count
            })

        return results

    @classmethod
    def _get_trending_by_sanctions(cls, limit: int) -> List[Dict]:
        """Get entities ranked by sanctions matches."""
        from core.models import SanctionsMatch

        # Get entities with sanctions matches
        # Count sanctions matches per entity
        entities_with_sanctions = Entity.objects.filter(
            mentions__event__sanctions_matches__isnull=False
        ).distinct().annotate(
            sanctions_count=Count('mentions__event__sanctions_matches')
        ).order_by('-sanctions_count', '-mention_count')[:limit]

        # Build result list
        results = []
        for entity in entities_with_sanctions:
            results.append({
                'entity_id': str(entity.id),
                'canonical_name': entity.canonical_name,
                'entity_type': entity.entity_type,
                'score': entity.sanctions_count,
                'mention_count': entity.mention_count
            })

        return results
