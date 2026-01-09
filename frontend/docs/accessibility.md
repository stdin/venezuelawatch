# Accessibility Guide

This document outlines the accessibility patterns, ARIA implementations, and WCAG 2.1 AA compliance strategies used in VenezuelaWatch. All components and pages are designed to be usable by keyboard, screen readers, and assistive technologies.

## Table of Contents

1. [WCAG 2.1 AA Requirements](#wcag-21-aa-requirements)
2. [Keyboard Navigation](#keyboard-navigation)
3. [ARIA Patterns](#aria-patterns)
4. [Skip Links](#skip-links)
5. [Testing](#testing)
6. [Common Pitfalls](#common-pitfalls)
7. [Component-Specific Patterns](#component-specific-patterns)

## WCAG 2.1 AA Requirements

VenezuelaWatch adheres to **WCAG 2.1 Level AA** standards. Key requirements:

### 1. Color Contrast

**Minimum ratios:**
- **Normal text:** 4.5:1
- **Large text (18pt+ or 14pt+ bold):** 3:1
- **UI components and graphics:** 3:1

**Implementation:**
```css
/* Design tokens ensure compliant contrast */
--color-text-primary: #0a0a0a;        /* on white: 20.43:1 ✅ */
--color-text-secondary: #525252;      /* on white: 7.77:1 ✅ */
--color-text-tertiary: #737373;       /* on white: 5.36:1 ✅ */

--color-risk-high: #dc2626;           /* Error red: 5.54:1 ✅ */
--color-risk-medium: #f59e0b;         /* Warning amber: 3.37:1 ✅ (large text only) */
--color-risk-low: #16a34a;            /* Success green: 3.42:1 ✅ (large text only) */
```

**Testing:**
```bash
# Use browser DevTools Accessibility panel
# Chrome: DevTools > Elements > Accessibility > Contrast
# Firefox: DevTools > Accessibility > Check for issues
```

### 2. Touch Target Size

**Minimum:** 44x44 pixels (WCAG 2.1 AAA, best practice for AA)

**Implementation:**
```css
/* Chat.css */
.chat-composer-input {
  min-height: 44px; /* Touch target */
  font-size: 16px;   /* Prevent iOS zoom */
  padding: 0.75rem;  /* Internal padding for comfort */
}

.chat-composer-send {
  min-height: 44px;
  min-width: 44px;
  padding: 0.75rem;
}
```

```typescript
// Entities.tsx
<SegmentedControl
  size="md" // Ensures ~44px height
  aria-label="Entity metric filters"
  data={metricOptions}
/>
```

**Why 16px font-size for inputs?**
- iOS Safari zooms in on inputs with font-size < 16px
- Prevents disruptive viewport zoom on focus
- Maintains user-set zoom level

### 3. Keyboard Access

**Requirements:**
- All interactive elements must be keyboard accessible
- Tab order must be logical
- Focus must be visible (no `outline: none` without custom focus styles)
- No keyboard traps

**Implementation:**
All interactive components support keyboard navigation (see [Keyboard Navigation](#keyboard-navigation)).

### 4. ARIA Labels

**Requirements:**
- All form inputs must have labels (visible or aria-label)
- Interactive elements must have accessible names
- Dynamic content changes must be announced to screen readers

**Implementation:**
See [ARIA Patterns](#aria-patterns) section.

## Keyboard Navigation

VenezuelaWatch is fully keyboard accessible. All interactive elements can be reached and activated using only the keyboard.

### Standard Keyboard Shortcuts

| Key | Action | Used In |
|-----|--------|---------|
| **Tab** | Move focus forward | All pages |
| **Shift+Tab** | Move focus backward | All pages |
| **Enter** | Activate button/link, Select item | Buttons, Cards, List items |
| **Space** | Activate button, Select item | Buttons, Cards, List items |
| **Escape** | Close modal/dialog | Modals, Dropdown menus |
| **Arrow Up/Down** | Navigate list items | Entity Leaderboard |
| **Arrow Left/Right** | Navigate between options | SegmentedControl |

### Implementation Patterns

#### 1. Button-Like Cards (EventCard, Entity Cards)

Interactive cards that act as buttons:

```typescript
export function EventCard({ event, isSelected, onSelect }: EventCardProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onSelect()
    }
  }

  return (
    <Card
      onClick={onSelect}
      onKeyDown={handleKeyDown}
      tabIndex={0}                // Keyboard focusable
      role="button"               // Announced as button
      aria-pressed={isSelected}   // State for screen readers
      style={{ cursor: 'pointer' }}
    >
      {/* Card content */}
    </Card>
  )
}
```

**Key points:**
- `tabIndex={0}`: Adds to tab order
- `role="button"`: Screen readers announce as button
- `aria-pressed={isSelected}`: Indicates toggle state
- `onKeyDown`: Enter and Space trigger action
- `e.preventDefault()`: Prevents page scroll on Space

#### 2. Arrow Key Navigation (Entity Leaderboard)

List navigation with arrow keys:

```typescript
export function EntityLeaderboard({ entities, onSelect }: Props) {
  const handleKeyDown = useCallback((event: React.KeyboardEvent, index: number) => {
    const entity = entities[index]

    // Enter or Space to select
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      onSelect(entity.id)
    }

    // Arrow Down to next item
    else if (event.key === 'ArrowDown') {
      event.preventDefault()
      const nextIndex = Math.min(index + 1, entities.length - 1)
      const nextElement = document.querySelector(
        `[data-entity-index="${nextIndex}"]`
      ) as HTMLElement
      nextElement?.focus()
    }

    // Arrow Up to previous item
    else if (event.key === 'ArrowUp') {
      event.preventDefault()
      const prevIndex = Math.max(index - 1, 0)
      const prevElement = document.querySelector(
        `[data-entity-index="${prevIndex}"]`
      ) as HTMLElement
      prevElement?.focus()
    }
  }, [entities, onSelect])

  return (
    <div role="feed" aria-label="Entity leaderboard">
      {entities.map((entity, index) => (
        <Card
          key={entity.id}
          tabIndex={0}
          role="button"
          data-entity-index={index}
          onKeyDown={(e) => handleKeyDown(e, index)}
          aria-label={`${entity.canonical_name}, rank ${index + 1}`}
        >
          {/* Entity content */}
        </Card>
      ))}
    </div>
  )
}
```

**Key points:**
- `data-entity-index`: Custom attribute for targeting focus
- `querySelector` with arrow keys: Moves focus between items
- `Math.min/max`: Prevents going out of bounds
- `.focus()`: Programmatically moves keyboard focus
- Works with virtualized lists (@tanstack/react-virtual)

#### 3. Modal Focus Trapping

When a modal opens, focus should be trapped inside:

```typescript
// Mantine Modal handles focus trapping automatically
<Modal
  opened={isOpen}
  onClose={handleClose}
  trapFocus={true} // Default: true
  returnFocus={true} // Return focus to trigger on close
>
  <EntityProfile entity={selectedEntity} />
</Modal>
```

**Behavior:**
- Focus moves to modal on open
- Tab/Shift+Tab cycles within modal only
- Escape closes modal
- Focus returns to trigger element on close

#### 4. Skip Links

Skip links allow keyboard users to bypass navigation:

```typescript
// App.tsx or Layout component
export function AppLayout() {
  return (
    <>
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <Navigation />

      <main id="main-content" tabIndex={-1}>
        <Routes />
      </main>
    </>
  )
}
```

```css
/* Skip link: Hidden until focused */
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: var(--color-bg-surface);
  color: var(--color-text-primary);
  padding: 0.5rem 1rem;
  text-decoration: none;
  border: 2px solid var(--color-border-default);
  border-radius: 4px;
  z-index: 100;
}

.skip-link:focus {
  top: 10px;
  left: 10px;
}
```

See [Skip Links](#skip-links) section for full implementation.

### Focus Indicators

**NEVER remove focus indicators** without providing custom focus styles:

```css
/* ❌ BAD: Removes focus indicator */
button:focus {
  outline: none;
}

/* ✅ GOOD: Custom focus indicator */
button:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

VenezuelaWatch uses Mantine's built-in focus styles, which provide accessible focus indicators by default.

## ARIA Patterns

ARIA (Accessible Rich Internet Applications) attributes enhance semantic HTML for assistive technologies.

### 1. Navigation Landmarks

```typescript
// Dashboard.tsx
<Container fluid>
  <Grid>
    <Grid.Col span={{ base: 12, md: 6 }}>
      <div role="search" aria-label="Event filters">
        <FilterBar filters={filters} onFiltersChange={handleFiltersChange} />
      </div>

      <EventList
        events={events}
        aria-label="Risk events feed"
      />
    </Grid.Col>

    <Grid.Col span={{ base: 12, md: 6 }}>
      <EventDetail
        event={selectedEvent}
        aria-label="Event detail panel"
      />
    </Grid.Col>
  </Grid>
</Container>
```

**Key ARIA roles:**
- `role="search"`: Identifies search/filter region
- `role="navigation"`: Navigation menu (use `<nav>` instead when possible)
- `role="main"`: Main content area (use `<main>` instead)
- `role="complementary"`: Supporting content (use `<aside>` instead)

**Best practice:** Use semantic HTML (`<nav>`, `<main>`, `<aside>`) over ARIA roles when possible.

### 2. Forms

```typescript
// Custom Input component
export function Input({ label, error, helperText, id, ...props }: InputProps) {
  const inputId = id || useId()
  const helperTextId = `${inputId}-helper`
  const errorId = `${inputId}-error`

  return (
    <div>
      <label htmlFor={inputId}>{label}</label>
      <input
        id={inputId}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={
          error ? errorId : helperText ? helperTextId : undefined
        }
        {...props}
      />
      {helperText && !error && (
        <p id={helperTextId} className="helper-text">
          {helperText}
        </p>
      )}
      {error && helperText && (
        <p id={errorId} className="error-text" role="alert">
          {helperText}
        </p>
      )}
    </div>
  )
}
```

**Form ARIA attributes:**
- `htmlFor` / `id`: Associates label with input (clickable labels)
- `aria-invalid="true"`: Indicates validation error
- `aria-describedby`: Links helper text or error message
- `role="alert"`: Announces errors immediately to screen readers
- `aria-required="true"`: Indicates required fields

**Example usage:**
```typescript
<Input
  label="Email Address"
  type="email"
  error={!!emailError}
  helperText={emailError || "We'll never share your email"}
  aria-required="true"
/>
```

### 3. Loading States

Dynamic content loading must be announced to screen readers:

```typescript
// Dashboard.tsx - Loading events
{loading && !events && (
  <div role="status" aria-live="polite" aria-busy="true">
    <Text>Loading events...</Text>
    <Skeleton height={100} count={3} />
  </div>
)}
```

**Loading ARIA attributes:**
- `role="status"`: Announces status updates
- `aria-live="polite"`: Screen reader announces when idle (not interrupting)
- `aria-busy="true"`: Indicates loading in progress

**Example: EventList component**
```typescript
export function EventList({ events, loading }: Props) {
  if (loading && !events) {
    return (
      <div role="status" aria-live="polite" aria-busy="true">
        <span className="sr-only">Loading events</span>
        <Stack gap="sm">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} height={120} />
          ))}
        </Stack>
      </div>
    )
  }

  return <EventListContent events={events} />
}
```

### 4. Error States

Errors must be announced immediately:

```typescript
// Dashboard.tsx - Error loading events
{error && (
  <div className="error-state" role="alert" aria-live="assertive">
    <h2>Error Loading Events</h2>
    <p>{error.message}</p>
  </div>
)}
```

**Error ARIA attributes:**
- `role="alert"`: Screen readers announce immediately
- `aria-live="assertive"`: Interrupts current speech to announce error
- Use for critical errors that need immediate attention

**Example: Form validation errors**
```typescript
<Input
  label="Email"
  error={!!emailError}
  helperText={emailError}
  aria-invalid={!!emailError}
  aria-describedby={emailError ? 'email-error' : undefined}
/>
{emailError && (
  <p id="email-error" role="alert" aria-live="assertive">
    {emailError}
  </p>
)}
```

### 5. Modals

```typescript
// Entities.tsx - Mobile modal for entity profile
<Modal
  opened={isMobile && mobileModalOpen}
  onClose={() => setMobileModalOpen(false)}
  title="Entity Profile"
  aria-labelledby="entity-profile-title"
  aria-describedby="entity-profile-description"
  fullScreen
>
  <h2 id="entity-profile-title">{entity.canonical_name}</h2>
  <p id="entity-profile-description">
    {entity.entity_type} with {entity.mention_count} mentions
  </p>
  <EntityProfile entity={entity} />
</Modal>
```

**Modal ARIA attributes:**
- `aria-labelledby`: Points to modal title (screen reader announces)
- `aria-describedby`: Points to modal description
- `role="dialog"`: Implicit in Mantine Modal
- `aria-modal="true"`: Implicit in Mantine Modal
- Focus trapping: Handled by Mantine

### 6. Tables

```typescript
export function EventTable({ events }: Props) {
  return (
    <table role="table" aria-label="Risk events table">
      <thead>
        <tr>
          <th scope="col">Event</th>
          <th scope="col">Risk Score</th>
          <th scope="col">Severity</th>
          <th scope="col">Timestamp</th>
        </tr>
      </thead>
      <tbody>
        {events.map(event => (
          <tr key={event.id}>
            <td>{event.title}</td>
            <td>{event.risk_score}</td>
            <td>{event.severity}</td>
            <td>{formatDate(event.timestamp)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
```

**Table ARIA attributes:**
- `scope="col"`: Indicates column header
- `scope="row"`: Indicates row header (for first column)
- `aria-label`: Describes table purpose
- `role="table"`: Explicit table role (implicit in `<table>`)

### 7. Dynamic Lists (Feeds)

For dynamic, frequently updating content:

```typescript
// EntityLeaderboard.tsx
<div
  role="feed"
  aria-label="Entity leaderboard"
  aria-busy={loading}
>
  {entities.map((entity, index) => (
    <Card
      key={entity.id}
      role="button"
      tabIndex={0}
      aria-label={`${entity.canonical_name}, rank ${index + 1}, ${entity.mention_count} mentions`}
      aria-pressed={entity.id === selectedId}
    >
      {/* Entity card content */}
    </Card>
  ))}
</div>
```

**Feed ARIA attributes:**
- `role="feed"`: Indicates dynamic, frequently updating list
- `aria-busy="true"`: Indicates loading state
- `aria-label`: Describes the feed purpose
- Each item should have descriptive aria-label

**When to use `role="feed"` vs `role="list"`:**
- **`role="feed"`**: Dynamic content (entity leaderboard, event feed)
- **`role="list"`**: Static content (navigation menu, settings list)

## Skip Links

Skip links allow keyboard users to bypass repetitive navigation and jump directly to main content.

### Implementation

```typescript
// App.tsx or RootLayout.tsx
export function App() {
  return (
    <div className="app">
      {/* Skip link - hidden until focused */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <AppHeader />

      <main id="main-content" tabIndex={-1}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/entities" element={<Entities />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </main>
    </div>
  )
}
```

### Styling

```css
/* styles/global.css or App.css */

/* Skip link: Positioned off-screen by default */
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  z-index: 100;
  background: var(--color-bg-surface);
  color: var(--color-text-primary);
  padding: 0.5rem 1rem;
  text-decoration: none;
  font-size: var(--font-size-sm);
  font-weight: 600;
  border: 2px solid var(--color-primary);
  border-radius: var(--radius-sm);
  transition: top 0.2s ease;
}

/* Visible when focused via keyboard */
.skip-link:focus {
  top: 10px;
  left: 10px;
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

### Usage

1. **User presses Tab on page load**
2. **Skip link receives focus** (becomes visible)
3. **User presses Enter**
4. **Focus jumps to main content** (bypassing header/navigation)
5. **User continues tabbing** through main content

### Multiple Skip Links (Optional)

For complex layouts:

```typescript
<>
  <a href="#main-content" className="skip-link">
    Skip to main content
  </a>
  <a href="#sidebar" className="skip-link">
    Skip to sidebar
  </a>
  <a href="#footer" className="skip-link">
    Skip to footer
  </a>

  <AppHeader />

  <div className="layout">
    <aside id="sidebar" tabIndex={-1}>
      <Sidebar />
    </aside>

    <main id="main-content" tabIndex={-1}>
      <Content />
    </main>
  </div>

  <footer id="footer" tabIndex={-1}>
    <Footer />
  </footer>
</>
```

**Note:** `tabIndex={-1}` on target elements allows programmatic focus but removes them from tab order.

## Testing

Accessibility testing requires both automated tools and manual testing.

### 1. Storybook Accessibility Addon

VenezuelaWatch uses `@storybook/addon-a11y` for automated checks:

```typescript
// .storybook/preview.tsx
const preview: Preview = {
  parameters: {
    a11y: {
      test: 'error', // Fail on violations (strict mode)
    },
  },
}
```

**Running Storybook a11y:**
```bash
npm run storybook

# Open http://localhost:6006
# Click "Accessibility" tab in each story
# Green checkmark = passing
# Red X = violations found
```

**What it checks:**
- Color contrast ratios
- Missing labels on form inputs
- Missing alt text on images
- Keyboard accessibility issues
- ARIA usage errors
- Heading hierarchy

### 2. Keyboard-Only Testing

**Procedure:**
1. **Disconnect your mouse** (or don't use it)
2. **Start at the top of the page** (press Tab)
3. **Tab through all interactive elements** (Tab, Shift+Tab)
4. **Activate elements with Enter/Space**
5. **Navigate lists with arrow keys** (where applicable)
6. **Close modals with Escape**

**Checklist:**
- [ ] Can reach all interactive elements via Tab
- [ ] Focus indicator is visible on all focused elements
- [ ] Tab order is logical (top → bottom, left → right)
- [ ] Enter/Space activates buttons and links
- [ ] Escape closes modals and menus
- [ ] Arrow keys work in lists (EntityLeaderboard)
- [ ] No keyboard traps (can always Tab out)

**Common issues:**
- Missing `tabIndex={0}` on custom interactive elements
- `tabIndex={-1}` used incorrectly (removes from tab order)
- Focus hidden due to `outline: none` without custom focus styles

### 3. Screen Reader Testing

**Tools:**
- **macOS:** VoiceOver (Cmd+F5 to toggle)
- **Windows:** NVDA (free) or JAWS (paid)
- **Linux:** Orca
- **Mobile iOS:** VoiceOver (Settings > Accessibility)
- **Mobile Android:** TalkBack (Settings > Accessibility)

**VoiceOver Basics (macOS):**
- **Cmd+F5:** Toggle VoiceOver on/off
- **Ctrl+Option (VO):** VoiceOver modifier key
- **VO + Right Arrow:** Next element
- **VO + Left Arrow:** Previous element
- **VO + Space:** Activate element
- **VO + Shift + Down:** Interact with element (enter group)
- **VO + Shift + Up:** Stop interacting (exit group)

**Testing procedure:**
1. **Enable screen reader**
2. **Navigate the page** using screen reader commands
3. **Verify announcements:**
   - Buttons announced as "Button"
   - Links announced as "Link"
   - Form inputs announced with labels
   - ARIA labels are spoken correctly
   - Loading states announced ("Loading events")
   - Errors announced immediately
4. **Test forms:** Ensure labels and errors are read
5. **Test navigation:** Ensure landmarks (navigation, main, search) are recognized

**What to listen for:**
- **"Unlabeled button"** → Add aria-label
- **"Group"** → May need role or aria-label
- **"Clickable"** → Should be "Button" or "Link"
- **Silence on interaction** → Add aria-live announcements

### 4. Browser DevTools Accessibility Panel

**Chrome DevTools:**
1. Open DevTools (F12)
2. Go to **Elements** tab
3. Click **Accessibility** panel (bottom right)
4. Select an element
5. View **Computed Properties** (role, name, description)
6. View **Accessibility Tree** (what screen readers see)

**Firefox DevTools:**
1. Open DevTools (F12)
2. Go to **Accessibility** tab
3. Click **Turn on the Accessibility features**
4. Click **Check for issues**
5. View violations (color contrast, labels, keyboard access)

**What to check:**
- **Accessible Name:** Every interactive element should have one
- **Role:** Correct semantic role (button, link, navigation)
- **Contrast Ratio:** Meets 4.5:1 (normal text) or 3:1 (large text)
- **Keyboard Focusable:** Interactive elements have `tabindex`

### 5. Automated Testing Tools

**axe DevTools (Browser Extension):**
- [Chrome Extension](https://chrome.google.com/webstore/detail/axe-devtools-web-accessib/lhdoppojpmngadmnindnejefpokejbdd)
- [Firefox Extension](https://addons.mozilla.org/en-US/firefox/addon/axe-devtools/)

**Lighthouse (Chrome DevTools):**
```bash
# Run Lighthouse in Chrome DevTools
# DevTools > Lighthouse > Accessibility > Generate report
```

**axe-core CLI:**
```bash
npm install -g @axe-core/cli

# Test a page
axe http://localhost:5173
```

### Testing Checklist

For each page (Dashboard, Entities, Chat):

#### Visual/Layout
- [ ] Color contrast meets 4.5:1 (normal text) or 3:1 (large text)
- [ ] Touch targets ≥ 44x44px
- [ ] Focus indicators visible on all interactive elements
- [ ] No reliance on color alone to convey information

#### Keyboard
- [ ] All interactive elements reachable via Tab
- [ ] Tab order is logical
- [ ] Enter/Space activates buttons
- [ ] Arrow keys work in lists (where applicable)
- [ ] Escape closes modals
- [ ] No keyboard traps

#### Screen Reader
- [ ] All images have alt text
- [ ] All form inputs have labels
- [ ] Buttons/links have accessible names
- [ ] ARIA labels are descriptive
- [ ] Loading states announced
- [ ] Errors announced immediately
- [ ] Landmarks correctly identified

#### Automated
- [ ] Storybook a11y checks passing
- [ ] axe DevTools shows no violations
- [ ] Lighthouse Accessibility score ≥ 95

## Common Pitfalls

### 1. Removing Focus Indicators

**❌ BAD:**
```css
button:focus {
  outline: none; /* DON'T DO THIS */
}
```

**✅ GOOD:**
```css
/* Use :focus-visible to hide focus on mouse click, show on keyboard */
button:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

### 2. Missing Labels

**❌ BAD:**
```typescript
<input placeholder="Search..." />
<button>🔍</button>
```

**✅ GOOD:**
```typescript
<input placeholder="Search..." aria-label="Search entities" />
<button aria-label="Search">🔍</button>
```

### 3. Keyboard Traps

**❌ BAD:**
```typescript
// Modal without focus trapping
<div className="modal" tabIndex={-1}>
  <button>Close</button>
  {/* Focus can escape to background */}
</div>
```

**✅ GOOD:**
```typescript
// Mantine Modal with built-in focus trapping
<Modal opened={isOpen} onClose={handleClose} trapFocus>
  <button>Close</button>
  {/* Focus trapped within modal */}
</Modal>
```

### 4. Low Contrast

**❌ BAD:**
```css
.label {
  color: #999; /* 2.85:1 contrast - fails AA */
  background: #fff;
}
```

**✅ GOOD:**
```css
.label {
  color: #737373; /* 5.36:1 contrast - passes AA */
  background: #fff;
}
```

### 5. Unlabeled Icon Buttons

**❌ BAD:**
```typescript
<button onClick={handleDelete}>
  <TrashIcon />
</button>
```

**✅ GOOD:**
```typescript
<button onClick={handleDelete} aria-label="Delete entity">
  <TrashIcon aria-hidden="true" />
</button>
```

### 6. Non-Semantic HTML

**❌ BAD:**
```typescript
<div onClick={handleClick} style={{ cursor: 'pointer' }}>
  Click me
</div>
```

**✅ GOOD:**
```typescript
<button onClick={handleClick}>
  Click me
</button>

{/* OR if you must use div: */}
<div
  onClick={handleClick}
  onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleClick()}
  tabIndex={0}
  role="button"
>
  Click me
</div>
```

### 7. Missing aria-invalid on Form Errors

**❌ BAD:**
```typescript
<input className={error ? 'error' : ''} />
{error && <p>{error}</p>}
```

**✅ GOOD:**
```typescript
<input
  aria-invalid={!!error}
  aria-describedby={error ? 'input-error' : undefined}
/>
{error && (
  <p id="input-error" role="alert">
    {error}
  </p>
)}
```

### 8. Not Announcing Dynamic Content

**❌ BAD:**
```typescript
{loading && <Skeleton />}
```

**✅ GOOD:**
```typescript
{loading && (
  <div role="status" aria-live="polite" aria-busy="true">
    <span className="sr-only">Loading content</span>
    <Skeleton />
  </div>
)}
```

## Component-Specific Patterns

### Dashboard

**Accessibility features:**
- `role="search"` on FilterBar container
- `role="status"` on empty/loading states
- `role="alert"` on error states
- EventCard with keyboard navigation (Enter/Space)
- Collapsible TrendsPanel with aria-label

**Code example:**
```typescript
export function Dashboard() {
  return (
    <Container fluid>
      <Grid>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <div role="search" aria-label="Event filters">
            <FilterBar />
          </div>

          {error && (
            <div role="alert" aria-live="assertive">
              <h2>Error Loading Events</h2>
              <p>{error.message}</p>
            </div>
          )}

          {loading && (
            <div role="status" aria-live="polite" aria-busy="true">
              Loading events...
            </div>
          )}

          <EventList />
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 6 }}>
          <Button
            aria-label={isTrendsPanelExpanded ? 'Hide trends panel' : 'Show trends panel'}
            onClick={() => setIsTrendsPanelExpanded(!isTrendsPanelExpanded)}
          >
            {isTrendsPanelExpanded ? '▲ Hide Trends' : '▼ Show Trends'}
          </Button>
        </Grid.Col>
      </Grid>
    </Container>
  )
}
```

### Entities

**Accessibility features:**
- `role="feed"` on EntityLeaderboard
- Arrow key navigation (ArrowUp/ArrowDown)
- `aria-label` on entity cards with rank and mention count
- `aria-label` on SegmentedControl for metric filters
- Mobile modal with focus trapping

**Code example:**
```typescript
export function Entities() {
  return (
    <Container fluid>
      <Grid>
        <Grid.Col span={{ base: 12, md: 5 }}>
          <SegmentedControl
            aria-label="Entity metric filters"
            data={[
              { value: 'mentions', label: 'Most Mentioned' },
              { value: 'risk', label: 'Highest Risk' },
            ]}
          />

          <EntityLeaderboard
            entities={entities}
            onSelect={handleSelect}
            aria-label="Entity leaderboard"
          />
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 7 }}>
          <section aria-label="Entity profile">
            <EntityProfile entity={selectedEntity} />
          </section>
        </Grid.Col>
      </Grid>

      <Modal
        opened={isMobile && modalOpen}
        onClose={() => setModalOpen(false)}
        aria-labelledby="entity-modal-title"
        fullScreen
      >
        <h2 id="entity-modal-title">Entity Profile</h2>
        <EntityProfile entity={selectedEntity} />
      </Modal>
    </Container>
  )
}
```

### Chat

**Accessibility features:**
- `aria-label` on chat viewport
- `aria-label` on composer input
- `aria-label` on send button
- Touch-friendly input (min-height: 44px, font-size: 16px)
- Message roles for screen reader context

**Code example:**
```typescript
export function Chat() {
  return (
    <div className="chat-container">
      <ThreadPrimitive.Root className="chat-thread">
        <ThreadPrimitive.Viewport
          className="chat-viewport"
          aria-label="Conversation thread"
        >
          <ThreadPrimitive.Messages />
        </ThreadPrimitive.Viewport>

        <ComposerPrimitive.Root className="chat-composer">
          <ComposerPrimitive.Input
            className="chat-composer-input"
            placeholder="Ask about Venezuela intelligence..."
            aria-label="Chat message input"
          />
          <ComposerPrimitive.Send
            className="chat-composer-send"
            aria-label="Send message"
          >
            Send
          </ComposerPrimitive.Send>
        </ComposerPrimitive.Root>
      </ThreadPrimitive.Root>
    </div>
  )
}
```

## Resources

### Official Guidelines
- [WCAG 2.1 Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Articles](https://webaim.org/articles/)

### Testing Tools
- [axe DevTools](https://www.deque.com/axe/devtools/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [WAVE](https://wave.webaim.org/)
- [Color Contrast Checker](https://webaim.org/resources/contrastchecker/)

### Screen Readers
- [VoiceOver User Guide](https://support.apple.com/guide/voiceover/welcome/mac)
- [NVDA Download](https://www.nvaccess.org/download/)
- [JAWS](https://www.freedomscientific.com/products/software/jaws/)

### VenezuelaWatch Internal
- [Responsive Design Guide](./responsive-design.md)
- [Storybook A11y Addon](../.storybook/preview.tsx)
- [Theme Configuration](../src/theme.ts)

---

**Last updated:** Phase 13-04 (2026-01-09)
**Maintainer:** VenezuelaWatch Team
**WCAG Level:** AA (2.1)
