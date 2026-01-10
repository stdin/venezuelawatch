---
phase: 15-correlation-pattern-analysis
plan: 01
subsystem: analytics
tags: [scipy, statsmodels, correlation, pearson, spearman, bonferroni, bigquery, django-ninja]

# Dependency graph
requires:
  - phase: 14.3-complete-bigquery-migration
    provides: BigQuery time-series data (events, entity mentions, FRED indicators)
provides:
  - Statistical correlation computation with scipy/statsmodels
  - Bonferroni correction for multiple comparisons
  - Stationarity checks for time-series (ADF test)
  - Django REST API endpoint for correlation analysis
affects: [15-02-correlation-graph-ui, custom-reports, pattern-detection]

# Tech tracking
tech-stack:
  added: [scipy==1.16.1, pandas==2.2.3, statsmodels==0.14.4, scikit-learn==1.5.2]
  patterns: [statistical-significance-testing, bonferroni-correction, stationarity-checks, parameterized-bigquery-queries]

key-files:
  created:
    - backend/api/correlation/compute.py
    - backend/api/correlation/views.py
    - backend/api/correlation/__init__.py
    - backend/api/correlation/time_series.py
  modified:
    - backend/requirements.txt
    - backend/venezuelawatch/api.py

key-decisions:
  - "Use scipy.stats.pearsonr/spearmanr (not custom formulas) for correlation computation"
  - "Apply Bonferroni correction via statsmodels (not FDR) for conservative multiple comparison control"
  - "Default thresholds: alpha=0.05, min_effect_size=0.7 for strong correlations only"
  - "Stationarity check enabled by default with ADF test and automatic differencing"
  - "Parameterized BigQuery queries for all data extraction (security)"
  - "Inner join for time-series alignment (drops dates missing from any variable)"

patterns-established:
  - "Statistical rigor pattern: correlation + p-value + Bonferroni correction + effect size filter"
  - "Time-series preprocessing: ADF test → differencing if non-stationary → correlation"
  - "API response includes metadata: n_tested, n_significant, bonferroni_threshold"

issues-created: []

# Metrics
duration: 4min
completed: 2026-01-10
---

# Phase 15 Plan 01: Correlation Backend API Summary

**Statistical correlation engine: scipy/statsmodels backend with Bonferroni correction, stationarity checks, and BigQuery time-series integration for investment-grade rigor.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-10T04:04:46Z
- **Completed:** 2026-01-10T04:08:41Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Installed scipy 1.16.1 and statsmodels 0.14.4 for statistical correlation
- Created correlation computation service with Pearson/Spearman methods
- Implemented Bonferroni correction for multiple comparisons (statsmodels.stats.multitest)
- Added ADF stationarity test with automatic differencing for time-series
- Built Django API endpoint for correlation analysis (POST /api/correlation/compute/)
- Integrated BigQuery queries for entity risk scores, FRED indicators, event counts
- Applied significance (p_adjusted < alpha) AND effect size (|r| >= threshold) filtering
- Used parameterized BigQuery queries for SQL injection prevention

## Task Commits

Each task was committed atomically:

1. **Task 1: Install scipy and statsmodels dependencies** - `2df57e5` (chore)
2. **Task 2: Create correlation computation service** - `ee8f3d4` (feat)
3. **Task 3: Create Django API endpoint** - `75c57ce` (feat)

## Files Created/Modified

- `backend/requirements.txt` - Added scipy, pandas, statsmodels, scikit-learn
- `backend/api/correlation/compute.py` - Correlation computation with significance testing
- `backend/api/correlation/__init__.py` - Package init
- `backend/api/correlation/time_series.py` - Time-series data extraction placeholder
- `backend/api/correlation/views.py` - Django REST API endpoint
- `backend/venezuelawatch/api.py` - Added correlation router

## Decisions Made

- Used scipy.stats.pearsonr/spearmanr (not custom formulas) per research guidance
- Applied Bonferroni correction (not FDR) for conservative multiple comparison control
- Default thresholds: alpha=0.05, min_effect_size=0.7 for strong correlations only
- Stationarity check enabled by default for time-series (ADF test with differencing)
- Parameterized BigQuery queries for all data extraction (security best practice)
- Inner join for time-series alignment (drops dates missing from any variable)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

**Ready for 15-02-PLAN.md** (Frontend correlation graph visualization with Reagraph)

Backend correlation API complete with:
- Statistical rigor: Bonferroni correction + effect size filtering
- Time-series support: stationarity checks with ADF test
- BigQuery integration: entity risk, FRED indicators, event counts
- Secure parameterized queries
- OpenAPI documentation (django-ninja auto-generated)

No blockers for frontend visualization phase.

---
*Phase: 15-correlation-pattern-analysis*
*Completed: 2026-01-10*
