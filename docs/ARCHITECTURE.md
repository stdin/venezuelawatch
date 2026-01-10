# VenezuelaWatch Architecture

**Last Updated:** Phase 18-03 (January 2026)
**Status:** GCP-Native Architecture (Celery Migration Complete)

## Overview

VenezuelaWatch is a geopolitical intelligence platform built on Google Cloud Platform (GCP) using a microservices-based, event-driven architecture. The platform ingests data from multiple external sources, performs AI-powered analysis, and provides real-time insights through interactive dashboards.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         External Data Sources                            │
├─────────────────────────────────────────────────────────────────────────┤
│  GDELT    │  ReliefWeb  │  FRED  │  UN Comtrade  │  World Bank  │ OFAC │
└─────┬───────────┬───────────┬────────────┬──────────────┬─────────┬─────┘
      │           │           │            │              │         │
      ▼           ▼           ▼            ▼              ▼         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Cloud Scheduler (Periodic Tasks)                  │
├─────────────────────────────────────────────────────────────────────────┤
│ • gdelt-sync (15 min)           • comtrade-sync (monthly)               │
│ • reliefweb-updates (daily)     • worldbank-sync (quarterly)            │
│ • fred-series-sync (daily)      • sanctions-screening (daily 4 AM UTC)  │
└─────┬───────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Cloud Functions (Data Ingestion)                  │
├─────────────────────────────────────────────────────────────────────────┤
│ • gdelt_sync_trigger      • comtrade_sync_trigger                       │
│ • reliefweb_sync_trigger  • worldbank_sync_trigger                      │
│ • fred_sync_trigger       • sanctions_screening_trigger                 │
└─────┬───────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        BigQuery (Data Warehouse)                         │
├─────────────────────────────────────────────────────────────────────────┤
│ Dataset: venezuelawatch_analytics                                       │
│                                                                          │
│ Tables:                                                                  │
│ • events - News articles, reports, economic indicators                  │
│ • sanctions - OFAC sanctions screening results                          │
│ • entity_mentions - Named entity occurrences                            │
│ • supply_chain_risks - Trade flow analysis                              │
│ • forecasts - Vertex AI model predictions                               │
│                                                                          │
│ Features:                                                                │
│ • Partitioned by mentioned_at (date)                                    │
│ • Clustered by source_name, event_type                                  │
│ • Streaming inserts for real-time data                                  │
│ • 90-day rolling aggregations via scheduled queries                     │
└─────┬───────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Pub/Sub (Event Bus)                               │
├─────────────────────────────────────────────────────────────────────────┤
│ Topics:                                                                  │
│ • event-created - New events from data sources                          │
│ • analyze-intelligence - Trigger LLM analysis                           │
│ • extract-entities - Trigger entity extraction                          │
│ • calculate-risk - Trigger risk scoring                                 │
│                                                                          │
│ Subscriptions:                                                           │
│ • event-created-sub → Cloud Run (intelligence handler)                  │
│ • analyze-intelligence-sub → Cloud Tasks queue                          │
│ • extract-entities-sub → Cloud Run (entity handler)                     │
└─────┬───────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Cloud Run (Application Services)                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ ┌─────────────────────────────────────────────────────────────────┐    │
│ │ venezuelawatch-api (Public API)                                 │    │
│ │ • Django 5.2 + django-ninja                                     │    │
│ │ • REST API for frontend                                         │    │
│ │ • Authentication (django-allauth)                               │    │
│ │ • WebSocket support (Django Channels)                           │    │
│ │ • Port: 8080                                                    │    │
│ └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│ ┌─────────────────────────────────────────────────────────────────┐    │
│ │ Internal API Handlers (Private endpoints)                       │    │
│ │ • /api/internal/analyze-intelligence (Cloud Tasks)              │    │
│ │ • /api/internal/extract-entities (Pub/Sub)                      │    │
│ │ • /api/internal/calculate-risk (Pub/Sub)                        │    │
│ │ • IAM-authenticated only (no public access)                     │    │
│ └─────────────────────────────────────────────────────────────────┘    │
└─────┬───────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Cloud Tasks (Background Jobs)                     │
├─────────────────────────────────────────────────────────────────────────┤
│ Queues:                                                                  │
│ • intelligence-analysis - LLM analysis tasks (rate-limited)             │
│ • entity-extraction - Entity processing                                 │
│ • risk-calculation - Risk scoring                                       │
│                                                                          │
│ Features:                                                                │
│ • Rate limiting (10/sec to respect Claude API limits)                   │
│ • Retry with exponential backoff                                        │
│ • Task deduplication                                                    │
│ • Dead letter queue for failed tasks                                    │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        AI/ML Services                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ ┌─────────────────────────────────────────────────────────────────┐    │
│ │ Claude API (Anthropic)                                          │    │
│ │ • Event intelligence analysis                                   │    │
│ │ • Sentiment scoring                                             │    │
│ │ • Entity extraction                                             │    │
│ │ • Risk assessment                                               │    │
│ │ • Summary generation                                            │    │
│ │ Models: claude-3-haiku (fast), claude-3-sonnet (standard)       │    │
│ └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│ ┌─────────────────────────────────────────────────────────────────┐    │
│ │ Vertex AI                                                       │    │
│ │ • Time series forecasting (AutoML)                              │    │
│ │ • Economic indicator predictions                                │    │
│ │ • Risk trajectory modeling                                      │    │
│ │ • Batch prediction jobs (daily)                                 │    │
│ └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        Storage & Caching                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ ┌─────────────────────────────────────────────────────────────────┐    │
│ │ Cloud SQL (PostgreSQL 15)                                       │    │
│ │ • User accounts and authentication                              │    │
│ │ • Entity normalization (Entity, EntityMention tables)           │    │
│ │ • Entity relationships graph                                    │    │
│ │ • Application metadata                                          │    │
│ └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│ ┌─────────────────────────────────────────────────────────────────┐    │
│ │ Redis (Memorystore)                                             │    │
│ │ • Trending entity scores (sorted sets)                          │    │
│ │ • Real-time leaderboards                                        │    │
│ │ • Django session cache                                          │    │
│ │ • API response cache                                            │    │
│ │ NOTE: Redis no longer used for Celery broker/results            │    │
│ └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│ ┌─────────────────────────────────────────────────────────────────┐    │
│ │ Cloud Storage                                                   │    │
│ │ • Static assets (CSS, JS, images)                               │    │
│ │ • User uploads                                                  │    │
│ │ • Cloud Function source code                                    │    │
│ │ Bucket: venezuelawatch-static                                   │    │
│ └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                           │
├─────────────────────────────────────────────────────────────────────────┤
│ • React 18 with TypeScript                                              │
│ • TanStack Query for data fetching                                      │
│ • Recharts for visualizations                                           │
│ • TailwindCSS for styling                                               │
│ • Deployed to Cloud Run or Firebase Hosting                             │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Periodic Data Ingestion (Cloud Scheduler → Cloud Functions)

