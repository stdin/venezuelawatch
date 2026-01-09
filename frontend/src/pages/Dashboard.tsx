import { useState, useEffect } from 'react'
import { useRiskEvents } from '../hooks/useRiskEvents'
import { EventList } from '../components/EventList'
import { FilterBar } from '../components/FilterBar'
import { EventDetail } from '../components/EventDetail'
import { TrendsPanel } from '../components/TrendsPanel'
import { loadFiltersFromStorage, saveFiltersToStorage } from '../lib/filterStorage'
import type { EventFilterParams } from '../lib/types'
import './Dashboard.css'

/**
 * Dashboard page with split-view layout
 * Left panel: Risk-prioritized event list with filters
 * Right panel: Event detail panel
 */
export function Dashboard() {
  const [filters, setFilters] = useState<EventFilterParams>(() => loadFiltersFromStorage())
  const { events, loading, error } = useRiskEvents(filters, { pollInterval: 60000 })
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null)

  // Save filters to storage whenever they change
  useEffect(() => {
    saveFiltersToStorage(filters)
  }, [filters])

  const handleFiltersChange = (newFilters: EventFilterParams) => {
    setFilters(newFilters)
  }

  return (
    <div className="dashboard-container">
      {/* Left panel: Event list */}
      <div className="events-panel">
        <FilterBar filters={filters} onFiltersChange={handleFiltersChange} />

        {loading && !events && (
          <div className="loading-state">Loading events...</div>
        )}

        {error && (
          <div className="error-state">
            <h2>Error Loading Events</h2>
            <p>{error.message}</p>
          </div>
        )}

        {!loading && !error && (!events || events.length === 0) && (
          <div className="empty-state">No events found with current filters</div>
        )}

        {events && events.length > 0 && (
          <EventList
            events={events}
            selectedEventId={selectedEventId}
            onSelectEvent={setSelectedEventId}
          />
        )}

        {loading && events && (
          <div className="loading-overlay">Updating...</div>
        )}
      </div>

      {/* Right panel: Trends and Event details */}
      <div className="detail-panel">
        {events && events.length > 0 && <TrendsPanel events={events} />}
        <EventDetail
          event={events?.find(e => e.id === selectedEventId) || null}
          allEvents={events || []}
          onSelectEvent={setSelectedEventId}
        />
      </div>
    </div>
  )
}
