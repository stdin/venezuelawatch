import { Card, Text, Stack, Title } from '@mantine/core'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { RiskEvent } from '../lib/types'
import RiskTrendChart from './charts/RiskTrendChart'

interface TrendsPanelProps {
  events: RiskEvent[]
}

/**
 * Group events by day and calculate average risk score
 */
function groupEventsByDay(events: RiskEvent[]): Array<{ date: string; riskScore: number }> {
  // Filter to last 30 days
  const thirtyDaysAgo = new Date()
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)

  const recentEvents = events.filter(e => {
    const eventDate = new Date(e.timestamp)
    return eventDate >= thirtyDaysAgo && e.risk_score !== null
  })

  // Group by day
  const groupedByDay = new Map<string, number[]>()

  recentEvents.forEach(event => {
    const date = new Date(event.timestamp)
    const dateKey = date.toISOString().split('T')[0] // YYYY-MM-DD

    if (!groupedByDay.has(dateKey)) {
      groupedByDay.set(dateKey, [])
    }
    groupedByDay.get(dateKey)!.push(event.risk_score!)
  })

  // Calculate averages and sort by date
  const results = Array.from(groupedByDay.entries())
    .map(([date, scores]) => ({
      date,
      riskScore: scores.reduce((sum, score) => sum + score, 0) / scores.length,
    }))
    .sort((a, b) => a.date.localeCompare(b.date))

  return results
}

/**
 * Count events by type
 */
function countEventsByType(events: RiskEvent[]): Array<{ type: string; count: number }> {
  const counts = new Map<string, number>()

  events.forEach(event => {
    const type = event.event_type
    counts.set(type, (counts.get(type) || 0) + 1)
  })

  return Array.from(counts.entries())
    .map(([type, count]) => ({ type, count }))
    .sort((a, b) => b.count - a.count) // Sort by count descending
}

/**
 * Trends panel with risk over time and event distribution charts
 * Uses Mantine Cards and Recharts for data visualization
 */
export function TrendsPanel({ events }: TrendsPanelProps) {
  if (!events || events.length === 0) {
    return (
      <Card padding="md" withBorder>
        <Text c="dimmed" ta="center">No data available</Text>
      </Card>
    )
  }

  const riskTrendData = groupEventsByDay(events)
  const eventTypeData = countEventsByType(events)

  return (
    <Stack gap="md">
      {/* Risk Trend Chart */}
      <Card padding="md" withBorder>
        <Title order={4} mb="md">Risk Trend (Last 30 Days)</Title>
        {riskTrendData.length > 0 ? (
          <RiskTrendChart data={riskTrendData} />
        ) : (
          <Text c="dimmed" ta="center">No risk data for last 30 days</Text>
        )}
      </Card>

      {/* Events by Category Chart */}
      <Card padding="md" withBorder>
        <Title order={4} mb="md">Events by Category</Title>
        {eventTypeData.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={eventTypeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="type" tick={{ fontSize: 12 }} />
              <YAxis
                tick={{ fontSize: 12 }}
                label={{ value: 'Count', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip />
              <Bar dataKey="count" fill="var(--mantine-color-blue-filled)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <Text c="dimmed" ta="center">No event data available</Text>
        )}
      </Card>
    </Stack>
  )
}
