import { useRef } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import type { Entity } from '../lib/types'
import './EntityLeaderboard.css'

interface EntityLeaderboardProps {
  entities: Entity[]
  selectedId: string | null
  onSelect: (id: string) => void
}

/**
 * Get entity type badge class and color
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
export function EntityLeaderboard({ entities, selectedId, onSelect }: EntityLeaderboardProps) {
  const parentRef = useRef<HTMLDivElement>(null)

  // Set up virtualizer for performance with large lists
  const virtualizer = useVirtualizer({
    count: entities.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80, // Estimated row height
    overscan: 5,
  })

  const virtualItems = virtualizer.getVirtualItems()

  if (entities.length === 0) {
    return (
      <div className="entity-leaderboard-empty">
        No entities found
      </div>
    )
  }

  return (
    <div ref={parentRef} className="entity-leaderboard-container">
      <div
        className="entity-leaderboard-inner"
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          position: 'relative',
        }}
      >
        {virtualItems.map((virtualItem) => {
          const entity = entities[virtualItem.index]
          const typeInfo = getEntityTypeBadge(entity.entity_type)
          const isSelected = entity.id === selectedId
          const rank = entity.trending_rank || virtualItem.index + 1

          return (
            <div
              key={entity.id}
              className="virtual-item"
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              <div
                className={`entity-row ${isSelected ? 'entity-row-selected' : ''}`}
                onClick={() => onSelect(entity.id)}
              >
                {/* Rank badge */}
                <div className="entity-rank">
                  <span className="rank-number">#{rank}</span>
                </div>

                {/* Entity info */}
                <div className="entity-info">
                  <div className="entity-name">{entity.canonical_name}</div>
                  <div className="entity-meta">
                    <span className={`entity-type-badge ${typeInfo.className}`}>
                      {typeInfo.label}
                    </span>
                    <span className="entity-mentions">
                      {entity.mention_count} {entity.mention_count === 1 ? 'mention' : 'mentions'}
                    </span>
                  </div>
                </div>

                {/* Metric value */}
                <div className="entity-metric">
                  {formatMetricValue(entity)}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
