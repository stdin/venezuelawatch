# VenezuelaWatch Cloud Functions

GCP-native serverless data ingestion functions for VenezuelaWatch. Replaces Celery-based ingestion tasks with Cloud Functions orchestrated by Cloud Scheduler and Workflows.

## Architecture

Each Cloud Function:
- **HTTP Trigger**: Invoked by Cloud Scheduler or Workflows
- **ADC Auth**: Uses Application Default Credentials (no API keys in code)
- **BigQuery Insert**: Streams data to BigQuery tables
- **Pub/Sub Publish**: Triggers LLM analysis via 'event-analysis' topic
- **Standalone**: No Django dependencies

## Functions

### 1. GDELT Sync (`gdelt_sync/`)

**Purpose**: Sync Venezuela events from GDELT native BigQuery (`gdelt-bq.gdeltv2`)

**Schedule**: Every 15 minutes (matches GDELT update frequency)

**Entry Point**: `sync_gdelt_events`

**Request Body**:
```json
{
  "lookback_minutes": 15
}
```

**Response**:
```json
{
  "events_created": 42,
  "events_skipped": 8,
  "events_fetched": 50
}
```

**Logic**:
- Queries GDELT BigQuery for Venezuela events (ActionGeo/Actor country codes)
- Maps GDELT schema to VenezuelaWatch events table
- Deduplicates by GLOBALEVENTID
- Publishes event IDs to Pub/Sub for LLM analysis

---

### 2. ReliefWeb (`reliefweb/`)

**Purpose**: Fetch humanitarian reports from ReliefWeb API

**Schedule**: Daily

**Entry Point**: `sync_reliefweb`

**Request Body**:
```json
{
  "lookback_days": 1
}
```

**Response**:
```json
{
  "events_created": 5,
  "events_skipped": 2,
  "reports_fetched": 7
}
```

**Logic**:
- Calls ReliefWeb API with Venezuela country filter (ISO3:VEN)
- Maps humanitarian reports to events
- Deduplicates by source_url (30-day window)
- Publishes to Pub/Sub for LLM analysis

---

### 3. FRED Economic Indicators (`fred/`)

**Purpose**: Fetch Venezuela economic series from FRED

**Schedule**: Daily

**Entry Point**: `sync_fred`

**Request Body**:
```json
{
  "lookback_days": 7
}
```

**Response**:
```json
{
  "series_processed": 6,
  "observations_created": 24,
  "observations_skipped": 3,
  "threshold_alerts": 2
}
```

**Series Tracked**:
- Oil prices: WTI crude, Brent crude
- Venezuela macro: CPI inflation, GDP per capita
- Reserves: Total reserves
- Exchange rate: VEF/USD

**Logic**:
- Fetches 6 economic series from FRED API
- Inserts to `fred_indicators` table
- Detects threshold breaches (e.g., oil < $50/barrel)
- Creates alert events for breaches
- Uses Secret Manager for FRED API key

---

### 4. UN Comtrade (`comtrade/`)

**Purpose**: Fetch Venezuela trade flows (imports/exports)

**Schedule**: Monthly

**Entry Point**: `sync_comtrade`

**Request Body**:
```json
{
  "lookback_months": 3
}
```

**Response**:
```json
{
  "commodities_processed": 9,
  "trade_flows_created": 47,
  "trade_flows_skipped": 12,
  "total_trade_value_usd": 1250000000
}
```

**Commodities Tracked**:
- Energy: Crude oil, refined petroleum
- Food: Wheat, maize, beef
- Healthcare: Medicaments
- Technology: Computing machinery, telecom equipment
- Total trade (all commodities)

**Logic**:
- Fetches import/export data for 9 commodity codes
- Filters for significant flows (> $10M USD)
- Inserts to `un_comtrade` table
- Accounts for 2-3 month Comtrade data lag

---

### 5. World Bank (`worldbank/`)

**Purpose**: Fetch Venezuela development indicators

**Schedule**: Monthly

**Entry Point**: `sync_worldbank`

**Request Body**:
```json
{
  "lookback_years": 2
}
```

**Response**:
```json
{
  "indicators_processed": 10,
  "observations_created": 20,
  "observations_skipped": 0,
  "indicators_failed": 0
}
```

**Indicators Tracked**:
- Economic: GDP, inflation, GDP per capita
- Labor: Unemployment rate
- Social: Poverty ratio, education/health expenditure
- Infrastructure: Electricity access, internet users
- Demographic: Population

**Logic**:
- Fetches 10 development indicators using wbgapi
- Inserts annual data to `world_bank` table
- No API key required (World Bank Open Data)

---

### 6. Sanctions Screening (`sanctions/`)

**Purpose**: Re-screen recent events for OFAC sanctions matches

**Schedule**: Daily

**Entry Point**: `sync_sanctions`

**Request Body**:
```json
{
  "lookback_days": 7
}
```

**Response**:
```json
{
  "screened": 150,
  "matches_found": 8,
  "errors": 2,
  "lookback_days": 7,
  "status": "success"
}
```

