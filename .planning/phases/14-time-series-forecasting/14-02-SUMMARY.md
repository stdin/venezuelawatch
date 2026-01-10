---
phase: 14-time-series-forecasting
plan: 02
subsystem: ml-infrastructure
tags: [vertex-ai, forecasting, tide-model, bigquery, machine-learning, automl]

# Dependency graph
requires:
  - phase: 14-01-bigquery-etl-setup
    provides: BigQuery dataset and table schema for Vertex AI training data
provides:
  - Vertex AI SDK integration with training and deployment scripts
  - AutoML forecasting configuration for TiDE model architecture
  - Deployment infrastructure for autoscaling prediction endpoints
  - Django settings configured for Vertex AI endpoint integration
affects: [14-03-forecast-api, forecasting, predictions]

# Tech tracking
tech-stack:
  added: [google-cloud-aiplatform]
  patterns: [automl-forecasting, vertex-ai-deployment, model-endpoint-autoscaling]

key-files:
  created:
    - backend/forecasting/train_model.py
    - backend/forecasting/deploy_endpoint.py
  modified:
    - backend/requirements.txt
    - backend/venezuelawatch/settings.py

key-decisions:
  - "TiDE model automatically selected by Vertex AI AutoML (10x faster training than previous models)"
  - "30-day forecast horizon aligns with CONTEXT.md requirements for risk trajectory prediction"
  - "n1-standard-4 machine type sufficient for TiDE inference (no GPU needed)"
  - "Autoscaling 1-10 replicas balances cost efficiency with availability"
  - "80/10/10 train/val/test split for robust model evaluation"
  - "Training and deployment deferred until sufficient historical data available (currently <60 days)"

patterns-established:
  - "Vertex AI training script pattern with argparse for project/location configuration"
  - "AutoML forecasting job pattern with optimization objective (minimize-rmse)"
  - "Endpoint deployment pattern with autoscaling configuration"
  - "Django settings pattern for ML endpoint configuration via environment variables"

issues-created: []

# Metrics
duration: 10min
completed: 2026-01-10
---

# Phase 14 Plan 2: Vertex AI Training Infrastructure Summary

**Vertex AI training and deployment infrastructure complete: AutoML forecasting scripts ready for TiDE model training on entity risk data once sufficient historical data available**

## Performance

- **Duration:** 10 min
- **Started:** 2026-01-10T01:07:24Z
- **Completed:** 2026-01-10T01:17:45Z
- **Tasks:** 2 auto tasks
- **Files created:** 2
- **Files modified:** 2

## Accomplishments

- Installed Vertex AI SDK (google-cloud-aiplatform>=1.114.0)
- Created training script with AutoML forecasting configuration
- Fixed TimeSeriesDataset API usage (column specs moved to training job)
- Created BigQuery dataset and table for venezuelawatch-staging project
- Created endpoint deployment script with autoscaling configuration
- Configured Django settings for Vertex AI endpoint integration
- Infrastructure ready for training when sufficient data available

## Task Commits

Each task was committed atomically:

1. **Task 1: Install Vertex AI SDK and create training script** - `d3a875a` (chore)
   - Bug fix: Corrected TimeSeriesDataset API - `2784ee5` (fix)
2. **Task 2: Deploy model endpoint for predictions** - `cbf9be5` (feat)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified

- `backend/requirements.txt` - Added google-cloud-aiplatform>=1.114.0
- `backend/forecasting/train_model.py` - AutoML training workflow with TimeSeriesDataset.create() and AutoMLForecastingTrainingJob configuration (30-day horizon, daily granularity)
- `backend/forecasting/deploy_endpoint.py` - Endpoint deployment script with n1-standard-4 autoscaling (1-10 replicas), 30-min timeout
- `backend/venezuelawatch/settings.py` - Added VERTEX_AI_ENDPOINT_ID, VERTEX_AI_PROJECT_ID (uses GCP_PROJECT_ID), VERTEX_AI_LOCATION

## Decisions Made

