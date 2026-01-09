---
phase: 07-ai-chat-interface
plan: 03
subsystem: ui

tags: [assistant-ui, react, tool-ui, makeAssistantToolUI, recharts, perplexity-style]

# Dependency graph
requires:
  - phase: 07-ai-chat-interface
    provides: Backend chat API with tool calling, SSE streaming, assistant-ui React integration
  - phase: 05-dashboard-events-feed
    provides: EventCard styling patterns, risk score badges, severity classification UI
  - phase: 06-entity-watch
    provides: EntityLeaderboard styling patterns, entity type badges, metric displays
provides:
  - EventPreviewCard for search_events tool with expand-in-place functionality
  - EntityPreviewCard for get_entity_profile tool with sanctions alerts and profile details
  - TrendingEntitiesCard for get_trending_entities tool with ranked entity lists
  - RiskTrendsChart for analyze_risk_trends tool with recharts line visualization
  - Perplexity-style inline preview cards with visual indicators and contextual metadata

affects: [07-04-chat-page, frontend-chat-integration]

# Tech tracking
tech-stack:
  added: [makeAssistantToolUI from @assistant-ui/react]
  patterns: [Tool UI components pattern, expand-in-place cards, compact inline chat displays]

key-files:
  created:
    - frontend/src/components/chat/EventPreviewCard.tsx
    - frontend/src/components/chat/EventPreviewCard.css
    - frontend/src/components/chat/EntityPreviewCard.tsx
    - frontend/src/components/chat/EntityPreviewCard.css
    - frontend/src/components/chat/RiskTrendsChart.tsx
    - frontend/src/components/chat/RiskTrendsChart.css
  modified:
    - frontend/src/lib/chatRuntime.ts

key-decisions:
  - "makeAssistantToolUI pattern for custom tool rendering tied to backend tool names"
  - "Expand-in-place pattern (not navigation) for preview card interactions"
  - "Compact inline display optimized for chat context (smaller than dashboard components)"
  - "Tool name matching: search_events, get_entity_profile, get_trending_entities, analyze_risk_trends"
  - "TypeScript types matching backend tool response schemas exactly"
  - "Recharts for risk trends visualization (consistent with TrendsPanel)"
  - "Visual indicators: risk score colors (red >70, yellow 40-70, green <40), severity badges (SEV1-5), entity type badges (Person=blue, Org=purple, Gov=red, Location=green)"
  - "Sanctions alert badge with pulse animation for high visibility"
  - "Optional value handling (number | undefined) for recharts Tooltip formatter"

patterns-established:
  - "Tool UI pattern: makeAssistantToolUI<Args, Result>({ toolName, render }) for each backend tool"
  - "Compact card layout: header with title/badges, meta row, expandable details, toggle button"
  - "Expand state management: useState for expand/collapse within each card"
  - "Badge system: consistent colors and sizes across all tool UIs"
  - "Empty state handling: friendly messages when no data returned"
  - "Date formatting: formatDate() helper for consistent date display across components"

issues-created: []

# Metrics
duration: 15min
completed: 2026-01-08
---

# Phase 7: AI Chat Interface - Plan 3 Summary

**Custom tool UI components for all 4 VenezuelaWatch tools with Perplexity-style rich previews and expand-in-place functionality**

## Performance

- **Duration:** 15 min
- **Started:** 2026-01-08T23:45:00Z
- **Completed:** 2026-01-09T00:00:00Z
- **Tasks:** 3
- **Files created:** 6
- **Files modified:** 1

## Accomplishments

- EventPreviewCard displays search_events results with compact event lists, risk/severity badges, and expandable summaries
- EntityPreviewCard shows entity profiles with sanctions alerts, mention trends, recent event lists, and profile expansion
- TrendingEntitiesCard renders entity leaderboards with ranked lists, type badges, and trend indicators
- RiskTrendsChart visualizes risk score trends over time with recharts line chart and summary statistics
- All components use makeAssistantToolUI pattern for seamless assistant-ui integration
- Perplexity-style inline previews with visual indicators (badges, colors, trend arrows)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create EventPreviewCard tool UI component** - `17f3452` (feat)
2. **Task 2: Create EntityPreviewCard tool UI component** - `9a45242` (feat)
3. **Task 3: Create RiskTrendsChart tool UI component** - `c641005` (feat)
4. **TypeScript compilation fixes** - `90142df` (fix)

