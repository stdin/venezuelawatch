import * as React from 'react';
import { Button as MantineButton } from '@mantine/core';

export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  children?: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', children, ...props }, ref) => {
    // Map our variants to Mantine variants
    const mantineVariant = variant === 'primary' ? 'filled' : variant === 'secondary' ? 'light' : 'subtle';
    const mantineSize = size === 'sm' ? 'sm' : size === 'lg' ? 'lg' : 'md';

    return (
      <MantineButton
        ref={ref}
        variant={mantineVariant}
        size={mantineSize}
        {...props}
      >
        {children}
      </MantineButton>
    );
  }
);

Button.displayName = 'Button';

export { Button };
