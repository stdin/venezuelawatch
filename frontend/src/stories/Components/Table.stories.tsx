import type { Meta, StoryObj } from '@storybook/react';
import { Table, type TableColumn } from '../../components/ui/Table';

// Sample entity data
interface Entity {
  id: number;
  name: string;
  riskScore: number;
  sanctioned: boolean;
  pepStatus: boolean;
  lastUpdated: string;
}

// Generate sample data
const generateEntities = (count: number): Entity[] => {
  const names = [
    'Nicolás Maduro',
    'Diosdado Cabello',
    'Vladimir Padrino López',
    'Tareck El Aissami',
    'Delcy Rodríguez',
    'Jorge Rodríguez',
    'Néstor Reverol',
    'Manuel Quevedo',
    'Rafael Lacava',
    'Freddy Bernal',
  ];

  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    name: names[i % names.length] + (i >= 10 ? ` (${Math.floor(i / 10) + 1})` : ''),
    riskScore: Math.floor(Math.random() * 100),
    sanctioned: Math.random() > 0.7,
    pepStatus: Math.random() > 0.5,
    lastUpdated: new Date(Date.now() - Math.random() * 10000000000).toLocaleDateString(),
  }));
};

const basicData = generateEntities(10);
const largeData = generateEntities(150);

// Column definitions
const columns: TableColumn<Entity>[] = [
  {
    key: 'name',
    header: 'Name',
    accessor: (row) => row.name,
    sortable: true,
  },
  {
    key: 'riskScore',
    header: 'Risk Score',
    accessor: (row) => (
      <span
        style={{
          fontWeight: 600,
          color:
            row.riskScore >= 75
              ? 'var(--color-risk-high)'
              : row.riskScore >= 50
              ? 'var(--color-risk-medium)'
              : 'var(--color-risk-low)',
        }}
      >
        {row.riskScore}
      </span>
    ),
    sortable: true,
  },
  {
    key: 'sanctioned',
    header: 'Sanctioned',
    accessor: (row) => (
      <span
        style={{
          display: 'inline-block',
          padding: '2px 8px',
          borderRadius: 'var(--radius-sm)',
          fontSize: 'var(--font-size-xs)',
          fontWeight: 600,
          backgroundColor: row.sanctioned
            ? 'var(--color-risk-high)'
            : 'var(--color-neutral-200)',
          color: row.sanctioned ? 'white' : 'var(--color-text-primary)',
        }}
      >
        {row.sanctioned ? 'Yes' : 'No'}
      </span>
    ),
  },
  {
    key: 'pepStatus',
    header: 'PEP',
    accessor: (row) => (
      <span
        style={{
          display: 'inline-block',
          padding: '2px 8px',
          borderRadius: 'var(--radius-sm)',
          fontSize: 'var(--font-size-xs)',
          fontWeight: 600,
          backgroundColor: row.pepStatus
            ? 'var(--color-risk-medium)'
            : 'var(--color-neutral-200)',
          color: row.pepStatus ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
        }}
      >
        {row.pepStatus ? 'Yes' : 'No'}
      </span>
    ),
  },
  {
    key: 'lastUpdated',
    header: 'Last Updated',
    accessor: (row) => (
      <span style={{ color: 'var(--color-text-secondary)' }}>{row.lastUpdated}</span>
    ),
    sortable: true,
  },
];

const meta = {
  title: 'Components/Table',
  component: Table,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Table>;

export default meta;
type Story = StoryObj<typeof meta>;

export const BasicTable: Story = {
  args: {
    data: basicData,
    columns: columns as TableColumn<unknown>[],
    virtualized: false,
  },
  parameters: {
    docs: {
      description: {
        story:
          'A basic table with 10 rows. No virtualization needed for small datasets. Includes sortable columns and styled data cells.',
      },
    },
  },
};

export const LargeTable: Story = {
  args: {
    data: largeData,
    columns: columns as TableColumn<unknown>[],
    virtualized: true,
    rowHeight: 48,
  },
  parameters: {
    docs: {
      description: {
        story:
          'A large table with 150+ rows using @tanstack/react-virtual for performance. Scroll smoothly through the data without lag. The virtualized prop enables efficient rendering by only displaying visible rows.',
      },
    },
  },
};

export const SortableHeaders: Story = {
  args: {
    data: basicData,
    columns: columns as TableColumn<unknown>[],
    virtualized: false,
  },
  render: () => (
    <div>
      <div
        style={{
          marginBottom: 'var(--spacing-md)',
          padding: 'var(--spacing-md)',
          backgroundColor: 'var(--color-bg-elevated)',
          borderRadius: 'var(--radius-md)',
        }}
      >
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
          Click on column headers (Name, Risk Score, Last Updated) to sort. The sortable columns
          show up/down arrows to indicate sort direction.
        </p>
      </div>
      <Table data={basicData} columns={columns} virtualized={false} />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Demonstrates sortable column headers with visual indicators. Click headers to toggle sort direction.',
      },
    },
  },
};

