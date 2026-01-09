---
phase: 06-entity-watch
plan: 02
subsystem: data-pipeline

tags: [celery, redis, entity-extraction, trending, time-decay, exponential-decay]

# Dependency graph
requires:
  - phase: 06-entity-watch
    provides: Entity and EntityMention models with fuzzy matching (06-01)
  - phase: 03-data-pipeline-architecture
    provides: Celery + Redis infrastructure for async tasks
  - phase: 04-risk-intelligence-core
    provides: Event.llm_analysis with structured entity data
provides:
  - TrendingService with Redis Sorted Sets and exponential time-decay (7-day half-life)
  - extract_entities_from_event Celery task for LLM entity extraction
  - backfill_entities task for batch processing existing events
  - extract_entities management command with --days, --all, --sync-trending options
  - End-to-end entity extraction pipeline from Event to Entity/EntityMention to Redis trending
affects: [06-entity-watch, entity-api, dashboard-integration]

# Tech tracking
tech-stack:
  added: []
  patterns: [redis-sorted-sets, exponential-time-decay, celery-async-extraction]

key-files:
  created:
    - backend/data_pipeline/services/trending_service.py
    - backend/data_pipeline/tasks/entity_extraction.py
    - backend/data_pipeline/management/commands/extract_entities.py
  modified:
    - backend/data_pipeline/services/trending_service.py (timezone fix)

key-decisions:
  - "Exponential time-decay with 7-day half-life (168 hours) for trending scores"
  - "Redis Sorted Sets for O(log N) trending operations (not PostgreSQL materialized views)"
  - "Three trending metrics: mentions (time-decay), risk (avg score), sanctions (count)"
  - "Bulk Entity fetch in trending queries to avoid N+1 problem"
  - "Use timezone.now() not datetime.utcnow() for timezone-aware calculations"
  - "Extract from Event.llm_analysis.entities with fallback to Event.entities array"
  - "Heuristic entity type inference for unstructured data"

patterns-established:
  - "Trending pattern: Redis for real-time scores, periodic sync to PostgreSQL for persistence"
  - "Entity extraction pattern: LLM structured data -> EntityService normalization -> EntityMention link -> TrendingService update"
  - "Management command pattern: Queue Celery tasks, show stats, optional sync operations"

issues-created: []

# Metrics
duration: 5min
completed: 2026-01-09
---

# Phase 6 Plan 2: Entity Extraction Celery Task Summary

**Celery-based entity extraction pipeline with Redis trending leaderboard (7-day exponential decay) and management commands for backfill**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-09T06:20:48Z
- **Completed:** 2026-01-09T06:26:07Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- TrendingService with Redis Sorted Sets for O(log N) trending operations
- Exponential time-decay scoring with 7-day half-life (score = weight × e^(-age_hours / 168))
- Three trending metrics: mentions (time-decay), risk (avg score), sanctions (count)
- Celery tasks for entity extraction (extract_entities_from_event, backfill_entities)
- Management command for extraction and trending sync (extract_entities)
- End-to-end pipeline tested: Event → Entity/EntityMention → Redis trending scores

## Task Commits

Each task was committed atomically:

1. **Task 1: Create TrendingService with Redis Sorted Sets and time-decay** - `73fc91e` (feat)
2. **Task 2: Create extract_entities Celery task for event processing** - `67601fd` (feat)
3. **Task 3: Create management command and test entity extraction on sample events** - `2c1c618` (feat)

## Files Created/Modified

- `backend/data_pipeline/services/trending_service.py` - TrendingService with update_entity_score, get_trending_entities (3 metrics), get_entity_rank, sync_trending_scores
- `backend/data_pipeline/tasks/entity_extraction.py` - extract_entities_from_event and backfill_entities Celery tasks with LLM extraction and fallback
- `backend/data_pipeline/management/commands/extract_entities.py` - Django management command with --days, --all, --sync-trending options

## Decisions Made

**Exponential time-decay formula:**
- Using score = weight × e^(-age_hours / 168) with 7-day half-life
- Provides gradual decay (not cliff-based like HN/Reddit algorithms)
- Recent mentions heavily weighted, old mentions fade naturally

**Three trending metrics:**
- `mentions`: Time-decayed trending score from Redis (real-time)
- `risk`: Average risk_score from linked events (analytical)
- `sanctions`: Count of sanctions matches (compliance focus)

**Timezone-aware datetime:**
- Changed from `datetime.utcnow()` to `timezone.now()`
- Fixes "can't subtract offset-naive and offset-aware datetimes" error
- Django best practice for timezone support

**Bulk Entity fetch in trending:**
- Get entity IDs from Redis, then bulk fetch Entity objects
- Avoids N+1 query problem (N separate queries for N entities)
- Maintains Redis ordering in final results

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Auto-fix blocker] Timezone-aware datetime error**
- **Found during:** Task 3 (Testing entity extraction)
- **Issue:** TrendingService.update_entity_score() used `datetime.utcnow()` (naive) but Event.timestamp is timezone-aware, causing TypeError
- **Fix:** Changed to `timezone.now()` from django.utils for timezone-aware datetime
- **Files modified:** backend/data_pipeline/services/trending_service.py
- **Verification:** Entity extraction test passed, trending scores calculated without error
- **Committed in:** 2c1c618 (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (blocking)
**Impact on plan:** Critical fix for production use. No scope creep.

## Issues Encountered

**Timezone mismatch error:**
- Problem: `datetime.utcnow()` returns naive datetime, but Django models use timezone-aware
- Symptom: "can't subtract offset-naive and offset-aware datetimes" TypeError
- Resolution: Used `timezone.now()` from django.utils (timezone-aware)
- Learning: Always use Django's timezone utilities, not Python's datetime.utcnow()

## Testing Results

Tested entity extraction on sample event (WTI Crude Oil Prices):
- **Entities extracted:** 5 (PDVSA, FRED, Venezuelan Government, Venezuela, Global Energy Markets)
- **Entity types:** 3 organizations, 2 locations
- **EntityMention records:** 5 created successfully
- **Trending scores:** Calculated with time-decay (Venezuela: 0.96, PDVSA: 0.93)
- **Redis leaderboard:** Populated and queryable via get_trending_entities()

Management command verification:
- `python manage.py extract_entities --days 7` → Queued 1 event for extraction
- `python manage.py extract_entities --sync-trending` → Synced 5 mentions to Redis, displayed top 10 trending entities

## Next Phase Readiness

**Ready for 06-03-PLAN.md (Entity API & Trending Endpoints):**
- TrendingService provides get_trending_entities() for API endpoints
- Entity and EntityMention models populated with real data
- Redis trending scores updated in real-time
- Management commands available for backfill and maintenance

**No blockers** - entity extraction pipeline fully functional end-to-end

---
*Phase: 06-entity-watch*
*Completed: 2026-01-09*
