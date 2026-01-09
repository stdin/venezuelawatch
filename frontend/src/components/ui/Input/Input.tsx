import * as React from 'react';
import { clsx } from 'clsx';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: boolean;
  helperText?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error = false, helperText, className, id: providedId, ...props }, ref) => {
    const generatedId = React.useId();
    const id = providedId || generatedId;
    const helperTextId = `${id}-helper`;

    const inputStyles = clsx(
      'w-full',
      'h-[40px]',
      'px-[var(--spacing-sm)]',
      'text-[length:var(--font-size-sm)]',
      'font-[var(--font-family-sans)]',
      'bg-[var(--color-bg-surface)]',
      'border',
      'rounded-[var(--radius-lg)]',
      'transition-colors',
      'focus:outline-none',
      'focus:ring-2',
      'focus:ring-offset-2',
      'disabled:opacity-50',
      'disabled:cursor-not-allowed',
      error
        ? [
            'border-[var(--color-risk-high)]',
            'text-[var(--color-text-primary)]',
            'focus:ring-[var(--color-risk-high)]',
          ]
        : [
            'border-[var(--color-border-default)]',
            'text-[var(--color-text-primary)]',
            'focus:ring-[var(--color-interactive-primary)]',
            'focus:border-[var(--color-interactive-primary)]',
          ],
      className
    );

    const labelStyles = clsx(
      'block',
      'text-[length:var(--font-size-sm)]',
      'font-medium',
      'mb-[var(--spacing-xs)]',
      error ? 'text-[var(--color-risk-high)]' : 'text-[var(--color-text-primary)]'
    );

    const helperTextStyles = clsx(
      'mt-[var(--spacing-xs)]',
      'text-[length:var(--font-size-xs)]',
      error ? 'text-[var(--color-risk-high)]' : 'text-[var(--color-text-secondary)]'
    );

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={id} className={labelStyles}>
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          className={inputStyles}
          aria-invalid={error}
          aria-describedby={helperText ? helperTextId : undefined}
          {...props}
        />
        {helperText && (
          <p id={helperTextId} className={helperTextStyles}>
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export { Input };