export const ResponsiveTable: Story = {
  args: {
    data: basicData,
    columns: columns as TableColumn<unknown>[],
    virtualized: false,
  },
  render: () => (
    <div style={{ maxWidth: '600px' }}>
      <div
        style={{
          marginBottom: 'var(--spacing-md)',
          padding: 'var(--spacing-md)',
          backgroundColor: 'var(--color-bg-elevated)',
          borderRadius: 'var(--radius-md)',
        }}
      >
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
          Table is horizontally scrollable on narrow viewports. Try resizing the viewport to see
          the scroll behavior.
        </p>
      </div>
      <Table data={basicData} columns={columns} virtualized={false} />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Table with responsive behavior - horizontal scroll on small viewports to prevent layout breaking.',
      },
    },
  },
};

export const MinimalColumns: Story = {
  args: {
    data: basicData,
    columns: [
      {
        key: 'name',
        header: 'Entity Name',
        accessor: (row: unknown) => (row as Entity).name,
      },
      {
        key: 'riskScore',
        header: 'Score',
        accessor: (row: unknown) => {
          const entity = row as Entity;
          return (
            <strong
              style={{
                color:
                  entity.riskScore >= 75
                    ? 'var(--color-risk-high)'
                    : entity.riskScore >= 50
                    ? 'var(--color-risk-medium)'
                    : 'var(--color-risk-low)',
              }}
            >
              {entity.riskScore}
            </strong>
          );
        },
      },
    ],
    virtualized: false,
  },
  parameters: {
    docs: {
      description: {
        story: 'Table with minimal columns for simpler layouts. Demonstrates flexible column configuration.',
      },
    },
  },
};

export const CustomStyling: Story = {
  args: {
    data: basicData.slice(0, 5),
    columns: columns as TableColumn<unknown>[],
    virtualized: false,
    className: 'custom-table-demo',
  },
  render: (args) => (
    <div>
      <style>
        {`
          .custom-table-demo table {
            border: 2px solid var(--color-border-strong);
          }
          .custom-table-demo thead {
            background: linear-gradient(to bottom, var(--color-bg-elevated), var(--color-neutral-200));
          }
          .custom-table-demo tbody tr:nth-child(even) {
            background: var(--color-bg-elevated);
          }
        `}
      </style>
      <div
        style={{
          marginBottom: 'var(--spacing-md)',
          padding: 'var(--spacing-md)',
          backgroundColor: 'var(--color-bg-elevated)',
          borderRadius: 'var(--radius-md)',
        }}
      >
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
          The Table component accepts a className prop for custom styling. This example shows striped rows and a gradient header.
        </p>
      </div>
      <Table {...args} />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates custom styling capabilities using the className prop.',
      },
    },
  },
};

export const DesignTokens: Story = {
  args: {
    data: basicData.slice(0, 3),
    columns: columns as TableColumn<unknown>[],
    virtualized: false,
  },
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>
      <Table data={basicData.slice(0, 3)} columns={columns} virtualized={false} />
      <div
        style={{
          padding: 'var(--spacing-md)',
          backgroundColor: 'var(--color-bg-elevated)',
          borderRadius: 'var(--radius-md)',
        }}
      >
        <h4
          style={{
            fontSize: 'var(--font-size-md)',
            fontWeight: 600,
            marginBottom: 'var(--spacing-sm)',
            color: 'var(--color-text-primary)',
          }}
        >
          Design Token Integration
        </h4>
        <ul
          style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-secondary)',
            paddingLeft: 'var(--spacing-lg)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--spacing-xs)',
          }}
        >
          <li>
            <strong>Borders:</strong> var(--color-border-default) and var(--color-border-subtle)
          </li>
          <li>
            <strong>Hover:</strong> var(--color-bg-elevated) for row hover state
          </li>
          <li>
            <strong>Header:</strong> var(--color-bg-elevated) background
          </li>
          <li>
            <strong>Spacing:</strong> var(--spacing-md) for cell padding
          </li>
          <li>
            <strong>Typography:</strong> var(--font-size-sm) for table text
          </li>
          <li>
            <strong>Risk colors:</strong> var(--color-risk-high/medium/low) for risk scoring
          </li>
        </ul>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Shows the design tokens used throughout the Table component for consistent theming.',
      },
    },
  },
};

export const VirtualizationComparison: Story = {
  args: {
    data: basicData,
    columns: columns as TableColumn<unknown>[],
    virtualized: false,
  },
  render: () => (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-xl)' }}>
      <div>
        <h4
          style={{
            fontSize: 'var(--font-size-md)',
            fontWeight: 600,
            marginBottom: 'var(--spacing-sm)',
            color: 'var(--color-text-primary)',
          }}
        >
          Without Virtualization (10 rows)
        </h4>
        <p
          style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-secondary)',
            marginBottom: 'var(--spacing-md)',
          }}
        >
          All rows rendered in DOM
        </p>
        <Table data={basicData} columns={columns.slice(0, 3)} virtualized={false} />
      </div>
      <div>
        <h4
          style={{
            fontSize: 'var(--font-size-md)',
            fontWeight: 600,
            marginBottom: 'var(--spacing-sm)',
            color: 'var(--color-text-primary)',
          }}
        >
          With Virtualization (150 rows)
        </h4>
        <p
          style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-secondary)',
            marginBottom: 'var(--spacing-md)',
          }}
        >
          Only visible rows rendered
        </p>
        <Table data={largeData} columns={columns.slice(0, 3)} virtualized={true} />
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Side-by-side comparison showing when to use virtualization. Use virtualized={true} for 100+ rows to maintain performance.',
      },
    },
  },
};