```
Cloud Scheduler (cron)
  → Cloud Function (HTTP trigger)
  → External API (GDELT, FRED, etc.)
  → BigQuery (streaming insert)
  → Pub/Sub (event-created topic)
  → Cloud Run (intelligence handler)
  → Cloud Tasks (LLM analysis queue)
  → Claude API (analysis)
  → BigQuery (update event with analysis)
```

**Example: GDELT Sync (every 15 minutes)**

1. Cloud Scheduler triggers `gdelt-sync` job
2. Cloud Function `gdelt_sync_trigger` executes
3. Function queries GDELT DOC API v2.0 for last 15 minutes
4. Function filters Venezuela-related articles
5. Function inserts events to `events` table in BigQuery
6. Function publishes message to `event-created` Pub/Sub topic
7. Pub/Sub triggers Cloud Run internal handler
8. Handler enqueues Cloud Task for LLM analysis
9. Cloud Task invokes `/api/internal/analyze-intelligence`
10. Django app calls Claude API for comprehensive analysis
11. Analysis results update event in BigQuery

### 2. Event-Driven Processing (Pub/Sub → Cloud Run)

```
BigQuery Insert
  → Pub/Sub Notification (event-created)
  → Cloud Run Handler (push subscription)
  → Processing Logic (entity extraction, risk calculation)
  → BigQuery Update
  → Redis Update (trending scores)
```

**Example: Entity Extraction**

1. New event inserted to BigQuery
2. Pub/Sub `event-created` topic receives notification
3. `extract-entities` subscription triggers Cloud Run handler
4. Handler reads event from BigQuery
5. Handler extracts entities from LLM analysis
6. Handler normalizes entities using `EntityService`
7. Handler creates `EntityMention` records in PostgreSQL
8. Handler updates trending scores in Redis sorted sets
9. Frontend polls `/api/entities/trending` endpoint
10. API reads from Redis and returns ranked entities

### 3. Background Task Execution (Cloud Tasks)

```
Cloud Run Handler
  → Cloud Tasks Queue (create task)
  → Rate Limiting (10 tasks/sec)
  → Cloud Run Handler (task execution)
  → External API Call (Claude, Vertex AI)
  → BigQuery Update
```

**Example: Intelligence Analysis (Rate-Limited)**

1. Event created in BigQuery
2. Cloud Run handler enqueues task to `intelligence-analysis` queue
3. Cloud Tasks enforces rate limit (10/sec for Claude API)
4. Task invokes `/api/internal/analyze-intelligence` with event ID
5. Django app reads event from BigQuery
6. Django app calls Claude API (with retries)
7. Claude returns comprehensive analysis JSON
8. Django app updates event in BigQuery with:
   - `sentiment` (score -1 to +1)
   - `risk_score` (0-100)
   - `entities` (array of names)
   - `summary` (concise text)
   - `llm_analysis` (full JSON)
   - `themes`, `urgency`, `language`
