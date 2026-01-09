import { useState } from 'react'
import type { EventFilterParams } from '../lib/types'
import './FilterBar.css'

interface FilterBarProps {
  filters: EventFilterParams
  onFiltersChange: (filters: EventFilterParams) => void
}

const SEVERITY_LEVELS = [
  { value: 'SEV1_CRITICAL', label: 'SEV1', description: 'Critical' },
  { value: 'SEV2_HIGH', label: 'SEV2', description: 'High' },
  { value: 'SEV3_MEDIUM', label: 'SEV3', description: 'Medium' },
  { value: 'SEV4_LOW', label: 'SEV4', description: 'Low' },
  { value: 'SEV5_MINIMAL', label: 'SEV5', description: 'Minimal' },
]

const EVENT_TYPES = [
  { value: '', label: 'All Types' },
  { value: 'POLITICAL', label: 'Political' },
  { value: 'ECONOMIC', label: 'Economic' },
  { value: 'HUMANITARIAN', label: 'Humanitarian' },
  { value: 'TRADE', label: 'Trade' },
]

const TIME_RANGES = [
  { value: 1, label: 'Last 24h' },
  { value: 7, label: 'Last week' },
  { value: 30, label: 'Last month' },
  { value: 90, label: 'Last 3 months' },
]

/**
 * Filter bar component for dashboard event filtering
 */
export function FilterBar({ filters, onFiltersChange }: FilterBarProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  // Parse severity string to array
  const selectedSeverities = filters.severity ? filters.severity.split(',') : SEVERITY_LEVELS.map(s => s.value)

  // Handle severity checkbox change
  const handleSeverityChange = (severityValue: string, checked: boolean) => {
    let newSeverities = [...selectedSeverities]
    if (checked) {
      newSeverities.push(severityValue)
    } else {
      newSeverities = newSeverities.filter(s => s !== severityValue)
    }

    onFiltersChange({
      ...filters,
      severity: newSeverities.length > 0 ? newSeverities.join(',') : undefined,
    })
  }

  // Handle risk score changes
  const handleMinRiskChange = (value: string) => {
    const numValue = value === '' ? undefined : parseInt(value, 10)
    onFiltersChange({
      ...filters,
      min_risk_score: numValue,
    })
  }

  const handleMaxRiskChange = (value: string) => {
    const numValue = value === '' ? undefined : parseInt(value, 10)
    onFiltersChange({
      ...filters,
      max_risk_score: numValue,
    })
  }

  // Handle sanctions toggle
  const handleSanctionsChange = (checked: boolean) => {
    onFiltersChange({
      ...filters,
      has_sanctions: checked || undefined,
    })
  }

  // Handle event type change
  const handleEventTypeChange = (value: string) => {
    onFiltersChange({
      ...filters,
      event_type: value || undefined,
    })
  }

  // Handle time range change
  const handleTimeRangeChange = (value: string) => {
    const numValue = parseInt(value, 10)
    onFiltersChange({
      ...filters,
      days_back: numValue,
    })
  }

  // Clear all filters
  const handleClearFilters = () => {
    onFiltersChange({
      days_back: 30,
      min_risk_score: 0,
      max_risk_score: 100,
    })
  }

  return (
    <div className="filter-bar">
      <div className="filter-bar-header">
        <h3>Filters</h3>
        <div className="filter-bar-actions">
          <button onClick={handleClearFilters} className="btn-clear">
            Clear Filters
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="btn-toggle"
            aria-label={isExpanded ? 'Collapse filters' : 'Expand filters'}
          >
            {isExpanded ? '▲' : '▼'}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="filter-bar-content">
          {/* Severity filters */}
          <div className="filter-group">
            <label className="filter-label">Severity</label>
            <div className="filter-checkboxes">
              {SEVERITY_LEVELS.map(sev => (
                <label key={sev.value} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={selectedSeverities.includes(sev.value)}
                    onChange={(e) => handleSeverityChange(sev.value, e.target.checked)}
                  />
                  <span className="checkbox-text" title={sev.description}>
                    {sev.label}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Risk score range */}
          <div className="filter-group">
            <label className="filter-label">Risk Score</label>
            <div className="filter-range">
              <input
                type="number"
                min="0"
                max="100"
                value={filters.min_risk_score ?? 0}
                onChange={(e) => handleMinRiskChange(e.target.value)}
                placeholder="Min"
                className="input-number"
              />
              <span className="range-separator">to</span>
              <input
                type="number"
                min="0"
                max="100"
                value={filters.max_risk_score ?? 100}
                onChange={(e) => handleMaxRiskChange(e.target.value)}
                placeholder="Max"
                className="input-number"
              />
            </div>
          </div>

          {/* Event type */}
          <div className="filter-group">
            <label className="filter-label">Event Type</label>
            <select
              value={filters.event_type ?? ''}
              onChange={(e) => handleEventTypeChange(e.target.value)}
              className="filter-select"
            >
              {EVENT_TYPES.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Sanctions toggle */}
          <div className="filter-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.has_sanctions ?? false}
                onChange={(e) => handleSanctionsChange(e.target.checked)}
              />
              <span className="checkbox-text">Show only sanctioned events</span>
            </label>
          </div>

          {/* Time range */}
          <div className="filter-group">
            <label className="filter-label">Time Range</label>
            <select
              value={filters.days_back ?? 30}
              onChange={(e) => handleTimeRangeChange(e.target.value)}
              className="filter-select"
            >
              {TIME_RANGES.map(range => (
                <option key={range.value} value={range.value}>
                  {range.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}
    </div>
  )
}
