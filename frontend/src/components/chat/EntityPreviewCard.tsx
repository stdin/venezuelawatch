import { useState } from 'react'
import { makeAssistantToolUI } from '@assistant-ui/react'
import './EntityPreviewCard.css'

/**
 * Types matching backend get_entity_profile tool
 */
interface EntityProfileArgs {
  entity_name: string
}

interface EntityProfileResult {
  id: string
  name: string
  type: string
  mention_count: number
  avg_risk_score: number | null
  is_sanctioned: boolean
  first_seen: string | null
  last_seen: string | null
  recent_mentions: Array<{
    title: string
    date: string
    source: string
    risk_score: number
  }>
}

/**
 * Types matching backend get_trending_entities tool
 */
interface TrendingEntitiesArgs {
  metric?: string
  limit?: number
}

interface TrendingEntitiesResult {
  entities: Array<{
    id: string
    name: string
    type: string
    trend_score: number
    mention_count: number
  }>
  count: number
  metric: string
}

/**
 * Get entity type badge class and label
 */
function getEntityTypeBadge(type: string): { className: string; label: string } {
  const typeMap: Record<string, { className: string; label: string }> = {
    PERSON: { className: 'entity-type-person', label: 'Person' },
    ORGANIZATION: { className: 'entity-type-org', label: 'Org' },
    GOVERNMENT: { className: 'entity-type-gov', label: 'Gov' },
    LOCATION: { className: 'entity-type-location', label: 'Location' },
  }
  return typeMap[type] || { className: 'entity-type-default', label: type }
}

/**
 * Format date for display
 */
function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

/**
 * Get risk score color
 */
function getRiskScoreColor(score: number | null): string {
  if (score === null) return '#9ca3af'
  if (score >= 70) return '#dc2626'
  if (score >= 40) return '#f59e0b'
  return '#10b981'
}

/**
 * Get trend arrow for mention count
 */
function getTrendArrow(count: number): string {
  if (count >= 50) return '↑↑'
  if (count >= 20) return '↑'
  if (count >= 10) return '→'
  return '↓'
}

/**
 * Entity profile card with expand/collapse
 */
const EntityProfileCardContent = ({ result }: { result: EntityProfileResult }) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const typeInfo = getEntityTypeBadge(result.type)
  const trendArrow = getTrendArrow(result.mention_count)

  return (
    <div className="entity-preview-card">
      {/* Compact view - always visible */}
      <div className="entity-preview-header">
        <div className="entity-preview-title-row">
          <h4 className="entity-preview-name">{result.name}</h4>
          {result.is_sanctioned && (
            <span className="badge badge-sanctioned">Sanctioned</span>
          )}
        </div>
        <div className="entity-preview-meta">
          <span className={`entity-type-badge ${typeInfo.className}`}>
            {typeInfo.label}
          </span>
          <span className="entity-mentions">
            {result.mention_count} mentions {trendArrow}
          </span>
          {result.avg_risk_score !== null && (
            <span
              className="entity-risk-score"
              style={{ color: getRiskScoreColor(result.avg_risk_score) }}
            >
              Risk: {Math.round(result.avg_risk_score)}
            </span>
          )}
        </div>
      </div>

      {/* Expanded view - conditional */}
      {isExpanded && (
        <div className="entity-preview-details">
          <div className="entity-detail-section">
            <h5 className="entity-detail-heading">Recent Mentions</h5>
            {result.recent_mentions.length > 0 ? (
              <ul className="entity-mentions-list">
                {result.recent_mentions.map((mention, idx) => (
                  <li key={idx} className="entity-mention-item">
                    <div className="entity-mention-title">{mention.title}</div>
                    <div className="entity-mention-meta">
                      <span>{formatDate(mention.date)}</span>
                      <span className="entity-mention-source">{mention.source}</span>
                      <span
                        className="entity-mention-risk"
                        style={{ color: getRiskScoreColor(mention.risk_score) }}
                      >
                        Risk: {Math.round(mention.risk_score)}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="entity-no-mentions">No recent mentions</p>
            )}
          </div>

          {(result.first_seen || result.last_seen) && (
            <div className="entity-detail-section">
              <div className="entity-timeline">
                {result.first_seen && (
                  <span>First seen: {formatDate(result.first_seen)}</span>
                )}
                {result.last_seen && (
                  <span>Last seen: {formatDate(result.last_seen)}</span>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Toggle button */}
      <button
        className="entity-preview-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? 'Collapse' : 'Show profile'}
      </button>
    </div>
  )
}

/**
 * Trending entities list card
 */
const TrendingEntitiesCardContent = ({ result }: { result: TrendingEntitiesResult }) => {
  if (!result.entities || result.entities.length === 0) {
    return (
      <div className="entity-preview-empty">
        No trending entities found.
      </div>
    )
  }

  const metricLabel = result.metric === 'mentions'
    ? 'Most Mentioned'
    : result.metric === 'risk'
    ? 'Highest Risk'
    : 'Recently Sanctioned'

  return (
    <div className="trending-entities-card">
      <div className="trending-entities-header">
        <h3 className="trending-entities-title">{metricLabel} Entities</h3>
        <span className="trending-entities-count">{result.count} entities</span>
      </div>
      <div className="trending-entities-list">
        {result.entities.map((entity, idx) => {
          const typeInfo = getEntityTypeBadge(entity.type)
          const trendArrow = getTrendArrow(entity.mention_count)

          return (
            <div key={entity.id} className="trending-entity-item">
              <div className="trending-entity-rank">#{idx + 1}</div>
              <div className="trending-entity-info">
                <div className="trending-entity-name">{entity.name}</div>
                <div className="trending-entity-meta">
                  <span className={`entity-type-badge ${typeInfo.className}`}>
                    {typeInfo.label}
                  </span>
                  <span className="entity-mentions">
                    {entity.mention_count} {trendArrow}
                  </span>
                </div>
              </div>
              <div className="trending-entity-score">
                {entity.trend_score.toFixed(2)}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/**
 * Tool UI component for get_entity_profile tool
 */
export const EntityPreviewCard = makeAssistantToolUI<EntityProfileArgs, EntityProfileResult>({
  toolName: 'get_entity_profile',
  render: ({ result }) => {
    if (!result) return null
    return <EntityProfileCardContent result={result} />
  },
})

/**
 * Tool UI component for get_trending_entities tool
 */
export const TrendingEntitiesCard = makeAssistantToolUI<TrendingEntitiesArgs, TrendingEntitiesResult>({
  toolName: 'get_trending_entities',
  render: ({ result }) => {
    if (!result) return null
    return <TrendingEntitiesCardContent result={result} />
  },
})
