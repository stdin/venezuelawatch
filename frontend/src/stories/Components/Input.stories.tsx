import type { Meta, StoryObj } from 'storybook/internal/types';
import { Input } from '../../components/ui/Input';

const meta: Meta<typeof Input> = {
  title: 'Components/Input',
  component: Input,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    label: {
      control: 'text',
      description: 'Label text for the input',
    },
    error: {
      control: 'boolean',
      description: 'Error state styling',
    },
    helperText: {
      control: 'text',
      description: 'Helper or error message below input',
    },
    disabled: {
      control: 'boolean',
      description: 'Disabled state',
    },
    placeholder: {
      control: 'text',
      description: 'Placeholder text',
    },
  },
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
  args: {
    placeholder: 'Enter text...',
  },
};

export const WithLabel: Story = {
  args: {
    label: 'Email Address',
    placeholder: 'you@example.com',
  },
};

export const WithHelperText: Story = {
  args: {
    label: 'Username',
    placeholder: 'Choose a username',
    helperText: 'Must be 3-20 characters',
  },
};

export const WithError: Story = {
  args: {
    label: 'Email Address',
    placeholder: 'you@example.com',
    error: true,
    helperText: 'Please enter a valid email address',
  },
};

export const Disabled: Story = {
  args: {
    label: 'Disabled Input',
    placeholder: 'Cannot edit',
    disabled: true,
  },
};

export const DisabledWithValue: Story = {
  args: {
    label: 'Disabled Input',
    value: 'Read-only value',
    disabled: true,
  },
};

export const AllStates: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-xl)', width: '400px' }}>
      <Input label="Default State" placeholder="Enter text..." />
      <Input label="With Helper Text" placeholder="Enter text..." helperText="This is helper text" />
      <Input label="Error State" placeholder="Enter text..." error helperText="This field is required" />
      <Input label="Disabled State" placeholder="Cannot edit" disabled />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'All input states side by side for comparison.',
      },
    },
  },
};

export const LabelAssociation: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)', width: '400px' }}>
      <Input label="Click the label to focus" placeholder="Input will focus" />
      <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
        Click the label above and the input will receive focus. This demonstrates proper accessibility with htmlFor/id
        association.
      </p>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Labels are properly associated with inputs using htmlFor/id. Clicking the label will focus the input.',
      },
    },
  },
};

export const FocusRing: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)', width: '400px' }}>
      <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--spacing-md)' }}>
        Use keyboard (Tab) to navigate between inputs and see the focus ring:
      </p>
      <Input label="First Input" placeholder="Tab to next..." />
      <Input label="Second Input" placeholder="Tab to next..." />
      <Input label="Third Input (Error)" error placeholder="Tab to next..." />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'All inputs include focus rings for keyboard navigation accessibility. Error state inputs have a red focus ring.',
      },
    },
  },
};

export const ErrorAccessibility: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)', width: '400px' }}>
      <Input
        label="Email Address"
        placeholder="you@example.com"
        error
        helperText="Invalid email format"
        defaultValue="not-an-email"
      />
      <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
        Error inputs have aria-invalid="true" and the error message is linked via aria-describedby for screen reader
        support.
      </p>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Error states are communicated to assistive technologies using aria-invalid and aria-describedby attributes.',
      },
    },
  },
};
