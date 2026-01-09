import type { Meta, StoryObj } from '@storybook/react';

const SpacingBox = ({ token, size }: { token: string; size: string }) => {
  return (
    <div style={{ marginBottom: 'var(--spacing-lg)' }}>
      <div
        style={{
          width: `var(${token})`,
          height: `var(${token})`,
          backgroundColor: 'var(--color-interactive-primary)',
          borderRadius: 'var(--radius-sm)',
        }}
      />
      <div style={{ marginTop: 'var(--spacing-xs)', fontSize: 'var(--font-size-xs)' }}>
        <code>{token}</code>
        <span style={{ color: 'var(--color-text-tertiary)', marginLeft: 'var(--spacing-2xs)' }}>
          ({size})
        </span>
      </div>
    </div>
  );
};

const SpacingDemo = () => {
  return (
    <div style={{ padding: 'var(--spacing-lg)' }}>
      <h1>Spacing Scale</h1>
      <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--spacing-xl)' }}>
        Consistent spacing for margins, padding, and gaps
      </p>

      <section style={{ marginBottom: 'var(--spacing-2xl)' }}>
        <h2 style={{ fontSize: 'var(--font-size-lg)', marginBottom: 'var(--spacing-md)' }}>
          Spacing Tokens
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 'var(--spacing-xl)' }}>
          <SpacingBox token="--spacing-2xs" size="4px" />
          <SpacingBox token="--spacing-xs" size="8px" />
          <SpacingBox token="--spacing-sm" size="12px" />
          <SpacingBox token="--spacing-md" size="16px" />
          <SpacingBox token="--spacing-lg" size="24px" />
          <SpacingBox token="--spacing-xl" size="32px" />
          <SpacingBox token="--spacing-2xl" size="48px" />
          <SpacingBox token="--spacing-3xl" size="64px" />
        </div>
      </section>

      <section style={{ marginBottom: 'var(--spacing-2xl)' }}>
        <h2 style={{ fontSize: 'var(--font-size-lg)', marginBottom: 'var(--spacing-md)' }}>
          Border Radius
        </h2>
        <div style={{ display: 'flex', gap: 'var(--spacing-xl)', flexWrap: 'wrap' }}>
          <div>
            <div
              style={{
                width: '80px',
                height: '80px',
                backgroundColor: 'var(--color-interactive-primary)',
                borderRadius: 'var(--radius-sm)',
              }}
            />
            <code style={{ fontSize: 'var(--font-size-xs)', display: 'block', marginTop: 'var(--spacing-xs)' }}>
              --radius-sm (2px)
            </code>
          </div>
          <div>
            <div
              style={{
                width: '80px',
                height: '80px',
                backgroundColor: 'var(--color-interactive-primary)',
                borderRadius: 'var(--radius-md)',
              }}
            />
            <code style={{ fontSize: 'var(--font-size-xs)', display: 'block', marginTop: 'var(--spacing-xs)' }}>
              --radius-md (6px)
            </code>
          </div>
          <div>
            <div
              style={{
                width: '80px',
                height: '80px',
                backgroundColor: 'var(--color-interactive-primary)',
                borderRadius: 'var(--radius-lg)',
              }}
            />
            <code style={{ fontSize: 'var(--font-size-xs)', display: 'block', marginTop: 'var(--spacing-xs)' }}>
              --radius-lg (8px)
            </code>
          </div>
          <div>
            <div
              style={{
                width: '80px',
                height: '80px',
                backgroundColor: 'var(--color-interactive-primary)',
                borderRadius: 'var(--radius-full)',
              }}
            />
            <code style={{ fontSize: 'var(--font-size-xs)', display: 'block', marginTop: 'var(--spacing-xs)' }}>
              --radius-full
            </code>
          </div>
        </div>
      </section>

      <section>
        <h2 style={{ fontSize: 'var(--font-size-lg)', marginBottom: 'var(--spacing-md)' }}>
          Shadows
        </h2>
        <div style={{ display: 'flex', gap: 'var(--spacing-xl)', flexWrap: 'wrap' }}>
          <div>
            <div
              style={{
                width: '120px',
                height: '120px',
                backgroundColor: 'var(--color-bg-surface)',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-sm)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              SM
            </div>
            <code style={{ fontSize: 'var(--font-size-xs)', display: 'block', marginTop: 'var(--spacing-xs)' }}>
              --shadow-sm
            </code>
          </div>
          <div>
            <div
              style={{
                width: '120px',
                height: '120px',
                backgroundColor: 'var(--color-bg-surface)',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-md)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              MD
            </div>
            <code style={{ fontSize: 'var(--font-size-xs)', display: 'block', marginTop: 'var(--spacing-xs)' }}>
              --shadow-md
            </code>
          </div>
          <div>
            <div
              style={{
                width: '120px',
                height: '120px',
                backgroundColor: 'var(--color-bg-surface)',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-lg)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              LG
            </div>
            <code style={{ fontSize: 'var(--font-size-xs)', display: 'block', marginTop: 'var(--spacing-xs)' }}>
              --shadow-lg
            </code>
          </div>
        </div>
      </section>
    </div>
  );
};

const meta: Meta<typeof SpacingDemo> = {
  title: 'Design Tokens/Spacing',
  component: SpacingDemo,
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const SpacingScale: Story = {};
