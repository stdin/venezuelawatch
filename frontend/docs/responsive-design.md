# Responsive Design Guide

This document outlines the responsive design patterns and practices used in VenezuelaWatch. All pages are designed to work seamlessly from 320px (mobile) to 1440px+ (large desktop) viewports.

## Table of Contents

1. [Breakpoints](#breakpoints)
2. [Responsive Utilities](#responsive-utilities)
3. [Grid Patterns](#grid-patterns)
4. [Component Examples](#component-examples)
5. [Mobile-First Approach](#mobile-first-approach)
6. [Testing](#testing)
7. [Common Patterns](#common-patterns)

## Breakpoints

VenezuelaWatch uses custom Mantine breakpoints defined in `src/theme.ts`:

```typescript
export const theme = createTheme({
  breakpoints: {
    xs: '36em',  // 576px - Mobile devices
    sm: '48em',  // 768px - Tablets portrait
    md: '62em',  // 992px - Tablets landscape / small laptops
    lg: '75em',  // 1200px - Desktops
    xl: '88em',  // 1408px - Large desktops
  },
})
```

### When to Use Each Breakpoint

- **base (< 576px)**: Mobile phones in portrait mode
- **xs (576px+)**: Mobile phones in landscape mode, small tablets
- **sm (768px+)**: Tablets in portrait mode
- **md (992px+)**: Tablets in landscape mode, small laptops
- **lg (1200px+)**: Desktop displays
- **xl (1408px+)**: Large desktop displays

## Responsive Utilities

Mantine provides three main approaches for responsive behavior:

### 1. useMediaQuery Hook

Use for **component-level responsive logic** (showing/hiding components, changing behavior):

```typescript
import { useMediaQuery } from '@mantine/hooks'

function MyComponent() {
  const isMobile = useMediaQuery('(max-width: 48em)') // < 768px

  return (
    <div>
      {isMobile ? (
        <MobileView />
      ) : (
        <DesktopView />
      )}
    </div>
  )
}
```

**When to use:**
- Conditional rendering based on viewport size
- Changing component behavior (e.g., opening modals on mobile vs side panels on desktop)
- Dashboard TrendsPanel collapse behavior

**Example from Dashboard:**
```typescript
const isMobile = useMediaQuery('(max-width: 48em)')

{isMobile && (
  <Button onClick={() => setIsTrendsPanelExpanded(!isTrendsPanelExpanded)}>
    {isTrendsPanelExpanded ? '▲ Hide Trends' : '▼ Show Trends'}
  </Button>
)}
```

### 2. useMatches Hook

Use for **selecting values based on breakpoint** (more granular than useMediaQuery):

```typescript
import { useMatches } from '@mantine/core'

function MyComponent() {
  const isMobile = useMatches({
    base: true,   // mobile: true
    md: false,    // desktop: false
  })

  const columns = useMatches({
    base: 1,      // mobile: 1 column
    sm: 2,        // tablet: 2 columns
    lg: 3,        // desktop: 3 columns
  })

  return <div>Content</div>
}
```

**When to use:**
- Need different values at different breakpoints
- More than 2 breakpoint variations
- Non-boolean responsive values

**Example from Entities:**
```typescript
const isMobile = useMatches({
  base: true,
  md: false,
})

// On mobile, open modal. On desktop, show in side panel
const handleEntitySelect = (id: string) => {
  setSelectedEntityId(id)
  if (isMobile) {
    setMobileModalOpen(true)
  }
}
```

### 3. Responsive Props

Use for **component styling** (most common, least code):

```typescript
import { Grid, Stack, Title } from '@mantine/core'

function MyComponent() {
  return (
    <Stack gap={{ base: 'sm', md: 'lg' }}>
      <Title order={{ base: 3, md: 2 }} />
      <Grid>
        <Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
          Content
        </Grid.Col>
      </Grid>
    </Stack>
  )
}
```

**When to use:**
- Changing component props at different breakpoints
- Layout adjustments (spacing, sizing, spans)
- Most styling scenarios

## Grid Patterns

### Two-Column Split View (Dashboard, Entities)

Desktop: 50/50 split
Mobile: Stacked full-width

```typescript
<Grid>
  {/* Left column: List/Feed */}
  <Grid.Col span={{ base: 12, md: 6 }}>
    <EventList />
  </Grid.Col>

  {/* Right column: Detail */}
  <Grid.Col span={{ base: 12, md: 6 }}>
    <EventDetail />
  </Grid.Col>
</Grid>
```

### Dashboard Pattern (40/60 Split on Entities)

```typescript
<Grid>
  {/* Left: Entity leaderboard (narrower) */}
  <Grid.Col span={{ base: 12, md: 5 }}>
    <EntityLeaderboard />
  </Grid.Col>

  {/* Right: Entity profile (wider) */}
  <Grid.Col span={{ base: 12, md: 7 }}>
    <EntityProfile />
  </Grid.Col>
</Grid>
```

### Responsive Card Grid

```typescript
<Grid>
  <Grid.Col span={{ base: 12, sm: 6, lg: 4 }}>
    <Card>Metric 1</Card>
  </Grid.Col>
  <Grid.Col span={{ base: 12, sm: 6, lg: 4 }}>
    <Card>Metric 2</Card>
  </Grid.Col>
  <Grid.Col span={{ base: 12, sm: 6, lg: 4 }}>
    <Card>Metric 3</Card>
  </Grid.Col>
</Grid>
```

## Component Examples

### Dashboard: 2-Column Layout with Collapsible Panel

**Desktop (≥ 768px):**
- Events list: Left 50%
- Trends + Detail: Right 50%
- Trends panel always visible

**Mobile (< 768px):**
- Events list: Full width
- Trends: Collapsible with toggle button
- Detail: Full width below

```typescript
export function Dashboard() {
  const isMobile = useMediaQuery('(max-width: 48em)')
  const [isTrendsPanelExpanded, setIsTrendsPanelExpanded] = useState(false)

  return (
    <Container fluid>
      <Grid>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <FilterBar />
          <EventList />
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 6 }}>
          {isMobile && (
            <Button onClick={() => setIsTrendsPanelExpanded(!isTrendsPanelExpanded)}>
              {isTrendsPanelExpanded ? '▲ Hide Trends' : '▼ Show Trends'}
            </Button>
          )}
          <Collapse in={!isMobile || isTrendsPanelExpanded}>
            <TrendsPanel />
          </Collapse>
          <EventDetail />
        </Grid.Col>
      </Grid>
    </Container>
  )
}
```

### Entities: Split-View → Modal Pattern

**Desktop (≥ 992px):**
- Entity list: Left 40%
- Entity profile: Right 60% (persistent side panel)

**Mobile (< 992px):**
- Entity list: Full width
- Entity profile: Fullscreen modal (overlay)

```typescript
export function Entities() {
  const [mobileModalOpen, setMobileModalOpen] = useState(false)

  const isMobile = useMatches({
    base: true,
    md: false,
  })

  const handleEntitySelect = (id: string) => {
    setSelectedEntityId(id)
    if (isMobile) {
      setMobileModalOpen(true)
    }
  }

  return (
    <Container fluid>
      <Grid>
        <Grid.Col span={{ base: 12, md: 5 }}>
          <EntityLeaderboard onSelect={handleEntitySelect} />
        </Grid.Col>

        {/* Desktop: Side panel */}
        {!isMobile && (
          <Grid.Col span={7}>
            <EntityProfile entity={selectedEntity} />
          </Grid.Col>
        )}
      </Grid>

      {/* Mobile: Modal */}
      <Modal opened={isMobile && mobileModalOpen} onClose={() => setMobileModalOpen(false)} fullScreen>
        <EntityProfile entity={selectedEntity} />
      </Modal>
    </Container>
  )
}
```

### Chat: Center-Focused Layout

**All viewports:**
- Centered content column
- Max-width: 44rem (704px)
- Fluid padding scales with viewport

```typescript
// Chat.css
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: clamp(0.5rem, 2vw, 1.5rem); /* 8px → 24px */
}

.chat-content {
  width: 100%;
  max-width: 44rem; /* 704px */
  margin: 0 auto;
}
```

## Mobile-First Approach

VenezuelaWatch follows a **mobile-first design strategy**:

1. **Base styles target mobile** (< 576px)
2. **Progressive enhancement** adds complexity at larger breakpoints
3. **Syntax: `{ base, md, lg }`**

### Mobile-First Examples

```typescript
// ✅ GOOD: Mobile-first
<Stack gap={{ base: 'sm', md: 'md', lg: 'xl' }}>
  // Starts at 'sm' (8px), grows to 'md' (16px) at 992px, 'xl' (32px) at 1200px
</Stack>

<Grid.Col span={{ base: 12, md: 6, lg: 4 }}>
  // Mobile: full width, Tablet: half width, Desktop: third width
</Grid.Col>

<Title order={{ base: 3, md: 2, lg: 1 }}>
  // Mobile: h3 (smaller), Tablet: h2, Desktop: h1 (largest)
</Title>
```

```typescript
// ❌ BAD: Desktop-first (avoid)
<Stack gap={{ lg: 'xl', md: 'md', base: 'sm' }}>
  // Works but harder to reason about
</Stack>
```

### Progressive Enhancement Pattern

```typescript
function EventCard() {
  return (
    <Card padding={{ base: 'sm', md: 'md', lg: 'lg' }}>
      <Stack gap={{ base: 'xs', md: 'sm' }}>
        <Title order={{ base: 4, md: 3 }}>Event Title</Title>
        <Text size={{ base: 'xs', md: 'sm' }}>Description</Text>
      </Stack>
    </Card>
  )
}
```

**Progression:**
- **Mobile (base):** Compact spacing (xs), smaller text (xs), h4 title
- **Tablet (md):** More breathing room (sm/md), readable text (sm), h3 title
- **Desktop (lg):** Generous spacing (lg), comfortable reading

## Testing

### Browser DevTools Testing

1. **Chrome/Firefox DevTools:**
   - Open DevTools (F12)
   - Click "Toggle Device Toolbar" (Ctrl+Shift+M / Cmd+Shift+M)
   - Select preset devices or enter custom dimensions
   - Test breakpoints: 320px, 375px, 768px, 992px, 1200px, 1440px

2. **Responsive Design Mode (Firefox):**
   - More accurate than Chrome for testing touch targets
   - Shows actual device pixel ratios
   - Built-in device presets

### Key Test Dimensions

| Device Type | Width | Breakpoint | Notes |
|-------------|-------|------------|-------|
| iPhone SE | 320px | base | Smallest modern phone |
| iPhone 12/13 | 390px | base | Common mobile size |
| Tablet Portrait | 768px | sm | Breakpoint boundary |
| Tablet Landscape | 1024px | md | Common tablet size |
| Laptop | 1280px | lg | Common laptop |
| Desktop | 1440px | xl | Large desktop |

### Testing Checklist

For each page (Dashboard, Entities, Chat):

- [ ] **320px:** Content doesn't overflow, text is readable
- [ ] **375px:** Comfortable mobile experience
- [ ] **768px:** Transition to tablet layout is smooth
- [ ] **992px:** Desktop layout appears, all features accessible
- [ ] **1440px+:** Content doesn't look sparse, max-widths prevent line length issues

### Actual Device Testing

Emulators are good but not perfect. Test on real devices when possible:

- **iOS Safari:** Different rendering engine (WebKit)
- **Android Chrome:** Test touch targets and gestures
- **iPad:** Verify tablet layouts
- **Physical keyboard:** Test on laptops for keyboard interactions

### Automated Testing

```bash
# Run Storybook and test responsive stories
npm run storybook

# Build and check for responsive issues
npm run build
```

## Common Patterns

### 1. Responsive Stack Spacing

```typescript
<Stack gap={{ base: 'sm', md: 'md', lg: 'xl' }}>
  <Child1 />
  <Child2 />
</Stack>
```

### 2. Responsive Typography

```typescript
<Title order={{ base: 3, md: 2 }}>Page Title</Title>
<Text size={{ base: 'sm', md: 'md' }}>Body text</Text>
```

### 3. Responsive Container Padding

```typescript
<Container fluid px={{ base: 'xs', sm: 'md', lg: 'xl' }}>
  Content
</Container>
```

### 4. Responsive Button Groups

```typescript
<Group
  justify={{ base: 'center', md: 'flex-start' }}
  gap={{ base: 'xs', md: 'sm' }}
>
  <Button>Action 1</Button>
  <Button>Action 2</Button>
</Group>
```

### 5. Responsive Cards

```typescript
<Card
  padding={{ base: 'sm', md: 'md', lg: 'lg' }}
  radius={{ base: 'sm', md: 'md' }}
>
  <Stack gap={{ base: 'xs', md: 'sm' }}>
    <Title order={{ base: 4, md: 3 }}>Card Title</Title>
    <Text size={{ base: 'xs', md: 'sm' }}>Card content</Text>
  </Stack>
</Card>
```

### 6. Touch-Friendly Targets (Mobile)

Ensure interactive elements meet **44x44px** minimum (WCAG 2.1 AA):

```css
/* Chat.css */
.chat-composer-input {
  min-height: 44px; /* WCAG touch target */
  font-size: 16px;   /* Prevent iOS zoom on focus */
}

.chat-composer-send {
  min-height: 44px;
  min-width: 44px;
}
```

```typescript
// Entities page
<SegmentedControl
  size="md" // 'md' = ~44px height for touch
  data={metricOptions}
/>
```

### 7. Fluid Typography with clamp()

```css
/* Chat.css */
.chat-container {
  padding: clamp(0.5rem, 2vw, 1.5rem);
}

.chat-welcome-title {
  font-size: clamp(1.5rem, 4vw, 2.5rem);
}
```

**Pattern:** `clamp(min, preferred, max)`
- **min:** Smallest value (mobile)
- **preferred:** Viewport-relative (scales)
- **max:** Largest value (desktop cap)

### 8. Conditional Mobile Modals

```typescript
// Desktop: Side panel
// Mobile: Fullscreen modal

const isMobile = useMatches({ base: true, md: false })

<Modal
  opened={isMobile && isOpen}
  onClose={handleClose}
  fullScreen // Mobile gets fullscreen
>
  <Content />
</Modal>
```

### 9. Responsive Grid Columns

```typescript
// 1 column mobile → 2 columns tablet → 3 columns desktop
<Grid>
  {items.map(item => (
    <Grid.Col key={item.id} span={{ base: 12, sm: 6, lg: 4 }}>
      <ItemCard item={item} />
    </Grid.Col>
  ))}
</Grid>
```

### 10. Responsive Image Sizing

```typescript
<Image
  src={imageUrl}
  width={{ base: '100%', md: '50%', lg: '33%' }}
  height="auto"
  fit="cover"
/>
```

## Best Practices Summary

1. **Use responsive props first** for simple styling (gap, padding, span)
2. **Use useMatches for values** when you need more than 2 breakpoints
3. **Use useMediaQuery for behavior** when showing/hiding components
4. **Test at all 5 breakpoints** (320px, 768px, 992px, 1200px, 1440px)
5. **Touch targets ≥ 44x44px** for mobile (WCAG 2.1 AA)
6. **Font-size ≥ 16px** for inputs (prevents iOS zoom)
7. **Use clamp() for fluid scaling** instead of multiple breakpoints
8. **Mobile-first syntax** (base → md → lg progression)
9. **Container fluid** for edge-to-edge layouts, Container for max-width
10. **Test on real devices** for final validation

## Resources

- [Mantine Responsive Docs](https://mantine.dev/styles/responsive/)
- [Mantine Breakpoints](https://mantine.dev/theming/theme-object/#breakpoints)
- [WCAG 2.1 Touch Target Size](https://www.w3.org/WAI/WCAG21/Understanding/target-size.html)
- [VenezuelaWatch Theme Config](../src/theme.ts)

---

**Last updated:** Phase 13-04 (2026-01-09)
**Maintainer:** VenezuelaWatch Team
