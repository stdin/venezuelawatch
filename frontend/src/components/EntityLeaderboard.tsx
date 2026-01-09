import { useRef } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { Card, Badge, Text, Group, Stack, Skeleton } from '@mantine/core'
import type { Entity } from '../lib/types'

interface EntityLeaderboardProps {
  entities: Entity[]
  selectedId: string | null
  onSelect: (id: string) => void
  loading?: boolean
}

/**
 * Get entity type badge color for Mantine Badge
 */
function getEntityTypeBadgeColor(type: string): string {
  const colorMap: Record<string, string> = {
    PERSON: 'blue',
    ORGANIZATION: 'grape',
    GOVERNMENT: 'red',
    LOCATION: 'green',
  }
  return colorMap[type] || 'gray'
}

/**
 * Get entity type label
 */
function getEntityTypeLabel(type: string): string {
  const labelMap: Record<string, string> = {
    PERSON: 'Person',
    ORGANIZATION: 'Org',
    GOVERNMENT: 'Gov',
    LOCATION: 'Location',
  }
  return labelMap[type] || type
}

/**
 * Format metric value for display
 */
function formatMetricValue(entity: Entity): string {
  // If trending_score exists, show it with rank
  if (entity.trending_score !== undefined && entity.trending_score !== null) {
    return entity.trending_score.toFixed(2)
  }
  // Otherwise show mention count
  return entity.mention_count.toString()
}

/**
 * Virtualized entity leaderboard component
 * Displays entities with rank, name, type badge, and metric value
 */
export function EntityLeaderboard({ entities, selectedId, onSelect, loading }: EntityLeaderboardProps) {
  const parentRef = useRef<HTMLDivElement>(null)

  // Set up virtualizer for performance with large lists
  const virtualizer = useVirtualizer({
    count: entities.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80, // Estimated row height
    overscan: 5,
  })

  const virtualItems = virtualizer.getVirtualItems()

  // Skeleton loading state
  if (loading) {
    return (
      <Stack gap="sm" p="sm">
        {Array.from({ length: 5 }).map((_, index) => (
          <Card key={index} padding="sm" withBorder>
            <Stack gap="xs">
              <Skeleton height={20} width="80%" />
              <Skeleton height={14} width="60%" />
              <Skeleton height={14} width="40%" />
            </Stack>
          </Card>
        ))}
      </Stack>
    )
  }

  if (entities.length === 0) {
    return (
      <Text c="dimmed" ta="center" p="xl" size="sm">
        No entities found
      </Text>
    )
  }

  return (
    <div
      ref={parentRef}
      style={{
        flex: 1,
        width: '100%',
        overflowY: 'auto',
        overflowX: 'hidden',
      }}
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualItems.map((virtualItem) => {
          const entity = entities[virtualItem.index]
          const isSelected = entity.id === selectedId
          const rank = entity.trending_rank || virtualItem.index + 1

          return (
            <div
              key={entity.id}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualItem.start}px)`,
                padding: '0 0.5rem',
              }}
            >
              <Card
                padding="sm"
                withBorder
                onClick={() => onSelect(entity.id)}
                style={{
                  cursor: 'pointer',
                  backgroundColor: isSelected ? 'var(--mantine-color-blue-light)' : undefined,
                  marginBottom: '8px',
                }}
              >
                <Group justify="space-between">
                  {/* Left side: Rank, name, type badge */}
                  <Group gap="xs" style={{ flex: 1, minWidth: 0 }}>
                    {/* Rank badge */}
                    <Badge size="lg" variant="filled" circle color="gray">
                      #{rank}
                    </Badge>

                    {/* Entity info */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <Text size="sm" fw={500} truncate>
                        {entity.canonical_name}
                      </Text>
                      <Group gap="xs" mt={4}>
                        <Badge size="sm" color={getEntityTypeBadgeColor(entity.entity_type)}>
                          {getEntityTypeLabel(entity.entity_type)}
                        </Badge>
                        <Text size="xs" c="dimmed">
                          {entity.mention_count} {entity.mention_count === 1 ? 'mention' : 'mentions'}
                        </Text>
                      </Group>
                    </div>
                  </Group>

                  {/* Right side: Metric value */}
                  <Text size="xs" c="dimmed" style={{ flexShrink: 0, minWidth: '60px', textAlign: 'right' }}>
                    {formatMetricValue(entity)}
                  </Text>
                </Group>
              </Card>
            </div>
          )
        })}
      </div>
    </div>
  )
}
