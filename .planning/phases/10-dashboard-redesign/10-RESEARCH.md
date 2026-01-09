# Phase 10: Dashboard Redesign - Research

**Researched:** 2026-01-09
**Domain:** React dashboard design, data visualization, real-time UX
**Confidence:** HIGH

<research_summary>
## Summary

Researched modern dashboard design patterns for 2025, focusing on data visualization libraries, layout patterns, filtering UX, and real-time data updates. The standard approach uses Recharts for data visualization (1M+ weekly downloads, React-first), CSS Grid for responsive layouts, and either polling or WebSocket for real-time updates.

Key finding: Don't hand-roll chart components or layout grids. Recharts provides production-ready, responsive charts with animation and composability. Mantine's Grid system handles responsive layouts. Focus on the 5-second rule: users should find information within 5 seconds.

**Primary recommendation:** Use Recharts + Mantine Grid + React Query with polling for real-time updates. Start with live filtering (instant feedback), skeleton loading states, and progressive disclosure patterns for complex data.
</research_summary>

<standard_stack>
## Standard Stack

The established libraries/tools for dashboard design:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| recharts | 2.x/3.x | Data visualization | 1M+ weekly downloads, React-first, composable |
| @mantine/core | 7.x | UI components | 500k+ weekly, comprehensive dashboard components |
| @tanstack/react-query | 5.x | Data fetching/caching | Industry standard for server state |
| react-grid-layout | 1.x | Drag-drop grid | Optional: user-customizable layouts |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| date-fns | 2.x | Date manipulation | Date filtering, time-series |
| @mantine/dates | 7.x | Date picker components | Calendar-based filtering |
| @mantine/notifications | 7.x | Toast notifications | Real-time data alerts |
| zustand | 4.x | Client state | Dashboard UI state (filters, collapsed panels) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Recharts | ApexCharts | ApexCharts has more chart types but heavier, Recharts more React-idiomatic |
| Recharts | D3.js | D3 offers ultimate control but steep learning curve, Recharts is faster to implement |
| React Query polling | WebSocket | WebSocket for truly real-time (<1s latency), polling simpler for 15-30s refresh |

**Installation:**
```bash
npm install recharts @tanstack/react-query date-fns
# Mantine already installed from Phase 9
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
src/
├── components/
│   ├── dashboard/
│   │   ├── DashboardLayout.tsx    # Grid layout wrapper
│   │   ├── DashboardFilters.tsx   # Left sidebar filters
│   │   ├── EventsFeed.tsx         # Main content area
│   │   └── TrendsPanel.tsx        # Right panel charts
│   ├── charts/
│   │   ├── RiskTrendChart.tsx     # Reusable Recharts wrappers
│   │   ├── EventTimelineChart.tsx
│   │   └── MetricsCard.tsx        # KPI card with chart
│   └── ui/                        # Phase 9 components
└── hooks/
    ├── useEventsFeed.ts           # React Query for events
    ├── useDashboardFilters.ts     # Filter state management
    └── useRealTimeUpdates.ts      # Polling/WebSocket logic
```

### Pattern 1: Responsive Dashboard Layout with Mantine Grid
**What:** CSS Grid-based layout that adapts from desktop (3 columns) to mobile (1 column)
**When to use:** All dashboard pages
**Example:**
```tsx
import { Grid, Container } from '@mantine/core';

function DashboardLayout() {
  return (
    <Container fluid>
      <Grid>
        {/* Filters: 3 cols desktop, full width mobile */}
        <Grid.Col span={{ base: 12, md: 3 }}>
          <DashboardFilters />
        </Grid.Col>

        {/* Main content: 6 cols desktop, full width mobile */}
        <Grid.Col span={{ base: 12, md: 6 }}>
          <EventsFeed />
        </Grid.Col>

        {/* Trends: 3 cols desktop, full width mobile */}
        <Grid.Col span={{ base: 12, md: 3 }}>
          <TrendsPanel />
        </Grid.Col>
      </Grid>
    </Container>
  );
}
```