**Logic**:
- Queries BigQuery for recent events with LLM analysis
- Calls Django backend sanctions screening endpoint for each event
- Django SanctionsScreener matches entities against OFAC SDN list
- Stores matches in PostgreSQL (SanctionsMatch model)

**Note**: This function is a lightweight orchestrator. The actual OFAC SDN list matching logic remains in the Django backend (`data_pipeline.services.sanctions_screener.SanctionsScreener`).

---

## Shared Utilities (`shared/`)

### `bigquery_client.py`

**Purpose**: Reusable BigQuery client with ADC auth

**Methods**:
- `insert_events()`: Insert to events table
- `insert_fred_indicators()`: Insert to fred_indicators table
- `insert_un_comtrade()`: Insert to un_comtrade table
- `insert_world_bank()`: Insert to world_bank table
- `check_duplicate_event()`: Check if event ID exists
- `check_duplicate_by_url()`: Check if URL exists (with lookback window)
- `get_previous_fred_value()`: Get previous FRED value for change calculation

### `secrets.py`

**Purpose**: GCP Secret Manager integration

**Methods**:
- `get_secret(secret_id)`: Get secret from Secret Manager or env var
  - Falls back to environment variables if Secret Manager unavailable
  - In-memory caching to reduce API calls
  - Converts `api-fred-key` -> `API_FRED_KEY` for env vars

### `pubsub_client.py`

**Purpose**: Pub/Sub client for event analysis

**Methods**:
- `publish_event_for_analysis(event_id, model)`: Publish single event
- `publish_events_for_analysis(event_ids, model)`: Publish batch

**Topic**: `event-analysis` (consumed by LLM analysis Cloud Function)

**Message Format**:
```json
{
  "event_id": "uuid-string",
  "model": "fast" | "standard"
}
```

---

## Environment Variables

All functions require:

```bash
GCP_PROJECT_ID=venezuelawatch-project
BIGQUERY_DATASET=venezuelawatch
```

Sanctions function additionally requires:

```bash
DJANGO_BACKEND_URL=https://api.venezuelawatch.com
```

---

## Deployment

Deploy each function using `gcloud functions deploy`:

```bash
# GDELT Sync (every 15 minutes)
gcloud functions deploy gdelt-sync \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=./gdelt_sync \
  --entry-point=sync_gdelt_events \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=venezuelawatch-project,BIGQUERY_DATASET=venezuelawatch

# ReliefWeb (daily)
gcloud functions deploy reliefweb \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=./reliefweb \
  --entry-point=sync_reliefweb \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=venezuelawatch-project,BIGQUERY_DATASET=venezuelawatch

# FRED (daily)
gcloud functions deploy fred \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=./fred \
  --entry-point=sync_fred \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=venezuelawatch-project,BIGQUERY_DATASET=venezuelawatch

# Comtrade (monthly)
gcloud functions deploy comtrade \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=./comtrade \
  --entry-point=sync_comtrade \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=venezuelawatch-project,BIGQUERY_DATASET=venezuelawatch

# World Bank (monthly)
gcloud functions deploy worldbank \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=./worldbank \
  --entry-point=sync_worldbank \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=venezuelawatch-project,BIGQUERY_DATASET=venezuelawatch

# Sanctions (daily)
gcloud functions deploy sanctions \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=./sanctions \
  --entry-point=sync_sanctions \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=venezuelawatch-project,BIGQUERY_DATASET=venezuelawatch,DJANGO_BACKEND_URL=https://api.venezuelawatch.com
```

---

## Orchestration

### Cloud Scheduler Jobs

```yaml
# GDELT: Every 15 minutes
gdelt-sync-schedule:
  schedule: "*/15 * * * *"
  target: https://us-central1-venezuelawatch-project.cloudfunctions.net/gdelt-sync
  body: '{"lookback_minutes": 15}'

# ReliefWeb: Daily at 6 AM UTC
reliefweb-schedule:
  schedule: "0 6 * * *"
  target: https://us-central1-venezuelawatch-project.cloudfunctions.net/reliefweb
  body: '{"lookback_days": 1}'

# FRED: Daily at 10 AM UTC (after US market data release)
fred-schedule:
  schedule: "0 10 * * *"
  target: https://us-central1-venezuelawatch-project.cloudfunctions.net/fred
  body: '{"lookback_days": 7}'

# Comtrade: 1st of each month at 2 AM UTC
comtrade-schedule:
  schedule: "0 2 1 * *"
  target: https://us-central1-venezuelawatch-project.cloudfunctions.net/comtrade
  body: '{"lookback_months": 3}'

# World Bank: 1st of each month at 3 AM UTC
worldbank-schedule:
  schedule: "0 3 1 * *"
  target: https://us-central1-venezuelawatch-project.cloudfunctions.net/worldbank
  body: '{"lookback_years": 2}'

# Sanctions: Daily at 8 AM UTC (after LLM analysis completes)
sanctions-schedule:
  schedule: "0 8 * * *"
  target: https://us-central1-venezuelawatch-project.cloudfunctions.net/sanctions
  body: '{"lookback_days": 7}'
```

