import { makeAssistantToolUI } from '@assistant-ui/react'
import { Card, Text, Title, Group, Stack } from '@mantine/core'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

/**
 * Types matching backend analyze_risk_trends tool
 */
interface RiskTrendsArgs {
  days_back?: number
  event_types?: string
}

interface RiskTrendsResult {
  trends: Array<{
    date: string
    avg_risk_score: number
    event_count: number
  }>
  count: number
  date_range: {
    from: string
    to: string
  }
}

/**
 * Format date for display
 */
function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

/**
 * Format date for tooltip
 */
function formatTooltipDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

/**
 * Get risk level color based on score (using design tokens)
 */
function getRiskColor(score: number): string {
  if (score >= 75) return 'var(--color-risk-high)'
  if (score >= 50) return 'var(--color-risk-medium)'
  return 'var(--mantine-color-blue-filled)'
}

/**
 * Risk trends chart card
 */
const RiskTrendsChartContent = ({ result }: { result: RiskTrendsResult }) => {
  if (!result.trends || result.trends.length === 0) {
    return (
      <Card size="sm" padding="md" withBorder>
        <Text c="dimmed" ta="center">
          No risk trend data available for the specified period.
        </Text>
      </Card>
    )
  }

  // Calculate average risk for gradient coloring
  const avgRisk =
    result.trends.reduce((sum, t) => sum + t.avg_risk_score, 0) / result.trends.length

  return (
    <Card size="sm" padding="md" withBorder>
      <Stack gap="xs">
        <Group justify="space-between" align="center">
          <Title order={4}>Risk Score Trends</Title>
          <Text size="sm" c="dimmed">
            {formatDate(result.date_range.from)} - {formatDate(result.date_range.to)}
          </Text>
        </Group>

        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={result.trends} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: '#6b7280' }}
              tickFormatter={formatDate}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fontSize: 10, fill: '#6b7280' }}
              label={{
                value: 'Risk Score',
                angle: -90,
                position: 'insideLeft',
                style: { fontSize: 10, fill: '#6b7280' },
              }}
            />
            <Tooltip
              contentStyle={{
                background: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                fontSize: '11px',
                padding: '8px',
              }}
              labelFormatter={formatTooltipDate}
              formatter={(value: number | undefined, name: string | undefined, props: any) => {
                if (name === 'avg_risk_score' && value !== undefined) {
                  return [
                    <>
                      <span style={{ color: getRiskColor(value), fontWeight: 600 }}>
                        {value.toFixed(1)}
                      </span>
                      {props.payload.event_count && (
                        <span style={{ color: '#6b7280', marginLeft: '4px' }}>
                          ({props.payload.event_count} events)
                        </span>
                      )}
                    </>,
                    'Avg Risk',
                  ]
                }
                return [value ?? 0, name ?? '']
              }}
            />
            <Line
              type="monotone"
              dataKey="avg_risk_score"
              stroke={getRiskColor(avgRisk)}
              strokeWidth={2}
              dot={{ fill: getRiskColor(avgRisk), r: 3 }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>

        <Group gap="md" justify="space-between">
          <Group gap="xs">
            <Text size="sm" c="dimmed">Avg Risk:</Text>
            <Text size="sm" fw={600} style={{ color: getRiskColor(avgRisk) }}>
              {avgRisk.toFixed(1)}
            </Text>
          </Group>
          <Group gap="xs">
            <Text size="sm" c="dimmed">Data Points:</Text>
            <Text size="sm" fw={600}>{result.count}</Text>
          </Group>
          {result.trends.length > 0 && (
            <Group gap="xs">
              <Text size="sm" c="dimmed">Total Events:</Text>
              <Text size="sm" fw={600}>
                {result.trends.reduce((sum, t) => sum + t.event_count, 0)}
              </Text>
            </Group>
          )}
        </Group>
      </Stack>
    </Card>
  )
}

/**
 * Tool UI component for analyze_risk_trends tool
 */
export const RiskTrendsChart = makeAssistantToolUI<RiskTrendsArgs, RiskTrendsResult>({
  toolName: 'analyze_risk_trends',
  render: ({ result }) => {
    if (!result) return null
    return <RiskTrendsChartContent result={result} />
  },
})