### Pattern 2: Recharts with Real-Time Data Updates
**What:** Line/Area chart that updates when new data arrives via React Query
**When to use:** Time-series data, trend visualization
**Example:**
```tsx
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';
import { useQuery } from '@tanstack/react-query';

function RiskTrendChart() {
  const { data } = useQuery({
    queryKey: ['risk-trends'],
    queryFn: fetchRiskTrends,
    refetchInterval: 30000, // Poll every 30s
  });

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Line
          type="monotone"
          dataKey="riskScore"
          stroke="#8884d8"
          isAnimationActive={true}
          animationDuration={500}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

### Pattern 3: Live Filtering with Instant Feedback
**What:** Filters that update results in real-time as user types/selects
**When to use:** Search, date range, category filters
**Example:**
```tsx
import { TextInput, MultiSelect } from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';

function DashboardFilters({ onChange }) {
  const [search, setSearch] = useState('');
  const [debouncedSearch] = useDebouncedValue(search, 300);

  useEffect(() => {
    onChange({ search: debouncedSearch });
  }, [debouncedSearch]);

  return (
    <Stack>
      <TextInput
        placeholder="Search events..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      {/* Visual feedback: show result count */}
      <Text size="sm" c="dimmed">
        {resultCount} events found
      </Text>
    </Stack>
  );
}
```

### Pattern 4: Skeleton Loading States
**What:** Show placeholder layout while data loads
**When to use:** Initial page load, filter changes
**Example:**
```tsx
import { Skeleton, Stack } from '@mantine/core';

function EventsFeed() {
  const { data, isLoading } = useQuery({ queryKey: ['events'] });

  if (isLoading) {
    return (
      <Stack>
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} height={120} radius="md" />
        ))}
      </Stack>
    );
  }

  return <EventList events={data} />;
}
```

### Anti-Patterns to Avoid
- **Hard-coded chart dimensions:** Always use ResponsiveContainer, breaks on mobile
- **No loading states:** Users see blank screen, think it's broken
- **Slow filters:** Debounce input but show instant visual feedback
- **Too many charts:** Follow 5-second rule, limit to 3-5 key metrics per view
- **Rebuilding Recharts:** Don't create custom SVG charts, compose Recharts components
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Chart rendering | Custom Canvas/SVG | Recharts components | Animation, responsiveness, tooltips, legends all handled |
| Responsive grid | Custom media queries | Mantine Grid system | Handles breakpoints, gap spacing, nested grids |
| Date filtering | Custom date picker | @mantine/dates | Keyboard nav, accessibility, range selection, presets |
| Real-time updates | Custom polling logic | React Query refetchInterval | Handles background refetch, cache invalidation, error retry |
| Loading skeletons | Custom placeholders | Mantine Skeleton | Matches component shapes, pulse animation |
| Empty states | Conditional rendering | Mantine Empty State pattern | Icon, message, action button in consistent pattern |
| Data table | Custom table HTML | Mantine DataTable | Sorting, pagination, row selection, virtualization |

**Key insight:** Dashboard development in 2025 is about composition, not custom implementation. Recharts handles all chart complexity (scaling, animation, tooltips). Mantine provides all layout primitives. React Query manages all data fetching patterns. Fighting these leads to bugs in edge cases (window resize, slow network, missing data).
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Information Overload
**What goes wrong:** Dashboard shows 20+ metrics, users can't find key information
**Why it happens:** Adding every possible metric instead of prioritizing
**How to avoid:** Follow 5-second rule - user should find their answer in 5 seconds. Limit to 3-5 key metrics per view. Use progressive disclosure (expand for details).
**Warning signs:** Users ask "where do I find X?" repeatedly, high bounce rate

### Pitfall 2: Poor Loading Performance
**What goes wrong:** Dashboard takes 5+ seconds to load, feels broken
**Why it happens:** Loading all data upfront, no skeleton states, blocking requests
**How to avoid:** Skeleton loading states, React Query with staleTime, paginate/virtualize large lists
**Warning signs:** Users refresh page thinking it's stuck, abandon before data loads

### Pitfall 3: No Mobile Responsiveness
**What goes wrong:** Desktop-only layout breaks on tablet/mobile
**Why it happens:** Hard-coded widths, assuming large screens
**How to avoid:** Use Mantine Grid with span={{ base: 12, md: 6 }}, ResponsiveContainer for charts, test on mobile
**Warning signs:** Horizontal scrolling, overlapping elements, tiny text on mobile

### Pitfall 4: Stale Data Display
**What goes wrong:** Dashboard shows old data, users make decisions on outdated info
**Why it happens:** No refresh mechanism, cache never invalidates
**How to avoid:** React Query refetchInterval (15-30s for real-time dashboards), show last updated timestamp, visual indicator when refreshing
**Warning signs:** Users manually refresh page constantly, notice discrepancies with other sources

### Pitfall 5: Filter UX Confusion
**What goes wrong:** Users apply filters but don't see changes, or see changes too slowly
**Why it happens:** No visual feedback, debounce too long, no "applying" state
**How to avoid:** Show result count immediately, debounce input (300ms) but update count on every keystroke, show loading spinner in results area
**Warning signs:** Users re-apply same filter multiple times, complain filters "don't work"

### Pitfall 6: Chart Accessibility
**What goes wrong:** Screen readers can't interpret charts, keyboard nav doesn't work
**Why it happens:** SVG charts without ARIA labels, no alternative data view
**How to avoid:** Add aria-label to charts, provide data table toggle, ensure tooltips keyboard-accessible
**Warning signs:** Accessibility audit failures, complaints from users with disabilities
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from official sources:

### Dashboard with Real-Time Updates
```tsx
// Source: React Query + Recharts best practices
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { Skeleton } from '@mantine/core';

