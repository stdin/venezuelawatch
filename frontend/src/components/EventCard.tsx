import { Card, Text, Badge, Group, Stack } from '@mantine/core'
import type { RiskEvent } from '../lib/types'

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
 * Get risk score Badge color based on value
 */
function getRiskScoreColor(score: number): string {
  if (score >= 70) return 'red'
  if (score >= 50) return 'orange'
  return 'blue'
}

/**
 * Get severity Badge color based on SEV level
 */
function getSeverityColor(severity: string): string {
  const severityMap: Record<string, string> = {
    SEV1_CRITICAL: 'red',
    SEV2_HIGH: 'orange',
    SEV3_MEDIUM: 'yellow',
    SEV4_LOW: 'blue',
    SEV5_MINIMAL: 'gray',
  }
  return severityMap[severity] || 'gray'
}

/**
 * Get severity label (SEV1, SEV2, etc.)
 */
function getSeverityLabel(severity: string): string {
  const match = severity.match(/^SEV(\d)/)
  return match ? `SEV${match[1]}` : severity
}

/**
 * Get sentiment indicator
 */
function getSentimentInfo(sentiment: number): { icon: string; label: string } {
  if (sentiment > 0.3) return { icon: '↑', label: 'Positive' }
  if (sentiment < -0.3) return { icon: '↓', label: 'Negative' }
  return { icon: '→', label: 'Neutral' }
}

/**
 * Event card component displaying moderate information density
 */
export function EventCard({ event, isSelected, onSelect }: EventCardProps) {
  const riskColor = getRiskScoreColor(event.risk_score)
  const severityColor = getSeverityColor(event.severity)
  const severityLabel = getSeverityLabel(event.severity)
  const sentimentInfo = getSentimentInfo(event.sentiment)
  const relativeTime = formatRelativeTime(event.timestamp)

  return (
    <Card
      padding="md"
      withBorder
      onClick={onSelect}
      style={{
        cursor: 'pointer',
        backgroundColor: isSelected ? 'var(--mantine-color-blue-light)' : undefined,
      }}
    >
      <Stack gap="xs">
        {/* Title and badges */}
        <Group justify="space-between" align="flex-start">
          <Text size="sm" fw={700} style={{ flex: 1 }}>
            {event.title}
          </Text>
          <Group gap="xs">
            <Badge color={riskColor} size="sm">
              {Math.round(event.risk_score)}
            </Badge>
            <Badge color={severityColor} size="sm">
              {severityLabel}
            </Badge>
          </Group>
        </Group>

        {/* Timestamp */}
        <Text size="xs" c="dimmed">
          {relativeTime}
        </Text>

        {/* Summary */}
        <Text size="sm" lineClamp={2}>
          {event.summary}
        </Text>

        {/* Footer: Source and sentiment */}
        <Group justify="space-between">
          <Badge variant="light" size="sm">
            {event.source}
          </Badge>
          <Text size="xs" c="dimmed" title={sentimentInfo.label}>
            {sentimentInfo.icon}
          </Text>
        </Group>
      </Stack>
    </Card>
  )
}
