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

interface UseGraphDataReturn {
  nodes: GraphNode[]
  edges: GraphEdge[]
  highRiskCluster: number | null
  communities: Record<string, CommunityInfo>
  loading: boolean
  error: string | null
}

/**
 * Hook to fetch and transform graph data from backend
 * Uses backend /api/graph/entities endpoint
 */
export function useGraphData(
  minCooccurrence: number = 3,
  timeRange: string = '30d'
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
  }, [minCooccurrence, timeRange])

  return {
    nodes: data?.nodes || [],
    edges: data?.edges || [],
    highRiskCluster: data?.high_risk_cluster || null,
    communities: data?.communities || {},
    loading,
    error,
  }
}
