import { useState } from 'react'
import { makeAssistantToolUI } from '@assistant-ui/react'
import { Card, Badge, Text, Group, Stack, Button } from '@mantine/core'
import { format } from 'date-fns'

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
 * Get risk score Badge color based on value
 */
function getRiskScoreColor(score: number): string {
  if (score >= 75) return 'red'
  if (score >= 50) return 'orange'
  return 'blue'
}

/**
 * Get severity Badge color
 */
function getSeverityColor(severity: string): string {
  if (severity === 'SEV1_CRITICAL') return 'red'
  if (severity === 'SEV2_HIGH') return 'orange'
  if (severity === 'SEV3_MEDIUM') return 'yellow'
  if (severity === 'SEV4_LOW') return 'blue'
  if (severity === 'SEV5_MINIMAL') return 'gray'
  return 'gray'
}

/**
 * Get severity display label
 */
function getSeverityLabel(severity: string): string {
  const severityMap: Record<string, string> = {
    SEV1_CRITICAL: 'SEV1',
    SEV2_HIGH: 'SEV2',
    SEV3_MEDIUM: 'SEV3',
    SEV4_LOW: 'SEV4',
    SEV5_MINIMAL: 'SEV5',
  }
  return severityMap[severity] || severity
}

/**
 * Individual event card with expand/collapse
 */
function EventItem({ event }: { event: SearchEventsResult['events'][0] }) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <Card size="sm" padding="xs" withBorder>
      <Stack gap="xs">
        {/* Title and badges */}
        <Group justify="space-between" wrap="nowrap">
          <Text size="sm" fw={500} lineClamp={isExpanded ? undefined : 1}>
            {event.title}
          </Text>
        </Group>

        {/* Metadata row */}
        <Group gap="xs">
          <Text size="xs" c="dimmed">
            {format(new Date(event.date), 'MMM d, yyyy')}
          </Text>
          <Badge size="sm" variant="light">
            {event.source}
          </Badge>
          <Badge size="sm" color={getRiskScoreColor(event.risk_score)}>
            {Math.round(event.risk_score)}
          </Badge>
          <Badge size="sm" color={getSeverityColor(event.severity)}>
            {getSeverityLabel(event.severity)}
          </Badge>
        </Group>

        {/* Expanded summary */}
        {isExpanded && (
          <Text size="xs" c="dimmed">
            {event.summary}
          </Text>
        )}

        {/* Toggle button */}
        <Button
          variant="subtle"
          size="xs"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? 'Collapse' : 'Show details'}
        </Button>
      </Stack>
    </Card>
  )
}

/**
 * Event preview card for search_events tool results
 * Displays list of events with expand-in-place functionality
 */
const EventPreviewCardContent = ({ result }: { result: SearchEventsResult }) => {
  if (!result.events || result.events.length === 0) {
    return (
      <Text size="sm" c="dimmed">
        No events found for the specified criteria.
      </Text>
    )
  }

  return (
    <Stack gap="xs">
      {/* Header */}
      <Group justify="space-between">
        <Text size="sm" fw={600}>Found {result.count} Events</Text>
        {result.date_range && (
          <Text size="xs" c="dimmed">
            {format(new Date(result.date_range.from), 'MMM d, yyyy')} - {format(new Date(result.date_range.to), 'MMM d, yyyy')}
          </Text>
        )}
      </Group>

      {/* Event list */}
      <Stack gap="xs">
        {result.events.map((event) => (
          <EventItem key={event.id} event={event} />
        ))}
      </Stack>
    </Stack>
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
