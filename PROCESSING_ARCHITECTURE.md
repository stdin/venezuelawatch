# Processing Architecture (Phase 18 - GCP-Native Pipeline)

## Overview

VenezuelaWatch uses a fully event-driven, GCP-native processing architecture for data ingestion, intelligence analysis, and entity extraction.

**Migration Status:** Phase 18-02 complete - Celery tasks replaced by Cloud Run + Pub/Sub + Cloud Tasks

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      INGESTION LAYER                             │
│  Cloud Scheduler → Cloud Functions → BigQuery (events table)    │
│                                                                  │
│  Functions:                                                      │
│  - gdelt_sync (every 15 min)                                    │
│  - reliefweb (daily)                                            │
│  - fred (daily)                                                 │
│  - comtrade (monthly)                                           │
│  - worldbank (quarterly)                                        │
│  - sanctions (daily)                                            │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ↓ Publishes to Pub/Sub (event-analysis topic)
┌─────────────────────────────────────────────────────────────────┐
│                    PROCESSING LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Pub/Sub Topic: event-analysis                                  │
│  ├─ Push Subscription: event-analysis-sub                      │
│  │   └─ Endpoint: /api/internal/process-event (Cloud Run)      │
│  │       └─ Enqueues: Cloud Tasks (intelligence-analysis queue)│
│  │                                                               │
│  Cloud Tasks Queue: intelligence-analysis                        │
│  ├─ Handler: /api/internal/analyze-intelligence (Cloud Run)    │
│  │   ├─ Fetches event from BigQuery                            │
│  │   ├─ Runs LLM intelligence analysis (Claude API)            │
│  │   ├─ Updates event in BigQuery (sentiment, risk, entities)  │
│  │   └─ Publishes to Pub/Sub (entity-extraction topic)         │
│  │                                                               │
│  Pub/Sub Topic: entity-extraction                               │
│  ├─ Push Subscription: entity-extraction-sub                   │
│  │   └─ Endpoint: /api/internal/extract-entities (Cloud Run)   │
│  │       ├─ Creates/matches Entity records (PostgreSQL)         │
│  │       ├─ Creates EntityMention links                         │
│  │       └─ Updates trending scores (Redis)                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Ingestion Functions (Cloud Functions Gen2)

**Location:** `functions/{source}/main.py`

Each ingestion function:
1. Fetches data from external API (GDELT, ReliefWeb, FRED, etc.)
2. Maps to BigQuery event schema
3. Inserts events to BigQuery (`venezuelawatch_analytics.events` table)
4. **Publishes event IDs to Pub/Sub** via `pubsub_client.publish_events_for_analysis()`

**Key files:**
- `functions/shared/pubsub_client.py` - Pub/Sub publishing utility
- `functions/shared/bigquery_client.py` - BigQuery insertion utility

### 2. Internal API Handlers (Django + Cloud Run)

**Location:** `backend/api/views/internal.py`

Three HTTP endpoints for GCP service-to-service communication:

#### `/api/internal/process-event` (POST)
- **Triggered by:** Pub/Sub push subscription (`event-analysis-sub`)
- **Input:** Pub/Sub message with `{"event_id": "abc-123", "model": "fast"}`
- **Action:** Enqueues Cloud Tasks for LLM analysis
- **Output:** 200 OK with task name

#### `/api/internal/analyze-intelligence` (POST)
- **Triggered by:** Cloud Tasks (`intelligence-analysis` queue)
- **Input:** `{"event_id": "abc-123", "model": "fast"}`
- **Action:**
  1. Fetch event from BigQuery
  2. Run LLM intelligence analysis (reuses `LLMIntelligence.analyze_event_model()`)
  3. Update event in BigQuery with sentiment, risk, entities, summary, etc.
  4. Publish to `entity-extraction` Pub/Sub topic
- **Output:** 200 OK with analysis results

#### `/api/internal/extract-entities` (POST)
- **Triggered by:** Pub/Sub push subscription (`entity-extraction-sub`)
- **Input:** Pub/Sub message with `{"event_id": "abc-123"}`
- **Action:**
  1. Fetch event from BigQuery
  2. Extract entities from LLM analysis
  3. Find/create Entity records (reuses `EntityService.find_or_create_entity()`)
  4. Create EntityMention links
  5. Update trending scores in Redis (reuses `TrendingService.update_entity_score()`)
- **Output:** 200 OK with extraction statistics

### 3. GCP Infrastructure

**Pub/Sub Topics:**
- `event-analysis` - Event IDs for intelligence analysis
- `entity-extraction` - Event IDs for entity extraction

**Pub/Sub Subscriptions (Push):**
- `event-analysis-sub` → `/api/internal/process-event`
- `entity-extraction-sub` → `/api/internal/extract-entities`

**Cloud Tasks Queues:**
- `intelligence-analysis` - LLM analysis tasks (10 concurrent, 5 dispatches/sec)
- `entity-extraction` - Entity extraction tasks (20 concurrent, 10 dispatches/sec)

