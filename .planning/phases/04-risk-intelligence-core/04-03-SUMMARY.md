---
phase: 04-risk-intelligence-core
plan: 03
subsystem: risk-intelligence
tags: [severity-classification, NCISS, impact-assessment, llm, python, multi-criteria-scoring]

# Dependency graph
requires:
  - phase: 04-02
    provides: Multi-dimensional risk aggregation with weighted scoring pattern
  - phase: 03-04
    provides: LLM intelligence with comprehensive analysis
provides:
  - Event severity classification (SEV1-5) using NCISS-style weighted criteria
  - ImpactClassifier service with multi-criteria assessment
  - Severity field on Event model with database index
  - Batch severity classification task
  - Integration into intelligence pipeline
affects: [05-dashboard, 06-alerts, 07-api]

# Tech tracking
tech-stack:
  added: []
  patterns: [NCISS-weighted-criteria, severity-vs-risk-separation, llm-criteria-extraction]

key-files:
  created:
    - backend/data_pipeline/services/impact_classifier.py
    - backend/core/migrations/0006_add_severity.py
  modified:
    - backend/core/models.py
    - backend/core/admin.py
    - backend/data_pipeline/tasks/intelligence_tasks.py
    - backend/data_pipeline/tasks/__init__.py

key-decisions:
  - "NCISS-style weighted multi-criteria scoring (scope=0.35, duration=0.25, reversibility=0.20, economic_impact=0.20)"
  - "Severity independent of risk score (severity=impact, risk=probability×impact)"
  - "LLM for context-aware criteria extraction (not keyword matching)"
  - "SEV1-5 string choices (not integers) for self-documenting levels"
  - "Fallback to medium severity (0.5) on LLM errors for resilience"
  - "Use fast model (Haiku) for cost efficiency"

patterns-established:
  - "Severity classification: Multi-criteria weighted scoring using LLM to assess scope, duration, reversibility, economic impact"
  - "Impact vs Risk separation: Severity measures impact only, independent of probability"
  - "Robust JSON parsing: LLM structured output with fallback for non-native schema support"

issues-created: []

# Metrics
duration: 5min
completed: 2026-01-08
---

# Phase 4 Plan 3: Event Severity Classification Summary

**NCISS-style severity classification (SEV1-5) using LLM-assessed weighted criteria for scope, duration, reversibility, and economic impact, integrated into intelligence pipeline with batch processing**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-08T20:23:08Z
- **Completed:** 2026-01-08T20:28:58Z
- **Tasks:** 3/3 completed
- **Files modified:** 6

## Accomplishments

- Implemented ImpactClassifier service with NCISS-style weighted multi-criteria scoring
- Added severity field to Event model with SEV1-5 choices and database index for filtering
- Integrated severity classification into intelligence analysis pipeline
- Created batch_classify_severity task for classifying existing events
- Validated weights sum to 1.0 to prevent score inflation
- LLM-based context-aware criteria extraction with fallback to medium severity on errors
- Severity independently assessed from risk score (severity=impact, risk=probability×impact)

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement impact_classifier.py** - `708b9f0` (feat)
2. **Task 2: Add severity field to Event model** - `7ff3617` (feat)
3. **Task 3: Integrate into intelligence workflow** - `13a71a9` (feat)

**Plan metadata:** (pending - will be added in final commit)

## Files Created/Modified

- `backend/data_pipeline/services/impact_classifier.py` - New service implementing NCISS-style severity classification
  - ImpactClassifier class with classify_severity() method
  - WEIGHTS dict with normalized weights (sum=1.0): scope=0.35, duration=0.25, reversibility=0.20, economic_impact=0.20
  - SEVERITY_THRESHOLDS mapping 0.0-1.0 scores to SEV1-5 levels
  - _extract_severity_criteria() using LLM with structured JSON schema
  - Fallback to medium severity (0.5) on LLM errors
  - Uses Haiku (fast model) for cost efficiency

- `backend/core/models.py` - Event model with severity field
  - Added severity CharField with SEV1-5 choices
  - Database index for dashboard filtering performance
  - Updated __str__() to optionally display severity

- `backend/core/admin.py` - Admin interface updates
  - Added severity to list_display for event listing
  - Added severity to list_filter for filtering

- `backend/core/migrations/0006_add_severity.py` - Database migration
  - Adds severity field with db_index=True
  - Applied successfully

- `backend/data_pipeline/tasks/intelligence_tasks.py` - Intelligence pipeline integration
  - Updated analyze_event_intelligence() to classify and save severity
  - Updated update_sentiment_scores() to include severity classification
  - Added batch_classify_severity(lookback_days=30) task
  - Updated logging to include severity in output
  - Added severity to task return dictionaries

- `backend/data_pipeline/tasks/__init__.py` - Registered batch_classify_severity task

## Decisions Made

**1. NCISS-style weighted multi-criteria scoring**
- Rationale: CISA's NCISS (National Cyber Incident Severity Schema) proven methodology for severity assessment. Uses weighted arithmetic mean of multiple criteria (scope, duration, reversibility, economic impact) for nuanced classification instead of simple keyword matching.

**2. Severity independent of risk score**
- Rationale: Severity measures impact (how bad is it?), while risk combines probability and impact (how likely × how bad?). Separating these allows dashboard users to filter by worst-case impact independent of likelihood.

**3. LLM for context-aware criteria extraction**
- Rationale: Context matters - "economic crisis" could be SEV2-4 depending on actual scope and duration. LLM assesses context rather than keyword matching, handling nuanced situations correctly.

**4. String choices (SEV1_CRITICAL) not integers**
- Rationale: Self-documenting and prevents confusion about ordering (is 1 high or low?). Database queries use explicit labels: `severity='SEV1_CRITICAL'` vs ambiguous `severity=1`.

**5. Fallback to medium severity on errors**
- Rationale: LLM failures shouldn't block event processing. Fallback to SEV3_MEDIUM (0.5 for all criteria) provides reasonable default while logging warning for monitoring.

**6. Use Haiku (fast model) for cost efficiency**
- Rationale: Criteria extraction is structured task with clear rubric. Haiku provides sufficient quality at lower cost compared to Sonnet. Observed robust JSON parsing handles non-native schema support.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**OFAC API 404 errors during testing:**
- Issue: OFAC Sanctions Search API returns 404 errors for entity screening
- Context: Existing issue from previous phases, not specific to severity classification
- Impact: Sanctions screening falls back to 0.0 score when API unavailable
- Resolution: Not blocking for severity classification. Logged for Phase 5 API resilience work. Production will use OpenSanctions premium API or retry logic.

**LLM JSON parsing warnings:**
- Issue: "JSON parse failed, using robust parser" warnings during LLM calls
- Context: Haiku model doesn't support native JSON schema, falls back to prompt-based approach
- Impact: None - robust parser successfully extracts JSON from response
- Resolution: Expected behavior. Robust JSON parsing handles this gracefully.

## Next Phase Readiness

- Event severity classification fully operational
- Severity field indexed and ready for dashboard filtering
- Batch processing available for classifying existing events
- LLM-based context-aware assessment provides nuanced severity levels
- Independent severity dimension complements risk scoring
- Ready for Phase 4 Plan 4: Risk Intelligence API & Dashboard Integration
- No blockers

---
*Phase: 04-risk-intelligence-core*
*Completed: 2026-01-08*
