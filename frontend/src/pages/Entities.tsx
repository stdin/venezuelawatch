import { useState, useEffect } from 'react'
import { Container, Grid, Stack, Title, SegmentedControl } from '@mantine/core'
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
    <Container fluid>
      <Grid>
        {/* Left column: Leaderboard */}
        <Grid.Col span={{ base: 12, md: 5 }}>
          <Stack gap="md">
            {/* Header with title and metric toggles */}
            <Stack gap="sm">
              <Title order={2}>Entity Watch</Title>
              <SegmentedControl
                value={selectedMetric}
                onChange={(value) => setSelectedMetric(value as EntityMetric)}
                data={[
                  { value: 'mentions', label: 'Most Mentioned' },
                  { value: 'risk', label: 'Highest Risk' },
                  { value: 'sanctions', label: 'Recently Sanctioned' },
                ]}
                fullWidth
              />
            </Stack>

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
          </Stack>
        </Grid.Col>

        {/* Right column: Entity profile */}
        <Grid.Col span={{ base: 12, md: 7 }}>
          {selectedEntityId ? (
            <EntityProfile entityId={selectedEntityId} />
          ) : (
            <div className="entity-detail-placeholder">
              <p>Select an entity to view profile</p>
            </div>
          )}
        </Grid.Col>
      </Grid>
    </Container>
  )
}
