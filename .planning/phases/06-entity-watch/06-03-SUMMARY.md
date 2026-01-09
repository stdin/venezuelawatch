---
phase: 06-entity-watch
plan: 03
subsystem: api

tags: [django-ninja, pydantic, rest-api, entity-trending, redis, openapi]

# Dependency graph
requires:
  - phase: 06-entity-watch
    provides: TrendingService with Redis leaderboards (06-02)
  - phase: 06-entity-watch
    provides: Entity and EntityMention models (06-01)
  - phase: 05-dashboard-events-feed
    provides: API pattern with django-ninja routers and Pydantic schemas
provides:
  - Entity API with three endpoints: trending, profile, timeline
  - EntitySchema, EntityProfileSchema, EntityMentionSchema, EntityTimelineResponse
  - OpenAPI documentation at /api/docs with Entity Watch tag
  - Comprehensive entity-api.md documentation with examples
affects: [06-entity-watch, frontend-integration, dashboard-ui]

# Tech tracking
tech-stack:
  added: []
  patterns: [api-router-pattern, pydantic-schema-validation, metric-toggle-pattern]

key-files:
  created:
    - backend/docs/entity-api.md
  modified:
    - backend/data_pipeline/schemas.py
    - backend/data_pipeline/api.py
    - backend/venezuelawatch/api.py
    - backend/README.md

key-decisions:
  - "Metric toggle pattern for trending: mentions (time-decay), risk (avg score), sanctions (count)"
  - "Entity profile aggregates sanctions_status and risk_score on-the-fly (no denormalization)"
  - "Timeline endpoint denormalizes mentioned_at for efficient time-range queries"
  - "OpenAPI automatic documentation generation for all entity endpoints"

patterns-established:
  - "API endpoint pattern: GET /api/entities/trending, /api/entities/{id}, /api/entities/{id}/timeline"
  - "Metric toggle pattern: Single endpoint with ?metric=mentions|risk|sanctions query param"
  - "Profile aggregation pattern: Compute sanctions_status and avg risk_score from related objects"

issues-created: []

# Metrics
duration: 6min
completed: 2026-01-09
---

# Phase 6 Plan 3: Entity API & Trending Endpoints Summary

**REST API with trending leaderboard (3 metrics), entity profiles with sanctions status, and mention timelines for Phase 6 dashboard integration**

## Performance

- **Duration:** 6 min
- **Started:** 2026-01-09T06:28:46Z
- **Completed:** 2026-01-09T06:34:31Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- Entity API router with 3 endpoints supporting metric toggles and time-range filtering
- Pydantic schemas for entity responses (EntitySchema, EntityProfileSchema, EntityTimelineResponse)
- Comprehensive entity-api.md documentation with curl examples and frontend integration guide
- OpenAPI automatic documentation at /api/docs with "Entity Watch" tag
- All endpoints tested with curl, returning valid JSON responses

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Pydantic schemas for entity API responses** - `a81296c` (feat)
2. **Task 2: Create entity API router with trending, profile, timeline endpoints** - `04201d9` (feat)
3. **Task 3: Test entity API endpoints with curl and document responses** - `19f35a1` (test)

## Files Created/Modified

- `backend/data_pipeline/schemas.py` - Added EntitySchema, EntityProfileSchema, EntityMentionSchema, EntityTimelineResponse
- `backend/data_pipeline/api.py` - Added entity_router with trending, profile, timeline endpoints
- `backend/venezuelawatch/api.py` - Registered entity_router at /api/entities/
- `backend/docs/entity-api.md` - Comprehensive API documentation with examples
- `backend/README.md` - Added link to entity-api.md in Additional Documentation section

## Decisions Made

**Metric toggle pattern:**
- Single /trending endpoint with ?metric=mentions|risk|sanctions query parameter
- Mentions: Time-decayed trending score from Redis (real-time)
- Risk: Average risk_score aggregated from events
- Sanctions: Count of sanctions matches (compliance focus)

**Profile aggregation strategy:**
- Compute sanctions_status and avg risk_score on-the-fly (no denormalization)
- Prefetch recent events with select_related('event') to avoid N+1 queries
- Return last 5 events in profile response for context

**Timeline denormalization:**
- EntityMention.mentioned_at copied from Event.timestamp
- Enables efficient time-range queries without JOIN
- Consistent with Phase 6 Plan 1 design decision

## Deviations from Plan

None - plan executed exactly as written

## Issues Encountered

None

## Testing Results

All entity API endpoints tested with curl:

**Trending endpoint (mentions metric):**
- Request: `GET /api/entities/trending?metric=mentions&limit=10`
- Response: 5 entities with trending_score and trending_rank
- Top entity: Venezuela (LOCATION) with score 0.963

**Trending endpoint (risk metric):**
- Request: `GET /api/entities/trending?metric=risk&limit=5`
- Response: 5 entities ranked by avg risk_score (43.52)

**Trending endpoint (sanctions metric):**
- Request: `GET /api/entities/trending?metric=sanctions&limit=5`
- Response: Empty array (no sanctions matches in test data)

**Entity profile:**
- Request: `GET /api/entities/6c13323a-1cf8-4fb8-99a3-83caa797a071`
- Response: Full profile with aliases, metadata, sanctions_status=false, risk_score=43.52, recent_events array

**Entity timeline:**
- Request: `GET /api/entities/6c13323a-1cf8-4fb8-99a3-83caa797a071/timeline?days=30`
- Response: Timeline with 1 mention, event_summary with full event details

**OpenAPI documentation:**
- All endpoints visible at /api/openapi.json under "Entity Watch" tag
- Interactive docs at /api/docs showing entity endpoints

## Next Phase Readiness

**Ready for 06-04-PLAN.md (Frontend Entity Leaderboard & Profiles):**
- Entity API endpoints fully functional and documented
- OpenAPI specs available for TypeScript client generation
- Comprehensive entity-api.md documentation for frontend integration
- Tested examples showing all response formats
- Metric toggle pattern ready for dashboard controls

**No blockers** - API ready for frontend consumption

---
*Phase: 06-entity-watch*
*Completed: 2026-01-09*
