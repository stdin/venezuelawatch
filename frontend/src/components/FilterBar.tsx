import { useState } from 'react'
import { Stack, Group, MultiSelect, NumberInput, Select, Checkbox, Button, Collapse, Text, Title } from '@mantine/core'
import type { EventFilterParams } from '../lib/types'

interface FilterBarProps {
  filters: EventFilterParams
  onFiltersChange: (filters: EventFilterParams) => void
}

const SEVERITY_LEVELS = [
  { value: 'SEV1_CRITICAL', label: 'SEV1 - Critical' },
  { value: 'SEV2_HIGH', label: 'SEV2 - High' },
  { value: 'SEV3_MEDIUM', label: 'SEV3 - Medium' },
  { value: 'SEV4_LOW', label: 'SEV4 - Low' },
  { value: 'SEV5_MINIMAL', label: 'SEV5 - Minimal' },
]

const EVENT_TYPES = [
  { value: 'POLITICAL', label: 'Political' },
  { value: 'ECONOMIC', label: 'Economic' },
  { value: 'HUMANITARIAN', label: 'Humanitarian' },
  { value: 'TRADE', label: 'Trade' },
]

const TIME_RANGES = [
  { value: '1', label: 'Last 24h' },
  { value: '7', label: 'Last week' },
  { value: '30', label: 'Last month' },
  { value: '90', label: 'Last 3 months' },
]

/**
 * Filter bar component for dashboard event filtering
 * Uses Mantine form components for professional UI
 */
export function FilterBar({ filters, onFiltersChange }: FilterBarProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  // Parse severity string to array for MultiSelect
  const selectedSeverities = filters.severity ? filters.severity.split(',') : []

  // Handle severity change from MultiSelect
  const handleSeverityChange = (values: string[]) => {
    onFiltersChange({
      ...filters,
      severity: values.length > 0 ? values.join(',') : undefined,
    })
  }

  // Handle risk score changes
  const handleMinRiskChange = (value: number | string) => {
    const numValue = typeof value === 'number' ? value : undefined
    onFiltersChange({
      ...filters,
      min_risk_score: numValue,
    })
  }

  const handleMaxRiskChange = (value: number | string) => {
    const numValue = typeof value === 'number' ? value : undefined
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
  const handleEventTypeChange = (value: string | null) => {
    onFiltersChange({
      ...filters,
      event_type: value || undefined,
    })
  }

  // Handle time range change
  const handleTimeRangeChange = (value: string | null) => {
    const numValue = value ? parseInt(value, 10) : 30
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
    <Stack gap="md">
      <Group justify="space-between">
        <Title order={4}>Filters</Title>
        <Group gap="xs">
          <Button variant="subtle" size="compact-sm" onClick={handleClearFilters}>
            Clear
          </Button>
          <Button
            variant="subtle"
            size="compact-sm"
            onClick={() => setIsExpanded(!isExpanded)}
            aria-label={isExpanded ? 'Collapse filters' : 'Expand filters'}
          >
            {isExpanded ? '▲' : '▼'}
          </Button>
        </Group>
      </Group>

      <Collapse in={isExpanded}>
        <Stack gap="md">
          {/* Severity MultiSelect */}
          <MultiSelect
            label="Severity"
            placeholder="Select severity levels"
            data={SEVERITY_LEVELS}
            value={selectedSeverities}
            onChange={handleSeverityChange}
            clearable
            searchable
          />

          {/* Risk Score Range */}
          <div>
            <Text size="sm" fw={500} mb="xs">Risk Score</Text>
            <Group gap="xs" grow>
              <NumberInput
                placeholder="Min"
                min={0}
                max={100}
                value={filters.min_risk_score ?? 0}
                onChange={handleMinRiskChange}
              />
              <Text ta="center" pt="xs">to</Text>
              <NumberInput
                placeholder="Max"
                min={0}
                max={100}
                value={filters.max_risk_score ?? 100}
                onChange={handleMaxRiskChange}
              />
            </Group>
          </div>

          {/* Event Type Select */}
          <Select
            label="Event Type"
            placeholder="All types"
            data={EVENT_TYPES}
            value={filters.event_type ?? null}
            onChange={handleEventTypeChange}
            clearable
          />

          {/* Sanctions Checkbox */}
          <Checkbox
            label="Show only sanctioned events"
            checked={filters.has_sanctions ?? false}
            onChange={(e) => handleSanctionsChange(e.currentTarget.checked)}
          />

          {/* Time Range Select */}
          <Select
            label="Time Range"
            data={TIME_RANGES}
            value={filters.days_back?.toString() ?? '30'}
            onChange={handleTimeRangeChange}
          />
        </Stack>
      </Collapse>
    </Stack>
  )
}
