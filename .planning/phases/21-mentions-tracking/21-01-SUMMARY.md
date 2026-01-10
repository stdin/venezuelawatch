---
phase: 21-mentions-tracking
plan: "01"
subsystem: data-pipeline
tags: [bigquery, gdelt, mentions, spike-detection, rolling-statistics, window-functions]

# Dependency graph
requires:
  - phase: 20-gkg-integration
    provides: BigQuery partition filtering patterns and parameterized queries
  - phase: 14.3-event-migration
    provides: Polyglot persistence architecture (PostgreSQL + BigQuery)
provides:
  - MentionSpike Django model for spike metadata storage
  - GDELTMentionsService with 7-day rolling window statistics
  - Infrastructure for mention spike detection (data model + query service)
affects: [22-spike-intelligence, 23-narrative-tracking]

# Tech tracking
tech-stack:
  added: []
  patterns: [7-day-rolling-window-excluding-current-day, bigquery-window-functions-stddev-avg]

key-files:
  created:
    - backend/data_pipeline/models.py
    - backend/data_pipeline/migrations/0001_initial.py
    - backend/api/services/gdelt_mentions_service.py
  modified:
    - backend/venezuelawatch/settings.py
    - backend/data_pipeline/services/trending_service.py

key-decisions:
  - "Event ID as CharField (not ForeignKey) for polyglot architecture consistency"
  - "7-day rolling window with ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING (excludes current day from baseline)"
  - "30-day lookback for mention queries (provides 7-day baselines for recent events)"
  - "Partition filtering mandatory in all queries (avoids 532GB table scans)"
  - "Added REDIS_URL setting to replace removed CELERY_BROKER_URL from Phase 18"

patterns-established:
  - "Window function pattern: STDDEV_POP and AVG with ROWS BETWEEN for rolling statistics"
  - "Baseline exclusion pattern: X PRECEDING AND 1 PRECEDING (prevents self-inflation)"

issues-created: []

# Metrics
duration: 6min
completed: 2026-01-09
---

# Phase 21 Plan 01: Mention Tracking Infrastructure Summary

**PostgreSQL spike model and BigQuery mentions service with 7-day rolling window statistics for detecting unusual media attention**

## Performance

- **Duration:** 6 min
- **Started:** 2026-01-09T23:30:00Z
- **Completed:** 2026-01-09T23:36:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Created MentionSpike Django model with spike detection fields and composite indexes
- Built GDELTMentionsService for querying 2.5B mention records with partition filtering
- Implemented 7-day rolling baseline pattern that excludes current day (prevents spike self-inflation)
- Established window function queries with AVG and STDDEV_POP over ROWS BETWEEN windows
- Fixed REDIS_URL configuration issue from Phase 18 Celery removal

## Task Commits

Each task was committed atomically:

1. **Task 1: Create MentionSpike Django Model** - `34cb266` (feat)
2. **Task 2: Create GDELT Mentions BigQuery Service** - `72cd12b` (feat)

## Files Created/Modified

- `backend/data_pipeline/models.py` - MentionSpike model with spike detection fields
- `backend/data_pipeline/migrations/0001_initial.py` - Database migration for MentionSpike table
- `backend/api/services/gdelt_mentions_service.py` - BigQuery service for mention statistics with window functions
- `backend/venezuelawatch/settings.py` - Added REDIS_URL setting (replaced CELERY_BROKER_URL)
- `backend/data_pipeline/services/trending_service.py` - Updated to use REDIS_URL

## Decisions Made

- **Event ID as CharField (not ForeignKey)**: Maintains polyglot architecture consistency where events live in BigQuery, not PostgreSQL. No foreign key constraint since event table is external.
- **7-day rolling window with ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING**: Window function excludes current day from baseline calculation to prevent spike from inflating its own baseline statistics.
- **30-day lookback for mention queries**: Provides sufficient history for 7-day rolling baselines while limiting BigQuery scan size.
- **Partition filtering mandatory**: All queries include `_PARTITIONTIME >= TIMESTAMP_SUB()` to avoid scanning full 532GB table (2.5B rows).
- **Return only last 7 days**: Focus on recent spike candidates rather than entire 30-day history.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing google-cloud-tasks dependency**

- **Found during:** Task 1 (running makemigrations)
- **Issue:** ImportError for google.cloud.tasks_v2 in api/views/internal.py prevented Django from starting
- **Fix:** Installed google-cloud-tasks package via pip
- **Files modified:** N/A (pip install only)
- **Verification:** Django starts successfully, makemigrations runs
- **Committed in:** 34cb266 (part of Task 1 commit)

**2. [Rule 3 - Blocking] Missing REDIS_URL setting after Celery removal**

- **Found during:** Task 1 (running makemigrations)
- **Issue:** trending_service.py referenced settings.CELERY_BROKER_URL which was removed in Phase 18 when Celery was replaced with GCP-native services. Redis was retained for trending cache but REDIS_URL setting was never added.
- **Fix:** Added REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0') to settings.py and updated trending_service.py to use it
- **Files modified:** venezuelawatch/settings.py, data_pipeline/services/trending_service.py
- **Verification:** Django starts successfully, migrations run
- **Committed in:** 34cb266 (part of Task 1 commit)

---

**Total deviations:** 2 auto-fixed (both blocking), 0 deferred
**Impact on plan:** Both fixes necessary to unblock Django startup and migrations. No scope creep.

## Issues Encountered

None - blocking issues were resolved during execution via deviation rules.

## Next Phase Readiness

Ready for Plan 21-02 (TDD spike detection logic) - data infrastructure complete.

---
*Phase: 21-mentions-tracking*
*Completed: 2026-01-09*
