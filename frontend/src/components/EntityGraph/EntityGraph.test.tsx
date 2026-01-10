import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { forwardRef } from 'react'
import { EntityGraph } from './EntityGraph'
import type { GraphCanvasRef } from 'reagraph'

// Mock the useGraphData hook
vi.mock('./useGraphData', () => ({
  useGraphData: vi.fn()
}))

// Create mock centerGraph function that we can spy on
const mockCenterGraph = vi.fn()

// Mock Reagraph's GraphCanvas
vi.mock('reagraph', () => ({
  GraphCanvas: forwardRef<GraphCanvasRef, any>((props, ref) => {
    // Expose ref methods for testing
    if (ref && typeof ref === 'object' && 'current' in ref) {
      ref.current = {
        centerGraph: mockCenterGraph,
      } as any
    }
    return <div data-testid="graph-canvas" />
  })
}))

describe('EntityGraph - Camera Auto-Focus', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should auto-focus camera on high-risk cluster after graph renders', async () => {
    // Import after mocking
    const { useGraphData } = await import('./useGraphData')
    const { GraphCanvas } = await import('reagraph')

    // Mock graph data with high-risk cluster
    const mockNodes = [
      {
        id: '1',
        label: 'Entity 1',
        data: {
          risk_score: 80,
          sanctions_status: false,
          entity_type: 'PERSON',
          mention_count: 10,
          community: 0  // High-risk cluster
        }
      },
      {
        id: '2',
        label: 'Entity 2',
        data: {
          risk_score: 75,
          sanctions_status: false,
          entity_type: 'PERSON',
          mention_count: 8,
          community: 0  // High-risk cluster
        }
      },
      {
        id: '3',
        label: 'Entity 3',
        data: {
          risk_score: 30,
          sanctions_status: false,
          entity_type: 'ORG',
          mention_count: 5,
          community: 1  // Different cluster
        }
      }
    ]

    const mockEdges = [
      { id: 'e1', source: '1', target: '2', weight: 5 }
    ]

    vi.mocked(useGraphData).mockReturnValue({
      nodes: mockNodes,
      edges: mockEdges,
      highRiskCluster: 0,
      communities: {
        '0': { id: 0, avg_risk: 77.5, sanctions_count: 0, node_count: 2 },
        '1': { id: 1, avg_risk: 30, sanctions_count: 0, node_count: 1 }
      },
      loading: false,
      error: null
    })

    // Render component
    render(
      <BrowserRouter>
        <EntityGraph />
      </BrowserRouter>
    )

    // Wait for auto-focus to trigger (500ms delay in implementation)
    await waitFor(() => {
      expect(mockCenterGraph).toHaveBeenCalled()
    }, { timeout: 1000 })
  })
})
