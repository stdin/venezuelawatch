"""
Graph API endpoint for entity relationship visualization.

Provides entity co-occurrence graph data with community detection.
"""
from typing import Optional, List, Dict, Any
from ninja import Router, Schema
from django.shortcuts import get_object_or_404

from data_pipeline.services.graph_builder import GraphBuilder
from data_pipeline.services.narrative_generator import NarrativeGenerator
from data_pipeline.services.lineage_builder import LineageBuilder
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
    themes: Optional[List[str]] = None
    category: Optional[str] = None


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


class EventNode(Schema):
    """Event node in lineage timeline."""
    id: str
    title: str
    published_at: Optional[str]
    risk_score: float
    severity: str
    themes: List[str]
    days_since_prev: Optional[int] = None


class EventLineage(Schema):
    """Event lineage timeline data."""
    events: List[EventNode]
    timeline_spans_days: int
    escalation_detected: bool
    dominant_themes: List[str]


class NarrativeResponse(Schema):
    """Response containing relationship narrative and supporting events."""
    narrative: str
    events: List[EventSummary]
    entity_a: EntityInfo
    entity_b: EntityInfo
    lineage: Optional[EventLineage] = None


# Router
graph_router = Router()


@graph_router.get("/entities", response=GraphResponse, tags=["Graph"])
def get_entity_graph(
    request,
    time_range: str = "30d",
    min_cooccurrence: int = 3,
    theme_categories: Optional[str] = None
):
    """
    Get entity relationship graph with community detection.

    Args:
        time_range: Time window ("7d", "30d", "90d")
        min_cooccurrence: Minimum co-occurrence count to include edge
        theme_categories: Optional comma-separated theme categories to filter by
                         (e.g., "sanctions,trade,energy")

    Returns:
        Graph with nodes, edges, community assignments, and high-risk cluster
    """
    builder = GraphBuilder()

    # Parse theme filter if provided
    theme_filter = None
    if theme_categories:
        theme_filter = [cat.strip() for cat in theme_categories.split(',') if cat.strip()]

    # Build base graph from entity co-occurrences
    graph_data = builder.build_entity_graph(
        time_range=time_range,
        min_cooccurrence=min_cooccurrence,
        theme_filter=theme_filter
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

    # Build event lineage
    lineage_builder = LineageBuilder()
    lineage_data = lineage_builder.build_event_lineage(
        entity_a_id=str(entity_a.id),
        entity_b_id=str(entity_b.id),
        max_events=20
    )

    # Convert to schema format
    lineage = EventLineage(
        events=[EventNode(**event) for event in lineage_data['events']],
        timeline_spans_days=lineage_data['timeline_spans_days'],
        escalation_detected=lineage_data['escalation_detected'],
        dominant_themes=lineage_data['dominant_themes']
    ) if lineage_data['events'] else None

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
        ),
        lineage=lineage
    )
