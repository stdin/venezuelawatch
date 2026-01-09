import * as React from 'react';
import { Slot } from 'radix-ui';
import { clsx } from 'clsx';

// Extract the Slot component from the namespace
const SlotComponent = Slot.Slot;

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', asChild = false, className, ...props }, ref) => {
    const Comp = asChild ? SlotComponent : 'button' as React.ElementType;

    const baseStyles = [
      'inline-flex',
      'items-center',
      'justify-center',
      'font-medium',
      'transition-colors',
      'focus-visible:outline-none',
      'focus-visible:ring-2',
      'focus-visible:ring-offset-2',
      'disabled:opacity-50',
      'disabled:pointer-events-none',
    ];

    const variantStyles = {
      primary: [
        'bg-[var(--color-interactive-primary)]',
        'text-[var(--color-text-inverse)]',
        'hover:bg-[var(--color-interactive-hover)]',
        'focus-visible:ring-[var(--color-interactive-primary)]',
      ],
      secondary: [
        'bg-[var(--color-bg-elevated)]',
        'text-[var(--color-text-primary)]',
        'border',
        'border-[var(--color-border-default)]',
        'hover:bg-[var(--color-neutral-200)]',
        'focus-visible:ring-[var(--color-border-strong)]',
      ],
      ghost: [
        'bg-transparent',
        'text-[var(--color-text-primary)]',
        'hover:bg-[var(--color-bg-elevated)]',
        'focus-visible:ring-[var(--color-border-default)]',
      ],
    };

    const sizeStyles = {
      sm: [
        'text-[length:var(--font-size-xs)]',
        'h-[32px]',
        'px-[var(--spacing-sm)]',
        'gap-[var(--spacing-xs)]',
        'rounded-[var(--radius-md)]',
      ],
      md: [
        'text-[length:var(--font-size-sm)]',
        'h-[40px]',
        'px-[var(--spacing-md)]',
        'gap-[var(--spacing-xs)]',
        'rounded-[var(--radius-lg)]',
      ],
      lg: [
        'text-[length:var(--font-size-md)]',
        'h-[48px]',
        'px-[var(--spacing-lg)]',
        'gap-[var(--spacing-sm)]',
        'rounded-[var(--radius-xl)]',
      ],
    };

    return (
      <Comp
        ref={ref}
        className={clsx(baseStyles, variantStyles[variant], sizeStyles[size], className)}
        {...props}
      />
    );
  }
);

Button.displayName = 'Button';

export { Button };
