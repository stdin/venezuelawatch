import { useState } from 'react'
import { GraphCanvas } from 'reagraph'
import { useNavigate } from 'react-router-dom'
import { Skeleton } from '@mantine/core'
import { useGraphData } from './useGraphData'
import type { GraphNode, GraphEdge } from './useGraphData'

/**
 * Get risk-based color for nodes
 * Follows Phase 10 risk score color patterns
 */
function getRiskColor(score: number): string {
  if (score > 70) return '#DC2626' // red
  if (score >= 50) return '#F97316' // orange
  return '#3B82F6' // blue
}

/**
 * EntityGraph component with Reagraph WebGL visualization
 * Shows entity relationship network with community detection and risk-based colors
 */
export function EntityGraph() {
  const { nodes, edges, highRiskCluster, loading, error } = useGraphData()
  const navigate = useNavigate()
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null)

  if (loading) {
    return <Skeleton height={600} />
  }

  if (error) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#DC2626' }}>
        Error loading graph: {error}
      </div>
    )
  }

  if (nodes.length === 0) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#64748B' }}>
        No entity relationships found. Try adjusting filters.
      </div>
    )
  }

  return (
    <GraphCanvas
      nodes={nodes}
      edges={edges}
      layoutType="forceDirected2d"
      sizingType="centrality" // Auto-size nodes by importance
      clusterAttribute="community" // Use community from backend
      draggable={true}
      
      // Directional weighted edges (CONTEXT.md requirement)
      edgeInterpolation="curved"
      edgeArrowPosition="end"
      
      // Visual styling
      theme={{
        canvas: {
          background: '#FFFFFF'
        },
        node: {
          fill: (node: GraphNode) => {
            // Sanctions status takes priority (red)
            if (node.data.sanctions_status) return '#DC2626'
            // Otherwise use risk score
            return getRiskColor(node.data.risk_score)
          },
          activeFill: '#3B82F6',
          opacity: 0.9,
          selectedOpacity: 1.0
        },
        edge: {
          fill: '#94A3B8',
          opacity: 0.6,
          selectedOpacity: 1.0,
          // Log scale for edge thickness based on weight
          width: (edge: GraphEdge) => Math.log(edge.weight + 1) * 2
        },
        cluster: {
          stroke: '#64748B',
          strokeWidth: 2,
          opacity: 0.1
        }
      }}
      
      // Click handlers
      onNodeClick={(node: GraphNode) => {
        navigate(`/entities/${node.id}`)
      }}
      onEdgeClick={(edge: GraphEdge) => {
        setSelectedEdge(edge)
        // TODO: Plan 26-03 will add narrative modal
        console.log('Edge clicked:', edge)
      }}
    />
  )
}
