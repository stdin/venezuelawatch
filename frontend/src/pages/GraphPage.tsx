import { Container, Title, Box, Text, Stack } from '@mantine/core'
import { useState } from 'react'
import { EntityGraph } from '../components/EntityGraph/EntityGraph'
import { ThemeFilter } from '../components/EntityGraph/ThemeFilter'

/**
 * Graph page with full-screen entity relationship visualization
 * Shows network visualization of entity connections and risk clusters
 */
export function GraphPage() {
  const [selectedThemes, setSelectedThemes] = useState<string[]>([])

  return (
    <Container fluid style={{ height: 'calc(100vh - 60px)' }}>
      <Stack gap="md" style={{ height: '100%' }}>
        <Box>
          <Title order={2}>Entity Relationship Graph</Title>
          <Text size="sm" c="dimmed">
            Network visualization of entity connections and risk clusters
          </Text>
        </Box>

        <Box>
          <Text size="sm" fw={500} mb="xs">
            Filter by Theme:
          </Text>
          <ThemeFilter selectedThemes={selectedThemes} onChange={setSelectedThemes} />
          {selectedThemes.length > 0 && (
            <Text size="xs" c="dimmed" mt="xs">
              Showing relationships in {selectedThemes.length} categor{selectedThemes.length === 1 ? 'y' : 'ies'}
            </Text>
          )}
        </Box>

        <Box
          style={{
            flex: 1,
            border: '1px solid var(--mantine-color-gray-3)',
            borderRadius: 4,
          }}
        >
          <EntityGraph selectedThemes={selectedThemes} />
        </Box>
      </Stack>
    </Container>
  )
}