---

## Monitoring

### Cloud Logging Queries

```sql
-- View GDELT sync logs
resource.type="cloud_function"
resource.labels.function_name="gdelt-sync"
severity>=INFO

-- View all ingestion errors
resource.type="cloud_function"
severity>=ERROR
jsonPayload.message=~"ingestion failed"

-- View threshold alerts created
resource.type="cloud_function"
jsonPayload.message=~"Threshold alert created"
```

### Metrics to Monitor

- **Event creation rate**: `events_created` per function
- **Duplicate rate**: `events_skipped / events_fetched`
- **Function duration**: Cloud Functions execution time
- **API failures**: HTTP 5xx responses from external APIs
- **BigQuery insert errors**: Streaming insert failures

---

## Differences from Original Tasks

### Key Changes

1. **No Django**: Pure Python with GCP client libraries only
2. **No Celery**: HTTP triggers via Cloud Scheduler
3. **No PostgreSQL writes**: Direct BigQuery inserts only
4. **Pub/Sub for async**: Replaces Celery task dispatch
5. **ADC auth**: No API key management in code
6. **Standalone functions**: Each function is independently deployable

### Data Flow

**Before (Celery)**:
```
Cloud Scheduler -> Celery Beat -> Celery Worker -> Django ORM -> PostgreSQL
                                                 -> BigQuery
                                                 -> Celery (LLM task)
```

**After (Cloud Functions)**:
```
Cloud Scheduler -> Cloud Function -> BigQuery
                                  -> Pub/Sub -> LLM Cloud Function
```

### Logic Preservation

All core ingestion logic is preserved:
- GDELT: GLOBALEVENTID deduplication, QuadClass mapping
- ReliefWeb: 30-day URL deduplication
- FRED: Threshold breach detection, economic alerts
- Comtrade: $10M minimum value filter, 2-3 month lag handling
- World Bank: Annual indicator fetching
- Sanctions: Django endpoint orchestration

---

## Testing

### Local Testing

```bash
# Install Functions Framework
pip install functions-framework

# Test GDELT function locally
cd functions/gdelt_sync
export GCP_PROJECT_ID=venezuelawatch-project
export BIGQUERY_DATASET=venezuelawatch
functions-framework --target=sync_gdelt_events --debug

# Send test request
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{"lookback_minutes": 15}'
```

### Integration Testing

```bash
# Deploy to test environment
gcloud functions deploy gdelt-sync-test \
  --runtime=python311 \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=test-project,BIGQUERY_DATASET=test_dataset

# Invoke manually
gcloud functions call gdelt-sync-test \
  --data '{"lookback_minutes": 15}'
```

---

## Troubleshooting

### Common Issues

**1. "GCP_PROJECT_ID environment variable not set"**
- Add `--set-env-vars GCP_PROJECT_ID=your-project` to deployment

**2. "Failed to retrieve secret from Secret Manager"**
- Ensure secret exists: `gcloud secrets list`
- Grant Cloud Function service account access:
  ```bash
  gcloud secrets add-iam-policy-binding api-fred-key \
    --member=serviceAccount:PROJECT_ID@appspot.gserviceaccount.com \
    --role=roles/secretmanager.secretAccessor
  ```

**3. "BigQuery insert errors"**
- Check schema matches: `bq show --schema --format=prettyjson venezuelawatch.events`
- Verify service account has BigQuery Data Editor role

**4. "Pub/Sub publish failed"**
- Ensure `event-analysis` topic exists
- Grant Pub/Sub Publisher role to Cloud Function service account

---

## Next Steps

After deploying Cloud Functions:

1. **Create Cloud Scheduler jobs** with schedules above
2. **Set up monitoring alerts** for function failures
3. **Provision secrets** in Secret Manager:
   - `api-fred-key`: FRED API key
   - `api-comtrade-key`: Comtrade API key (optional)
4. **Create Pub/Sub topic**: `event-analysis`
5. **Deploy LLM analysis function** to consume Pub/Sub messages
6. **Test end-to-end flow**:
   - Trigger GDELT sync manually
   - Verify events in BigQuery
   - Confirm Pub/Sub messages published
   - Check LLM analysis completes

---

## Plan 18-01 Completion

This implements **Phase 18-01: Replace Celery ingestion with Cloud Functions**.

**Files Created**:
- `shared/bigquery_client.py`: Reusable BigQuery client
- `shared/secrets.py`: Secret Manager integration
- `shared/pubsub_client.py`: Pub/Sub client
- `gdelt_sync/main.py`: GDELT ingestion function
- `reliefweb/main.py`: ReliefWeb ingestion function
- `fred/main.py`: FRED economic indicators function
- `comtrade/main.py`: UN Comtrade trade data function
- `worldbank/main.py`: World Bank indicators function
- `sanctions/main.py`: Sanctions screening orchestrator
- 6x `requirements.txt`: Dependencies for each function

**Next Phase**: 18-02 - Deploy and test Cloud Functions in GCP
