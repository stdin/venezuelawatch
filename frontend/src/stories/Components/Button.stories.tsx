import type { Meta, StoryObj } from '@storybook/react';
import { Button } from '../../components/ui/Button';

const meta: Meta<typeof Button> = {
  title: 'Components/Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'ghost'],
      description: 'Visual style variant',
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: 'Button size',
    },
    disabled: {
      control: 'boolean',
      description: 'Disabled state',
    },
    asChild: {
      control: 'boolean',
      description: 'Use Slot pattern to render as child element',
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    size: 'md',
    children: 'Primary Button',
  },
};

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    size: 'md',
    children: 'Secondary Button',
  },
};

export const Ghost: Story = {
  args: {
    variant: 'ghost',
    size: 'md',
    children: 'Ghost Button',
  },
};

export const Small: Story = {
  args: {
    variant: 'primary',
    size: 'sm',
    children: 'Small Button',
  },
};

export const Medium: Story = {
  args: {
    variant: 'primary',
    size: 'md',
    children: 'Medium Button',
  },
};

export const Large: Story = {
  args: {
    variant: 'primary',
    size: 'lg',
    children: 'Large Button',
  },
};

export const Disabled: Story = {
  args: {
    variant: 'primary',
    size: 'md',
    disabled: true,
    children: 'Disabled Button',
  },
};

export const AsChild: Story = {
  render: () => (
    <Button variant="primary" size="md" asChild>
      <a href="#" style={{ textDecoration: 'none' }}>
        Link styled as Button
      </a>
    </Button>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'The `asChild` prop uses the Slot pattern to render the button styles on a child element. This is useful for making links look like buttons while maintaining semantic HTML.',
      },
    },
  },
};

export const AllVariants: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: 'var(--spacing-md)', flexWrap: 'wrap' }}>
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="ghost">Ghost</Button>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'All three button variants side by side for comparison.',
      },
    },
  },
};

export const AllSizes: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: 'var(--spacing-md)', alignItems: 'center', flexWrap: 'wrap' }}>
      <Button size="sm">Small</Button>
      <Button size="md">Medium</Button>
      <Button size="lg">Large</Button>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'All three button sizes side by side for comparison.',
      },
    },
  },
};

export const FocusRing: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: 'var(--spacing-md)', flexDirection: 'column' }}>
      <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--spacing-md)' }}>
        Use keyboard (Tab) to navigate between buttons and see the focus ring:
      </p>
      <div style={{ display: 'flex', gap: 'var(--spacing-md)' }}>
        <Button variant="primary">First Button</Button>
        <Button variant="secondary">Second Button</Button>
        <Button variant="ghost">Third Button</Button>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'All buttons include focus-visible rings for keyboard navigation accessibility. The ring color matches the button variant.',
      },
    },
  },
};
