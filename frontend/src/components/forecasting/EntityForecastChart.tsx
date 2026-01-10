import { useState, useEffect } from 'react'
import { Card, Alert, Badge, Skeleton, Text } from '@mantine/core'
import { Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart } from 'recharts'
import { fetchEntityForecast, type ForecastResponse } from '../../lib/forecasting'
import { format, parseISO, formatDistanceToNow } from 'date-fns'

interface EntityForecastChartProps {
  entityId: string
  historicalData?: Array<{ date: string; risk_score: number }>
}

interface ChartDataPoint {
  date: string
  actual?: number
  forecast?: number
  forecast_lower?: number
  forecast_upper?: number
  type: 'historical' | 'predicted'
}

/**
 * Entity risk forecast chart component
 * Displays historical risk scores (solid line) and predicted future risk (dashed line)
 * with confidence bands (shaded area) showing prediction uncertainty
 */
export function EntityForecastChart({ entityId, historicalData }: EntityForecastChartProps) {
  const [data, setData] = useState<ForecastResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    async function fetchForecast() {
      try {
        setLoading(true)
        setError(null)
        const result = await fetchEntityForecast(entityId, 30)
        if (mounted) {
          setData(result)
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to load forecast')
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    fetchForecast()

    return () => {
      mounted = false
    }
  }, [entityId])

  if (loading) {
    return (
      <Card shadow="sm" padding="lg" radius="md" withBorder>
        <Skeleton height={300} />
      </Card>
    )
  }

  if (data?.status === 'insufficient_data') {
    return (
      <Card shadow="sm" padding="lg" radius="md" withBorder>
        <Alert color="gray" title="Insufficient Data">
          {data.message || 'Need at least 14 days of history to generate forecast'}
        </Alert>
      </Card>
    )
  }

  if (data?.status === 'error' || error) {
    return (
      <Card shadow="sm" padding="lg" radius="md" withBorder>
        <Alert color="red" title="Forecast Error">
          {data?.message || error || 'Unable to generate forecast'}
        </Alert>
      </Card>
    )
  }

  // Combine historical + forecast data
  const chartData: ChartDataPoint[] = [
    ...(historicalData?.map(d => ({
      date: d.date,
      actual: d.risk_score,
      type: 'historical' as const
    })) || []),
    ...(data?.forecast?.map(f => ({
      date: format(parseISO(f.ds), 'yyyy-MM-dd'),
      forecast: f.yhat,
      forecast_lower: f.yhat_lower,
      forecast_upper: f.yhat_upper,
      type: 'predicted' as const
    })) || [])
  ]

  const generatedAgo = data?.generated_at
    ? formatDistanceToNow(parseISO(data.generated_at), { addSuffix: true })
    : null

  return (
    <Card shadow="sm" padding="lg" radius="md" withBorder>
      <Card.Section p="sm" withBorder>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text size="lg" fw={600}>Risk Score Forecast</Text>
          {generatedAgo && (
            <Badge size="sm" variant="light" color="gray">
              Forecast generated {generatedAgo}
            </Badge>
          )}
        </div>
      </Card.Section>

      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--mantine-color-gray-3)" />
          <XAxis
            dataKey="date"
            tickFormatter={(date) => format(parseISO(date), 'MMM dd')}
            stroke="var(--mantine-color-gray-6)"
          />
          <YAxis
            domain={[0, 100]}
            stroke="var(--mantine-color-gray-6)"
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--mantine-color-body)',
              border: '1px solid var(--mantine-color-gray-3)'
            }}
            labelFormatter={(date) => format(parseISO(date as string), 'MMM dd, yyyy')}
          />
          <Legend />

          {/* Confidence band (shaded area) - must come before lines */}
          <Area
            type="monotone"
            dataKey="forecast_upper"
            stroke="none"
            fill="var(--color-risk-high)"
            fillOpacity={0.2}
            name="Confidence Upper"
            legendType="none"
          />
          <Area
            type="monotone"
            dataKey="forecast_lower"
            stroke="none"
            fill="var(--color-risk-high)"
            fillOpacity={0.2}
            name="Confidence Lower"
            legendType="none"
          />

          {/* Historical data line */}
          <Line
            type="monotone"
            dataKey="actual"
            stroke="var(--mantine-color-blue-filled)"
            strokeWidth={2}
            dot={false}
            name="Historical Risk"
            connectNulls={false}
          />

          {/* Forecast line */}
          <Line
            type="monotone"
            dataKey="forecast"
            stroke="var(--color-risk-high)"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            name="Forecasted Risk"
            connectNulls={false}
          />
        </ComposedChart>
      </ResponsiveContainer>

      <Text size="xs" c="dimmed" mt="sm">
        Directional indicator based on historical patterns. Confidence band shows prediction uncertainty.
      </Text>
    </Card>
  )
}
