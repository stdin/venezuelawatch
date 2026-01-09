import type { Meta, StoryObj } from '@storybook/react';

const TypographyDemo = () => {
  return (
    <div style={{ padding: 'var(--spacing-lg)' }}>
      <h1>Typography Scale</h1>
      <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--spacing-xl)' }}>
        Modular ratio: 1.25 (Major Third) - Optimized for data scanning
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>
        <div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'var(--font-weight-semibold)', lineHeight: 'var(--line-height-tight)' }}>
            Display 2XL (39px)
          </div>
          <code style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-xs)' }}>
            --font-size-2xl: 2.441rem
          </code>
        </div>

        <div>
          <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'var(--font-weight-semibold)', lineHeight: 'var(--line-height-tight)' }}>
            Heading XL (31px) - Page titles
          </div>
          <code style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-xs)' }}>
            --font-size-xl: 1.953rem
          </code>
        </div>

        <div>
          <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-semibold)', lineHeight: 'var(--line-height-tight)' }}>
            Heading LG (25px) - Section headings
          </div>
          <code style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-xs)' }}>
            --font-size-lg: 1.563rem
          </code>
        </div>

        <div>
          <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 'var(--font-weight-semibold)' }}>
            Heading MD (20px) - Card titles, small headings
          </div>
          <code style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-xs)' }}>
            --font-size-md: 1.25rem
          </code>
        </div>

        <div>
          <div style={{ fontSize: 'var(--font-size-sm)', lineHeight: 'var(--line-height-normal)' }}>
            Body SM (16px) - Base body text, event descriptions
          </div>
          <code style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-xs)' }}>
            --font-size-sm: 1rem (BASE)
          </code>
        </div>

        <div>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
            Caption XS (13px) - Labels, captions, table headers
          </div>
          <code style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-xs)' }}>
            --font-size-xs: 0.8rem
          </code>
        </div>

        <div>
          <div style={{ fontSize: 'var(--font-size-2xs)', color: 'var(--color-text-tertiary)' }}>
            Fine print 2XS (10px) - Metadata, timestamps
          </div>
          <code style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-xs)' }}>
            --font-size-2xs: 0.64rem
          </code>
        </div>
      </div>

      <div style={{ marginTop: 'var(--spacing-2xl)' }}>
        <h2 style={{ fontSize: 'var(--font-size-lg)', marginBottom: 'var(--spacing-md)' }}>Font Weights</h2>
        <div style={{ display: 'flex', gap: 'var(--spacing-xl)' }}>
          <div>
            <div style={{ fontWeight: 'var(--font-weight-normal)' }}>Normal (400)</div>
            <code style={{ fontSize: 'var(--font-size-xs)' }}>--font-weight-normal</code>
          </div>
          <div>
            <div style={{ fontWeight: 'var(--font-weight-medium)' }}>Medium (500)</div>
            <code style={{ fontSize: 'var(--font-size-xs)' }}>--font-weight-medium</code>
          </div>
          <div>
            <div style={{ fontWeight: 'var(--font-weight-semibold)' }}>Semibold (600)</div>
            <code style={{ fontSize: 'var(--font-size-xs)' }}>--font-weight-semibold</code>
          </div>
          <div>
            <div style={{ fontWeight: 'var(--font-weight-bold)' }}>Bold (700)</div>
            <code style={{ fontSize: 'var(--font-size-xs)' }}>--font-weight-bold</code>
          </div>
        </div>
      </div>
    </div>
  );
};

const meta: Meta<typeof TypographyDemo> = {
  title: 'Design Tokens/Typography',
  component: TypographyDemo,
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const TypeScale: Story = {};
