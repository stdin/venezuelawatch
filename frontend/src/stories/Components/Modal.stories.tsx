import type { Meta, StoryObj } from '@storybook/react';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import * as React from 'react';

const meta: Meta<typeof Modal.Root> = {
  title: 'Components/Modal',
  component: Modal.Root,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Modal.Root>
      <Modal.Trigger asChild>
        <Button variant="primary">Open Modal</Button>
      </Modal.Trigger>
      <Modal.Content>
        <Modal.Title
          style={{
            fontSize: 'var(--font-size-lg)',
            fontWeight: 600,
            color: 'var(--color-text-primary)',
          }}
        >
          Modal Title
        </Modal.Title>
        <Modal.Description
          style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-secondary)',
            marginTop: 'var(--spacing-xs)',
          }}
        >
          This is a modal dialog with title and description. Press Esc to close or click the X
          button.
        </Modal.Description>
        <div style={{ marginTop: 'var(--spacing-lg)', color: 'var(--color-text-primary)' }}>
          <p>
            Modal content goes here. The modal is built with Radix UI Dialog, which handles:
          </p>
          <ul style={{ paddingLeft: 'var(--spacing-lg)', marginTop: 'var(--spacing-sm)' }}>
            <li>Focus trap (Tab cycles within modal)</li>
            <li>Esc key closes the modal</li>
            <li>Focus restoration (returns to trigger button)</li>
            <li>Scroll lock on body</li>
            <li>ARIA attributes for accessibility</li>
          </ul>
        </div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: 'var(--spacing-sm)',
            marginTop: 'var(--spacing-lg)',
          }}
        >
          <Modal.Close asChild>
            <Button variant="ghost">Cancel</Button>
          </Modal.Close>
          <Modal.Close asChild>
            <Button variant="primary">Confirm</Button>
          </Modal.Close>
        </div>
      </Modal.Content>
    </Modal.Root>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'A basic modal with title, description, and action buttons. Demonstrates accessibility features like focus trap and keyboard navigation.',
      },
    },
  },
};

export const WithForm: Story = {
  render: () => {
    const [open, setOpen] = React.useState(false);
    const [formData, setFormData] = React.useState({ name: '', email: '', reason: '' });

    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault();
      console.log('Form submitted:', formData);
      setOpen(false);
    };

    return (
      <Modal.Root open={open} onOpenChange={setOpen}>
        <Modal.Trigger asChild>
          <Button variant="primary">Add Entity</Button>
        </Modal.Trigger>
        <Modal.Content>
          <Modal.Title
            style={{
              fontSize: 'var(--font-size-lg)',
              fontWeight: 600,
              color: 'var(--color-text-primary)',
            }}
          >
            Add New Entity
          </Modal.Title>
          <Modal.Description
            style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--color-text-secondary)',
              marginTop: 'var(--spacing-xs)',
            }}
          >
            Enter the entity details to add to the watchlist.
          </Modal.Description>

          <form onSubmit={handleSubmit}>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--spacing-md)',
                marginTop: 'var(--spacing-lg)',
              }}
            >
              <Input
                id="name"
                label="Entity Name"
                placeholder="Enter full name"
                value={formData.name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, name: e.target.value })}
                required
              />

              <Input
                id="email"
                label="Email Address"
                type="email"
                placeholder="email@example.com"
                value={formData.email}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, email: e.target.value })}
                required
              />

              <Input
                id="reason"
                label="Reason for Monitoring"
                placeholder="Brief description"
                value={formData.reason}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, reason: e.target.value })}
              />
            </div>

            <div
              style={{
                display: 'flex',
                justifyContent: 'flex-end',
                gap: 'var(--spacing-sm)',
                marginTop: 'var(--spacing-lg)',
              }}
            >
              <Modal.Close asChild>
                <Button variant="ghost" type="button">
                  Cancel
                </Button>
              </Modal.Close>
              <Button variant="primary" type="submit">
                Add Entity
              </Button>
            </div>
          </form>
        </Modal.Content>
      </Modal.Root>
    );
  },
  parameters: {
    docs: {
      description: {
        story:
          'Modal containing a form with multiple input fields. Demonstrates controlled open state and form submission.',
      },
    },
  },
};