function DashboardChart() {
  const { data, isLoading, dataUpdatedAt } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: fetchMetrics,
    refetchInterval: 30000, // 30 seconds
    staleTime: 25000, // Consider stale after 25s
  });

  if (isLoading) return <Skeleton height={300} />;

  return (
    <div>
      <Text size="xs" c="dimmed">
        Last updated: {new Date(dataUpdatedAt).toLocaleTimeString()}
      </Text>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <Line type="monotone" dataKey="value" stroke="#8884d8" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
```

### Filter Panel with Instant Feedback
```tsx
// Source: Mantine hooks + UX best practices
import { TextInput, MultiSelect, Stack, Text } from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';

function FilterPanel() {
  const [search, setSearch] = useState('');
  const [categories, setCategories] = useState([]);
  const [debouncedSearch] = useDebouncedValue(search, 300);

  const { data: events, isLoading } = useQuery({
    queryKey: ['events', debouncedSearch, categories],
    queryFn: () => fetchEvents({ search: debouncedSearch, categories }),
  });

  return (
    <Stack gap="md">
      <TextInput
        placeholder="Search events..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <MultiSelect
        data={['Political', 'Economic', 'Sanctions']}
        value={categories}
        onChange={setCategories}
        placeholder="Filter by category"
      />

      {/* Instant feedback */}
      <Text size="sm" c="dimmed">
        {isLoading ? 'Searching...' : `${events?.length ?? 0} events found`}
      </Text>
    </Stack>
  );
}
```

### Responsive Dashboard Grid
```tsx
// Source: Mantine Grid documentation
import { Grid, Container, Paper } from '@mantine/core';

function DashboardLayout() {
  return (
    <Container size="xl">
      <Grid gutter="md">
        {/* Filters: left sidebar on desktop, full width on mobile */}
        <Grid.Col span={{ base: 12, md: 3, lg: 2 }}>
          <Paper p="md" withBorder>
            <DashboardFilters />
          </Paper>
        </Grid.Col>

        {/* Main content */}
        <Grid.Col span={{ base: 12, md: 9, lg: 7 }}>
          <EventsFeed />
        </Grid.Col>

        {/* Trends panel: right sidebar on large screens, full width on small */}
        <Grid.Col span={{ base: 12, lg: 3 }}>
          <Paper p="md" withBorder>
            <TrendsChart />
          </Paper>
        </Grid.Col>
      </Grid>
    </Container>
  );
}
```

### Empty State with Action
```tsx
// Source: Mantine + UX empty state patterns
import { Stack, Text, Button } from '@mantine/core';
import { IconFilter } from '@tabler/icons-react';

function EventsFeed() {
  const { data: events } = useQuery({ queryKey: ['events'] });

  if (events?.length === 0) {
    return (
      <Stack align="center" gap="md" py="xl">
        <IconFilter size={48} stroke={1.5} color="gray" />
        <Text size="lg" fw={500}>No events found</Text>
        <Text size="sm" c="dimmed">
          Try adjusting your filters or search criteria
        </Text>
        <Button variant="light" onClick={clearFilters}>
          Clear Filters
        </Button>
      </Stack>
    );
  }

  return <EventList events={events} />;
}
```
</code_examples>

<sota_updates>
## State of the Art (2024-2025)

What's changed recently:

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Polling only | React Query with polling | 2023-2024 | Better cache management, automatic retry, background refetch |
| Hard-coded grid | CSS Grid with container queries | 2024-2025 | True component-based responsiveness, not just viewport |
| D3.js for everything | Recharts for standard charts | 2022-2024 | Faster implementation, React-first, only use D3 for custom viz |
| Custom date pickers | Mantine Dates | 2024 | Accessibility built-in, keyboard nav, consistent styling |
| Manual skeleton states | Component library skeletons | 2024-2025 | Consistent loading UX, less custom code |

**New tools/patterns to consider:**
- **Bento Grid Layouts:** Japanese lunch box-inspired modular layouts for organizing dashboard sections
- **Microinteractions:** Button hover states, chart tooltips, filter loading animations for polish
- **Progressive Disclosure:** Hide complexity behind "expand" affordances, show high-level first
- **Data Annotations:** Allow users to add notes/comments to specific chart data points (advanced feature)
- **Gesture-Based Interactions:** Touch/swipe for mobile dashboards (if mobile-first)

**Deprecated/outdated:**
- **Global filters only:** Modern dashboards use in-context filtering per component
- **"Apply" button for filters:** Live filtering with instant feedback is now standard
- **Desktop-only layouts:** Mobile-first or responsive-first is mandatory in 2025
- **No loading states:** Skeleton screens are now table stakes, not nice-to-have
</sota_updates>

<open_questions>
## Open Questions

Things that couldn't be fully resolved:

1. **Real-Time Update Frequency**
   - What we know: 15-30 second polling is common for dashboards, WebSocket for <1s latency
   - What's unclear: What's the right interval for VenezuelaWatch events feed?
   - Recommendation: Start with 30s polling via React Query refetchInterval, test with users, consider WebSocket if they need <10s updates

2. **Chart Performance with Large Datasets**
   - What we know: Recharts uses SVG, can slow down with >10k data points
   - What's unclear: How many events will typical dashboard view show?
   - Recommendation: Paginate/virtualize event lists, use time-based filtering to limit chart data to recent N days, add "Load More" if needed

3. **Drag-Drop Dashboard Customization**
   - What we know: react-grid-layout enables user-customizable layouts
   - What's unclear: Is this a v1.1 requirement or future enhancement?
   - Recommendation: Skip for Phase 10, add in future if users request custom layouts
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- /recharts/recharts - Context7 official docs (ResponsiveContainer, animations, chart types)
- Mantine 7.x documentation - Grid system, component props, hooks
- React Query 5.x documentation - polling patterns, cache management

### Secondary (MEDIUM confidence)
- UXPin Dashboard Design Principles (2025) - verified against Nielsen Norman Group patterns
- LogRocket Best React Chart Libraries (2025) - verified Recharts/ApexCharts stats with npm
- Pencil & Paper UX Patterns - verified filter UX against Mantine examples

### Tertiary (LOW confidence - needs validation)
- None - all dashboard UX findings verified with multiple authoritative sources
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: React + Mantine + Recharts
- Ecosystem: React Query, Mantine hooks, date-fns
- Patterns: Responsive grid, live filtering, real-time updates, loading states
- Pitfalls: Information overload, performance, mobile, stale data, filter UX

**Confidence breakdown:**
- Standard stack: HIGH - Recharts and Mantine verified as industry standard
- Architecture: HIGH - patterns from official docs and multiple sources
- Pitfalls: HIGH - from UX research firms (NN/g, UXPin, Pencil & Paper)
- Code examples: HIGH - from Recharts Context7, Mantine official docs

**Research date:** 2026-01-09
**Valid until:** 2026-02-09 (30 days - React/dashboard ecosystem stable)
</metadata>

---

*Phase: 10-dashboard-redesign*
*Research completed: 2026-01-09*
*Ready for planning: yes*
