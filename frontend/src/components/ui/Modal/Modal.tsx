import * as React from 'react';
import { Dialog } from 'radix-ui';
import { clsx } from 'clsx';
import { Button } from '../Button';

// Re-export Dialog primitives
const ModalRoot = Dialog.Root;
const ModalTrigger = Dialog.Trigger;
const ModalTitle = Dialog.Title;
const ModalDescription = Dialog.Description;
const ModalClose = Dialog.Close;

// Modal Overlay
interface ModalOverlayProps extends React.ComponentPropsWithoutRef<typeof Dialog.Overlay> {}

const ModalOverlay = React.forwardRef<
  React.ElementRef<typeof Dialog.Overlay>,
  ModalOverlayProps
>(({ className, ...props }, ref) => (
  <Dialog.Overlay
    ref={ref}
    className={clsx(
      'fixed',
      'inset-0',
      'z-50',
      'bg-[var(--color-bg-overlay)]',
      'data-[state=open]:animate-in',
      'data-[state=closed]:animate-out',
      'data-[state=closed]:fade-out-0',
      'data-[state=open]:fade-in-0',
      className
    )}
    {...props}
  />
));
ModalOverlay.displayName = 'Modal.Overlay';

// Modal Content - wraps Portal + Overlay + Content
export interface ModalContentProps extends React.ComponentPropsWithoutRef<typeof Dialog.Content> {
  showClose?: boolean;
}

const ModalContent = React.forwardRef<
  React.ElementRef<typeof Dialog.Content>,
  ModalContentProps
>(({ className, children, showClose = true, ...props }, ref) => (
  <Dialog.Portal>
    <ModalOverlay />
    <Dialog.Content
      ref={ref}
      className={clsx(
        'fixed',
        'left-[50%]',
        'top-[50%]',
        'z-50',
        'translate-x-[-50%]',
        'translate-y-[-50%]',
        'grid',
        'w-full',
        'max-w-[var(--size-lg)]',
        'gap-[var(--spacing-md)]',
        'bg-[var(--color-bg-surface)]',
        'p-[var(--spacing-lg)]',
        'shadow-[var(--shadow-lg)]',
        'border',
        'border-[var(--color-border-default)]',
        'rounded-[var(--radius-lg)]',
        'duration-200',
        'data-[state=open]:animate-in',
        'data-[state=closed]:animate-out',
        'data-[state=closed]:fade-out-0',
        'data-[state=open]:fade-in-0',
        'data-[state=closed]:zoom-out-95',
        'data-[state=open]:zoom-in-95',
        'data-[state=closed]:slide-out-to-left-1/2',
        'data-[state=closed]:slide-out-to-top-[48%]',
        'data-[state=open]:slide-in-from-left-1/2',
        'data-[state=open]:slide-in-from-top-[48%]',
        className
      )}
      {...props}
    >
      {children}
      {showClose && (
        <Dialog.Close asChild>
          <Button
            variant="ghost"
            size="sm"
            className={clsx(
              'absolute',
              'right-[var(--spacing-md)]',
              'top-[var(--spacing-md)]',
              'rounded-[var(--radius-sm)]',
              'opacity-70',
              'hover:opacity-100',
              'focus:opacity-100',
              'disabled:pointer-events-none'
            )}
            aria-label="Close"
          >
            <svg
              width="15"
              height="15"
              viewBox="0 0 15 15"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
            >
              <path
                d="M11.7816 4.03157C12.0062 3.80702 12.0062 3.44295 11.7816 3.2184C11.5571 2.99385 11.193 2.99385 10.9685 3.2184L7.50005 6.68682L4.03164 3.2184C3.80708 2.99385 3.44301 2.99385 3.21846 3.2184C2.99391 3.44295 2.99391 3.80702 3.21846 4.03157L6.68688 7.49999L3.21846 10.9684C2.99391 11.193 2.99391 11.557 3.21846 11.7816C3.44301 12.0061 3.80708 12.0061 4.03164 11.7816L7.50005 8.31316L10.9685 11.7816C11.193 12.0061 11.5571 12.0061 11.7816 11.7816C12.0062 11.557 12.0062 11.193 11.7816 10.9684L8.31322 7.49999L11.7816 4.03157Z"
                fill="currentColor"
                fillRule="evenodd"
                clipRule="evenodd"
              />
            </svg>
          </Button>
        </Dialog.Close>
      )}
    </Dialog.Content>
  </Dialog.Portal>
));
ModalContent.displayName = 'Modal.Content';

// Export as compound component
export const Modal = {
  Root: ModalRoot,
  Trigger: ModalTrigger,
  Content: ModalContent,
  Title: ModalTitle,
  Description: ModalDescription,
  Close: ModalClose,
};
