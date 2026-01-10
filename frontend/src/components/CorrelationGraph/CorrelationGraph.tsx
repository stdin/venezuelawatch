import React, { useMemo } from 'react';
import { GraphCanvas, type GraphNode, type GraphEdge } from 'reagraph';
import { Card, Slider, Text, Group, Badge, Stack } from '@mantine/core';

interface Correlation {
  source: string;
  target: string;
  correlation: number;
  p_adjusted: number;
  sample_size: number;
  warnings?: string[];
}

interface CorrelationGraphProps {
  correlations: Correlation[];
  variableLabels?: Map<string, string>;  // Map variable IDs to display labels
}

export const CorrelationGraph: React.FC<CorrelationGraphProps> = ({
  correlations,
  variableLabels = new Map()
}) => {
  const [minCorrelation, setMinCorrelation] = React.useState(0.7);
  const [selectedNode, setSelectedNode] = React.useState<string | null>(null);
  const [selectedEdge, setSelectedEdge] = React.useState<Correlation | null>(null);

  // Transform correlation data to Reagraph format
  const { nodes, edges } = useMemo(() => {
    // Filter by correlation strength
    const filtered = correlations.filter(c => Math.abs(c.correlation) >= minCorrelation);

    // Extract unique variables as nodes
    const variableSet = new Set<string>();
    filtered.forEach(c => {
      variableSet.add(c.source);
      variableSet.add(c.target);
    });

    const nodes: GraphNode[] = Array.from(variableSet).map(v => {
      const degree = filtered.filter(c => c.source === v || c.target === v).length;
      return {
        id: v,
        label: variableLabels.get(v) || v,
        // Node size based on degree centrality (number of connections)
        size: Math.max(10, degree * 3),
        // Color by variable type
        fill: v.startsWith('entity_') ? 'var(--mantine-color-blue-filled)' :
              v.endsWith('_count') ? 'var(--color-risk-high)' :
              'var(--mantine-color-grape-filled)'  // Economic indicators
      };
    });

    const edges: GraphEdge[] = filtered.map((c, i) => ({
      id: `edge-${i}`,
      source: c.source,
      target: c.target,
      label: `r=${c.correlation.toFixed(2)}`,
      // Edge color: blue for positive, red for negative correlation
      fill: c.correlation > 0 ? 'var(--mantine-color-blue-6)' : 'var(--color-risk-high)',
      // Edge thickness based on correlation strength
      size: Math.abs(c.correlation) * 5,
      data: c  // Store full correlation data for onClick
    }));

    return { nodes, edges };
  }, [correlations, minCorrelation, variableLabels]);

  return (
    <Stack gap="md">
      <Card padding="md" radius="md">
        <Group justify="space-between" mb="xs">
          <Text size="sm" fw={600}>Correlation Strength Filter</Text>
          <Badge color="blue">{nodes.length} variables, {edges.length} correlations</Badge>
        </Group>
        <Slider
          value={minCorrelation}
          onChange={setMinCorrelation}
          min={0.5}
          max={1.0}
          step={0.05}
          marks={[
            { value: 0.5, label: '0.5' },
            { value: 0.7, label: '0.7' },
            { value: 0.9, label: '0.9' }
          ]}
          label={(value) => `|r| ≥ ${value.toFixed(2)}`}
        />
        <Text size="xs" c="dimmed" mt="xs">
          Showing only correlations with absolute value above {minCorrelation.toFixed(2)}
        </Text>
      </Card>

      <Card padding="md" radius="md" style={{ height: '600px', position: 'relative' }}>
        {nodes.length === 0 ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%'
          }}>
            <Text c="dimmed">No correlations above threshold. Try lowering the filter.</Text>
          </div>
        ) : (
          <GraphCanvas
            nodes={nodes}
            edges={edges}
            layoutType="forceDirected2d"
            layoutOverrides={{
              linkDistance: 150,
              nodeStrength: -800,
              clusterStrength: 0.3
            }}
            draggable
            edgeInterpolation="curved"
            sizingType="centrality"
            labelType="auto"
            onNodeClick={(node) => {
              setSelectedNode(node.id);
              setSelectedEdge(null);
            }}
            onEdgeClick={(edge) => {
              const correlation = correlations.find(
                c => (c.source === edge.source && c.target === edge.target) ||
                     (c.source === edge.target && c.target === edge.source)
              );
              if (correlation) {
                setSelectedEdge(correlation);
                setSelectedNode(null);
              }
            }}
          />
        )}
      </Card>

      {/* Detail panel for selected node or edge */}
      {selectedNode && (
        <Card padding="md" radius="md">
          <Text size="sm" fw={600} mb="xs">Variable: {variableLabels.get(selectedNode) || selectedNode}</Text>
          <Text size="xs" c="dimmed">
            Connected to {edges.filter(e => e.source === selectedNode || e.target === selectedNode).length} other variables
          </Text>
        </Card>
      )}

      {selectedEdge && (
        <Card padding="md" radius="md">
          <Text size="sm" fw={600} mb="xs">Correlation Details</Text>
          <Group gap="xs">
            <Badge color={selectedEdge.correlation > 0 ? 'blue' : 'red'}>
              r = {selectedEdge.correlation.toFixed(3)}
            </Badge>
            <Badge color="gray">
              p = {selectedEdge.p_adjusted.toExponential(2)}
            </Badge>
            <Badge color="gray">
              n = {selectedEdge.sample_size}
            </Badge>
          </Group>
          {selectedEdge.warnings && selectedEdge.warnings.length > 0 && (
            <Text size="xs" c="orange" mt="xs">
              ⚠ {selectedEdge.warnings.join('; ')}
            </Text>
          )}
        </Card>
      )}
    </Stack>
  );
};
