import * as React from 'react';
import { clsx } from 'clsx';

// Card Root - Main container
export interface CardRootProps extends React.HTMLAttributes<HTMLDivElement> {}

const CardRoot = React.forwardRef<HTMLDivElement, CardRootProps>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'bg-[var(--color-bg-surface)]',
          'border',
          'border-[var(--color-border-default)]',
          'rounded-[var(--radius-md)]',
          'shadow-[var(--shadow-sm)]',
          className
        )}
        {...props}
      />
    );
  }
);
CardRoot.displayName = 'Card.Root';

// Card Header - Optional header section
export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {}

const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'flex',
          'flex-col',
          'gap-[var(--spacing-xs)]',
          'p-[var(--spacing-lg)]',
          'pb-[var(--spacing-md)]',
          className
        )}
        {...props}
      />
    );
  }
);
CardHeader.displayName = 'Card.Header';

// Card Title - Title with heading semantics
export interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {}

const CardTitle = React.forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ className, ...props }, ref) => {
    return (
      <h3
        ref={ref}
        className={clsx(
          'text-[length:var(--font-size-lg)]',
          'font-semibold',
          'leading-none',
          'tracking-tight',
          'text-[var(--color-text-primary)]',
          className
        )}
        {...props}
      />
    );
  }
);
CardTitle.displayName = 'Card.Title';

// Card Description - Subtitle/description text
export interface CardDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {}

const CardDescription = React.forwardRef<HTMLParagraphElement, CardDescriptionProps>(
  ({ className, ...props }, ref) => {
    return (
      <p
        ref={ref}
        className={clsx(
          'text-[length:var(--font-size-sm)]',
          'text-[var(--color-text-secondary)]',
          className
        )}
        {...props}
      />
    );
  }
);
CardDescription.displayName = 'Card.Description';

// Card Content - Main content area
export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {}

const CardContent = React.forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'p-[var(--spacing-lg)]',
          'pt-0',
          className
        )}
        {...props}
      />
    );
  }
);
CardContent.displayName = 'Card.Content';

// Card Footer - Optional footer section
export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {}

const CardFooter = React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'flex',
          'items-center',
          'p-[var(--spacing-lg)]',
          'pt-0',
          className
        )}
        {...props}
      />
    );
  }
);
CardFooter.displayName = 'Card.Footer';

// Export as compound component
export const Card = {
  Root: CardRoot,
  Header: CardHeader,
  Title: CardTitle,
  Description: CardDescription,
  Content: CardContent,
  Footer: CardFooter,
};
