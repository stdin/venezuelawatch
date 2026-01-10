import { useState, useEffect } from 'react'

export interface GraphNode {
  id: string
  label: string
  data: {
    risk_score: number
    sanctions_status: boolean
    entity_type: string
    mention_count: number
    community?: number
  }
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  weight: number
}

export interface CommunityInfo {
  id: number
  avg_risk: number
  sanctions_count: number
  node_count: number
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  communities: Record<string, CommunityInfo>
  high_risk_cluster: number | null
}

export interface ClusterCentroid {
  x: number
  y: number
  z: number
}

interface UseGraphDataReturn {
  nodes: GraphNode[]
  edges: GraphEdge[]
  highRiskCluster: number | null
  communities: Record<string, CommunityInfo>
  clusterCentroid: ClusterCentroid | null
  highRiskClusterNodeIds: string[]
  loading: boolean
  error: string | null
}

/**
 * Calculate the IDs of nodes in the high-risk cluster.
 * Used for camera auto-focus on critical intelligence.
 */
function getHighRiskClusterNodeIds(
  nodes: GraphNode[],
  highRiskCluster: number | null
): string[] {
  if (highRiskCluster === null) return []

  return nodes
    .filter(node => node.data.community === highRiskCluster)
    .map(node => node.id)
}

/**
 * Hook to fetch and transform graph data from backend
 * Uses backend /api/graph/entities endpoint
 */
export function useGraphData(
  minCooccurrence: number = 3,
  timeRange: string = '30d',
  selectedThemes: string[] = []
): UseGraphDataReturn {
  const [data, setData] = useState<GraphData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    async function fetchGraphData() {
      try {
        setLoading(true)
        setError(null)

        const params = new URLSearchParams({
          min_cooccurrence: minCooccurrence.toString(),
          time_range: timeRange,
        })

        // Add theme filter if selected
        if (selectedThemes.length > 0) {
          params.set('theme_categories', selectedThemes.join(','))
        }

        const response = await fetch(`/api/graph/entities?${params}`, {
          credentials: 'include',
        })

        if (!response.ok) {
          throw new Error(`Graph API error: ${response.status}`)
        }

        const graphData: GraphData = await response.json()

        if (mounted) {
          setData(graphData)
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to load graph data')
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    fetchGraphData()

    return () => {
      mounted = false
    }
  }, [minCooccurrence, timeRange, selectedThemes])

  const nodes = data?.nodes || []
  const highRiskCluster = data?.high_risk_cluster ?? null

  // Calculate high-risk cluster node IDs for camera focus
  const highRiskClusterNodeIds = getHighRiskClusterNodeIds(nodes, highRiskCluster)

  // Placeholder centroid - actual focusing uses node selection in Reagraph
  const clusterCentroid: ClusterCentroid | null =
    highRiskCluster !== null ? { x: 0, y: 0, z: 0 } : null

  return {
    nodes,
    edges: data?.edges || [],
    highRiskCluster,
    communities: data?.communities || {},
    clusterCentroid,
    highRiskClusterNodeIds,
    loading,
    error,
  }
}
