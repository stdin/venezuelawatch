import * as React from 'react';
import { Modal as MantineModal, Title, Text } from '@mantine/core';

// Modal Root - wrapper for state management
interface ModalRootProps {
  children: React.ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

const ModalRoot: React.FC<ModalRootProps> = ({ children, open, onOpenChange }) => {
  const [opened, setOpened] = React.useState(open || false);

  React.useEffect(() => {
    if (open !== undefined) {
      setOpened(open);
    }
  }, [open]);

  const handleChange = (value: boolean) => {
    setOpened(value);
    onOpenChange?.(value);
  };

  return (
    <div>
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, { opened, onClose: () => handleChange(false), onOpen: () => handleChange(true) } as any);
        }
        return child;
      })}
    </div>
  );
};

// Modal Trigger
interface ModalTriggerProps {
  children: React.ReactElement;
  onOpen?: () => void;
}

const ModalTrigger: React.FC<ModalTriggerProps> = ({ children, onOpen }) => {
  return React.cloneElement(children, {
    onClick: () => {
      onOpen?.();
      children.props.onClick?.();
    },
  });
};

// Modal Content
interface ModalContentProps {
  children: React.ReactNode;
  opened?: boolean;
  onClose?: () => void;
  title?: string;
  size?: string;
}

const ModalContent: React.FC<ModalContentProps> = ({ children, opened = false, onClose, title, size = 'md' }) => {
  return (
    <MantineModal opened={opened} onClose={onClose || (() => {})} title={title} size={size} centered>
      {children}
    </MantineModal>
  );
};

// Modal Title
const ModalTitle: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <Title order={3} mb="md">{children}</Title>;
};

// Modal Description
const ModalDescription: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <Text size="sm" c="dimmed" mb="md">{children}</Text>;
};

// Export as compound component
export const Modal = {
  Root: ModalRoot,
  Trigger: ModalTrigger,
  Content: ModalContent,
  Title: ModalTitle,
  Description: ModalDescription,
  Close: () => null, // Mantine handles close button internally
};
