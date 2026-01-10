import React from 'react';
import { Card, Text, Tooltip as MantineTooltip } from '@mantine/core';
import styles from './CorrelationHeatmap.module.css';

interface Correlation {
  source: string;
  target: string;
  correlation: number;
  p_adjusted: number;
}

interface CorrelationHeatmapProps {
  correlations: Correlation[];
  variableLabels?: Map<string, string>;
}

export const CorrelationHeatmap: React.FC<CorrelationHeatmapProps> = ({
  correlations,
  variableLabels = new Map()
}) => {
  // Extract unique variables (sorted alphabetically)
  const variables = Array.from(
    new Set(correlations.flatMap(c => [c.source, c.target]))
  ).sort();

  // Build correlation lookup matrix (symmetric)
  const correlationMap = new Map<string, number>();
  correlations.forEach(c => {
    correlationMap.set(`${c.source}-${c.target}`, c.correlation);
    correlationMap.set(`${c.target}-${c.source}`, c.correlation);
  });

  // Get correlation value (symmetric)
  const getCorrelation = (row: string, col: string): number | null => {
    if (row === col) return 1.0;  // Perfect self-correlation
    return correlationMap.get(`${row}-${col}`) ?? null;
  };

  // Color scale: -1 (red) to 0 (white) to +1 (blue)
  const getColor = (value: number | null): string => {
    if (value === null) return 'var(--mantine-color-gray-2)';
    const intensity = Math.abs(value);
    const alpha = 0.1 + intensity * 0.6;  // 0.1 to 0.7
    return value > 0
      ? `rgba(37, 99, 235, ${alpha})`  // Blue (positive)
      : `rgba(220, 38, 38, ${alpha})`;  // Red (negative)
  };

  return (
    <Card padding="md" radius="md">
      <Text size="sm" fw={600} mb="md">Correlation Matrix Heatmap</Text>
      <div className={styles.heatmapContainer}>
        <div
          className={styles.grid}
          style={{
            gridTemplateColumns: `120px repeat(${variables.length}, 1fr)`,
            gridTemplateRows: `30px repeat(${variables.length}, 1fr)`
          }}
        >
          {/* Top-left empty cell */}
          <div className={styles.cellEmpty} />

          {/* Column headers */}
          {variables.map(v => (
            <MantineTooltip key={`col-${v}`} label={variableLabels.get(v) || v}>
              <div className={styles.cellHeader}>
                {(variableLabels.get(v) || v).slice(0, 12)}
              </div>
            </MantineTooltip>
          ))}

          {/* Rows */}
          {variables.map(rowVar => (
            <React.Fragment key={`row-${rowVar}`}>
              {/* Row header */}
              <MantineTooltip label={variableLabels.get(rowVar) || rowVar}>
                <div className={styles.cellHeader}>
                  {(variableLabels.get(rowVar) || rowVar).slice(0, 15)}
                </div>
              </MantineTooltip>

              {/* Data cells */}
              {variables.map(colVar => {
                const value = getCorrelation(rowVar, colVar);
                return (
                  <MantineTooltip
                    key={`${rowVar}-${colVar}`}
                    label={
                      value !== null
                        ? `${variableLabels.get(rowVar) || rowVar} × ${variableLabels.get(colVar) || colVar}: r=${value.toFixed(3)}`
                        : 'No data'
                    }
                  >
                    <div
                      className={styles.cell}
                      style={{ backgroundColor: getColor(value) }}
                    >
                      {value !== null ? value.toFixed(2) : '—'}
                    </div>
                  </MantineTooltip>
                );
              })}
            </React.Fragment>
          ))}
        </div>

        <div className={styles.legend}>
          <Text size="xs" c="dimmed">Correlation:</Text>
          <div className={styles.legendBar}>
            <span className={styles.legendLabel}>-1.0 (strong negative)</span>
            <div className={styles.legendGradient} />
            <span className={styles.legendLabel}>+1.0 (strong positive)</span>
          </div>
        </div>
      </div>
    </Card>
  );
};
