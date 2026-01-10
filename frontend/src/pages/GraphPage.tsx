import { Container, Title, Box, Text } from '@mantine/core'
import { EntityGraph } from '../components/EntityGraph/EntityGraph'

/**
 * Graph page with full-screen entity relationship visualization
 * Shows network visualization of entity connections and risk clusters
 */
export function GraphPage() {
  return (
    <Container fluid style={{ height: 'calc(100vh - 60px)' }}>
      <Box mb="md">
        <Title order={2}>Entity Relationship Graph</Title>
        <Text size="sm" c="dimmed">
          Network visualization of entity connections and risk clusters
        </Text>
      </Box>

      <Box
        style={{
          height: 'calc(100% - 80px)',
          border: '1px solid var(--mantine-color-gray-3)',
          borderRadius: 4,
        }}
      >
        <EntityGraph />
      </Box>
    </Container>
  )
}
