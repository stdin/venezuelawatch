import React from 'react';
import { Card, Text, Badge, Stack, Group } from '@mantine/core';
import { ResponsiveContainer, ComposedChart, Line, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { format, parseISO } from 'date-fns';

interface Event {
  date: string;
  event_type: string;
  severity: string;
  title: string;
  risk_score?: number;
}

interface RiskEventTimelineProps {
  riskData: Array<{ date: string; risk_score: number }>;
  events: Event[];
  title?: string;
}

export const RiskEventTimeline: React.FC<RiskEventTimelineProps> = ({
  riskData,
  events,
  title = 'Risk Score & Events Timeline'
}) => {
  // Merge risk data and events by date
  const chartData = riskData.map(d => {
    const dayEvents = events.filter(e => e.date === d.date);
    return {
      date: d.date,
      risk_score: d.risk_score,
      // Mark severe events for scatter plot
      event_marker: dayEvents.length > 0 ? d.risk_score : null,
      event_count: dayEvents.length,
      events: dayEvents
    };
  });

  // Custom tooltip showing both risk score and events
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;

    const data = payload[0].payload;
    return (
      <div style={{
        backgroundColor: 'var(--mantine-color-body)',
        border: '1px solid var(--mantine-color-gray-3)',
        borderRadius: '4px',
        padding: '8px 12px'
      }}>
        <Text size="sm" fw={600} mb={4}>
          {format(parseISO(data.date), 'MMM dd, yyyy')}
        </Text>
        <Text size="sm">
          Risk Score: <strong>{data.risk_score?.toFixed(1)}</strong>
        </Text>
        {data.events && data.events.length > 0 && (
          <Stack gap={4} mt={8}>
            <Text size="xs" fw={600}>Events ({data.events.length}):</Text>
            {data.events.slice(0, 3).map((e: Event, i: number) => (
              <Group key={i} gap={4}>
                <Badge size="xs" color={
                  e.severity === 'SEV1' ? 'red' :
                  e.severity === 'SEV2' ? 'orange' :
                  e.severity === 'SEV3' ? 'yellow' : 'gray'
                }>
                  {e.event_type}
                </Badge>
                <Text size="xs" lineClamp={1}>{e.title}</Text>
              </Group>
            ))}
            {data.events.length > 3 && (
              <Text size="xs" c="dimmed">+{data.events.length - 3} more</Text>
            )}
          </Stack>
        )}
      </div>
    );
  };

  return (
    <Card padding="md" radius="md">
      <Text size="sm" fw={600} mb="md">{title}</Text>
      <ResponsiveContainer width="100%" height={350}>
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
            label={{ value: 'Risk Score', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />

          {/* Risk score line */}
          <Line
            type="monotone"
            dataKey="risk_score"
            stroke="var(--mantine-color-blue-filled)"
            strokeWidth={2}
            dot={false}
            name="Risk Score"
          />

          {/* Event markers (scatter points on days with events) */}
          <Scatter
            dataKey="event_marker"
            fill="var(--color-risk-high)"
            shape="circle"
            name="Events"
          />
        </ComposedChart>
      </ResponsiveContainer>
      <Text size="xs" c="dimmed" mt="xs">
        Red dots mark days with significant events. Hover for event details.
      </Text>
    </Card>
  );
};
