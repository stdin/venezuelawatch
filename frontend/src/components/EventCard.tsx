import type { RiskEvent } from '../lib/types'
import './EventCard.css'

interface EventCardProps {
  event: RiskEvent
  isSelected: boolean
  onSelect: () => void
}

/**
 * Format timestamp as relative time (e.g., "2 hours ago")
 */
function formatRelativeTime(timestamp: string): string {
  const now = new Date()
  const eventTime = new Date(timestamp)
  const diffMs = now.getTime() - eventTime.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return eventTime.toLocaleDateString()
}

/**
 * Get risk score color class based on value
 */
function getRiskScoreClass(score: number): string {
  if (score >= 75) return 'risk-critical'
  if (score >= 50) return 'risk-high'
  if (score >= 25) return 'risk-medium'
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
 * Get sentiment indicator
 */
function getSentimentInfo(sentiment: number): { icon: string; className: string; label: string } {
  if (sentiment > 0.3) return { icon: '↑', className: 'sentiment-positive', label: 'Positive' }
  if (sentiment < -0.3) return { icon: '↓', className: 'sentiment-negative', label: 'Negative' }
  return { icon: '→', className: 'sentiment-neutral', label: 'Neutral' }
}

/**
 * Event card component displaying moderate information density
 */
export function EventCard({ event, isSelected, onSelect }: EventCardProps) {
  const riskClass = getRiskScoreClass(event.risk_score)
  const severityInfo = getSeverityInfo(event.severity)
  const sentimentInfo = getSentimentInfo(event.sentiment)
  const relativeTime = formatRelativeTime(event.timestamp)

  return (
    <div
      className={`event-card ${isSelected ? 'event-card-selected' : ''}`}
      onClick={onSelect}
    >
      {/* Header: Title and badges */}
      <div className="event-card-header">
        <h3 className="event-card-title">{event.title}</h3>
        <div className="event-card-badges">
          <span className={`badge badge-risk ${riskClass}`}>
            {Math.round(event.risk_score)}
          </span>
          <span className={`badge badge-severity ${severityInfo.className}`}>
            {severityInfo.label}
          </span>
        </div>
      </div>

      {/* Timestamp */}
      <div className="event-card-timestamp">{relativeTime}</div>

      {/* Summary */}
      <p className="event-card-summary">{event.summary}</p>

      {/* Footer: Source and sentiment */}
      <div className="event-card-footer">
        <span className="badge badge-source">{event.source}</span>
        <span className={`sentiment-indicator ${sentimentInfo.className}`} title={sentimentInfo.label}>
          {sentimentInfo.icon}
        </span>
      </div>
    </div>
  )
}
