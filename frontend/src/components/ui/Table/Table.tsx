import * as React from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { clsx } from 'clsx';

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
  virtualized = false,
  className,
  rowHeight = 48,
}: TableProps<T>) {
  const parentRef = React.useRef<HTMLDivElement>(null);
  const [sortConfig, setSortConfig] = React.useState<{
    key: string;
    direction: 'asc' | 'desc';
  } | null>(null);

  // Virtual scroller for large datasets
  const virtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => rowHeight,
    enabled: virtualized,
  });

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

  // Render non-virtualized table
  if (!virtualized) {
    return (
      <div className={clsx('overflow-x-auto', className)}>
        <table
          className={clsx(
            'w-full',
            'border-collapse',
            'text-[length:var(--font-size-sm)]'
          )}
        >
          <thead>
            <tr className="border-b border-[var(--color-border-default)]">
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={clsx(
                    'text-left',
                    'p-[var(--spacing-md)]',
                    'font-semibold',
                    'text-[var(--color-text-primary)]',
                    'bg-[var(--color-bg-elevated)]',
                    column.sortable && 'cursor-pointer select-none hover:bg-[var(--color-neutral-200)]'
                  )}
                  onClick={() => column.sortable && handleSort(column.key)}
                  aria-sort={
                    sortConfig?.key === column.key
                      ? sortConfig.direction === 'asc'
                        ? 'ascending'
                        : 'descending'
                      : undefined
                  }
                >
                  <div className="flex items-center gap-[var(--spacing-xs)]">
                    {column.header}
                    {column.sortable && sortConfig?.key === column.key && (
                      <span aria-hidden="true">
                        {sortConfig.direction === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className={clsx(
                  'border-b',
                  'border-[var(--color-border-subtle)]',
                  'hover:bg-[var(--color-bg-elevated)]',
                  'transition-colors'
                )}
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className="p-[var(--spacing-md)] text-[var(--color-text-primary)]"
                  >
                    {column.accessor(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  // Render virtualized table
  const items = virtualizer.getVirtualItems();

  return (
    <div className={clsx('overflow-x-auto', className)}>
      <div className="relative">
        <table
          className={clsx(
            'w-full',
            'border-collapse',
            'text-[length:var(--font-size-sm)]'
          )}
        >
          <thead className="sticky top-0 z-10">
            <tr className="border-b border-[var(--color-border-default)]">
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={clsx(
                    'text-left',
                    'p-[var(--spacing-md)]',
                    'font-semibold',
                    'text-[var(--color-text-primary)]',
                    'bg-[var(--color-bg-elevated)]',
                    column.sortable && 'cursor-pointer select-none hover:bg-[var(--color-neutral-200)]'
                  )}
                  onClick={() => column.sortable && handleSort(column.key)}
                  aria-sort={
                    sortConfig?.key === column.key
                      ? sortConfig.direction === 'asc'
                        ? 'ascending'
                        : 'descending'
                      : undefined
                  }
                >
                  <div className="flex items-center gap-[var(--spacing-xs)]">
                    {column.header}
                    {column.sortable && sortConfig?.key === column.key && (
                      <span aria-hidden="true">
                        {sortConfig.direction === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
        </table>

        <div
          ref={parentRef}
          className="overflow-auto"
          style={{ height: '400px' }}
        >
          <div
            style={{
              height: `${virtualizer.getTotalSize()}px`,
              width: '100%',
              position: 'relative',
            }}
          >
            <table className="w-full border-collapse text-[length:var(--font-size-sm)]">
              <tbody>
                {items.map((virtualRow) => {
                  const row = data[virtualRow.index];
                  return (
                    <tr
                      key={virtualRow.index}
                      className={clsx(
                        'border-b',
                        'border-[var(--color-border-subtle)]',
                        'hover:bg-[var(--color-bg-elevated)]',
                        'transition-colors',
                        'absolute',
                        'top-0',
                        'left-0',
                        'w-full'
                      )}
                      style={{
                        height: `${virtualRow.size}px`,
                        transform: `translateY(${virtualRow.start}px)`,
                      }}
                    >
                      {columns.map((column) => (
                        <td
                          key={column.key}
                          className="p-[var(--spacing-md)] text-[var(--color-text-primary)]"
                        >
                          {column.accessor(row)}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

Table.displayName = 'Table';
