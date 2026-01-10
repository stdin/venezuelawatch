---
phase: 22-data-source-architecture
plan: 01
subsystem: data-pipeline
tags: [python, abc, adapter-pattern, plugin-system, pubsub, convention-over-configuration]

# Dependency graph
requires:
  - phase: 18-gcp-native-pipeline
    provides: Cloud Functions Gen2, Pub/Sub event publishing, standalone functions pattern
  - phase: 14.3-complete-event-migration
    provides: BigQuery Event schema, polyglot persistence architecture
provides:
  - DataSourceAdapter abstract base class (fetch, transform, validate, publish_events)
  - AdapterRegistry with convention-based discovery ({source}_adapter.py → {Source}Adapter)
  - Plugin system foundation for adding data sources (GDELT, ReliefWeb, World Bank, etc.)
  - Health tracking for adapter observability (in-memory metrics)
affects: [22-02-gdelt-refactor, 22-03-reliefweb-adapter, future-data-source-integrations]

# Tech tracking
tech-stack:
  added: []
  patterns: [adapter-pattern, plugin-discovery, convention-over-configuration, abc-abstract-methods]

key-files:
  created:
    - backend/data_pipeline/adapters/__init__.py
    - backend/data_pipeline/adapters/base.py
    - backend/data_pipeline/adapters/registry.py
  modified: []

key-decisions:
  - "Convention-based discovery: {source}_adapter.py → {Source}Adapter for zero-config plugin system"
  - "Separate validate() method from transform() for partial success publishing (97/100 valid events published vs all-or-nothing)"
  - "In-memory health tracking (not persistent) for lightweight observability without database overhead"
  - "Singleton registry with auto-discovery on import for global access without initialization code"

patterns-established:
  - "Plugin pattern: Drop file in adapters/, follow naming, auto-discovered (Django-style convention)"
  - "ABC contract: fetch (raw data) → transform (BigQuery schema) → validate (per-event) → publish (Pub/Sub)"
  - "publish_events() concrete helper method prevents code duplication across adapters"

issues-created: []

# Metrics
duration: 2 min
completed: 2026-01-10
---

# Phase 22 Plan 01: Data Source Architecture Summary

**Extensible adapter architecture with plugin-style discovery - drop file, follow naming convention, auto-registered**

## Performance

- **Duration:** 2 min
- **Started:** 2026-01-10T08:01:59Z
- **Completed:** 2026-01-10T08:04:30Z
- **Tasks:** 2/2
- **Files modified:** 3

## Accomplishments

- DataSourceAdapter ABC defines clear contract: fetch() → transform() → validate() → publish_events()
- AdapterRegistry discovers adapters by convention ({source}_adapter.py → {Source}Adapter class)
- Plugin system ready: adding new data source requires single file, zero registry code
- Comprehensive docstrings document how to implement adapters with full examples

## Task Commits

Each task was committed atomically:

1. **Task 1: Create DataSourceAdapter abstract base class** - `a047b7c` (feat)
   - Abstract methods: fetch, transform, validate (3 required implementations)
   - Class attributes: source_name, schedule_frequency, default_lookback_minutes
   - Helper method: publish_events validates and publishes to Pub/Sub
   - Type hints throughout using typing module

2. **Task 2: Build AdapterRegistry with convention-based discovery** - `012e0ef` (feat)
   - Singleton AdapterRegistry scans adapters/ for *_adapter.py files
   - Methods: discover_adapters, get_adapter, list_adapters, get_metadata
   - Health tracking: record_run, get_health (in-memory metrics)
   - Graceful handling of invalid adapters (logs warnings, continues)

## Files Created/Modified

**Created:**
- `backend/data_pipeline/adapters/__init__.py` - Package exports
- `backend/data_pipeline/adapters/base.py` - DataSourceAdapter ABC (251 lines with comprehensive docs)
- `backend/data_pipeline/adapters/registry.py` - AdapterRegistry singleton (330 lines with discovery logic)

## Decisions Made

**1. Convention-based discovery over explicit registration**
- Rationale: Zero-config plugin system - drop {source}_adapter.py with {Source}Adapter class, registry finds it automatically. Reduces boilerplate, follows Django patterns (apps, management commands).

**2. Separate validate() from transform() for partial success**
- Rationale: If 100 events fetched and 3 fail validation, publish the 97 valid ones rather than failing entire batch. Better resilience and observability.

**3. In-memory health tracking (not persistent)**
- Rationale: Lightweight observability without database writes. Cloud Functions Gen2 are stateless, persistent metrics would require BigQuery writes. In-memory sufficient for debugging during execution.

**4. publish_events() as concrete helper method**
- Rationale: All adapters publish to Pub/Sub the same way. Concrete method prevents duplication across implementations and ensures consistent validation before publishing.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

**Ready for Phase 22-02 (GDELT refactor):**
- Adapter contract defined and tested
- Registry discovers adapters automatically
- Reference implementation (GDELT) can now be refactored to adapter pattern

**Foundation supports:**
- ReliefWeb adapter (22-03)
- World Bank adapter (future)
- FRED adapter refactor (future)
- Any future data source integration

---
*Phase: 22-data-source-architecture*
*Completed: 2026-01-10*