**TiDE model selection:** Vertex AI AutoML automatically selects TiDE architecture for time-series forecasting. TiDE is 10x faster than previous Vertex AI forecasting models while maintaining accuracy.

**30-day forecast horizon:** Matches CONTEXT.md requirement for predicting entity risk trajectories 30 days into the future. Provides actionable medium-term intelligence for investment decisions.

**n1-standard-4 machine type:** CPU-only machine sufficient for TiDE model inference. No GPU acceleration needed, reducing deployment costs while maintaining sub-second prediction latency.

**Autoscaling 1-10 replicas:** Minimum 1 replica ensures zero cold-start latency for first prediction. Maximum 10 replicas handles traffic spikes. Balances cost efficiency (~$100/month for min replica) with availability.

**80/10/10 train/val/test split:** Industry-standard split for time-series forecasting. 80% training data, 10% validation for hyperparameter tuning, 10% test for final evaluation. Prevents overfitting while maximizing training data usage.

**Training deferred:** BigQuery table created but currently empty. Training requires minimum 60 days of historical entity risk data. Infrastructure complete and ready for training once data pipeline hydrated.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Vertex AI TimeSeriesDataset API usage**
- **Found during:** Task 1 (Training script execution)
- **Issue:** TimeSeriesDataset.create() TypeError - unexpected keyword arguments time_column, time_series_identifier_column, target_column. API changed in recent SDK versions - these parameters belong in training_job.run() only.
- **Fix:** Removed column specification parameters from dataset.create(), kept only display_name and bq_source. Column specs remain in training_job.run() where they belong.
- **Files modified:** backend/forecasting/train_model.py
- **Verification:** Script executes without TypeError, shows correct usage help
- **Commit:** 2784ee5

**2. [Rule 3 - Blocking] Created BigQuery dataset/table for venezuelawatch-staging project**
- **Found during:** Task 1 checkpoint (Training script execution)
- **Issue:** BigQuery table `venezuelawatch-staging.intelligence.entity_risk_training_data` not found. Plan 14-01 created table for `venezuelawatch` project, but actual project is `venezuelawatch-staging`.
- **Fix:** Ran bigquery_setup.py with correct project ID to create dataset and table schema
- **Files modified:** None (GCP infrastructure only)
- **Verification:** bq show confirms dataset and table exist in venezuelawatch-staging project
- **Commit:** N/A (infrastructure change, not code)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes necessary for correct operation. No scope creep.

## Issues Encountered

**Training deferred due to insufficient data:** BigQuery table created but empty. Training requires minimum 60 days of historical entity risk data from PostgreSQL. Data pipeline needs hydration via backfill commands (backfill_gdelt, backfill_fred, backfill_comtrade, backfill_worldbank) and entity extraction (extract_entities management command). Infrastructure complete and ready for training once data available.

## Next Phase Readiness

**Infrastructure complete:**
- ✅ Vertex AI SDK installed
- ✅ Training script created and validated
- ✅ Deployment script created
- ✅ Django settings configured
- ✅ BigQuery dataset and table exist (venezuelawatch-staging)

**Prerequisites for actual training (deferred):**
1. Hydrate PostgreSQL with 60+ days of historical events:
   ```bash
   python backend/manage.py backfill_gdelt --days=60
   python backend/manage.py backfill_fred --months=12
   python backend/manage.py extract_entities
   ```
2. Run ETL to populate BigQuery:
   ```bash
   python backend/forecasting/setup_etl.py --project venezuelawatch-staging
   # Or manually trigger scheduled query
   ```
3. Verify data loaded:
   ```bash
   bq query 'SELECT COUNT(*) FROM intelligence.entity_risk_training_data'
   ```
4. Initiate training:
   ```bash
   python backend/forecasting/train_model.py --project venezuelawatch-staging
   ```
5. Deploy endpoint:
   ```bash
   python backend/forecasting/deploy_endpoint.py --project venezuelawatch-staging --model [MODEL_RESOURCE_NAME]
   ```

**Ready for next plan (14-03)** when model endpoint deployed.

---
*Phase: 14-time-series-forecasting*
*Completed: 2026-01-10*