export const LongContent: Story = {
  render: () => (
    <Modal.Root>
      <Modal.Trigger asChild>
        <Button variant="primary">Open Long Modal</Button>
      </Modal.Trigger>
      <Modal.Content style={{ maxHeight: '80vh', overflowY: 'auto' }}>
        <Modal.Title
          style={{
            fontSize: 'var(--font-size-lg)',
            fontWeight: 600,
            color: 'var(--color-text-primary)',
          }}
        >
          Terms and Conditions
        </Modal.Title>
        <Modal.Description
          style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-secondary)',
            marginTop: 'var(--spacing-xs)',
          }}
        >
          Please read these terms carefully before proceeding.
        </Modal.Description>

        <div
          style={{
            marginTop: 'var(--spacing-lg)',
            color: 'var(--color-text-primary)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--spacing-md)',
          }}
        >
          {[...Array(10)].map((_, i) => (
            <div key={i}>
              <h4 style={{ fontWeight: 600, marginBottom: 'var(--spacing-xs)' }}>
                Section {i + 1}
              </h4>
              <p style={{ lineHeight: 1.6 }}>
                Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor
                incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
                exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute
                irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
                pariatur.
              </p>
            </div>
          ))}
        </div>

        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: 'var(--spacing-sm)',
            marginTop: 'var(--spacing-lg)',
            position: 'sticky',
            bottom: 0,
            backgroundColor: 'var(--color-bg-surface)',
            paddingTop: 'var(--spacing-md)',
          }}
        >
          <Modal.Close asChild>
            <Button variant="ghost">Decline</Button>
          </Modal.Close>
          <Modal.Close asChild>
            <Button variant="primary">Accept</Button>
          </Modal.Close>
        </div>
      </Modal.Content>
    </Modal.Root>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Modal with scrollable content. Tests scroll behavior and demonstrates sticky footer for actions.',
      },
    },
  },
};

export const NoCloseButton: Story = {
  render: () => (
    <Modal.Root>
      <Modal.Trigger asChild>
        <Button variant="primary">Open Alert</Button>
      </Modal.Trigger>
      <Modal.Content showClose={false}>
        <Modal.Title
          style={{
            fontSize: 'var(--font-size-lg)',
            fontWeight: 600,
            color: 'var(--color-text-primary)',
          }}
        >
          Destructive Action
        </Modal.Title>
        <Modal.Description
          style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-secondary)',
            marginTop: 'var(--spacing-xs)',
          }}
        >
          This action cannot be undone. Are you sure you want to proceed?
        </Modal.Description>

        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: 'var(--spacing-sm)',
            marginTop: 'var(--spacing-lg)',
          }}
        >
          <Modal.Close asChild>
            <Button variant="ghost">Cancel</Button>
          </Modal.Close>
          <Modal.Close asChild>
            <Button
              variant="primary"
              style={{
                backgroundColor: 'var(--color-risk-high)',
              }}
            >
              Delete
            </Button>
          </Modal.Close>
        </div>
      </Modal.Content>
    </Modal.Root>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Modal without the X close button, forcing users to use explicit action buttons. Good for destructive actions.',
      },
    },
  },
};

export const Accessibility: Story = {
  render: () => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
      <Modal.Root>
        <Modal.Trigger asChild>
          <Button variant="primary">Test Keyboard Navigation</Button>
        </Modal.Trigger>
        <Modal.Content>
          <Modal.Title
            style={{
              fontSize: 'var(--font-size-lg)',
              fontWeight: 600,
              color: 'var(--color-text-primary)',
            }}
          >
            Accessibility Features
          </Modal.Title>
          <Modal.Description
            style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--color-text-secondary)',
              marginTop: 'var(--spacing-xs)',
            }}
          >
            Test the following keyboard interactions:
          </Modal.Description>

          <div
            style={{
              marginTop: 'var(--spacing-lg)',
              color: 'var(--color-text-primary)',
            }}
          >
            <ul
              style={{
                paddingLeft: 'var(--spacing-lg)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--spacing-xs)',
              }}
            >
              <li>
                <strong>Tab:</strong> Cycles focus between interactive elements inside the modal
              </li>
              <li>
                <strong>Shift+Tab:</strong> Cycles focus backward
              </li>
              <li>
                <strong>Esc:</strong> Closes the modal
              </li>
              <li>
                <strong>Focus restoration:</strong> When modal closes, focus returns to the trigger
                button
              </li>
            </ul>

            <div
              style={{
                marginTop: 'var(--spacing-lg)',
                padding: 'var(--spacing-md)',
                backgroundColor: 'var(--color-bg-elevated)',
                borderRadius: 'var(--radius-md)',
              }}
            >
              <p style={{ fontSize: 'var(--font-size-sm)', marginBottom: 'var(--spacing-sm)' }}>
                Try tabbing through these buttons:
              </p>
              <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
                <Button variant="secondary" size="sm">
                  Button 1
                </Button>
                <Button variant="secondary" size="sm">
                  Button 2
                </Button>
                <Button variant="secondary" size="sm">
                  Button 3
                </Button>
              </div>
            </div>
          </div>

          <div
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              marginTop: 'var(--spacing-lg)',
            }}
          >
            <Modal.Close asChild>
              <Button variant="primary">Close</Button>
            </Modal.Close>
          </div>
        </Modal.Content>
      </Modal.Root>

      <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', maxWidth: '500px' }}>
        The Modal component uses Radix UI Dialog, which provides comprehensive accessibility
        features out of the box including proper ARIA attributes, focus management, and keyboard
        support.
      </p>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story:
          'Demonstrates accessibility features including focus trap, keyboard navigation, and focus restoration.',
      },
    },
  },
};
