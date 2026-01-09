import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'
import { format } from 'date-fns'

interface RiskTrendChartProps {
  data: Array<{ date: string; riskScore: number }>
}

/**
 * Risk trend line chart showing risk score over time
 * Uses Recharts for production-ready data visualization
 */
export default function RiskTrendChart({ data }: RiskTrendChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="date"
          tickFormatter={(value) => format(new Date(value), 'MM/dd')}
        />
        <YAxis domain={[0, 100]} label={{ value: 'Risk Score', angle: -90, position: 'insideLeft' }} />
        <Tooltip
          formatter={(value: number) => [value.toFixed(1), 'Risk Score']}
          labelFormatter={(label) => format(new Date(label), 'MMM dd, yyyy')}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="riskScore"
          stroke="var(--color-risk-high)"
          strokeWidth={2}
          dot={false}
          name="Risk Score"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
