import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { RiskEvent } from '../lib/types'
import './TrendsPanel.css'

interface TrendsPanelProps {
  events: RiskEvent[]
}

/**
 * Group events by day and calculate average risk score
 */
function groupEventsByDay(events: RiskEvent[]): Array<{ date: string; avgRisk: number }> {
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
      avgRisk: scores.reduce((sum, score) => sum + score, 0) / scores.length,
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
 */
export function TrendsPanel({ events }: TrendsPanelProps) {
  if (!events || events.length === 0) {
    return (
      <div className="trends-panel">
        <div className="trends-empty">No data available</div>
      </div>
    )
  }

  const riskTrendData = groupEventsByDay(events)
  const eventTypeData = countEventsByType(events)

  return (
    <div className="trends-panel">
      {/* Risk Over Time */}
      <div className="trend-section">
        <h3 className="trend-title">Risk Trend (Last 30 Days)</h3>
        <div className="chart-container">
          {riskTrendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={riskTrendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  tickFormatter={(value) => {
                    const date = new Date(value)
                    return `${date.getMonth() + 1}/${date.getDate()}`
                  }}
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  label={{ value: 'Risk Score', angle: -90, position: 'insideLeft', style: { fontSize: 12, fill: '#6b7280' } }}
                />
                <Tooltip
                  contentStyle={{
                    background: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '4px',
                    fontSize: '12px',
                  }}
                  labelFormatter={(value) => new Date(value).toLocaleDateString()}
                  formatter={(value) => [`${(value as number).toFixed(1)}`, 'Avg Risk']}
                />
                <Line
                  type="monotone"
                  dataKey="avgRisk"
                  stroke="#ea580c"
                  strokeWidth={2}
                  dot={{ fill: '#ea580c', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="chart-empty">No risk data for last 30 days</div>
          )}
        </div>
      </div>

      {/* Events by Category */}
      <div className="trend-section">
        <h3 className="trend-title">Events by Category</h3>
        <div className="chart-container">
          {eventTypeData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={eventTypeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="type"
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  label={{ value: 'Count', angle: -90, position: 'insideLeft', style: { fontSize: 12, fill: '#6b7280' } }}
                />
                <Tooltip
                  contentStyle={{
                    background: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '4px',
                    fontSize: '12px',
                  }}
                  formatter={(value) => [`${value}`, 'Events']}
                />
                <Bar dataKey="count" fill="#2563eb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="chart-empty">No event data available</div>
          )}
        </div>
      </div>
    </div>
  )
}
