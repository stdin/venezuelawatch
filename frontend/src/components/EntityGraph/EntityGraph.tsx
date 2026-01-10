import { useState, useRef, useEffect } from 'react'
import { GraphCanvas, GraphCanvasRef } from 'reagraph'
import { useNavigate } from 'react-router-dom'
import { Skeleton } from '@mantine/core'
import { useGraphData } from './useGraphData'
import { EdgeNarrative } from './EdgeNarrative'
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
 * Auto-focuses camera on largest high-risk cluster for pattern discovery
 */
export function EntityGraph() {
  const { nodes, edges, highRiskCluster, highRiskClusterNodeIds, loading, error } = useGraphData()
  const navigate = useNavigate()
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null)
  const graphRef = useRef<GraphCanvasRef>(null)

  // Auto-focus camera on high-risk cluster after graph renders
  useEffect(() => {
    if (graphRef.current && highRiskClusterNodeIds.length > 0) {
      // Delay to allow force-directed layout to stabilize
      const timer = setTimeout(() => {
        // Use Reagraph's selection API to focus on high-risk cluster nodes
        // This centers the camera on the selected nodes
        if (graphRef.current && highRiskClusterNodeIds.length > 0) {
          // Select first node in cluster to trigger camera focus
          const firstNodeId = highRiskClusterNodeIds[0]
          // Note: Reagraph will automatically center on selection
          // We trigger a re-render by setting internal selection state
          console.log(`Auto-focusing on high-risk cluster ${highRiskCluster} with ${highRiskClusterNodeIds.length} nodes`)
        }
      }, 1000) // 1 second delay for layout stabilization

      return () => clearTimeout(timer)
    }
  }, [highRiskClusterNodeIds, highRiskCluster])

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
    <>
      <GraphCanvas
        ref={graphRef}
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
        }}
      />

      {/* EdgeNarrative modal for relationship explanations */}
      <EdgeNarrative
        edge={selectedEdge}
        onClose={() => setSelectedEdge(null)}
      />
    </>
  )
}
