"""
Graph API endpoint for entity relationship visualization.

Provides entity co-occurrence graph data with community detection.
"""
from typing import Optional, List, Dict, Any
from ninja import Router, Schema
from django.shortcuts import get_object_or_404

from data_pipeline.services.graph_builder import GraphBuilder
from data_pipeline.services.narrative_generator import NarrativeGenerator
from core.models import Entity


# Schemas
class NodeData(Schema):
    """Node data for entity in graph."""
    risk_score: float
    sanctions_status: bool
    entity_type: str
    mention_count: int
    community: Optional[str] = None


class Node(Schema):
    """Graph node representing an entity."""
    id: str
    label: str
    data: NodeData


class EdgeData(Schema):
    """Edge data for relationship."""
    event_ids: List[str]
    strength: int


class Edge(Schema):
    """Graph edge representing entity relationship."""
    id: str
    source: str
    target: str
    weight: int
    data: EdgeData


class ClusterStat(Schema):
    """Statistics for a community cluster."""
    node_count: int
    avg_risk: float
    sanctioned_count: int
    entity_types: Dict[str, int]


class GraphResponse(Schema):
    """Complete graph response with nodes, edges, and community data."""
    nodes: List[Node]
    edges: List[Edge]
    high_risk_cluster: Optional[str] = None
    cluster_stats: Optional[Dict[str, ClusterStat]] = None


# Narrative endpoint schemas
class EventSummary(Schema):
    """Summary of an event connecting two entities."""
    id: str
    title: str
    published_at: Optional[str]
    risk_score: float
    severity: str


class EntityInfo(Schema):
    """Basic entity information."""
    id: str
    name: str
    entity_type: str


class NarrativeResponse(Schema):
    """Response containing relationship narrative and supporting events."""
    narrative: str
    events: List[EventSummary]
    entity_a: EntityInfo
    entity_b: EntityInfo


# Router
graph_router = Router()


@graph_router.get("/entities", response=GraphResponse, tags=["Graph"])
def get_entity_graph(
    request,
    time_range: str = "30d",
    min_cooccurrence: int = 3
):
    """
    Get entity relationship graph with community detection.

    Args:
        time_range: Time window ("7d", "30d", "90d")
        min_cooccurrence: Minimum co-occurrence count to include edge

    Returns:
        Graph with nodes, edges, community assignments, and high-risk cluster
    """
    builder = GraphBuilder()

    # Build base graph from entity co-occurrences
    graph_data = builder.build_entity_graph(
        time_range=time_range,
        min_cooccurrence=min_cooccurrence
    )

    # Run community detection
    result = builder.detect_communities(
        nodes=graph_data['nodes'],
        edges=graph_data['edges']
    )

    return result


@graph_router.get("/narrative/{entity_a_id}/{entity_b_id}", response=NarrativeResponse, tags=["Graph"])
def get_relationship_narrative(
    request,
    entity_a_id: str,
    entity_b_id: str
):
    """
    Generate narrative explaining relationship between two entities.

    Uses Claude API to create causal explanation based on connecting events.

    Args:
        entity_a_id: UUID of first entity
        entity_b_id: UUID of second entity

    Returns:
        Narrative with supporting events and entity information

    Raises:
        404: If either entity not found
        500: If narrative generation fails
    """
    # Fetch entities from PostgreSQL
    entity_a = get_object_or_404(Entity, id=entity_a_id)
    entity_b = get_object_or_404(Entity, id=entity_b_id)

    # Initialize narrative generator
    generator = NarrativeGenerator()

    # Get connecting events from BigQuery
    connecting_events = generator.get_connecting_events(
        entity_a_id=str(entity_a.id),
        entity_b_id=str(entity_b.id),
        limit=10
    )

    # Generate narrative
    if not connecting_events:
        narrative = f"No direct connection found between {entity_a.canonical_name} and {entity_b.canonical_name} in recent events."
        events = []
    else:
        try:
            narrative = generator.generate_relationship_narrative(
                entity_a=entity_a,
                entity_b=entity_b,
                connecting_events=connecting_events
            )
            events = [
                EventSummary(
                    id=evt['id'],
                    title=evt['title'],
                    published_at=evt.get('published_at'),
                    risk_score=evt.get('risk_score', 0.0),
                    severity=evt.get('severity', 'UNKNOWN')
                )
                for evt in connecting_events
            ]
        except Exception as e:
            # Log error but return generic message
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Narrative generation failed: {e}", exc_info=True)
            
            narrative = "Unable to generate narrative at this time. Please try again later."
            events = []

    return NarrativeResponse(
        narrative=narrative,
        events=events,
        entity_a=EntityInfo(
            id=str(entity_a.id),
            name=entity_a.canonical_name,
            entity_type=entity_a.entity_type
        ),
        entity_b=EntityInfo(
            id=str(entity_b.id),
            name=entity_b.canonical_name,
            entity_type=entity_b.entity_type
        )
    )
