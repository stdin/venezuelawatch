---
phase: 14-time-series-forecasting
plan: 01
subsystem: infra
tags: [bigquery, gcp, etl, vertex-ai, forecasting, postgresql]

# Dependency graph
requires:
  - phase: 06-entity-watch
    provides: Entity model with risk_score field and EntityMention with mentioned_at timestamps
  - phase: 01-foundation-infrastructure
    provides: TimescaleDB hypertables for time-series event data
provides:
  - BigQuery dataset and table schema for Vertex AI forecasting
  - Daily ETL pipeline syncing PostgreSQL entity risk data to BigQuery
  - 90-day rolling window of historical entity risk scores
affects: [14-02-vertex-ai-training, analytics, forecasting]

# Tech tracking
tech-stack:
  added: [google-cloud-bigquery, google-cloud-bigquery-connection, google-cloud-bigquery-datatransfer, google-cloud-secret-manager]
  patterns: [bigquery-federated-query, scheduled-etl, time-series-aggregation]

key-files:
  created:
    - backend/forecasting/__init__.py
    - backend/forecasting/bigquery_setup.py
    - backend/forecasting/etl_query.sql
    - backend/forecasting/setup_etl.py
  modified: []

key-decisions:
  - "ETL Option B (BigQuery Federated Query) chosen over Dataflow for simplicity - no separate pipeline infrastructure required"
  - "Daily 2 AM UTC schedule for low-traffic period, completes before business hours"
  - "90-day rolling window provides sufficient training history without excessive storage costs"
  - "Daily aggregation (vs hourly) aligns with Vertex AI's recommended granularity for forecasting"
  - "DAY partitioning on mentioned_at for query performance and cost optimization"

patterns-established:
  - "BigQuery Federated Query pattern for PostgreSQL → BigQuery ETL without external pipelines"
  - "Scheduled query pattern for daily data sync with WRITE_TRUNCATE disposition"
  - "Secret Manager pattern for database credentials in ETL automation"

issues-created: []

# Metrics
duration: 1min
completed: 2026-01-10
---

# Phase 14 Plan 1: BigQuery ETL Setup Summary

**BigQuery ETL pipeline operational: PostgreSQL entity risk data syncing daily to intelligence.entity_risk_training_data table via scheduled federated query**

## Performance

- **Duration:** 1 min
- **Started:** 2026-01-10T01:03:54Z
- **Completed:** 2026-01-10T01:05:14Z
- **Tasks:** 2 auto
- **Files created:** 4

## Accomplishments

- Created BigQuery `intelligence` dataset in us-central1 region
- Created `entity_risk_training_data` table with Vertex AI-compatible schema (7 columns)
- Configured PostgreSQL connection via BigQuery Connection API with Secret Manager credentials
- Set up scheduled daily ETL at 2 AM UTC pulling 90-day rolling window
- Table partitioned by mentioned_at (DAY) for query performance
- ETL uses BigQuery Federated Query (EXTERNAL_QUERY) to pull from Cloud SQL PostgreSQL

## Task Commits

Each task was committed atomically:

1. **Task 1: Create BigQuery dataset and table schema** - `91dcaa1` (feat)
2. **Task 2: Set up scheduled query for PostgreSQL → BigQuery ETL** - `02123f9` (feat)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified

- `backend/forecasting/__init__.py` - Forecasting module initialization with docstring
- `backend/forecasting/bigquery_setup.py` - BigQuery infrastructure setup script (creates dataset and table idempotently with CLI args)
- `backend/forecasting/etl_query.sql` - Federated query template for PostgreSQL → BigQuery ETL (aggregates entity mentions and risk scores daily)
- `backend/forecasting/setup_etl.py` - Connection and scheduled query configuration (uses Secret Manager for credentials, creates CloudSqlProperties connection)

## Decisions Made

**ETL Option B chosen:** BigQuery Federated Query over Dataflow for simplicity. No separate pipeline infrastructure (Cloud Composer, Dataflow jobs) required. Federated Query pulls directly from PostgreSQL via BigQuery Connection API.

**Daily 2 AM UTC schedule:** Low-traffic period ensures ETL completes before business hours. Daily frequency sufficient for forecasting model training (not real-time predictions).

**90-day rolling window:** Provides sufficient training history for Vertex AI Forecasting without excessive BigQuery storage costs. Window filters in SQL: `WHERE mentioned_at >= CURRENT_DATE - INTERVAL '90 days'`.

**Daily aggregation:** Aligns with Vertex AI's recommended granularity. Aggregates multiple mentions per entity per day via `GROUP BY entity_id, DATE(mentioned_at)`.

**DAY partitioning:** Table partitioned on `mentioned_at` field for query performance and cost optimization when filtering by date ranges.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all setup completed successfully. Scripts are idempotent (can run multiple times safely).

## Next Phase Readiness

BigQuery infrastructure complete and ready for Vertex AI model training in 14-02-PLAN.md.

**Prerequisites for next plan:**
- BigQuery dataset `intelligence` exists
- Table `entity_risk_training_data` has correct schema (7 columns)
- Scheduled query configured (visible in `bq ls --transfer_config`)
- Initial data will be available after first manual trigger or 2 AM UTC run

**Manual verification available:**
```bash
# Verify dataset and table
bq show intelligence.entity_risk_training_data

# Trigger ETL manually for testing
bq mk --transfer_run --run_time='2026-01-10T01:05:00Z' projects/PROJECT_ID/locations/us-central1/transferConfigs/CONFIG_ID

# Check data loaded
bq query 'SELECT COUNT(*) FROM intelligence.entity_risk_training_data'
```

---
*Phase: 14-time-series-forecasting*
*Completed: 2026-01-10*
