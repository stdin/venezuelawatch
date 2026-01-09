import * as React from 'react';
import { Card as MantineCard, Title, Text } from '@mantine/core';

// Card Root - Main container
export interface CardRootProps {
  children?: React.ReactNode;
  className?: string;
}

const CardRoot = React.forwardRef<HTMLDivElement, CardRootProps>(
  ({ children, ...props }, ref) => {
    return (
      <MantineCard shadow="sm" padding="lg" radius="md" withBorder ref={ref} {...props}>
        {children}
      </MantineCard>
    );
  }
);
CardRoot.displayName = 'Card.Root';

// Card Header - Optional header section
export interface CardHeaderProps {
  children?: React.ReactNode;
}

const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ children }, ref) => {
    return (
      <div ref={ref} style={{ marginBottom: '16px' }}>
        {children}
      </div>
    );
  }
);
CardHeader.displayName = 'Card.Header';

// Card Title - Title with heading semantics
export interface CardTitleProps {
  children?: React.ReactNode;
}

const CardTitle = React.forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ children }, ref) => {
    return (
      <Title order={3} ref={ref as any}>
        {children}
      </Title>
    );
  }
);
CardTitle.displayName = 'Card.Title';

// Card Description - Subtitle/description text
export interface CardDescriptionProps {
  children?: React.ReactNode;
}

const CardDescription = React.forwardRef<HTMLParagraphElement, CardDescriptionProps>(
  ({ children }, ref) => {
    return (
      <Text size="sm" c="dimmed" ref={ref as any}>
        {children}
      </Text>
    );
  }
);
CardDescription.displayName = 'Card.Description';

// Card Content - Main content area
export interface CardContentProps {
  children?: React.ReactNode;
}

const CardContent = React.forwardRef<HTMLDivElement, CardContentProps>(
  ({ children }, ref) => {
    return <div ref={ref}>{children}</div>;
  }
);
CardContent.displayName = 'Card.Content';

// Card Footer - Optional footer section
export interface CardFooterProps {
  children?: React.ReactNode;
}

const CardFooter = React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({ children }, ref) => {
    return (
      <div ref={ref} style={{ marginTop: '16px', display: 'flex', alignItems: 'center' }}>
        {children}
      </div>
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
