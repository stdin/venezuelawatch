import { useState, useEffect } from 'react'
import { Container, Grid, Stack, Title, SegmentedControl, Modal, useMatches } from '@mantine/core'
import { api } from '../lib/api'
import { EntityLeaderboard } from '../components/EntityLeaderboard'
import { EntityProfile } from '../components/EntityProfile'
import type { Entity, EntityMetric } from '../lib/types'

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
  const [mobileModalOpen, setMobileModalOpen] = useState(false)

  // Detect mobile view (< 48em = 768px)
  const isMobile = useMatches({
    base: true,
    md: false,
  })

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

  // Handle entity selection - on mobile, open modal
  const handleEntitySelect = (id: string) => {
    setSelectedEntityId(id)
    if (isMobile) {
      setMobileModalOpen(true)
    }
  }

  // Close mobile modal
  const handleCloseMobileModal = () => {
    setMobileModalOpen(false)
  }

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
                size="md"
                aria-label="Entity metric filters"
              />
            </Stack>

            {/* Error state */}
            {error && (
              <div className="error-state">
                <h2>Error Loading Entities</h2>
                <p>{error}</p>
              </div>
            )}

            {/* Entity list with loading state */}
            {!error && (
              <EntityLeaderboard
                entities={entities}
                selectedId={selectedEntityId}
                onSelect={handleEntitySelect}
                loading={loading && entities.length === 0}
              />
            )}
          </Stack>
        </Grid.Col>

        {/* Right column: Entity profile - desktop split-view */}
        {!isMobile && (
          <Grid.Col span={{ base: 12, md: 7 }} aria-label="Entity profile">
            {selectedEntityId ? (
              <EntityProfile entityId={selectedEntityId} />
            ) : (
              <div className="entity-detail-placeholder">
                <p>Select an entity to view profile</p>
              </div>
            )}
          </Grid.Col>
        )}
      </Grid>

      {/* Mobile modal for entity profile */}
      <Modal
        opened={isMobile && mobileModalOpen}
        onClose={handleCloseMobileModal}
        title="Entity Profile"
        size="lg"
        fullScreen
      >
        {selectedEntityId && <EntityProfile entityId={selectedEntityId} />}
      </Modal>
    </Container>
  )
}
