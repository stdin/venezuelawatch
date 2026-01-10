import React, { useState } from 'react';
import { Container, Grid, Card, Title, Text, MultiSelect, Select, NumberInput, Button, Stack, Alert } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { CorrelationGraph } from '../components/CorrelationGraph';

// Available variables for correlation analysis - using Mantine's grouped format
const AVAILABLE_VARIABLES = [
  {
    group: 'Entity Risk',
    items: [
      { value: 'entity_pdvsa_risk', label: 'PDVSA Risk Score' },
      { value: 'entity_maduro_risk', label: 'Maduro Risk Score' },
    ]
  },
  {
    group: 'Economic Indicators',
    items: [
      { value: 'oil_price', label: 'WTI Oil Price' },
      { value: 'inflation', label: 'Venezuela Inflation Rate' },
      { value: 'gdp', label: 'Venezuela GDP' },
      { value: 'exchange_rate', label: 'VEF/USD Exchange Rate' },
    ]
  },
  {
    group: 'Event Counts',
    items: [
      { value: 'sanctions_count', label: 'Sanctions Events/Day' },
      { value: 'political_count', label: 'Political Events/Day' },
      { value: 'humanitarian_count', label: 'Humanitarian Events/Day' },
    ]
  }
];

// Flat list for label mapping
const ALL_VARIABLES = AVAILABLE_VARIABLES.flatMap(g => g.items);

export const CorrelationAnalysis: React.FC = () => {
  const [selectedVariables, setSelectedVariables] = useState<string[]>([]);
  const [method, setMethod] = useState<'pearson' | 'spearman'>('pearson');
  const [minEffectSize, setMinEffectSize] = useState(0.7);
  const [alpha, setAlpha] = useState(0.05);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['correlations', selectedVariables, method, minEffectSize, alpha],
    queryFn: async () => {
      const response = await fetch('/api/correlation/compute/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          variables: selectedVariables,
          start_date: '2024-01-01',  // TODO: Make configurable
          end_date: '2024-12-31',
          method,
          min_effect_size: minEffectSize,
          alpha
        })
      });
      if (!response.ok) throw new Error('Failed to compute correlations');
      return response.json();
    },
    enabled: selectedVariables.length >= 2  // Need at least 2 variables
  });

  // Create variable label map for graph
  const variableLabels = new Map(
    ALL_VARIABLES.map(v => [v.value, v.label])
  );

  return (
    <Container fluid>
      <Title order={1} mb="xl">Correlation & Pattern Analysis</Title>
      <Text c="dimmed" mb="lg">
        Discover relationships between entities, events, and economic data.
        Statistical significance (p &lt; α) and strong effect size (|r| ≥ threshold) required.
      </Text>

      <Grid gutter="md">
        {/* Controls column */}
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card padding="lg" radius="md">
            <Stack gap="md">
              <div>
                <Text size="sm" fw={600} mb="xs">Select Variables (min 2)</Text>
                <MultiSelect
                  data={AVAILABLE_VARIABLES}
                  value={selectedVariables}
                  onChange={setSelectedVariables}
                  searchable
                  clearable
                  placeholder="Choose variables to correlate"
                  maxDropdownHeight={300}
                />
              </div>

              <div>
                <Text size="sm" fw={600} mb="xs">Correlation Method</Text>
                <Select
                  value={method}
                  onChange={(v) => setMethod(v as 'pearson' | 'spearman')}
                  data={[
                    { value: 'pearson', label: 'Pearson (linear relationships)' },
                    { value: 'spearman', label: 'Spearman (monotonic relationships)' }
                  ]}
                />
                <Text size="xs" c="dimmed" mt={4}>
                  Pearson for linear, Spearman for ranked/ordinal data
                </Text>
              </div>

              <div>
                <Text size="sm" fw={600} mb="xs">Min Correlation Strength</Text>
                <NumberInput
                  value={minEffectSize}
                  onChange={(v) => setMinEffectSize(Number(v))}
                  min={0.5}
                  max={1.0}
                  step={0.05}
                  decimalScale={2}
                />
                <Text size="xs" c="dimmed" mt={4}>
                  Only show correlations with |r| ≥ {minEffectSize} (0.7+ = strong)
                </Text>
              </div>

              <div>
                <Text size="sm" fw={600} mb="xs">Significance Level (α)</Text>
                <NumberInput
                  value={alpha}
                  onChange={(v) => setAlpha(Number(v))}
                  min={0.01}
                  max={0.10}
                  step={0.01}
                  decimalScale={2}
                />
                <Text size="xs" c="dimmed" mt={4}>
                  P-value threshold after Bonferroni correction
                </Text>
              </div>

              <Button
                onClick={() => refetch()}
                loading={isLoading}
                disabled={selectedVariables.length < 2}
                fullWidth
              >
                Compute Correlations
              </Button>

              {data && (
                <Alert color="blue" title="Results">
                  <Text size="sm">Tested: {data.n_tested} pairs</Text>
                  <Text size="sm">Significant: {data.n_significant} pairs</Text>
                  <Text size="xs">Bonferroni threshold: p &lt; {data.bonferroni_threshold.toFixed(6)}</Text>
                </Alert>
              )}

              {error && (
                <Alert color="red" title="Error">
                  Failed to compute correlations. Check backend logs.
                </Alert>
              )}
            </Stack>
          </Card>
        </Grid.Col>

        {/* Graph column */}
        <Grid.Col span={{ base: 12, md: 8 }}>
          {!data ? (
            <Card padding="lg" radius="md" style={{ minHeight: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Text c="dimmed">Select at least 2 variables and click "Compute Correlations" to begin</Text>
            </Card>
          ) : (
            <CorrelationGraph
              correlations={data.correlations}
              variableLabels={variableLabels}
            />
          )}
        </Grid.Col>
      </Grid>
    </Container>
  );
};
