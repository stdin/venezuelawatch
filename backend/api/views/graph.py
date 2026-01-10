"""
Graph API endpoint for entity relationship visualization.

Provides entity co-occurrence graph data with community detection.
"""
from typing import Optional, List, Dict, Any
from ninja import Router, Schema

from data_pipeline.services.graph_builder import GraphBuilder


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
