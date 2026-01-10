"""
Graph builder service for entity relationship visualization.

Builds entity co-occurrence graphs from PostgreSQL EntityMention data,
calculates relationship weights, and prepares data for frontend visualization.
"""
import json
import subprocess
import tempfile
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Union, Optional
from pathlib import Path
from django.db.models import Count, Q
from django.utils import timezone

from core.models import Entity, EntityMention
from data_pipeline.services.theme_enricher import ThemeEnricher


class GraphBuilder:
    """Builds entity relationship graphs from co-occurrence patterns."""

    def build_entity_graph(
        self,
        time_range: str = "30d",
        min_cooccurrence: int = 3,
        theme_filter: Optional[Union[str, List[str]]] = None
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

        # Apply theme filtering if requested
        if theme_filter:
            # Normalize theme_filter to list
            if isinstance(theme_filter, str):
                filter_categories = [theme_filter]
            else:
                filter_categories = theme_filter

            # Enrich edges with themes
            enricher = ThemeEnricher()
            filtered_edges = []

            for edge in edges:
                # Enrich edge with themes from events
                enriched_edge = enricher.enrich_edge_with_themes(
                    edge=edge,
                    event_ids=edge['data']['event_ids']
                )

                # Filter by category
                edge_category = enriched_edge['data'].get('category', 'other')
                if edge_category in filter_categories:
                    filtered_edges.append(enriched_edge)

            edges = filtered_edges

            # Remove nodes that have no remaining edges (isolated nodes)
            entities_in_filtered_graph = set()
            for edge in edges:
                entities_in_filtered_graph.add(edge['source'])
                entities_in_filtered_graph.add(edge['target'])

            nodes = [node for node in nodes if node['id'] in entities_in_filtered_graph]

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

    def detect_communities(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
        """
        Detect communities in graph using Graphology Louvain algorithm.

        Runs Node.js subprocess with Graphology library to perform community detection.
        Returns nodes with community assignments and identifies high-risk cluster.

        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries

        Returns:
            Dictionary with nodes (including community field) and high_risk_cluster ID
        """
        # Create temporary JSON file with graph data
        graph_data = {
            'nodes': nodes,
            'edges': edges
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(graph_data, tmp_file)
            tmp_path = tmp_file.name

        try:
            # Get path to Node.js community detection script
            script_dir = Path(__file__).parent.parent / 'scripts'
            script_path = script_dir / 'community_detection.js'

            # Execute Node.js script
            result = subprocess.run(
                ['node', str(script_path), tmp_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"Community detection failed: {result.stderr}")

            # Parse JSON response
            detection_result = json.loads(result.stdout)

            # Assign community field to nodes
            community_map = detection_result['communities']
            for node in nodes:
                node_id = node['id']
                if node_id in community_map:
                    if 'data' not in node:
                        node['data'] = {}
                    node['data']['community'] = str(community_map[node_id])

            return {
                'nodes': nodes,
                'edges': edges,
                'high_risk_cluster': str(detection_result.get('high_risk_cluster')),
                'cluster_stats': detection_result.get('cluster_stats', {})
            }

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
