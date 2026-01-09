import { useState, useEffect } from 'react'
import { Container, Grid, Button, Collapse } from '@mantine/core'
import { useMediaQuery } from '@mantine/hooks'
import { useRiskEvents } from '../hooks/useRiskEvents'
import { EventList } from '../components/EventList'
import { FilterBar } from '../components/FilterBar'
import { EventDetail } from '../components/EventDetail'
import { TrendsPanel } from '../components/TrendsPanel'
import { loadFiltersFromStorage, saveFiltersToStorage } from '../lib/filterStorage'
import type { EventFilterParams } from '../lib/types'

/**
 * Dashboard page with split-view layout
 * Left panel: Risk-prioritized event list with filters
 * Right panel: Event detail panel
 */
export function Dashboard() {
  const [filters, setFilters] = useState<EventFilterParams>(() => loadFiltersFromStorage())
  const { events, loading, error } = useRiskEvents(filters, { pollInterval: 60000 })
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null)
  const [isTrendsPanelExpanded, setIsTrendsPanelExpanded] = useState(false)

  // Detect mobile viewport (below 768px = 48em)
  const isMobile = useMediaQuery('(max-width: 48em)')

  // Save filters to storage whenever they change
  useEffect(() => {
    saveFiltersToStorage(filters)
  }, [filters])

  const handleFiltersChange = (newFilters: EventFilterParams) => {
    setFilters(newFilters)
  }

  return (
    <Container fluid>
      <Grid>
        {/* Events feed: 6 cols desktop, full width mobile */}
        <Grid.Col span={{ base: 12, md: 6 }}>
          <FilterBar filters={filters} onFiltersChange={handleFiltersChange} />

          {error && (
            <div className="error-state">
              <h2>Error Loading Events</h2>
              <p>{error.message}</p>
            </div>
          )}

          {!loading && !error && (!events || events.length === 0) && (
            <div className="empty-state">No events found with current filters</div>
          )}

          {!error && (
            <EventList
              events={events || []}
              selectedEventId={selectedEventId}
              onSelectEvent={setSelectedEventId}
              loading={loading && !events}
            />
          )}
        </Grid.Col>

        {/* Trends and detail: 6 cols desktop, full width mobile */}
        <Grid.Col span={{ base: 12, md: 6 }}>
          {events && events.length > 0 && (
            <>
              {isMobile && (
                <Button
                  fullWidth
                  variant="light"
                  mb="md"
                  onClick={() => setIsTrendsPanelExpanded(!isTrendsPanelExpanded)}
                  aria-label={isTrendsPanelExpanded ? 'Hide trends panel' : 'Show trends panel'}
                >
                  {isTrendsPanelExpanded ? '▲ Hide Trends' : '▼ Show Trends'}
                </Button>
              )}
              <Collapse in={!isMobile || isTrendsPanelExpanded}>
                <TrendsPanel events={events} />
              </Collapse>
            </>
          )}
          <EventDetail
            event={events?.find(e => e.id === selectedEventId) || null}
            allEvents={events || []}
            onSelectEvent={setSelectedEventId}
          />
        </Grid.Col>
      </Grid>
    </Container>
  )
}
