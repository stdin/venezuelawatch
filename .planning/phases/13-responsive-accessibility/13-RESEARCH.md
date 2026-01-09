# Phase 13: Responsive Design & Accessibility Tooling Research

**Project Context:** React 19.2 + Mantine UI 8.3.11 + TypeScript
**Stack:** Storybook 10 + @storybook/addon-a11y
**Compliance Target:** WCAG 2.1 AA
**Pages in Scope:** Dashboard, Entities, Chat

---

## Table of Contents

1. [Mantine Responsive Utilities](#mantine-responsive-utilities)
2. [Recommended Breakpoints](#recommended-breakpoints)
3. [Accessibility Testing Workflow](#accessibility-testing-workflow)
4. [ARIA Patterns for Common UI Elements](#aria-patterns-for-common-ui-elements)
5. [Keyboard Navigation Best Practices](#keyboard-navigation-best-practices)
6. [Touch Target & Mobile Requirements](#touch-target--mobile-requirements)
7. [Implementation Checklist](#implementation-checklist)

---

## Mantine Responsive Utilities

### 1. **useMediaQuery Hook** (Runtime Media Queries)

A hook that queries media conditions and returns boolean values. Useful for dynamic, component-level logic.

**Usage:**
```tsx
import { useMediaQuery } from '@mantine/hooks';

function Demo() {
  const isDesktop = useMediaQuery('(min-width: 1024px)');
  const isMobile = useMediaQuery('(max-width: 48em)');

  return (
    <div>
      {isDesktop && <DesktopLayout />}
      {isMobile && <MobileLayout />}
    </div>
  );
}
```

**TypeScript Definition:**
```tsx
interface UseMediaQueryOptions {
  getInitialValueInEffect: boolean;
}

function useMediaQuery(
  query: string,
  initialValue?: boolean,
  options?: UseMediaQueryOptions,
): boolean;
```

**Server-Side Rendering:**
```tsx
// Prevent SSR issues where window.matchMedia is unavailable
const matches = useMediaQuery('(max-width: 40em)', true, {
  getInitialValueInEffect: false,
});
```

### 2. **useMatches Hook** (Multiple Media Queries)

An alternative to `useMediaQuery` when matching multiple media queries and applying different values.

**Usage:**
```tsx
import { Box, useMatches } from '@mantine/core';

function Demo() {
  const color = useMatches({
    base: 'blue.9',    // Default (mobile-first)
    sm: 'orange.9',    // Small screens
    lg: 'red.9',       // Large screens
  });

  return (
    <Box bg={color} c="white" p="xl">
      Box with responsive color
    </Box>
  );
}
```

### 3. **Responsive Props (Inline Breakpoints)**

Most Mantine components support responsive object syntax for their props.

**Grid Example:**
```tsx
import { Grid } from '@mantine/core';

function ResponsiveGrid() {
  return (
    <Grid>
      <Grid.Col span={{ base: 12, md: 6, lg: 3 }}>
        Mobile: 12/12 cols | Tablet: 6/12 cols | Desktop: 3/12 cols
      </Grid.Col>
    </Grid>
  );
}
```

**Other Responsive Props:**
```tsx
import { SimpleGrid } from '@mantine/core';

function Demo() {
  return (
    <SimpleGrid
      cols={{ base: 1, sm: 2, lg: 5 }}           // Responsive columns
      spacing={{ base: 10, sm: 'xl' }}           // Responsive spacing
      verticalSpacing={{ base: 'md', sm: 'xl' }} // Responsive vertical spacing
      gutter={{ base: 'sm', md: 'lg' }}          // Responsive gutter
    >
      {/* Grid items */}
    </SimpleGrid>
  );
}
```

### 4. **Visibility Props: hiddenFrom & visibleFrom**

Declarative conditional rendering based on breakpoints. Uses CSS utility classes under the hood.

**Component Props:**
```tsx
import { Button, Group } from '@mantine/core';

function Demo() {
  return (
    <Group justify="center">
      <Button hiddenFrom="sm" color="orange">
        Only visible on mobile (xs breakpoint)
      </Button>
      <Button visibleFrom="sm" color="cyan">
        Hidden on mobile, visible from sm (small) up
      </Button>
      <Button visibleFrom="md" color="pink">
        Hidden on mobile/tablet, visible from md (medium) up
      </Button>
    </Group>
  );
}
```

**CSS Utility Classes:**
```tsx
function CustomComponent() {
  return (
    <>
      <div className="mantine-hidden-from-md">Hidden from md breakpoint</div>
      <div className="mantine-visible-from-xl">Only visible at xl and above</div>
    </>
  );
}
```

### 5. **MediaQuery Component** (CSS-Based Queries)

Lower-level component for custom media query logic. Typically used less often than utilities above.

**Pattern:**
```tsx
import { MediaQuery, Box } from '@mantine/core';

function Demo() {
  return (
    <>
      <MediaQuery smallerThan="sm" styles={{ display: 'none' }}>
        <Box>Hidden on mobile</Box>
      </MediaQuery>
      <MediaQuery largerThan="sm" styles={{ display: 'none' }}>
        <Box>Hidden on tablet and desktop</Box>
      </MediaQuery>
    </>
  );
}
```

### 6. **Container Queries Support**

For component-based responsive design (respond to container width, not viewport).

**Usage:**
```tsx
import { Grid } from '@mantine/core';

function Demo() {
  return (
    <div style={{ resize: 'horizontal', overflow: 'hidden', maxWidth: '100%' }}>
      <Grid
        type="container"
        breakpoints={{ xs: '100px', sm: '200px', md: '300px', lg: '400px', xl: '500px' }}
      >
        <Grid.Col span={{ base: 12, md: 6, lg: 3 }}>Item</Grid.Col>
      </Grid>
    </div>
  );
}
```

---

## Recommended Breakpoints

### Default Mantine Breakpoints (in em units)

```tsx
const theme = createTheme({
  breakpoints: {
    xs: '30em',  // 480px @ 16px base
    sm: '48em',  // 768px @ 16px base
    md: '64em',  // 1024px @ 16px base
    lg: '74em',  // 1184px @ 16px base
    xl: '90em',  // 1440px @ 16px base
  },
});
```

### Recommended Usage Pattern for Venezuela Watch

```tsx
// mobile-first approach
const theme = createTheme({
  breakpoints: {
    xs: '36em',   // 576px - Mobile phones
    sm: '48em',   // 768px - Tablets (portrait)
    md: '62em',   // 992px - Tablets (landscape) / Small laptops
    lg: '75em',   // 1200px - Desktops
    xl: '88em',   // 1408px - Large desktops
  },
});
```

### Apply Theme Globally

```tsx
import { MantineProvider, createTheme } from '@mantine/core';

const theme = createTheme({
  breakpoints: {
    xs: '36em',
    sm: '48em',
    md: '62em',
    lg: '75em',
    xl: '88em',
  },
});

function App() {
  return (
    <MantineProvider theme={theme}>
      {/* Application */}
    </MantineProvider>
  );
}
```

---

## Accessibility Testing Workflow

### Storybook A11y Addon Setup

Storybook 10 already includes `@storybook/addon-a11y` which runs **axe-core** automated checks.

### 1. Basic Configuration

**In `.storybook/preview.ts` (or `preview.js`):**

```typescript
import type { Preview } from '@storybook/react';

const preview: Preview = {
  parameters: {
    a11y: {
      // Axe-core context parameter
      context: {},

      // Axe-core configuration
      config: {},

      // Axe-core options parameter
      options: {},

      // Test behavior: 'error' | 'warn' | 'todo' | 'manual'
      test: 'error', // Fail on accessibility violations
    },
  },
  globals: {
    a11y: {
      // Optional: allow manual override per story
      manual: false,
    },
  },
};

export default preview;
```

### 2. Story-Level Configuration

```typescript
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from '@mantine/core';

const meta = {
  component: Button,
  parameters: {
    a11y: {
      // Override global settings for specific stories
      test: 'warn',  // Only warn on this story
      config: {
        rules: [
          {
            // Disable specific rules for known issues
            id: 'color-contrast',
            enabled: false,
          },
        ],
      },
    },
  },
  globals: {
    a11y: {
      // Set to true to allow manual testing bypass
      manual: false,
    },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {};

export const DataTable: Story = {
  parameters: {
    // Mark work-in-progress components
    a11y: { test: 'todo' },
  },
};
```

### 3. Test Behavior Modes

```typescript
// 'error' - Fail tests if violations found
a11y: { test: 'error' }

// 'warn' - Show warnings but don't fail
a11y: { test: 'warn' }

// 'todo' - Work-in-progress; violations shown as warnings
a11y: { test: 'todo' }

// 'manual' - Require manual trigger of checks
a11y: { test: 'manual' }
```

### 4. Testing Workflow in Storybook UI

1. Open Storybook locally: `npm run storybook`
2. Navigate to a component story
3. Click **"Accessibility"** tab in bottom panel
4. View violations, warnings, and passes from axe-core
5. Fix issues directly in code based on suggestions

### 5. Advanced Configuration (Rules)

```typescript
const meta = {
  parameters: {
    a11y: {
      config: {
        rules: [
          {
            id: 'color-contrast',
            enabled: true,
            options: { level: 'AAA' }, // Stricter than AA
          },
          {
            id: 'heading-order',
            enabled: true,
          },
          {
            id: 'image-alt', // Still important
            enabled: true,
          },
        ],
      },
    },
  },
};
```

### Integration with CI/CD

Storybook tests can run in CI via `test-storybook` command (requires additional setup with @storybook/test-runner):

```bash
npm run test-storybook -- --all
```

---

## ARIA Patterns for Common UI Elements

### 1. Navigation Patterns

**Primary Navigation (Desktop):**
```tsx
<nav aria-label="Main navigation">
  <ul>
    <li><a href="/dashboard" aria-current="page">Dashboard</a></li>
    <li><a href="/entities">Entities</a></li>
    <li><a href="/chat">Chat</a></li>
  </ul>
</nav>
```

**Mobile Navigation Toggle:**
```tsx
function MobileNav() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        aria-label="Toggle navigation menu"
        aria-expanded={isOpen}
        onClick={() => setIsOpen(!isOpen)}
      >
        Menu
      </button>
      {isOpen && (
        <nav aria-label="Mobile navigation">
          {/* Navigation items */}
        </nav>
      )}
    </>
  );
}
```

### 2. Form Elements

**Labeled Input:**
```tsx
<div>
  <label htmlFor="search-input">Search entities</label>
  <input
    id="search-input"
    type="search"
    placeholder="Enter name or ID"
    aria-describedby="search-help"
  />
  <small id="search-help">Use spaces to separate multiple terms</small>
</div>
```

**Custom Checkbox (Mantine):**
```tsx
import { Checkbox } from '@mantine/core';

<Checkbox
  label="I agree to terms"
  aria-label="Agree to terms and conditions"
  required
/>
```

**Form Validation:**
```tsx
function FormWithValidation() {
  const [error, setError] = useState('');

  return (
    <div>
      <label htmlFor="email">Email</label>
      <input
        id="email"
        type="email"
        aria-invalid={!!error}
        aria-describedby={error ? 'email-error' : undefined}
      />
      {error && (
        <span id="email-error" role="alert" style={{ color: 'red' }}>
          {error}
        </span>
      )}
    </div>
  );
}
```

### 3. Loading & Async States

**Loading Indicator:**
```tsx
function AsyncData() {
  const [loading, setLoading] = useState(true);

  return (
    <div>
      {loading ? (
        <div
          role="status"
          aria-live="polite"
          aria-label="Loading data"
        >
          <Loader />
          <span>Loading entities...</span>
        </div>
      ) : (
        <DataList />
      )}
    </div>
  );
}
```

**Live Region for Status Updates:**
```tsx
<div
  role="status"
  aria-live="polite"
  aria-atomic="true"
>
  {statusMessage}
</div>
```

**Aria-Live Values:**
- `polite` - Announce after speaking current content
- `assertive` - Interrupt and announce immediately
- `off` - Do not announce

### 4. Modals/Dialogs

**Dialog with Focus Management:**
```tsx
import { Modal } from '@mantine/core';

function ConfirmDialog({ isOpen, onClose, onConfirm }) {
  return (
    <Modal
      opened={isOpen}
      onClose={onClose}
      title="Confirm Action"
      aria-labelledby="dialog-title"
      aria-describedby="dialog-description"
    >
      <div id="dialog-description">
        Are you sure you want to proceed?
      </div>
      <Button onClick={onConfirm}>Confirm</Button>
      <Button onClick={onClose}>Cancel</Button>
    </Modal>
  );
}
```

### 5. Tabs Component

**Accessible Tab Navigation:**
```tsx
import { Tabs } from '@mantine/core';

function TabsExample() {
  return (
    <Tabs
      value="dashboard"
      aria-label="Navigation tabs"
    >
      <Tabs.List>
        <Tabs.Tab value="dashboard">Dashboard</Tabs.Tab>
        <Tabs.Tab value="entities">Entities</Tabs.Tab>
        <Tabs.Tab value="chat">Chat</Tabs.Tab>
      </Tabs.List>

      <Tabs.Panel value="dashboard">Dashboard content</Tabs.Panel>
      <Tabs.Panel value="entities">Entities content</Tabs.Panel>
      <Tabs.Panel value="chat">Chat content</Tabs.Panel>
    </Tabs>
  );
}
```

### 6. Data Tables

**Table with Headers:**
```tsx
<table role="table" aria-label="Entities list">
  <caption>Complete list of tracked entities</caption>
  <thead>
    <tr>
      <th scope="col">Name</th>
      <th scope="col">Type</th>
      <th scope="col">Status</th>
    </tr>
  </thead>
  <tbody>
    {/* Rows */}
  </tbody>
</table>
```

**Sortable Column Header:**
```tsx
<th
  scope="col"
  role="button"
  tabIndex={0}
  aria-sort="ascending"
  onClick={handleSort}
  onKeyDown={(e) => e.key === 'Enter' && handleSort()}
>
  Name
</th>
```

---

## Keyboard Navigation Best Practices

### 1. Tab Order & Focus Management

**Natural Tab Order:**
```tsx
// DO: Follow HTML structure (left to right, top to bottom)
<div>
  <input type="text" placeholder="Search" />
  <button>Go</button>
  <a href="#results">Skip to results</a>
</div>

// DON'T: Use tabIndex for visual layout
// Avoid: tabIndex="1", tabIndex="2" (non-negative values)
// Only use tabIndex="0" (include in tab order) or tabIndex="-1" (exclude)
```

**Skip Links:**
```tsx
function Layout() {
  return (
    <>
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <header>Navigation</header>
      <main id="main-content">
        Page content
      </main>
    </>
  );
}
```

CSS for skip link (visible on focus only):
```css
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: #000;
  color: white;
  padding: 8px;
  z-index: 100;
}

.skip-link:focus {
  top: 0;
}
```

### 2. Focus Visibility

**Ensure Visible Focus Indicator:**
```css
/* DO: Keep visible focus indicators */
button:focus-visible {
  outline: 3px solid #0066cc;
  outline-offset: 2px;
}

/* DON'T: Remove focus indicators */
/* Avoid: outline: none; */
```

**Mantine Focus Styles:**
```tsx
import { Button } from '@mantine/core';

// Mantine buttons include visible focus indicators by default
<Button>Click me (focus-visible included)</Button>
```

### 3. Arrow Key Navigation

**Dropdown/Select Menu:**
```tsx
function Dropdown() {
  const [focused, setFocused] = useState(0);
  const items = ['Option 1', 'Option 2', 'Option 3'];

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setFocused((prev) => (prev + 1) % items.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setFocused((prev) => (prev - 1 + items.length) % items.length);
    } else if (e.key === 'Enter') {
      // Select current item
    }
  };

  return (
    <ul role="listbox" onKeyDown={handleKeyDown}>
      {items.map((item, i) => (
        <li
          key={item}
          role="option"
          aria-selected={i === focused}
          tabIndex={i === focused ? 0 : -1}
        >
          {item}
        </li>
      ))}
    </ul>
  );
}
```

### 4. Enter & Space Key Handling

**Custom Button:**
```tsx
function CustomButton({ onClick }) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick();
    }
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onClick={onClick}
    >
      Click me
    </div>
  );
}

// Better: Use Mantine Button or HTML <button>
<button onClick={onClick}>Click me</button>
```

### 5. Focus Trapping in Modals

```tsx
import { Modal, Button } from '@mantine/core';
import { useEffect, useRef } from 'react';

function ModalWithFocusTrap({ isOpen, onClose }) {
  const firstButtonRef = useRef<HTMLButtonElement>(null);
  const lastButtonRef = useRef<HTMLButtonElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key !== 'Tab') return;

    if (e.shiftKey) {
      // Shift+Tab on first element → focus last
      if (document.activeElement === firstButtonRef.current) {
        e.preventDefault();
        lastButtonRef.current?.focus();
      }
    } else {
      // Tab on last element → focus first
      if (document.activeElement === lastButtonRef.current) {
        e.preventDefault();
        firstButtonRef.current?.focus();
      }
    }
  };

  return (
    <Modal opened={isOpen} onClose={onClose} onKeyDown={handleKeyDown}>
      <Button ref={firstButtonRef}>First Action</Button>
      <Button ref={lastButtonRef} onClick={onClose}>
        Close
      </Button>
    </Modal>
  );
}
```

### 6. Escape Key Handling

```tsx
function SearchBox({ onClose }) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    }
  };

  return (
    <input
      type="search"
      onKeyDown={handleKeyDown}
      placeholder="Search..."
    />
  );
}
```

---

## Touch Target & Mobile Requirements

### 1. Minimum Touch Target Size (WCAG 2.1 AA)

**Requirement:** 44×44 CSS pixels minimum

**Implementation:**
```tsx
// Good: 44px minimum (can be larger)
<button style={{ padding: '12px 16px', minHeight: '44px', minWidth: '44px' }}>
  Tap me
</button>

// Using Mantine (default Button includes appropriate padding)
import { Button } from '@mantine/core';

<Button size="md" p="md">
  Tap me
</Button>
```

**Mantine Button Sizes & Touch Targets:**
```tsx
// xs: 22px height (too small - combine with wider padding)
// sm: 30px height (too small alone)
// md: 36px height (meets 44px with padding)
// lg: 40px height (meets 44px with padding)
// xl: 48px height (exceeds 44px)

// Recommended for mobile: size="lg" or size="xl" with appropriate padding
<Button size="lg">Tap (44px+ touch area)</Button>
```

### 2. Spacing Between Interactive Elements

```tsx
// Minimum 8px spacing to prevent accidental taps
<Group spacing="md" p="md">
  <Button>Action 1</Button>
  <Button>Action 2</Button>
  <Button>Action 3</Button>
</Group>
```

### 3. Mobile-First Responsive Layout

**Pattern for Venezuela Watch Pages:**

```tsx
import { Box, Container, Grid, Stack } from '@mantine/core';

function DashboardPage() {
  return (
    <Container size="xl" py="xl">
      <Stack gap={{ base: 'md', md: 'lg' }}>
        {/* Single column mobile (100% width) */}
        <Grid gutter={{ base: 'sm', md: 'lg' }}>
          <Grid.Col span={{ base: 12, md: 6 }}>
            <SearchWidget />
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 6 }}>
            <FiltersWidget />
          </Grid.Col>
        </Grid>

        {/* Content area - responsive columns */}
        <Grid gutter={{ base: 'sm', md: 'lg' }}>
          <Grid.Col span={{ base: 12, sm: 6, md: 4 }}>
            <SidePanel />
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6, md: 8 }}>
            <MainContent />
          </Grid.Col>
        </Grid>
      </Stack>
    </Container>
  );
}
```

### 4. Responsive Typography

```tsx
import { Title, Text } from '@mantine/core';

// Font sizes scale on mobile
<Title order={1} size={{ base: 'h3', md: 'h1' }}>
  Responsive Heading
</Title>

<Text size={{ base: 'sm', md: 'md' }}>
  Responsive body text
</Text>
```

### 5. Mobile-Specific Navigation

```tsx
import { AppShell, Button, Drawer } from '@mantine/core';
import { useState } from 'react';
import { useMediaQuery } from '@mantine/hooks';

function AppLayout() {
  const [navOpen, setNavOpen] = useState(false);
  const isDesktop = useMediaQuery('(min-width: 48em)'); // sm breakpoint

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{
        width: 300,
        breakpoint: 'sm',
        collapsed: { mobile: !navOpen, desktop: false },
      }}
    >
      <AppShell.Header>
        {!isDesktop && (
          <Button onClick={() => setNavOpen(true)}>Menu</Button>
        )}
      </AppShell.Header>

      <AppShell.Navbar>
        <nav>Navigation</nav>
      </AppShell.Navbar>

      <AppShell.Main>Content</AppShell.Main>
    </AppShell>
  );
}
```

### 6. Viewport Meta Tag

**Ensure in HTML head:**
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0" />
```

---

## Implementation Checklist

### Phase 13 Tasks

#### Responsive Design Setup
- [ ] Verify Mantine breakpoints are configured in `theme.ts`
  - Use recommended values: `xs: 36em, sm: 48em, md: 62em, lg: 75em, xl: 88em`
- [ ] Document responsive prop usage pattern in component guidelines
- [ ] Create story examples for responsive behavior:
  - [ ] Dashboard with `useMatches` hook
  - [ ] Entities table with responsive columns
  - [ ] Chat interface with mobile-optimized layout
- [ ] Test responsive breakpoints across all three pages
  - [ ] Test at 320px (mobile), 768px (tablet), 1024px (desktop)

#### Accessibility Audit
- [ ] Configure Storybook a11y addon settings in `.storybook/preview.ts`
  - [ ] Set default test behavior to `'error'`
  - [ ] Create axe-core rules configuration
- [ ] Create accessibility checklist story template
- [ ] Audit all components against WCAG 2.1 AA:
  - [ ] Dashboard page
  - [ ] Entities page
  - [ ] Chat page

#### Touch Target & Mobile Optimization
- [ ] Audit all interactive elements for 44×44px minimum size
  - [ ] Update button sizes on mobile breakpoints
  - [ ] Verify spacing between touch targets (min 8px)
  - [ ] Test on actual mobile devices (iOS Safari, Android Chrome)

#### Keyboard Navigation
- [ ] Implement skip links on all pages
- [ ] Test Tab/Shift+Tab navigation order
  - [ ] Verify logical visual flow (left-to-right, top-to-bottom)
  - [ ] No keyboard traps (focus can always escape)
  - [ ] Focus indicators visible at all times
- [ ] Implement keyboard handlers for:
  - [ ] Navigation menus (Tab, Arrow keys, Enter)
  - [ ] Form inputs (Tab, Enter, Escape for modals)
  - [ ] Dropdowns/Selects (Arrow keys, Enter, Escape)
  - [ ] Modal dialogs (Focus trapping, Escape to close)

#### ARIA Implementation
- [ ] Navigation elements
  - [ ] `<nav aria-label>` for all navigation regions
  - [ ] `aria-current="page"` for active links
  - [ ] Mobile nav toggle: `aria-expanded` and `aria-label`
- [ ] Form elements
  - [ ] All inputs have associated labels (via `<label>` or `aria-label`)
  - [ ] Error states use `aria-invalid` and `aria-describedby`
  - [ ] Required fields marked with `required` or `aria-required`
- [ ] Dynamic content
  - [ ] Loading states: `role="status"` with `aria-live="polite"`
  - [ ] Form validation: `role="alert"` for error messages
  - [ ] Table headers: `scope="col"` for column headers
- [ ] Modals/Dialogs
  - [ ] `aria-labelledby` for title
  - [ ] `aria-describedby` for description
  - [ ] Focus management and trapping

#### Testing & Documentation
- [ ] Write React Testing Library tests for keyboard navigation
  - [ ] Test `userEvent.tab()` navigation order
  - [ ] Test keyboard-only scenarios
  - [ ] Test screen reader text via `getByRole` and `getByLabelText`
- [ ] Manual testing with:
  - [ ] Keyboard only (no mouse)
  - [ ] Screen reader (VoiceOver on Mac, NVDA or Narrator on Windows)
  - [ ] Browser zoom (up to 200%)
  - [ ] High contrast mode
- [ ] Document responsive utilities in `/docs/responsive-design.md`:
  - [ ] When to use `useMediaQuery` vs. `useMatches` vs. responsive props
  - [ ] Mobile-first CSS patterns
  - [ ] Component examples
- [ ] Document accessibility patterns in `/docs/accessibility.md`:
  - [ ] ARIA usage guidelines
  - [ ] Keyboard navigation requirements
  - [ ] Testing procedures

#### Storybook Stories
- [ ] Create responsive design stories:
  - [ ] `responsive/breakpoints.stories.tsx` - Show all breakpoints
  - [ ] `responsive/useMediaQuery.stories.tsx` - Hook examples
  - [ ] `responsive/useMatches.stories.tsx` - Multiple queries
- [ ] Create accessibility stories:
  - [ ] `accessibility/forms.stories.tsx` - ARIA form patterns
  - [ ] `accessibility/navigation.stories.tsx` - ARIA nav patterns
  - [ ] `accessibility/keyboard.stories.tsx` - Keyboard behavior
  - [ ] `accessibility/touch-targets.stories.tsx` - Button sizes for mobile
- [ ] Mark work-in-progress components with `a11y: { test: 'todo' }`

---

## Tools & Resources

### Storybook Plugins
- **@storybook/addon-a11y** (already installed) - Automated axe-core checks

### Testing Tools
- **axe-core** - Automated accessibility testing (via Storybook addon)
- **@testing-library/react** - Query by accessible selectors
- **eslint-plugin-jsx-a11y** - Catch accessibility issues at lint time

### Browser Tools
- **Chrome DevTools** - Accessibility panel, lighthouse
- **Firefox DevTools** - Accessibility inspector
- **Wave Browser Extension** - Visual feedback on accessibility issues
- **Axe DevTools** - Chrome/Firefox extension for detailed reports

### Screen Readers (Testing)
- **VoiceOver** (macOS/iOS built-in)
- **NVDA** (Windows, free)
- **Narrator** (Windows built-in)
- **ChromeVox** (Chrome extension)

### Reference Documentation
- **W3C WAI-ARIA Authoring Practices Guide (APG):** https://www.w3.org/WAI/ARIA/apg/
- **WCAG 2.1 Level AA Checklist:** https://www.w3.org/WAI/test-evaluate/
- **Mantine Responsive Documentation:** https://mantine.dev/styles/responsive/
- **Mantine Accessibility:** https://mantine.dev/guides/accessibility/
- **Testing Library Accessibility:** https://testing-library.com/docs/dom-testing-library/api-accessibility/

---

## Next Steps

1. **Establish Baseline:** Document current state of each page's accessibility
2. **Setup Documentation:** Create `/docs/responsive-design.md` and `/docs/accessibility.md`
3. **Configure Tooling:** Update Storybook a11y configuration
4. **Implement Patterns:** Apply ARIA and keyboard navigation to core components
5. **Test & Iterate:** Use Storybook a11y panel and manual testing to identify and fix issues
6. **CI Integration:** (Optional) Add `test-storybook` to CI pipeline for automated checks

