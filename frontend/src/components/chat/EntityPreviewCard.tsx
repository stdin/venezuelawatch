import { useState } from 'react'
import { makeAssistantToolUI } from '@assistant-ui/react'
import { Card, Alert, Badge, Text, Group, Stack, Button, Divider } from '@mantine/core'
import { format } from 'date-fns'

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
 * Get entity type Badge color (Phase 11 pattern)
 */
function getEntityTypeColor(type: string): string {
  const typeMap: Record<string, string> = {
    PERSON: 'blue',
    ORGANIZATION: 'grape',
    GOVERNMENT: 'red',
    LOCATION: 'green',
  }
  return typeMap[type] || 'gray'
}

/**
 * Get entity type label
 */
function getEntityTypeLabel(type: string): string {
  const typeMap: Record<string, string> = {
    PERSON: 'Person',
    ORGANIZATION: 'Org',
    GOVERNMENT: 'Gov',
    LOCATION: 'Location',
  }
  return typeMap[type] || type
}

/**
 * Get risk score Badge color (Phase 10 pattern)
 */
function getRiskScoreColor(score: number | null): string {
  if (score === null) return 'gray'
  if (score >= 75) return 'red'
  if (score >= 50) return 'orange'
  return 'blue'
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
  const trendArrow = getTrendArrow(result.mention_count)

  return (
    <Card size="sm" padding="xs" withBorder>
      <Stack gap="xs">
        {/* Sanctions alert */}
        {result.is_sanctioned && (
          <Alert color="red" variant="filled" title="Sanctioned">
            <Text size="xs">This entity appears on sanctions lists</Text>
          </Alert>
        )}

        {/* Entity name */}
        <Text size="sm" fw={600}>
          {result.name}
        </Text>

        {/* Metadata row */}
        <Group gap="xs">
          <Badge size="sm" color={getEntityTypeColor(result.type)}>
            {getEntityTypeLabel(result.type)}
          </Badge>
          <Text size="xs" c="dimmed">
            {result.mention_count} mentions {trendArrow}
          </Text>
          {result.avg_risk_score !== null && (
            <Badge size="sm" color={getRiskScoreColor(result.avg_risk_score)}>
              Risk: {Math.round(result.avg_risk_score)}
            </Badge>
          )}
        </Group>

        {/* Expanded view */}
        {isExpanded && (
          <>
            <Divider />

            {/* Recent mentions section */}
            <Stack gap="xs">
              <Text size="xs" fw={500}>Recent Mentions</Text>
              {result.recent_mentions.length > 0 ? (
                <Stack gap="xs">
                  {result.recent_mentions.map((mention, idx) => (
                    <Stack key={idx} gap={4}>
                      <Text size="xs">{mention.title}</Text>
                      <Group gap="xs">
                        <Text size="xs" c="dimmed">
                          {format(new Date(mention.date), 'MMM d, yyyy')}
                        </Text>
                        <Text size="xs" c="dimmed">{mention.source}</Text>
                        <Badge size="xs" color={getRiskScoreColor(mention.risk_score)}>
                          {Math.round(mention.risk_score)}
                        </Badge>
                      </Group>
                    </Stack>
                  ))}
                </Stack>
              ) : (
                <Text size="xs" c="dimmed">No recent mentions</Text>
              )}
            </Stack>

            {/* Timeline section */}
            {(result.first_seen || result.last_seen) && (
              <>
                <Divider />
                <Group gap="md">
                  {result.first_seen && (
                    <Text size="xs" c="dimmed">
                      First seen: {format(new Date(result.first_seen), 'MMM d, yyyy')}
                    </Text>
                  )}
                  {result.last_seen && (
                    <Text size="xs" c="dimmed">
                      Last seen: {format(new Date(result.last_seen), 'MMM d, yyyy')}
                    </Text>
                  )}
                </Group>
              </>
            )}
          </>
        )}

        {/* Toggle button */}
        <Button
          variant="subtle"
          size="xs"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? 'Collapse' : 'Show profile'}
        </Button>
      </Stack>
    </Card>
  )
}

/**
 * Trending entities list card
 */
const TrendingEntitiesCardContent = ({ result }: { result: TrendingEntitiesResult }) => {
  if (!result.entities || result.entities.length === 0) {
    return (
      <Text size="sm" c="dimmed">
        No trending entities found.
      </Text>
    )
  }

  const metricLabel = result.metric === 'mentions'
    ? 'Most Mentioned'
    : result.metric === 'risk'
    ? 'Highest Risk'
    : 'Recently Sanctioned'

  return (
    <Stack gap="xs">
      {/* Header */}
      <Group justify="space-between">
        <Text size="sm" fw={600}>{metricLabel} Entities</Text>
        <Text size="xs" c="dimmed">{result.count} entities</Text>
      </Group>

      {/* Entity list */}
      <Stack gap="xs">
        {result.entities.map((entity, idx) => {
          const trendArrow = getTrendArrow(entity.mention_count)

          return (
            <Card key={entity.id} size="sm" padding="xs" withBorder>
              <Group gap="xs">
                <Badge size="lg" circle>
                  {idx + 1}
                </Badge>
                <Stack gap={4} style={{ flex: 1 }}>
                  <Text size="sm" fw={500}>
                    {entity.name}
                  </Text>
                  <Group gap="xs">
                    <Badge size="sm" color={getEntityTypeColor(entity.type)}>
                      {getEntityTypeLabel(entity.type)}
                    </Badge>
                    <Text size="xs" c="dimmed">
                      {entity.mention_count} {trendArrow}
                    </Text>
                  </Group>
                </Stack>
                <Text size="sm" fw={600} c="dimmed">
                  {entity.trend_score.toFixed(2)}
                </Text>
              </Group>
            </Card>
          )
        })}
      </Stack>
    </Stack>
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
