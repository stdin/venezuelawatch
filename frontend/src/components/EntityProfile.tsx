import { useState, useEffect } from 'react'
import { Card, Alert, Badge, Text, Title, Stack, Group, Divider, List, Skeleton } from '@mantine/core'
import { format } from 'date-fns'
import { api } from '../lib/api'
import type { EntityProfile as EntityProfileType } from '../lib/types'

interface EntityProfileProps {
  entityId: string
}

/**
 * Get entity type badge color for Mantine Badge
 */
function getEntityTypeBadgeColor(type: string): string {
  const colorMap: Record<string, string> = {
    PERSON: 'blue',
    ORGANIZATION: 'grape',
    GOVERNMENT: 'red',
    LOCATION: 'green',
  }
  return colorMap[type] || 'gray'
}

/**
 * Get entity type label
 */
function getEntityTypeLabel(type: string): string {
  const labelMap: Record<string, string> = {
    PERSON: 'Person',
    ORGANIZATION: 'Organization',
    GOVERNMENT: 'Government',
    LOCATION: 'Location',
  }
  return labelMap[type] || type
}

/**
 * Get risk score badge color
 */
function getRiskScoreColor(score: number | null | undefined): string {
  if (score === null || score === undefined) return 'gray'
  if (score >= 75) return 'red'
  if (score >= 50) return 'orange'
  return 'blue'
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
      <Stack gap="md" p="md">
        <Skeleton height={30} width="60%" />
        <Card padding="md" withBorder>
          <Stack gap="xs">
            <Skeleton height={20} width="40%" />
            <Skeleton height={16} width="80%" />
            <Skeleton height={16} width="70%" />
          </Stack>
        </Card>
        <Card padding="md" withBorder>
          <Stack gap="xs">
            <Skeleton height={20} width="40%" />
            <Skeleton height={16} width="60%" />
          </Stack>
        </Card>
      </Stack>
    )
  }

  if (error) {
    return (
      <Card padding="md" withBorder>
        <Stack gap="sm">
          <Title order={4} c="red">Error Loading Profile</Title>
          <Text c="dimmed">{error}</Text>
        </Stack>
      </Card>
    )
  }

  if (!profile) {
    return (
      <Card padding="md" withBorder>
        <Text c="dimmed" ta="center">Select an entity to view profile</Text>
      </Card>
    )
  }

  return (
    <Stack gap="md" p="md">
      {/* Header with entity name */}
      <Group justify="space-between">
        <Title order={3}>{profile.canonical_name}</Title>
        {profile.trending_rank && (
          <Badge size="lg" variant="outline" color="gray">
            #{profile.trending_rank}
          </Badge>
        )}
      </Group>

      {/* Sanctions Warning Alert */}
      {profile.sanctions_status && (
        <Alert color="red" variant="filled" title="Sanctioned Entity">
          This entity appears on sanctions lists
        </Alert>
      )}

      {/* Overview Card */}
      <Card padding="md" withBorder>
        <Stack gap="sm">
          <Title order={4}>Overview</Title>
          <Group gap="xs">
            <Badge color={getEntityTypeBadgeColor(profile.entity_type)}>
              {getEntityTypeLabel(profile.entity_type)}
            </Badge>
            <Text size="sm">
              {profile.mention_count} {profile.mention_count === 1 ? 'mention' : 'mentions'}
            </Text>
          </Group>
          <Divider />
          <Group justify="space-between">
            <Text size="sm" c="dimmed">First Seen</Text>
            <Text size="sm">{format(new Date(profile.first_seen), 'MMM d, yyyy')}</Text>
          </Group>
          <Group justify="space-between">
            <Text size="sm" c="dimmed">Last Seen</Text>
            <Text size="sm">{format(new Date(profile.last_seen), 'MMM d, yyyy')}</Text>
          </Group>
        </Stack>
      </Card>

      {/* Risk Intelligence Card */}
      {(profile.risk_score !== null && profile.risk_score !== undefined) && (
        <Card padding="md" withBorder>
          <Stack gap="sm">
            <Title order={4}>Risk Intelligence</Title>
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Risk Score</Text>
              <Badge size="lg" color={getRiskScoreColor(profile.risk_score)}>
                {Math.round(profile.risk_score)}
              </Badge>
            </Group>
            {profile.sanctions_status && (
              <Group justify="space-between">
                <Text size="sm" c="dimmed">Sanctions Status</Text>
                <Badge size="sm" color="red">Sanctioned</Badge>
              </Group>
            )}
          </Stack>
        </Card>
      )}

      {/* Known Aliases Card */}
      {profile.aliases && profile.aliases.length > 0 && (
        <Card padding="md" withBorder>
          <Stack gap="sm">
            <Title order={4}>Known Aliases</Title>
            <Group gap="xs">
              {profile.aliases.map((alias, idx) => (
                <Badge key={idx} variant="light" color="gray">
                  {alias}
                </Badge>
              ))}
            </Group>
          </Stack>
        </Card>
      )}

      {/* Recent Events Card */}
      {profile.recent_events && profile.recent_events.length > 0 && (
        <Card padding="md" withBorder>
          <Stack gap="sm">
            <Title order={4}>Recent Events ({profile.recent_events.length})</Title>
            <List spacing="md">
              {profile.recent_events.map((event) => (
                <List.Item key={event.id}>
                  <Stack gap="xs">
                    <Group justify="space-between">
                      <Text size="sm" fw={500}>{event.title}</Text>
                      {event.risk_score !== null && event.risk_score !== undefined && (
                        <Badge size="sm" color={getRiskScoreColor(event.risk_score)}>
                          {Math.round(event.risk_score)}
                        </Badge>
                      )}
                    </Group>
                    <Group gap="xs">
                      <Badge size="xs" variant="light">{event.source}</Badge>
                      <Text size="xs" c="dimmed">
                        {format(new Date(event.timestamp), 'MMM d, yyyy')}
                      </Text>
                    </Group>
                  </Stack>
                </List.Item>
              ))}
            </List>
          </Stack>
        </Card>
      )}
    </Stack>
  )
}
