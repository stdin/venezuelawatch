import type { Meta, StoryObj } from '@storybook/react';

const ColorSwatch = ({ label, token, value }: { label: string; token: string; value?: string }) => {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)' }}>
      <div
        style={{
          width: '80px',
          height: '80px',
          backgroundColor: `var(${token})`,
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border-default)',
          boxShadow: 'var(--shadow-sm)',
        }}
      />
      <div>
        <div style={{ fontWeight: 'var(--font-weight-medium)', marginBottom: 'var(--spacing-2xs)' }}>
          {label}
        </div>
        <code style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-tertiary)' }}>
          {token}
        </code>
        {value && (
          <div style={{ fontSize: 'var(--font-size-2xs)', color: 'var(--color-text-tertiary)', marginTop: '2px' }}>
            {value}
          </div>
        )}
      </div>
    </div>
  );
};

const ColorsDemo = () => {
  return (
    <div style={{ padding: 'var(--spacing-lg)' }}>
      <h1>Color Palette</h1>
      <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--spacing-xl)' }}>
        OKLCH color space - Perceptually uniform with predictable contrast
      </p>

      <section style={{ marginBottom: 'var(--spacing-2xl)' }}>
        <h2 style={{ fontSize: 'var(--font-size-lg)', marginBottom: 'var(--spacing-md)' }}>
          Risk Palette
        </h2>
        <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--spacing-lg)' }}>
          Semantic colors for risk intelligence (WCAG 4.5:1+ on white)
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 'var(--spacing-lg)' }}>
          <ColorSwatch label="Critical Risk" token="--color-risk-critical" value="oklch(0.577 0.245 27.325)" />
          <ColorSwatch label="High Risk" token="--color-risk-high" value="oklch(0.637 0.245 27.325)" />
          <ColorSwatch label="Medium Risk" token="--color-risk-medium" value="oklch(0.795 0.184 86.047)" />
          <ColorSwatch label="Low Risk" token="--color-risk-low" value="oklch(0.723 0.219 149.579)" />
          <ColorSwatch label="Minimal Risk" token="--color-risk-minimal" value="oklch(0.871 0.15 154.449)" />
          <ColorSwatch label="No Risk" token="--color-risk-none" value="oklch(0.906 0.095 163.23)" />
        </div>
      </section>

      <section style={{ marginBottom: 'var(--spacing-2xl)' }}>
        <h2 style={{ fontSize: 'var(--font-size-lg)', marginBottom: 'var(--spacing-md)' }}>
          Neutral Scale
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 'var(--spacing-lg)' }}>
          <ColorSwatch label="Neutral 50" token="--color-neutral-50" />
          <ColorSwatch label="Neutral 100" token="--color-neutral-100" />
          <ColorSwatch label="Neutral 200" token="--color-neutral-200" />
          <ColorSwatch label="Neutral 300" token="--color-neutral-300" />
          <ColorSwatch label="Neutral 500" token="--color-neutral-500" />
          <ColorSwatch label="Neutral 700" token="--color-neutral-700" />
          <ColorSwatch label="Neutral 900" token="--color-neutral-900" />
        </div>
      </section>

      <section>
        <h2 style={{ fontSize: 'var(--font-size-lg)', marginBottom: 'var(--spacing-md)' }}>
          Semantic Tokens
        </h2>
        <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--spacing-lg)' }}>
          Purpose-based tokens that adapt to theme
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 'var(--spacing-lg)' }}>
          <ColorSwatch label="Text Primary" token="--color-text-primary" />
          <ColorSwatch label="Text Secondary" token="--color-text-secondary" />
          <ColorSwatch label="Background Page" token="--color-bg-page" />
          <ColorSwatch label="Background Surface" token="--color-bg-surface" />
          <ColorSwatch label="Border Default" token="--color-border-default" />
          <ColorSwatch label="Interactive Primary" token="--color-interactive-primary" />
        </div>
      </section>
    </div>
  );
};

const meta: Meta<typeof ColorsDemo> = {
  title: 'Design Tokens/Colors',
  component: ColorsDemo,
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const RiskFirstPalette: Story = {};
