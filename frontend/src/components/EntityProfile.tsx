import { useState, useEffect } from 'react'
import { api } from '../lib/api'
import type { EntityProfile as EntityProfileType } from '../lib/types'
import './EntityProfile.css'

interface EntityProfileProps {
  entityId: string
}

/**
 * Format timestamp to readable date
 */
function formatDate(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

/**
 * Get entity type display info
 */
function getEntityTypeInfo(type: string): { className: string; label: string } {
  const typeMap: Record<string, { className: string; label: string }> = {
    PERSON: { className: 'entity-type-person', label: 'Person' },
    ORGANIZATION: { className: 'entity-type-org', label: 'Organization' },
    GOVERNMENT: { className: 'entity-type-gov', label: 'Government' },
    LOCATION: { className: 'entity-type-location', label: 'Location' },
  }
  return typeMap[type] || { className: 'entity-type-default', label: type }
}

/**
 * Get risk score color class
 */
function getRiskScoreClass(score: number | null | undefined): string {
  if (score === null || score === undefined) return 'risk-unknown'
  if (score >= 75) return 'risk-critical'
  if (score >= 50) return 'risk-high'
  if (score >= 25) return 'risk-medium'
  return 'risk-low'
}

/**
 * Entity profile detail component
 * Fetches and displays full entity profile with sanctions status, risk score, and recent events
 */
export function EntityProfile({ entityId }: EntityProfileProps) {
  const [profile, setProfile] = useState<EntityProfileType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    async function fetchProfile() {
      try {
        setLoading(true)
        setError(null)
        const data = await api.getEntityProfile(entityId)
        if (mounted) {
          setProfile(data)
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to load entity profile')
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    fetchProfile()

    return () => {
      mounted = false
    }
  }, [entityId])

  if (loading) {
    return (
      <div className="entity-profile-loading">
        <p>Loading entity profile...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="entity-profile-error">
        <h3>Error Loading Profile</h3>
        <p>{error}</p>
      </div>
    )
  }

  if (!profile) {
    return null
  }

  const typeInfo = getEntityTypeInfo(profile.entity_type)
  const riskClass = getRiskScoreClass(profile.risk_score)

  return (
    <div className="entity-profile">
      {/* Header */}
      <div className="entity-profile-header">
        <div className="entity-profile-title-row">
          <h2 className="entity-profile-name">{profile.canonical_name}</h2>
          {profile.trending_rank && (
            <span className="entity-profile-rank">#{profile.trending_rank}</span>
          )}
        </div>
        <div className="entity-profile-badges">
          <span className={`entity-type-badge ${typeInfo.className}`}>
            {typeInfo.label}
          </span>
        </div>
      </div>

      {/* Sanctions Warning */}
      {profile.sanctions_status && (
        <div className="sanctions-warning">
          <strong>⚠️ Sanctions Alert:</strong> This entity appears on sanctions lists
        </div>
      )}

      {/* Overview Stats */}
      <div className="entity-profile-section">
        <h3>Overview</h3>
        <div className="entity-stats-grid">
          <div className="stat-item">
            <span className="stat-label">Mentions</span>
            <span className="stat-value">{profile.mention_count}</span>
          </div>
          {profile.risk_score !== null && profile.risk_score !== undefined && (
            <div className="stat-item">
              <span className="stat-label">Risk Score</span>
              <span className={`stat-value stat-value-risk ${riskClass}`}>
                {Math.round(profile.risk_score)}
              </span>
            </div>
          )}
          <div className="stat-item">
            <span className="stat-label">First Seen</span>
            <span className="stat-value">{formatDate(profile.first_seen)}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Last Seen</span>
            <span className="stat-value">{formatDate(profile.last_seen)}</span>
          </div>
        </div>
      </div>

      {/* Aliases */}
      {profile.aliases && profile.aliases.length > 0 && (
        <div className="entity-profile-section">
          <h3>Known Aliases</h3>
          <div className="entity-aliases">
            {profile.aliases.map((alias, idx) => (
              <span key={idx} className="alias-tag">{alias}</span>
            ))}
          </div>
        </div>
      )}

      {/* Recent Events */}
      {profile.recent_events && profile.recent_events.length > 0 && (
        <div className="entity-profile-section">
          <h3>Recent Events ({profile.recent_events.length})</h3>
          <div className="recent-events-list">
            {profile.recent_events.map((event) => (
              <div key={event.id} className="recent-event-card">
                <div className="recent-event-header">
                  <h4 className="recent-event-title">{event.title}</h4>
                  {event.risk_score !== null && event.risk_score !== undefined && (
                    <span className={`badge badge-risk ${getRiskScoreClass(event.risk_score)}`}>
                      {Math.round(event.risk_score)}
                    </span>
                  )}
                </div>
                <div className="recent-event-meta">
                  <span className="badge badge-source">{event.source}</span>
                  <span className="recent-event-time">{formatDate(event.timestamp)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
