import { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { EntityLeaderboard } from '../components/EntityLeaderboard'
import { EntityProfile } from '../components/EntityProfile'
import type { Entity, EntityMetric } from '../lib/types'
import './Entities.css'

/**
 * Entities page with split-view layout
 * Left panel: Entity leaderboard with metric toggles
 * Right panel: Entity profile detail
 */
export function Entities() {
  const [selectedMetric, setSelectedMetric] = useState<EntityMetric>('mentions')
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null)
  const [entities, setEntities] = useState<Entity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch trending entities when metric changes
  useEffect(() => {
    let mounted = true

    async function fetchEntities() {
      try {
        setLoading(true)
        setError(null)
        const data = await api.getTrendingEntities(selectedMetric, 50)
        if (mounted) {
          setEntities(data)
          // Clear selected entity when switching metrics if it's not in new list
          if (selectedEntityId && !data.find(e => e.id === selectedEntityId)) {
            setSelectedEntityId(null)
          }
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to load trending entities')
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    fetchEntities()

    return () => {
      mounted = false
    }
  }, [selectedMetric, selectedEntityId])

  return (
    <div className="entities-container">
      {/* Left panel: Leaderboard */}
      <div className="entities-panel">
        {/* Top bar with title and metric toggles */}
        <div className="entities-header">
          <h1 className="entities-title">Entity Watch</h1>
          <div className="metric-toggles">
            <button
              className={`metric-toggle ${selectedMetric === 'mentions' ? 'metric-toggle-active' : ''}`}
              onClick={() => setSelectedMetric('mentions')}
            >
              Most Mentioned
            </button>
            <button
              className={`metric-toggle ${selectedMetric === 'risk' ? 'metric-toggle-active' : ''}`}
              onClick={() => setSelectedMetric('risk')}
            >
              Highest Risk
            </button>
            <button
              className={`metric-toggle ${selectedMetric === 'sanctions' ? 'metric-toggle-active' : ''}`}
              onClick={() => setSelectedMetric('sanctions')}
            >
              Recently Sanctioned
            </button>
          </div>
        </div>

        {/* Loading state */}
        {loading && !entities.length && (
          <div className="loading-state">Loading entities...</div>
        )}

        {/* Error state */}
        {error && (
          <div className="error-state">
            <h2>Error Loading Entities</h2>
            <p>{error}</p>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && entities.length === 0 && (
          <div className="empty-state">No entities found for this metric</div>
        )}

        {/* Entity list */}
        {entities.length > 0 && (
          <EntityLeaderboard
            entities={entities}
            selectedId={selectedEntityId}
            onSelect={setSelectedEntityId}
          />
        )}

        {/* Loading overlay for updates */}
        {loading && entities.length > 0 && (
          <div className="loading-overlay">Updating...</div>
        )}
      </div>

      {/* Right panel: Entity profile */}
      <div className="entity-detail-panel">
        {selectedEntityId ? (
          <EntityProfile entityId={selectedEntityId} />
        ) : (
          <div className="entity-detail-placeholder">
            <p>Select an entity to view profile</p>
          </div>
        )}
      </div>
    </div>
  )
}
