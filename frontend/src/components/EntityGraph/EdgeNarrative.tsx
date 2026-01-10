import { Modal, Text, Stack, Badge, Skeleton, Alert, Box, Group } from '@mantine/core'
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

          {data.events.length > 0 && (
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
