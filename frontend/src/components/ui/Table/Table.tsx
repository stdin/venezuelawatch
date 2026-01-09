import * as React from 'react';
import { Table as MantineTable } from '@mantine/core';

// Table column definition
export interface TableColumn<T> {
  key: string;
  header: string;
  accessor: (row: T) => React.ReactNode;
  sortable?: boolean;
}

// Table props
export interface TableProps<T> {
  data: T[];
  columns: TableColumn<T>[];
  virtualized?: boolean;
  className?: string;
  rowHeight?: number;
}

export function Table<T>({
  data,
  columns,
}: TableProps<T>) {
  const [sortConfig, setSortConfig] = React.useState<{
    key: string;
    direction: 'asc' | 'desc';
  } | null>(null);

  // Handle sort
  const handleSort = (columnKey: string) => {
    const column = columns.find((col) => col.key === columnKey);
    if (!column?.sortable) return;

    setSortConfig((current) => {
      if (current?.key === columnKey) {
        return current.direction === 'asc'
          ? { key: columnKey, direction: 'desc' }
          : null;
      }
      return { key: columnKey, direction: 'asc' };
    });
  };

  return (
    <MantineTable striped highlightOnHover withTableBorder withColumnBorders>
      <MantineTable.Thead>
        <MantineTable.Tr>
          {columns.map((column) => (
            <MantineTable.Th
              key={column.key}
              onClick={() => column.sortable && handleSort(column.key)}
              style={{ cursor: column.sortable ? 'pointer' : 'default' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {column.header}
                {column.sortable && sortConfig?.key === column.key && (
                  <span>{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
                )}
              </div>
            </MantineTable.Th>
          ))}
        </MantineTable.Tr>
      </MantineTable.Thead>
      <MantineTable.Tbody>
        {data.map((row, rowIndex) => (
          <MantineTable.Tr key={rowIndex}>
            {columns.map((column) => (
              <MantineTable.Td key={column.key}>
                {column.accessor(row)}
              </MantineTable.Td>
            ))}
          </MantineTable.Tr>
        ))}
      </MantineTable.Tbody>
    </MantineTable>
  );
}

Table.displayName = 'Table';
