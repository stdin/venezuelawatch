import type { Meta, StoryObj } from '@storybook/react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';

const meta: Meta<typeof Card.Root> = {
  title: 'Components/Card',
  component: Card.Root,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div style={{ width: '400px' }}>
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Card.Root>
      <Card.Header>
        <Card.Title>Card Title</Card.Title>
        <Card.Description>
          This is a description that provides additional context about the card content.
        </Card.Description>
      </Card.Header>
      <Card.Content>
        <p style={{ color: 'var(--color-text-primary)' }}>
          This is the main content area of the card. It can contain any type of content
          including text, images, forms, or other components.
        </p>
      </Card.Content>
      <Card.Footer>
        <Button variant="primary" size="sm">
          Action
        </Button>
        <Button variant="ghost" size="sm">
          Cancel
        </Button>
      </Card.Footer>
    </Card.Root>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'A complete card with all parts: Header with Title and Description, Content area, and Footer with actions.',
      },
    },
  },
};

export const HeaderOnly: Story = {
  render: () => (
    <Card.Root>
      <Card.Header>
        <Card.Title>Card with Header Only</Card.Title>
        <Card.Description>
          This card demonstrates using just the header section without content or footer.
        </Card.Description>
      </Card.Header>
    </Card.Root>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Card with only a header section - useful for simple informational cards.',
      },
    },
  },
};

export const ContentOnly: Story = {
  render: () => (
    <Card.Root>
      <Card.Content>
        <h4
          style={{
            fontSize: 'var(--font-size-md)',
            fontWeight: 600,
            marginBottom: 'var(--spacing-sm)',
            color: 'var(--color-text-primary)',
          }}
        >
          Flexible Content
        </h4>
        <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--spacing-md)' }}>
          The compound pattern allows you to use only the parts you need. This card uses Content
          directly without a Header or Footer.
        </p>
        <ul style={{ color: 'var(--color-text-primary)', paddingLeft: 'var(--spacing-lg)' }}>
          <li>Full control over structure</li>
          <li>No unnecessary markup</li>
          <li>Design token integration</li>
        </ul>
      </Card.Content>
    </Card.Root>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Card with only content - demonstrates the flexibility of the compound component pattern.',
      },
    },
  },
};

export const WithFooter: Story = {
  render: () => (
    <Card.Root>
      <Card.Header>
        <Card.Title>Risk Assessment Report</Card.Title>
        <Card.Description>Compliance check completed on 2026-01-09</Card.Description>
      </Card.Header>
      <Card.Content>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              color: 'var(--color-text-primary)',
            }}
          >
            <span>Risk Score:</span>
            <strong style={{ color: 'var(--color-risk-medium)' }}>Medium (65/100)</strong>
          </div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              color: 'var(--color-text-primary)',
            }}
          >
            <span>Sanctions:</span>
            <strong>No matches found</strong>
          </div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              color: 'var(--color-text-primary)',
            }}
          >
            <span>PEP Status:</span>
            <strong style={{ color: 'var(--color-risk-high)' }}>Flagged</strong>
          </div>
        </div>
      </Card.Content>
      <Card.Footer style={{ justifyContent: 'space-between' }}>
        <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
          Last updated: 2 hours ago
        </span>
        <div style={{ display: 'flex', gap: 'var(--spacing-xs)' }}>
          <Button variant="secondary" size="sm">
            View Details
          </Button>
          <Button variant="primary" size="sm">
            Export
          </Button>
        </div>
      </Card.Footer>
    </Card.Root>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Card with footer demonstrating a real-world use case with risk data and action buttons.',
      },
    },
  },
};

export const MultipleCards: Story = {
  render: () => (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-md)', width: '800px' }}>
      <Card.Root>
        <Card.Header>
          <Card.Title>High Risk</Card.Title>
          <Card.Description>Entities requiring immediate review</Card.Description>
        </Card.Header>
        <Card.Content>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--color-risk-high)' }}>
            23
          </div>
        </Card.Content>
      </Card.Root>

      <Card.Root>
        <Card.Header>
          <Card.Title>Medium Risk</Card.Title>
          <Card.Description>Entities under monitoring</Card.Description>
        </Card.Header>
        <Card.Content>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--color-risk-medium)' }}>
            145
          </div>
        </Card.Content>
      </Card.Root>

      <Card.Root>
        <Card.Header>
          <Card.Title>Low Risk</Card.Title>
          <Card.Description>Entities with clean status</Card.Description>
        </Card.Header>
        <Card.Content>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--color-risk-low)' }}>
            892
          </div>
        </Card.Content>
      </Card.Root>

      <Card.Root>
        <Card.Header>
          <Card.Title>Total Tracked</Card.Title>
          <Card.Description>All entities in database</Card.Description>
        </Card.Header>
        <Card.Content>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--color-text-primary)' }}>
            1,060
          </div>
        </Card.Content>
      </Card.Root>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Multiple cards in a grid layout demonstrating dashboard-style data visualization.',
      },
    },
  },
};

export const DesignTokens: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
      <Card.Root>
        <Card.Content>
          <h4 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, marginBottom: 'var(--spacing-sm)', color: 'var(--color-text-primary)' }}>
            Design Token Integration
          </h4>
          <ul style={{ color: 'var(--color-text-secondary)', paddingLeft: 'var(--spacing-lg)', display: 'flex', flexDirection: 'column', gap: 'var(--spacing-xs)' }}>
            <li><strong>Border:</strong> var(--color-border-default)</li>
            <li><strong>Background:</strong> var(--color-bg-surface)</li>
            <li><strong>Border Radius:</strong> var(--radius-md) = 4px</li>
            <li><strong>Shadow:</strong> var(--shadow-sm)</li>
            <li><strong>Spacing:</strong> var(--spacing-lg) padding</li>
          </ul>
        </Card.Content>
      </Card.Root>
      <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', maxWidth: '400px' }}>
        All styling uses design tokens for consistency and theme support. The reduced border radius (4px) was adjusted in Phase 8 based on user feedback.
      </p>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates the design tokens used in the Card component for consistent theming.',
      },
    },
  },
};
