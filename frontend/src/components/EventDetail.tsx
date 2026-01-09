import type { RiskEvent } from '../lib/types'
import './EventDetail.css'

interface EventDetailProps {
  event: RiskEvent | null
  allEvents: RiskEvent[]
  onSelectEvent: (eventId: string) => void
}

/**
 * Format timestamp to readable date/time
 */
function formatDateTime(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * Get sentiment label and class
 */
function getSentimentInfo(sentiment: number | null): { label: string; className: string } {
  if (sentiment === null) return { label: 'Unknown', className: 'sentiment-unknown' }
  if (sentiment > 0.3) return { label: 'Positive', className: 'sentiment-positive' }
  if (sentiment < -0.3) return { label: 'Negative', className: 'sentiment-negative' }
  return { label: 'Neutral', className: 'sentiment-neutral' }
}

/**
 * Get risk score color class
 */
function getRiskScoreClass(score: number | null): string {
  if (score === null) return 'risk-unknown'
  if (score >= 75) return 'risk-critical'
  if (score >= 50) return 'risk-high'
  if (score >= 25) return 'risk-medium'
  return 'risk-low'
}

/**
 * Comprehensive event detail component
 */
export function EventDetail({ event, allEvents, onSelectEvent }: EventDetailProps) {
  if (!event) {
    return (
      <div className="event-detail-empty">
        <p>Select an event to view details</p>
      </div>
    )
  }

  const sentimentInfo = getSentimentInfo(event.sentiment)
  const riskClass = getRiskScoreClass(event.risk_score)

  // Find related events (same source OR overlapping themes)
  const relatedEvents = allEvents
    .filter(e => {
      if (e.id === event.id) return false
      // Same source
      if (e.source === event.source) return true
      // Overlapping themes
      const overlap = e.themes.some(theme => event.themes.includes(theme))
      return overlap
    })
    .slice(0, 5)

  return (
    <div className="event-detail">
      {/* Header */}
      <div className="event-detail-header">
        <h2 className="event-detail-title">{event.title}</h2>
        <div className="event-detail-meta">
          <span className="badge badge-source">{event.source}</span>
          <span className="event-detail-timestamp">{formatDateTime(event.timestamp)}</span>
        </div>
        <div className="event-detail-scores">
          {event.risk_score !== null && (
            <div className={`risk-score-large ${riskClass}`}>
              <span className="risk-score-value">{Math.round(event.risk_score)}</span>
              <span className="risk-score-label">Risk Score</span>
            </div>
          )}
          <span className={`badge badge-severity severity-${event.severity.toLowerCase()}`}>
            {event.severity.replace('_', ' ')}
          </span>
        </div>
      </div>

      {/* Full Description */}
      {event.summary && (
        <div className="event-detail-section">
          <h3>Summary</h3>
          <p className="event-detail-summary">{event.summary}</p>
        </div>
      )}

      {/* Risk Breakdown */}
      {event.risk_score !== null && (
        <div className="event-detail-section">
          <h3>Risk Breakdown</h3>
          <p className="risk-breakdown-subtitle">How this risk score was calculated:</p>
          <div className="risk-dimensions">
            <div className="risk-dimension">
              <span className="dimension-label">LLM Base Risk</span>
              <span className="dimension-weight">25% weight</span>
            </div>
            <div className="risk-dimension">
              <span className="dimension-label">
                Sanctions {event.sanctions_matches.length > 0 && <strong>(Detected!)</strong>}
              </span>
              <span className="dimension-weight">30% weight</span>
            </div>
            <div className="risk-dimension">
              <span className="dimension-label">
                Sentiment: {event.sentiment !== null ? event.sentiment.toFixed(2) : 'N/A'}
              </span>
              <span className="dimension-weight">20% weight</span>
            </div>
            <div className="risk-dimension">
              <span className="dimension-label">Urgency: {event.urgency || 'N/A'}</span>
              <span className="dimension-weight">15% weight</span>
            </div>
            <div className="risk-dimension">
              <span className="dimension-label">Supply Chain</span>
              <span className="dimension-weight">10% weight</span>
            </div>
          </div>
          <p className="risk-breakdown-note">* Weights vary by event type</p>
        </div>
      )}

      {/* Sanctions Matches */}
      {event.sanctions_matches.length > 0 && (
        <div className="event-detail-section sanctions-section">
          <h3>Sanctions Matches</h3>
          {event.sanctions_matches.map((match, idx) => (
            <div key={idx} className={`sanctions-match ${match.match_score > 0.8 ? 'high-confidence' : ''}`}>
              <div className="sanctions-match-header">
                <strong>{match.entity_name}</strong>
                <span className="badge badge-sm">{match.entity_type}</span>
              </div>
              <div className="sanctions-match-details">
                <span>List: {match.sanctions_list}</span>
                <span>Confidence: {(match.match_score * 100).toFixed(0)}%</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Metadata */}
      <div className="event-detail-section">
        <h3>Metadata</h3>

        {event.themes.length > 0 && (
          <div className="metadata-row">
            <span className="metadata-label">Themes:</span>
            <div className="metadata-tags">
              {event.themes.map((theme, idx) => (
                <span key={idx} className="tag">{theme}</span>
              ))}
            </div>
          </div>
        )}

        {event.entities && (
          <>
            {event.entities.organizations?.length > 0 && (
              <div className="metadata-row">
                <span className="metadata-label">Organizations:</span>
                <div className="metadata-tags">
                  {event.entities.organizations.map((org: any, idx: number) => (
                    <span key={idx} className="tag">{org.name || org}</span>
                  ))}
                </div>
              </div>
            )}
            {event.entities.locations?.length > 0 && (
              <div className="metadata-row">
                <span className="metadata-label">Locations:</span>
                <div className="metadata-tags">
                  {event.entities.locations.map((loc: any, idx: number) => (
                    <span key={idx} className="tag">{loc.name || loc}</span>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        <div className="metadata-row">
          <span className="metadata-label">Event Type:</span>
          <span className="badge">{event.event_type}</span>
        </div>

        <div className="metadata-row">
          <span className="metadata-label">Sentiment:</span>
          <span className={`sentiment-badge ${sentimentInfo.className}`}>
            {sentimentInfo.label}
          </span>
        </div>
      </div>

      {/* Related Events */}
      {relatedEvents.length > 0 && (
        <div className="event-detail-section">
          <h3>Related Events</h3>
          <div className="related-events">
            {relatedEvents.map(relatedEvent => (
              <div
                key={relatedEvent.id}
                className="related-event-card"
                onClick={() => onSelectEvent(relatedEvent.id)}
              >
                <div className="related-event-header">
                  <span className="related-event-title">{relatedEvent.title}</span>
                  {relatedEvent.risk_score !== null && (
                    <span className={`badge badge-risk ${getRiskScoreClass(relatedEvent.risk_score)}`}>
                      {Math.round(relatedEvent.risk_score)}
                    </span>
                  )}
                </div>
                <span className="related-event-timestamp">
                  {formatDateTime(relatedEvent.timestamp)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