**Configuration script:** `scripts/setup_processing_infrastructure.sh`

### 4. Authentication

**OIDC tokens for service-to-service communication:**
- Pub/Sub → Cloud Run: `pubsub-invoker@venezuelawatch-447923.iam.gserviceaccount.com`
- Cloud Tasks → Cloud Run: `cloudrun-tasks@venezuelawatch-447923.iam.gserviceaccount.com`

**No API keys or authentication headers** - uses Google's OIDC token verification.

## Code Reuse

**100% of business logic reused from existing services:**

- `data_pipeline/services/llm_intelligence.py` - LLM analysis (unchanged)
- `data_pipeline/services/entity_service.py` - Entity extraction (unchanged)
- `data_pipeline/services/trending_service.py` - Trending scores (unchanged)
- `api/services/bigquery_service.py` - BigQuery operations (unchanged)

**Only orchestration changed:**
- **Old:** Celery Beat → Celery workers → PostgreSQL
- **New:** Cloud Scheduler → Cloud Functions → BigQuery → Pub/Sub → Cloud Run handlers

## Deprecated Components

### Celery Tasks (Marked for removal in Phase 18-03)

**Files:**
- `backend/data_pipeline/tasks/intelligence_tasks.py` - Replaced by `/api/internal/analyze-intelligence`
- `backend/data_pipeline/tasks/entity_extraction.py` - Replaced by `/api/internal/extract-entities`

**Status:** DEPRECATED with migration notes in docstrings. Will be removed after cutover validation.

## Deployment

### Prerequisites

1. Cloud Run service deployed with Django API
2. Pub/Sub topics and subscriptions created (run `scripts/setup_processing_infrastructure.sh`)
3. Cloud Tasks queues created
4. IAM permissions granted

### Environment Variables (Cloud Run)

```bash
GCP_PROJECT_ID=venezuelawatch-447923
GCP_LOCATION=us-central1
BIGQUERY_DATASET=venezuelawatch_analytics
REDIS_URL=redis://[memorystore-ip]:6379/0
ANTHROPIC_API_KEY=[from Secret Manager]
```

### Monitoring

**Cloud Logging queries:**

```
# Pub/Sub message processing
resource.type="cloud_run_revision"
jsonPayload.message=~"Received event analysis trigger"

# LLM analysis results
resource.type="cloud_run_revision"
jsonPayload.message=~"Event .* intelligence updated"

# Entity extraction results
resource.type="cloud_run_revision"
jsonPayload.message=~"Entity extraction complete"
```

**Cloud Monitoring alerts:**
- Internal endpoint error rate > 5%
- Cloud Tasks queue depth > 100 tasks
- Pub/Sub subscription backlog > 500 messages

## Testing

### Local Testing (requires Django runserver)

```bash
# Start Django dev server
python manage.py runserver

# Simulate Pub/Sub message
curl -X POST http://localhost:8000/api/internal/process-event \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "data": "'$(echo -n '{"event_id": "test-123"}' | base64)'",
      "messageId": "test-msg-123",
      "publishTime": "2026-01-10T00:00:00Z"
    }
  }'
```

### Production Testing

```bash
# Publish test event to Pub/Sub
gcloud pubsub topics publish event-analysis \
  --message '{"event_id": "abc-123"}' \
  --project venezuelawatch-447923

# Check Cloud Tasks queue
gcloud tasks list --queue intelligence-analysis --location us-central1

# Check Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

## Migration Timeline

- **Phase 18-01:** Ingestion layer migrated to Cloud Functions (COMPLETE)
- **Phase 18-02:** Processing layer migrated to Cloud Run + Pub/Sub + Cloud Tasks (COMPLETE)
- **Phase 18-03:** Celery cutover and cleanup (NEXT)

## Performance Characteristics

**Latency:**
- Ingestion → Pub/Sub: <100ms
- Pub/Sub → Cloud Run: <1s (includes cold start)
- LLM analysis: 10-30s (same as Celery)
- Entity extraction: 5-15s (same as Celery)
- **Total pipeline:** 15-50s (same as Celery, but with auto-scaling)

**Throughput:**
- Intelligence analysis: 5 tasks/second (Cloud Tasks rate limit)
- Entity extraction: 10 tasks/second (Cloud Tasks rate limit)
- **Scale:** Auto-scales to 100+ concurrent Cloud Run instances

**Cost:**
- Pub/Sub: Free (within quotas)
- Cloud Tasks: $0.12/month (300K tasks)
- Cloud Run: $15-30/month (pay-per-use)
- **Total:** ~$50/month (vs $175/month with Celery workers)

## Future Enhancements

- [ ] Add Cloud Workflows for multi-step orchestrations
- [ ] Integrate Vertex AI for ML-based analysis
- [ ] Add Cloud Trace for distributed tracing
- [ ] Configure dead-letter queues for failed tasks
- [ ] Add Cloud Armor for DDoS protection on public endpoints

---

**Last updated:** 2026-01-10 (Phase 18-02)
