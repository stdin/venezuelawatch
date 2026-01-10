---
phase: 18-gcp-native-pipeline-migration
plan: 03
subsystem: infrastructure
tags: [celery-migration, gcp-cutover, serverless, cleanup]

# Dependency graph
requires:
  - phase: 18-02-processing-layer-migration
    provides: Pub/Sub + Cloud Run + Cloud Tasks handlers
provides:
  - Cutover automation script for manual GCP deployment
  - Celery dependencies removed from codebase
  - GCP-native architecture documentation
  - Code ready for production cutover (deployment deferred)
affects: [production-deployment, phase-19+]

# Tech tracking
tech-stack:
  removed: [celery, django-celery-results, django-celery-beat]
  retained: [redis, django-redis] # For trending cache only
  patterns: [big-bang-cutover, manual-deployment-gates]

key-files:
  created:
    - scripts/cutover_to_gcp.sh
    - docs/ARCHITECTURE.md
  modified:
    - backend/venezuelawatch/settings.py
    - backend/requirements.txt
    - backend/data_pipeline/tasks/intelligence_tasks.py
    - backend/data_pipeline/tasks/entity_extraction.py
  deleted:
    - backend/data_pipeline/tasks/gdelt_tasks.py
    - backend/data_pipeline/tasks/base.py

key-decisions:
  - "Big-bang cutover approach (not gradual) for clean break"
  - "GCP deployment deferred to manual execution per safety config"
  - "Celery code removed proactively (deployment can be done later)"
  - "Redis retained for trending cache (downscaled from Celery queue usage)"

patterns-established:
  - "Cutover automation scripts document manual steps, not auto-execute"
  - "Safety gates prevent unintended GCP deployments"
  - "Code cleanup can precede infrastructure deployment"

issues-created: []

# Metrics
duration: 8min
completed: 2026-01-10
---

# Phase 18 Plan 03: Cutover & Infrastructure Cleanup Summary

**Celery dependencies removed, cutover automation ready, GCP deployment deferred to manual execution**

## Performance

- **Duration:** 8 min
- **Started:** 2026-01-10T05:31:42Z
- **Completed:** 2026-01-10T05:39:05Z
- **Tasks:** 2 (checkpoint skipped - manual deployment required)
- **Files modified:** 9

## Accomplishments

- Created comprehensive cutover automation script with rollback instructions
- Disabled Celery Beat schedule in Django settings
- Removed all Celery dependencies from requirements.txt
- Deleted deprecated task files (gdelt_tasks.py, base.py)
- Marked legacy task files as DEPRECATED with migration notes
- Removed all CELERY_* configuration from settings.py
- Created comprehensive GCP-native architecture documentation (530 lines)
- Retained Redis for trending cache (Memorystore can be downscaled)

## Task Commits

1. **Task 1: Create cutover script and disable Celery Beat** - `560d45f` (chore)
2. **Task 2: Remove Celery and Redis dependencies** - `3f86ccb` (chore)

**Plan metadata:** (pending - will be committed after this summary)

## Files Created/Modified

**Created:**
- `scripts/cutover_to_gcp.sh` - 240-line cutover automation script with 5-step manual process
- `docs/ARCHITECTURE.md` - 530-line comprehensive architecture documentation

**Modified:**
- `backend/venezuelawatch/settings.py` - Removed CELERY_BEAT_SCHEDULE and all CELERY_* settings
- `backend/requirements.txt` - Removed celery, django-celery-results, django-celery-beat
- `backend/data_pipeline/tasks/intelligence_tasks.py` - Added DEPRECATED header
- `backend/data_pipeline/tasks/entity_extraction.py` - Added DEPRECATED header

**Deleted:**
- `backend/data_pipeline/tasks/gdelt_tasks.py` - 194 lines (DOC API version, replaced by gdelt_sync_task.py)
- `backend/data_pipeline/tasks/base.py` - 90 lines (BaseIngestionTask class no longer needed)

**Not Found (already removed):**
- `backend/venezuelawatch/celery.py` - Previously deleted

## Decisions Made

**Big-bang cutover approach:**
- Disable Celery Beat completely, then enable Cloud Scheduler
- No gradual migration - clean break for operational simplicity
- 48-hour validation period before declaring success
- Full rollback capability via git history + script instructions

**Deployment deferred to manual execution:**
- GCP deployment requires external service operations
- Safety config (`always_confirm_external_services: true`) prevents auto-deployment
- Cutover script documents exact manual steps
- User controls timing of production cutover

**Redis retained for trending cache:**
- Trending entity scores still use Redis sorted sets
- Django session storage uses Redis
- Can be downscaled from Celery queue usage (~85% reduction)
- Optional future migration to BigQuery materialized views

**Celery dependencies removed proactively:**
- Code cleanup can precede infrastructure deployment
- Reduces dependency bloat immediately
- Forces migration to new architecture
- Rollback requires restoring from git history

## Deviations from Plan

None - plan adapted to skip GCP deployment per user choice.

**Note:** Original plan included checkpoint for 48-hour validation after GCP deployment. User chose "Create scripts only, skip deployment" so checkpoint was not executed. Deployment and validation deferred to manual execution when ready for production cutover.

## Issues Encountered

None

## Next Phase Readiness

**Code ready for GCP cutover, deployment deferred:**

1. **Manual steps required** (documented in `scripts/cutover_to_gcp.sh`):
   - Deploy Django to Cloud Run with Pub/Sub handlers
   - Run Phase 18-01 deployment scripts (Cloud Functions + Cloud Scheduler)
   - Run Phase 18-02 infrastructure setup (Pub/Sub topics + Cloud Tasks queues)
   - Enable Cloud Scheduler jobs (all 6 ingestion tasks)
   - Monitor for 48 hours (zero data loss validation)

2. **Verification criteria:**
   - All Cloud Scheduler jobs executing on schedule
   - Cloud Functions metrics show successful ingestion
   - BigQuery data validated (no duplicates, no gaps)
   - Pub/Sub & Cloud Tasks flow operational
   - Error rate < 1%
   - Cost within $1.60-3.60/month target

3. **Rollback plan available:**
   - Re-enable CELERY_BEAT_SCHEDULE from git history (commit `cb29c09`)
   - Restore Celery dependencies in requirements.txt
   - Pause Cloud Scheduler jobs (not delete)
   - Restart Celery workers
   - ~15 minutes to restore Celery-based ingestion

**Blockers:** None - all code complete and ready for manual deployment

**Next Step:** Execute manual GCP cutover when ready, then Phase 18 will be 100% complete

---

## Operational Wins (Post-Deployment)

**Once deployed, expected benefits:**

- **Cost reduction:** $20-40/month → $1.60-3.60/month (85-91% reduction)
- **Auto-scaling:** Cloud Run 0→100 instances (no manual worker management)
- **Unified observability:** All logs in Cloud Logging, Error Reporting, Trace
- **Simpler deployments:** Independent function deployments, no worker coordination
- **Built-in retries:** Cloud Tasks handles exponential backoff automatically
- **GCP-native:** No external services, everything in one cloud provider

---
*Phase: 18-gcp-native-pipeline-migration*
*Completed: 2026-01-10*