**Plan metadata:** (pending - will be created in next commit)

## Files Created/Modified

### Created
- `frontend/src/components/chat/EventPreviewCard.tsx` - Tool UI for search_events with event list and expand-in-place
- `frontend/src/components/chat/EventPreviewCard.css` - Compact inline styling for event preview cards
- `frontend/src/components/chat/EntityPreviewCard.tsx` - Tool UIs for get_entity_profile and get_trending_entities
- `frontend/src/components/chat/EntityPreviewCard.css` - Entity preview styling with sanctions alerts and type badges
- `frontend/src/components/chat/RiskTrendsChart.tsx` - Tool UI for analyze_risk_trends with recharts visualization
- `frontend/src/components/chat/RiskTrendsChart.css` - Compact chart styling for inline display

### Modified
- `frontend/src/lib/chatRuntime.ts` - Added convertMessage property to useExternalStoreRuntime adapter

## Decisions Made

**makeAssistantToolUI pattern for tool rendering:** Used @assistant-ui/react's makeAssistantToolUI to create custom renderers for each backend tool. This ties tool UI components directly to backend tool names (search_events, get_entity_profile, etc.) ensuring automatic rendering when Claude invokes tools.

**Expand-in-place interaction pattern:** Preview cards expand to show full details without navigating away from chat. This maintains conversational flow (Perplexity-style) where users can explore details inline and continue the conversation.

**Compact inline display optimization:** All components styled more compactly than dashboard equivalents (EventCard, EntityLeaderboard, TrendsPanel) to fit naturally in chat context. Smaller fonts, tighter spacing, shorter cards.

**TypeScript types matching backend schemas:** Tool argument and result types precisely match backend tool.py schemas. This ensures type safety and prevents runtime errors from schema mismatches.

**Visual indicators for at-a-glance assessment:**
- Risk score colors: Red (>70), yellow (40-70), green (<40)
- Severity badges: SEV1-5 with matching color scale
- Entity type badges: Person=blue, Organization=purple, Government=red, Location=green
- Trend arrows: ↑↑ (high), ↑ (medium), → (stable), ↓ (low)
- Sanctions alert: Red badge with pulse animation

**Recharts for consistency:** Used recharts library (already in project from TrendsPanel) for risk trends visualization. Maintains visual consistency between dashboard and chat.

**Optional value handling:** Added proper TypeScript typing (number | undefined, string | undefined) for recharts Tooltip formatter to handle edge cases where data might be undefined.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] TypeScript compilation errors in recharts formatter**
- **Found during:** Task 3 (Build verification after RiskTrendsChart creation)
- **Issue:** Recharts Tooltip formatter type expected optional parameters (number | undefined, string | undefined) but component specified non-optional (number, string)
- **Fix:** Updated formatter signature to handle undefined values: `(value: number | undefined, name: string | undefined, props: any)` with nullish coalescing for return values
- **Files modified:** frontend/src/components/chat/RiskTrendsChart.tsx
- **Verification:** npm run build succeeded with no TypeScript errors
- **Committed in:** 90142df (fix commit)

**2. [Rule 3 - Blocking] Missing convertMessage property in chatRuntime**
- **Found during:** Task 3 (Build verification)
- **Issue:** assistant-ui 0.11.53 useExternalStoreRuntime requires convertMessage property in adapter, but it was missing
- **Fix:** Added `convertMessage: (message) => message` as pass-through since messages already in correct format
- **Files modified:** frontend/src/lib/chatRuntime.ts
- **Verification:** npm run build succeeded, TypeScript type checking passed
- **Committed in:** 90142df (fix commit)

---

**Total deviations:** 2 auto-fixed (2 blocking TypeScript errors), 0 deferred
**Impact on plan:** Both fixes necessary for compilation. No scope changes or feature additions.

## Issues Encountered

None - implementation followed plan specifications. TypeScript compilation errors were caught and fixed during build verification as expected.

## Next Phase Readiness

- All 4 tool UI components complete and type-safe
- Components ready for integration in Chat page (Plan 4)
- makeAssistantToolUI pattern established for future tool additions
- Visual design consistent with existing dashboard components
- Frontend builds without errors, production-ready
- Ready for Phase 7 Plan 4: Chat page integration with Thread, Composer, and tool UI registration

---

*Phase: 07-ai-chat-interface*
*Completed: 2026-01-09*
