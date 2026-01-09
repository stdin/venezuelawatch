import { makeAssistantToolUI } from '@assistant-ui/react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import './RiskTrendsChart.css'

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
 * Get risk level color based on score
 */
function getRiskColor(score: number): string {
  if (score >= 70) return '#dc2626'
  if (score >= 50) return '#f59e0b'
  if (score >= 30) return '#eab308'
  return '#10b981'
}

/**
 * Risk trends chart card
 */
const RiskTrendsChartContent = ({ result }: { result: RiskTrendsResult }) => {
  if (!result.trends || result.trends.length === 0) {
    return (
      <div className="risk-trends-empty">
        No risk trend data available for the specified period.
      </div>
    )
  }

  // Calculate average risk for gradient coloring
  const avgRisk =
    result.trends.reduce((sum, t) => sum + t.avg_risk_score, 0) / result.trends.length

  return (
    <div className="risk-trends-card">
      <div className="risk-trends-header">
        <h3 className="risk-trends-title">Risk Score Trends</h3>
        <span className="risk-trends-period">
          {formatDate(result.date_range.from)} - {formatDate(result.date_range.to)}
        </span>
      </div>

      <div className="risk-trends-chart-container">
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
              formatter={(value: number, name: string, props: any) => {
                if (name === 'avg_risk_score') {
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
                return [value, name]
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
      </div>

      <div className="risk-trends-summary">
        <div className="risk-trends-stat">
          <span className="risk-trends-stat-label">Avg Risk:</span>
          <span
            className="risk-trends-stat-value"
            style={{ color: getRiskColor(avgRisk) }}
          >
            {avgRisk.toFixed(1)}
          </span>
        </div>
        <div className="risk-trends-stat">
          <span className="risk-trends-stat-label">Data Points:</span>
          <span className="risk-trends-stat-value">{result.count}</span>
        </div>
        {result.trends.length > 0 && (
          <div className="risk-trends-stat">
            <span className="risk-trends-stat-label">Total Events:</span>
            <span className="risk-trends-stat-value">
              {result.trends.reduce((sum, t) => sum + t.event_count, 0)}
            </span>
          </div>
        )}
      </div>
    </div>
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
