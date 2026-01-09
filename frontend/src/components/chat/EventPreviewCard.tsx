import { useState } from 'react'
import { makeAssistantToolUI } from '@assistant-ui/react'
import './EventPreviewCard.css'

/**
 * Types matching backend search_events tool
 */
interface SearchEventsArgs {
  date_from?: string
  date_to?: string
  risk_threshold?: number
  source?: string
  limit?: number
}

interface SearchEventsResult {
  events: Array<{
    id: string
    title: string
    date: string
    source: string
    risk_score: number
    severity: string
    summary: string
  }>
  count: number
  date_range?: {
    from: string
    to: string
  }
}

/**
 * Get risk score color class based on value
 */
function getRiskScoreClass(score: number): string {
  if (score >= 70) return 'risk-critical'
  if (score >= 40) return 'risk-high'
  return 'risk-low'
}

/**
 * Get severity display info
 */
function getSeverityInfo(severity: string): { label: string; className: string } {
  const severityMap: Record<string, { label: string; className: string }> = {
    SEV1_CRITICAL: { label: 'SEV1', className: 'severity-critical' },
    SEV2_HIGH: { label: 'SEV2', className: 'severity-high' },
    SEV3_MEDIUM: { label: 'SEV3', className: 'severity-medium' },
    SEV4_LOW: { label: 'SEV4', className: 'severity-low' },
    SEV5_MINIMAL: { label: 'SEV5', className: 'severity-minimal' },
  }
  return severityMap[severity] || { label: severity, className: 'severity-medium' }
}

/**
 * Format date for display
 */
function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

/**
 * Individual event card with expand/collapse
 */
function EventItem({ event }: { event: SearchEventsResult['events'][0] }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const riskClass = getRiskScoreClass(event.risk_score)
  const severityInfo = getSeverityInfo(event.severity)

  return (
    <div className="event-preview-item">
      {/* Compact view - always visible */}
      <div className="event-preview-header">
        <div className="event-preview-title-row">
          <h4 className="event-preview-title">
            {event.title}
          </h4>
        </div>
        <div className="event-preview-meta">
          <span className="event-preview-date">{formatDate(event.date)}</span>
          <span className={`badge badge-source`}>{event.source}</span>
          <span className={`badge badge-risk ${riskClass}`}>
            {Math.round(event.risk_score)}
          </span>
          <span className={`badge badge-severity ${severityInfo.className}`}>
            {severityInfo.label}
          </span>
        </div>
      </div>

      {/* Expanded view - conditional */}
      {isExpanded && (
        <div className="event-preview-details">
          <p className="event-preview-summary">{event.summary}</p>
        </div>
      )}

      {/* Toggle button */}
      <button
        className="event-preview-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? 'Collapse' : 'Show details'}
      </button>
    </div>
  )
}

/**
 * Event preview card for search_events tool results
 * Displays list of events with expand-in-place functionality
 */
const EventPreviewCardContent = ({ result }: { result: SearchEventsResult }) => {
  if (!result.events || result.events.length === 0) {
    return (
      <div className="event-preview-empty">
        No events found for the specified criteria.
      </div>
    )
  }

  return (
    <div className="event-preview-card">
      <div className="event-preview-card-header">
        <h3 className="event-preview-card-title">Found {result.count} Events</h3>
        {result.date_range && (
          <span className="event-preview-date-range">
            {formatDate(result.date_range.from)} - {formatDate(result.date_range.to)}
          </span>
        )}
      </div>
      <div className="event-preview-list">
        {result.events.map((event) => (
          <EventItem key={event.id} event={event} />
        ))}
      </div>
    </div>
  )
}

/**
 * Tool UI component for search_events tool
 */
export const EventPreviewCard = makeAssistantToolUI<SearchEventsArgs, SearchEventsResult>({
  toolName: 'search_events',
  render: ({ result }) => {
    if (!result) return null
    return <EventPreviewCardContent result={result} />
  },
})