8. BigQuery event now enriched and queryable

## Key Architectural Decisions

### Phase 18: Celery → GCP Migration

**Problem:** Celery + Redis introduced operational complexity:
- Redis instance required for broker and results
- Celery Beat for scheduling (single point of failure)
- Celery workers for execution (scaling challenges)
- Limited observability and debugging

**Solution:** Migrated to GCP-native services:

| Celery Component | GCP Replacement | Benefits |
|------------------|-----------------|----------|
| Celery Beat (scheduler) | Cloud Scheduler | Managed cron, no maintenance, HA by default |
| Celery Worker (execution) | Cloud Functions + Cloud Run | Auto-scaling, pay-per-use, no cold start issues |
| Redis (broker) | Pub/Sub | Unlimited throughput, at-least-once delivery |
| Redis (results) | BigQuery metadata | Queryable results, historical analysis |
| Celery Tasks (async) | Cloud Tasks | Rate limiting, retries, task deduplication |

**Redis Retention:** Redis (Memorystore) is retained for:
- Trending entity scores (sorted sets with time decay)
- Django session storage
- API response caching
- Real-time leaderboards

Redis is NO LONGER used for:
- Celery broker
- Celery results backend
- Task queue management

### BigQuery as Primary Data Store

**Rationale:**
- Native GDELT integration (public dataset)
- Columnar storage optimized for analytics
- Serverless, auto-scaling, no cluster management
- Cost-effective for append-heavy workloads
- SQL interface familiar to analysts
- Streaming inserts for real-time data

**PostgreSQL Role:**
- User authentication (django-allauth)
- Entity normalization (fuzzy matching)
- Entity relationships (graph queries)
- Application metadata
- OLTP workloads (reads/writes)

**Design Pattern:** PostgreSQL for OLTP, BigQuery for OLAP

### Event-Driven Architecture

**Pub/Sub Topics:**

1. **event-created**
   - Published: After new event inserted to BigQuery
   - Subscribers: Intelligence handler, entity handler

2. **analyze-intelligence**
   - Published: When event needs LLM analysis
   - Subscribers: Cloud Tasks (rate-limited queue)

3. **extract-entities**
   - Published: When event has entities to extract
   - Subscribers: Entity extraction handler

**Benefits:**
- Loose coupling between services
- Easy to add new subscribers
- Automatic retries and dead-letter queues
- Horizontal scalability

### Cloud Run for Django

**Why Cloud Run vs. App Engine or GKE:**

| Feature | Cloud Run | App Engine | GKE |
|---------|-----------|------------|-----|
| Containerization | Docker | Runtime-specific | Kubernetes |
| Auto-scaling | 0-1000 instances | 0-N instances | Manual/HPA |
| Cold start | ~1-2s | ~5-10s | No cold start |
| Cost | Pay per request | Pay per instance-hour | Pay per node |
| Complexity | Low | Low | High |
| WebSocket support | Yes (via Cloud CDN) | Limited | Full |

**Trade-offs:**
- Cloud Run has request timeout (60 min max)
- Long-running tasks use Cloud Tasks (detached from HTTP)
- WebSockets require Cloud CDN or direct connection

## Service Communication

### Authentication

- **Public API:** JWT tokens (django-allauth + simplejwt)
- **Internal APIs:** IAM authentication (service accounts)
- **Cloud Functions:** IAM or API Gateway (planned)

### Service Accounts

- `venezuelawatch-api@PROJECT.iam` - Cloud Run service
  - Permissions: BigQuery Data Editor, Pub/Sub Publisher, Cloud Tasks Enqueuer
- `cloud-scheduler@PROJECT.iam` - Cloud Scheduler
  - Permissions: Cloud Functions Invoker
- `cloud-run-invoker@PROJECT.iam` - Pub/Sub push subscriptions
  - Permissions: Cloud Run Invoker

### Network

- **VPC:** All services in same VPC (us-central1)
- **Cloud SQL:** Private IP only
- **Redis:** Private IP via VPC peering
- **Cloud Run:** Regional load balancer with Cloud CDN
- **Cloud Functions:** VPC connector for private resources

## Monitoring & Observability

### Cloud Logging

- **Cloud Run logs:** Structured JSON with trace IDs
- **Cloud Functions logs:** Automatic logging integration
- **BigQuery audit logs:** Query performance, costs
- **Pub/Sub logs:** Message delivery, dead letters

### Cloud Monitoring

