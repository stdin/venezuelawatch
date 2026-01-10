"""
Graph builder service for entity relationship visualization.

Builds entity co-occurrence graphs from PostgreSQL EntityMention data,
calculates relationship weights, and prepares data for frontend visualization.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from django.db.models import Count, Q
from django.utils import timezone

from core.models import Entity, EntityMention


class GraphBuilder:
    """Builds entity relationship graphs from co-occurrence patterns."""

    def build_entity_graph(
        self,
        time_range: str = "30d",
        min_cooccurrence: int = 3
    ) -> Dict[str, Any]:
        """
        Build entity relationship graph from co-occurrence in events.

        Args:
            time_range: Time window ("7d", "30d", "90d")
            min_cooccurrence: Minimum co-occurrence count to include edge

        Returns:
            Dictionary with 'nodes' and 'edges' lists for graph visualization
        """
        # Parse time range
        cutoff_date = self._parse_time_range(time_range)

        # Get all entity mentions in time window
        mentions = EntityMention.objects.filter(
            mentioned_at__gte=cutoff_date
        ).select_related('entity').values(
            'entity_id',
            'entity__canonical_name',
            'entity__entity_type',
            'event_id'
        )

        # Build event -> entities mapping
        event_entities = {}
        entity_data = {}

        for mention in mentions:
            event_id = str(mention['event_id'])
            entity_id = str(mention['entity_id'])

            # Track which entities appear in which events
            if event_id not in event_entities:
                event_entities[event_id] = []
            if entity_id not in event_entities[event_id]:
                event_entities[event_id].append(entity_id)

            # Store entity metadata (deduplicate by entity_id)
            if entity_id not in entity_data:
                entity_data[entity_id] = {
                    'name': mention['entity__canonical_name'],
                    'type': mention['entity__entity_type'],
                    'event_ids': set(),
                    'mention_count': 0
                }

            entity_data[entity_id]['event_ids'].add(event_id)
            entity_data[entity_id]['mention_count'] += 1

        # Build co-occurrence relationships
        cooccurrences = {}

        for event_id, entity_ids in event_entities.items():
            # For each pair of entities in the same event
            for i, entity_a in enumerate(entity_ids):
                for entity_b in entity_ids[i+1:]:
                    # Create sorted edge key (undirected graph)
                    edge_key = tuple(sorted([entity_a, entity_b]))

                    if edge_key not in cooccurrences:
                        cooccurrences[edge_key] = {
                            'count': 0,
                            'event_ids': set()
                        }

                    cooccurrences[edge_key]['count'] += 1
                    cooccurrences[edge_key]['event_ids'].add(event_id)

        # Filter by minimum co-occurrence threshold
        significant_cooccurrences = {
            k: v for k, v in cooccurrences.items()
            if v['count'] >= min_cooccurrence
        }

        # Get entities involved in significant relationships
        entities_in_graph = set()
        for (entity_a, entity_b) in significant_cooccurrences.keys():
            entities_in_graph.add(entity_a)
            entities_in_graph.add(entity_b)

        # Fetch additional entity metrics (risk score, sanctions status)
        entities = Entity.objects.filter(
            id__in=entities_in_graph
        ).values(
            'id',
            'canonical_name',
            'entity_type',
            'mention_count',
            'metadata'
        )

        entity_metrics = {}
        for entity in entities:
            entity_id = str(entity['id'])
            metadata = entity.get('metadata') or {}

            entity_metrics[entity_id] = {
                'risk_score': metadata.get('avg_risk_score', 0.0),
                'sanctions_status': metadata.get('is_sanctioned', False)
            }

        # Build nodes list
        nodes = []
        for entity_id in entities_in_graph:
            if entity_id not in entity_data:
                continue

            data = entity_data[entity_id]
            metrics = entity_metrics.get(entity_id, {'risk_score': 0.0, 'sanctions_status': False})

            nodes.append({
                'id': entity_id,
                'label': data['name'],
                'data': {
                    'risk_score': metrics['risk_score'],
                    'sanctions_status': metrics['sanctions_status'],
                    'entity_type': data['type'],
                    'mention_count': data['mention_count']
                }
            })

        # Build edges list
        edges = []
        for (entity_a, entity_b), rel_data in significant_cooccurrences.items():
            edge_id = f"{entity_a}-{entity_b}"

            edges.append({
                'id': edge_id,
                'source': entity_a,
                'target': entity_b,
                'weight': rel_data['count'],
                'data': {
                    'event_ids': list(rel_data['event_ids']),
                    'strength': rel_data['count']
                }
            })

        return {
            'nodes': nodes,
            'edges': edges
        }

    def _parse_time_range(self, time_range: str) -> datetime:
        """
        Parse time range string into cutoff datetime.

        Args:
            time_range: String like "7d", "30d", "90d"

        Returns:
            Datetime representing start of time window
        """
        now = timezone.now()

        if time_range.endswith('d'):
            days = int(time_range[:-1])
            return now - timedelta(days=days)
        elif time_range.endswith('h'):
            hours = int(time_range[:-1])
            return now - timedelta(hours=hours)
        else:
            # Default to 30 days
            return now - timedelta(days=30)
