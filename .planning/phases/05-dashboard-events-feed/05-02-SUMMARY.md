# Phase 5 Plan 2: Dashboard Layout & Event List Summary

**Built split-view dashboard with virtualized event list displaying risk-prioritized events with clean, modern UI**

## Accomplishments

- Installed @tanstack/react-virtual for efficient virtualized scrolling (only renders visible items)
- Created split-view Dashboard layout with 60/40 split (event list left, detail panel right)
- Implemented virtualized EventList component that sorts events by risk_score descending and renders only visible items
- Built EventCard component with moderate information density: title, risk score badge, severity badge, timestamp, summary, source badge, and sentiment indicator
- Integrated Dashboard into App.tsx as main authenticated view
- All components styled with clean, minimal Linear-inspired aesthetic using CSS custom properties

## Files Created/Modified

- `frontend/package.json` - Added @tanstack/react-virtual dependency
- `frontend/src/pages/Dashboard.tsx` - Split-view dashboard layout with loading/error states (new file)
- `frontend/src/pages/Dashboard.css` - Dashboard styling with CSS variables for theming (new file)
- `frontend/src/components/EventList.tsx` - Virtualized event list using TanStack Virtual (new file)
- `frontend/src/components/EventList.css` - Event list container and scrollbar styling (new file)
- `frontend/src/components/EventCard.tsx` - Event card with moderate info density (new file)
- `frontend/src/components/EventCard.css` - Event card styling with color-coded badges (new file)
- `frontend/src/App.tsx` - Updated to show Dashboard for authenticated users

## Decisions Made

- Used TanStack Virtual with estimateSize of 120px per card and overscan of 5 for smooth scrolling
- Risk score badges color-coded: 75-100 red (critical), 50-74 orange (high), 25-49 yellow (medium), 0-24 blue (low)
- Severity badges use separate color scheme (SEV1-5) distinct from risk scores
- Sentiment indicator shows simple arrows: ↑ positive (green), ↓ negative (red), → neutral (gray)
- Relative time formatting for timestamps: "2h ago", "5d ago", etc.
- Selected cards get 4px left border and subtle background highlight
- Split view is 60/40 to give more space to event list while maintaining readable detail panel

## Issues Encountered

- Fixed unused variable warning in App.tsx (removed 'logout' from destructuring since we're not showing user profile anymore)
- Fixed authentication issues during verification:
  - Added `/_allauth` proxy configuration to Vite for authentication endpoints
  - Added `CSRF_TRUSTED_ORIGINS` to Django settings for CSRF token validation
  - Implemented CSRF token handling in frontend API client (getCsrfToken helper, X-CSRFToken header)
  - Fixed django-allauth field names (uses `password` instead of `password1`/`password2`)
  - Updated AuthContext to initialize CSRF token on app load
- Fixed layout constraints:
  - Removed max-width and centering from #root and body elements
  - Dashboard now uses full viewport width and height

## Next Step

Ready for 05-03-PLAN.md (Filtering & Search)
