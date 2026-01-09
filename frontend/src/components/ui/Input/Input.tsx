import * as React from 'react';
import { TextInput } from '@mantine/core';

export interface InputProps {
  label?: string;
  error?: boolean | string;
  helperText?: string;
  placeholder?: string;
  value?: string;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
  disabled?: boolean;
  type?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error = false, helperText, ...props }, ref) => {
    return (
      <TextInput
        ref={ref}
        label={label}
        error={typeof error === 'string' ? error : (error ? helperText : undefined)}
        description={!error ? helperText : undefined}
        {...props}
      />
    );
  }
);

Input.displayName = 'Input';

export { Input };
