import { useRef, useMemo } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import type { RiskEvent } from '../lib/types'
import { EventCard } from './EventCard'
import './EventList.css'

interface EventListProps {
  events: RiskEvent[]
  selectedEventId: string | null
  onSelectEvent: (eventId: string) => void
}

/**
 * Virtualized event list component using TanStack Virtual
 * Renders only visible items for performance with large datasets
 */
export function EventList({ events, selectedEventId, onSelectEvent }: EventListProps) {
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

  return (
    <div ref={parentRef} className="event-list-container">
      <div
        className="event-list-inner"
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
              className="virtual-item"
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualItem.start}px)`,
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