- **Dashboards:**
  - API latency and error rates
  - BigQuery streaming insert lag
  - Pub/Sub message age and backlog
  - Cloud Tasks queue depth
  - Claude API rate limit usage

- **Alerts:**
  - Cloud Run error rate > 5%
  - Pub/Sub message age > 5 minutes
  - BigQuery streaming insert failures
  - Cloud Tasks dead letter queue not empty
  - Redis memory usage > 80%

### Cloud Trace

- Distributed tracing across Cloud Run, Cloud Functions, BigQuery
- Integration with Django middleware
- Trace IDs propagated via HTTP headers

## Cost Optimization

### BigQuery

- **Partitioning:** By `mentioned_at` (date) - prunes 90% of scans
- **Clustering:** By `source_name`, `event_type` - reduces slot usage
- **Scheduled queries:** Pre-aggregate 90-day windows (cheaper than on-demand)
- **Streaming inserts:** Free tier covers most usage (<200k rows/day)

### Cloud Run

- **Min instances:** 0 (scale to zero when idle)
- **Max instances:** 100 (prevent runaway costs)
- **CPU allocation:** CPU only during request (cheaper than always-on)
- **Memory:** 512 MB for API (enough for Django)

### Cloud Functions

- **Memory:** 256 MB (minimum for ingestion tasks)
- **Timeout:** 60s (fail fast on API errors)
- **Cold starts:** Accept 1-2s latency for cost savings

### Redis

- **Tier:** Basic (no HA) - trending data can tolerate downtime
- **Memory:** 1 GB (sufficient for entity trending)
- **Downscale option:** Can remove Redis entirely if trending moved to BigQuery

### Pub/Sub

- **Message retention:** 7 days (default)
- **Acknowledge deadline:** 10 seconds (fast processing)
- **Seek:** Disabled (save storage costs)

## Security

### IAM Policies

- **Principle of least privilege:** Each service account has minimal permissions
- **No service account keys:** Use Workload Identity for auth
- **Public API:** JWT-based auth, no API keys

### Secrets Management

- **Secret Manager:** API keys (FRED, Anthropic, etc.)
- **Environment variables:** Non-sensitive config only
- **No secrets in code:** All credentials from Secret Manager

### Data Protection

- **BigQuery:** Column-level security (future: mask PII)
- **Cloud SQL:** Encrypted at rest and in transit
- **Cloud Storage:** Public read (static assets), private write

### Network Security

- **Cloud Run:** HTTPS only, Cloud CDN for DDoS protection
- **Cloud Functions:** VPC Service Controls (future)
- **Cloud SQL:** Private IP, no public access

## Deployment

### CI/CD Pipeline

```
GitHub Push (main branch)
  → GitHub Actions
  → Build Docker Image
  → Push to Artifact Registry
  → Deploy to Cloud Run (staging)
  → Run Integration Tests
  → Manual Approval
  → Deploy to Cloud Run (production)
```

### Environments

- **Development:** Local Docker Compose
- **Staging:** Cloud Run (us-central1)
- **Production:** Cloud Run (us-central1) + Cloud CDN

### Rollback

- **Cloud Run:** Instant rollback to previous revision
- **BigQuery:** Time travel (7-day query history)
- **Cloud Functions:** Redeploy previous version

## Future Enhancements

### Short-term (Phase 19-20)

- [ ] Cloud Armor for WAF and DDoS protection
- [ ] Cloud CDN for static assets (reduce egress costs)
- [ ] Cloud Monitoring SLOs and error budgets
- [ ] Vertex AI pipelines for model training
- [ ] BigQuery ML for risk prediction

### Medium-term (Phase 21-25)

- [ ] Multi-region BigQuery (EU for GDPR compliance)
- [ ] Cloud Spanner for global entity graph
- [ ] Cloud Run multi-region (HA for API)
- [ ] Dataflow for real-time aggregations
- [ ] Cloud Composer for orchestration

### Long-term (Phase 26+)

- [ ] Kubernetes (GKE Autopilot) for advanced workloads
- [ ] Service mesh (Anthos) for fine-grained traffic control
- [ ] Cloud Bigtable for high-throughput trending
- [ ] AlloyDB for PostgreSQL workloads (if needed)
- [ ] Multi-cloud (AWS fallback for Claude API)

## References

- [GCP Architecture Framework](https://cloud.google.com/architecture/framework)
- [Event-Driven Architecture on GCP](https://cloud.google.com/eventarc/docs/event-driven-architectures)
- [BigQuery Best Practices](https://cloud.google.com/bigquery/docs/best-practices)
- [Cloud Run Production Guide](https://cloud.google.com/run/docs/production)
- [Django on Cloud Run](https://cloud.google.com/python/django/run)

---

**Document Version:** 1.0
**Last Reviewed:** Phase 18-03
**Next Review:** Phase 20 (Post-GCP Cutover Validation)
