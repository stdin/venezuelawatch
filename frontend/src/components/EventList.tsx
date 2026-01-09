import { useRef, useMemo } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { Stack, Skeleton, Card } from '@mantine/core'
import type { RiskEvent } from '../lib/types'
import { EventCard } from './EventCard'

interface EventListProps {
  events: RiskEvent[]
  selectedEventId: string | null
  onSelectEvent: (eventId: string) => void
  loading?: boolean
}

/**
 * Virtualized event list component using TanStack Virtual
 * Renders only visible items for performance with large datasets
 * Shows skeleton loading states during data fetch
 */
export function EventList({ events, selectedEventId, onSelectEvent, loading = false }: EventListProps) {
  const parentRef = useRef<HTMLDivElement>(null)

  // Sort events by risk_score descending (highest risk at top)
  const sortedEvents = useMemo(() => {
    return [...events].sort((a, b) => b.risk_score - a.risk_score)
  }, [events])

  // Set up virtualizer
  const virtualizer = useVirtualizer({
    count: sortedEvents.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 120, // Estimated card height in pixels
    overscan: 5, // Render 5 extra items above/below viewport for smooth scrolling
  })

  const virtualItems = virtualizer.getVirtualItems()

  // Show skeleton loading placeholders
  if (loading) {
    return (
      <div role="status" aria-live="polite" aria-label="Loading events">
        <Stack gap="sm" p="md">
          {[...Array(5)].map((_, i) => (
            <Card key={i} padding="md" withBorder>
              <Stack gap="xs">
                <Skeleton height={20} width="80%" />
                <Skeleton height={14} width="60%" />
                <Skeleton height={14} width="40%" />
              </Stack>
            </Card>
          ))}
        </Stack>
      </div>
    )
  }

  return (
    <div
      ref={parentRef}
      role="feed"
      aria-label="Event feed"
      style={{
        height: '100%',
        overflow: 'auto',
      }}
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          position: 'relative',
        }}
      >
        {virtualItems.map((virtualItem) => {
          const event = sortedEvents[virtualItem.index]
          return (
            <div
              key={event.id}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualItem.start}px)`,
                padding: '0.5rem',
              }}
            >
              <EventCard
                event={event}
                isSelected={event.id === selectedEventId}
                onSelect={() => onSelectEvent(event.id)}
              />
            </div>
          )
        })}
      </div>
    </div>
  )
}
