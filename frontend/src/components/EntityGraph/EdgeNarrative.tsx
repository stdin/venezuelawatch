import { Modal, Text, Stack, Badge, Skeleton, Alert, Box, Group, Timeline } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { fetchNarrative } from '@/lib/api'
import type { GraphEdge } from './useGraphData'

interface EdgeNarrativeProps {
  edge: GraphEdge | null
  onClose: () => void
}

/**
 * EdgeNarrative modal component
 * 
 * Displays LLM-generated causal narrative explaining how two entities
 * are connected through events. Follows Phase 26 progressive disclosure pattern.
 * Enhanced with timeline visualization showing temporal event lineage.
 */
export function EdgeNarrative({ edge, onClose }: EdgeNarrativeProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['narrative', edge?.source, edge?.target],
    queryFn: () => {
      if (!edge) throw new Error('No edge selected')
      return fetchNarrative(edge.source, edge.target)
    },
    enabled: !!edge,
    retry: 1,
  })

  return (
    <Modal
      opened={!!edge}
      onClose={onClose}
      title="Relationship Narrative"
      size="lg"
    >
      {isLoading && <Skeleton height={200} />}

      {error && (
        <Alert color="red" title="Error">
          Failed to load narrative. Please try again.
        </Alert>
      )}

      {data && (
        <Stack gap="md">
          <Box>
            <Text fw={600} mb="xs">
              Connection:
            </Text>
            <Text size="sm">
              {data.entity_a.name} ({data.entity_a.entity_type}) ↔{' '}
              {data.entity_b.name} ({data.entity_b.entity_type})
            </Text>
          </Box>

          <Box>
            <Text fw={600} mb="xs">
              Analysis:
            </Text>
            <Text>{data.narrative}</Text>
          </Box>

          {/* Event Timeline Visualization */}
          {data.lineage && data.lineage.events.length > 0 && (
            <Box mt="lg">
              <Group justify="space-between" mb="xs">
                <Text fw={600}>
                  Event Timeline ({data.lineage.timeline_spans_days} days)
                </Text>
                {data.lineage.dominant_themes.length > 0 && (
                  <Group gap={4}>
                    {data.lineage.dominant_themes.slice(0, 3).map(theme => (
                      <Badge key={theme} size="xs" variant="light">
                        {theme}
                      </Badge>
                    ))}
                  </Group>
                )}
              </Group>

              {data.lineage.escalation_detected && (
                <Alert color="orange" mb="xs" p="xs">
                  ⚠️ Escalation detected: Risk increased over time
                </Alert>
              )}

              <Timeline active={data.lineage.events.length - 1} bulletSize={24}>
                {data.lineage.events.map((event, idx) => (
                  <Timeline.Item
                    key={event.id}
                    title={event.title}
                    bullet={<Text size="xs">{idx + 1}</Text>}
                  >
                    <Group gap="xs" mt={4}>
                      <Badge size="sm">{event.severity}</Badge>
                      <Badge size="sm" color="orange">
                        Risk: {event.risk_score.toFixed(0)}
                      </Badge>
                      <Text size="xs" c="dimmed">
                        {event.published_at && new Date(event.published_at).toLocaleDateString()}
                        {event.days_since_prev && ` (+${event.days_since_prev}d)`}
                      </Text>
                    </Group>
                    {event.themes.length > 0 && (
                      <Group gap={4} mt={4}>
                        {event.themes.slice(0, 3).map(theme => (
                          <Badge key={theme} size="xs" variant="light">
                            {theme}
                          </Badge>
                        ))}
                      </Group>
                    )}
                  </Timeline.Item>
                ))}
              </Timeline>
            </Box>
          )}

          {/* Fallback to supporting events if no lineage */}
          {(!data.lineage || data.lineage.events.length === 0) && data.events.length > 0 && (
            <Box>
              <Text fw={600} mb="xs">
                Supporting Events ({data.events.length}):
              </Text>
              <Stack gap="xs">
                {data.events.map((event) => (
                  <Box
                    key={event.id}
                    p="xs"
                    style={{
                      border: '1px solid var(--mantine-color-gray-3)',
                      borderRadius: 4,
                    }}
                  >
                    <Text size="sm" fw={500}>
                      {event.title}
                    </Text>
                    <Group gap="xs" mt={4}>
                      <Badge size="sm" color="blue">
                        {event.severity}
                      </Badge>
                      <Badge size="sm" color="orange">
                        Risk: {event.risk_score.toFixed(0)}
                      </Badge>
                      {event.published_at && (
                        <Text size="xs" c="dimmed">
                          {new Date(event.published_at).toLocaleDateString()}
                        </Text>
                      )}
                    </Group>
                  </Box>
                ))}
              </Stack>
            </Box>
          )}
        </Stack>
      )}
    </Modal>
  )
}
