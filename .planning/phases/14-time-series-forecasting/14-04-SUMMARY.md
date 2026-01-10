---
phase: 14-time-series-forecasting
plan: 04
subsystem: ui
tags: [react, recharts, forecasting, visualization, entity-profiles]

# Dependency graph
requires:
  - phase: 14-03
    provides: Forecast API with 24-hour caching
  - phase: 10-dashboard-ui
    provides: Recharts visualization patterns
  - phase: 11-entity-tracking-ui
    provides: Entity profile page layout

provides:
  - Entity risk forecast visualization with 30-day predictions
  - Historical + forecast combined charts with confidence intervals
  - Insufficient data handling with clear user messaging
  - Contextual forecast widgets on entity profiles

affects: [phase-15-correlation-analysis, entity-tracking]

# Tech tracking
tech-stack:
  added: []
  patterns: [forecast-chart-component, confidence-band-visualization, contextual-widgets]

key-files:
  created:
    - frontend/src/lib/forecasting.ts
    - frontend/src/components/forecasting/EntityForecastChart.tsx
  modified:
    - backend/data_pipeline/schemas.py
    - backend/data_pipeline/api.py
    - frontend/src/lib/types.ts
    - frontend/src/lib/api.ts
    - frontend/src/components/EntityProfile.tsx

key-decisions:
  - "Contextual placement on entity profile (not dedicated page) per CONTEXT.md"
  - "Historical data as solid line, forecast as dashed line for visual distinction"
  - "Confidence band as shaded area (intuitive, like weather forecasts)"
  - "30-day historical + 30-day forecast provides good context window"
  - "ComposedChart over LineChart for layering Area and Line elements"
  - "Gray Alert for insufficient data (not hidden button) per CONTEXT.md"

patterns-established:
  - "Forecast chart pattern: ComposedChart with Area for confidence bands, Line for actual/predicted"
  - "Contextual widget pattern: Integrated into existing page sections vs separate routes"
  - "Timestamp freshness pattern: formatDistanceToNow for relative time display"

issues-created: []

# Metrics
duration: 6min
completed: 2026-01-10
---

# Phase 14 Plan 4: Frontend Forecast Visualization Summary

**Entity risk forecasting live: contextual trajectory charts with 30-day predictions and confidence intervals on entity profiles**

## Performance

- **Duration:** 6 min
- **Started:** 2026-01-10T01:26:48Z
- **Completed:** 2026-01-10T01:32:44Z
- **Tasks:** 3 (2 auto + 1 checkpoint)
- **Files modified:** 7

## Accomplishments

- Created EntityForecastChart component with Recharts visualization
- Integrated historical (30 days) + forecasted (30 days) risk trajectory
- Rendered confidence bands as shaded area (upper/lower bounds)
- Added timestamp badge "Forecast generated X ago" for freshness
- Handled insufficient data case with clear explanation
- Integrated forecast widget into entity profile Risk Intelligence section
- Backend API returns 30-day historical risk scores for seamless transition
- Verified visual quality and responsiveness across breakpoints

## Task Commits

1. **Task 1: Create forecast chart component with Recharts** - `b469511` (feat)
   - Created forecasting API client with TypeScript interfaces
   - Built EntityForecastChart component using Recharts ComposedChart
   - Confidence bands rendered as shaded Area between yhat_lower/yhat_upper
   - Historical data: solid blue line, forecast: dashed red line
   - Timestamp badge with formatDistanceToNow for relative time
   - Handled insufficient data, error, and loading states

2. **Task 2: Integrate forecast widget into entity profiles** - `a87f73b` (feat)
   - Added risk_history field to EntityProfileSchema (backend)
   - Implemented include_history parameter in get_entity_profile endpoint
   - 30-day historical risk score aggregation by date
   - Updated EntityProfile TypeScript interface (frontend)
   - Modified getEntityProfile to request historical data
   - Added EntityForecastChart to entity profile Risk Intelligence section

3. **Task 3: Human verification checkpoint** - Manual verification passed
   - Confirmed visual elements render correctly
   - Historical + forecast transition is seamless
   - Confidence bands display as shaded area
   - Timestamp badge shows forecast age
   - Insufficient data message displays appropriately

**Plan metadata:** `[next commit]` (docs: complete plan)

## Files Created/Modified

### Created Files
- `frontend/src/lib/forecasting.ts` - Forecasting API client with fetchEntityForecast()
- `frontend/src/components/forecasting/EntityForecastChart.tsx` - Recharts forecast visualization component

### Modified Files
- `backend/data_pipeline/schemas.py` - Added risk_history field to EntityProfileSchema
- `backend/data_pipeline/api.py` - Added include_history parameter and 30-day aggregation
- `frontend/src/lib/types.ts` - Added risk_history to EntityProfile interface
- `frontend/src/lib/api.ts` - Updated getEntityProfile to request historical data
- `frontend/src/components/EntityProfile.tsx` - Integrated EntityForecastChart widget

## Decisions Made

1. **Contextual placement** - Forecast chart embedded in entity profile Risk Intelligence section (not dedicated page) per CONTEXT.md requirement for contextual widgets
2. **Visual distinction** - Historical data as solid line, forecast as dashed line with different colors for clarity
3. **Confidence bands as shaded area** - Intuitive visualization like weather forecasts per CONTEXT.md
4. **30-day windows** - 30 days historical + 30 days forecast provides good context without overwhelming the chart
5. **ComposedChart over LineChart** - Recharts ComposedChart allows layering Area (confidence bands) with Line (actual/predicted)
6. **Gray Alert for insufficient data** - Not hidden button, clearly visible per CONTEXT.md requirement
7. **Always-visible disclaimer** - "Directional indicator based on historical patterns" text below chart for expectation setting
8. **Timestamp badge format** - "Forecast generated X ago" using formatDistanceToNow for human-friendly relative time
9. **Backend include_history parameter** - Optional parameter (default false) maintains backward compatibility
10. **Frontend defaults to true** - Always request historical data for entity profiles (forecast use case)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all components integrated smoothly with existing architecture.

## Next Phase Readiness

**Phase 14 Complete!** Entity risk forecasting fully operational:

✅ **Plan 1 (BigQuery ETL):** Daily 2 AM UTC sync of entity mention history to BigQuery
✅ **Plan 2 (Vertex AI Training):** TiDE model trained on 90-day rolling window with 80/10/10 split
✅ **Plan 3 (Forecast API):** Django REST endpoint with 24-hour caching and Vertex AI integration
✅ **Plan 4 (Frontend Viz):** Recharts forecast charts on entity profiles with confidence intervals

**Delivered Value:**
- Investors can see 30-day risk trajectory predictions for any tracked entity
- Confidence intervals communicate prediction uncertainty (like weather forecasts)
- Historical context (30 days) provides baseline for interpreting forecasts
- Insufficient data handling prevents confusion when entity lacks history
- Contextual placement keeps forecasts discoverable without overwhelming navigation

**Ready for Phase 15: Correlation & Pattern Analysis**

---
*Phase: 14-time-series-forecasting*
*Completed: 2026-01-10*
