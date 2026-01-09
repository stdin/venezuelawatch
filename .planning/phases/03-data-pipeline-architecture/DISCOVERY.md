# Phase 3 Discovery: Data Pipeline Architecture

## Research Summary

Investigated 7 external data sources and Django task queue architectures for real-time and batch data ingestion into VenezuelaWatch. Research focused on API characteristics, rate limits, ingestion patterns, and integration strategies for mixed-latency data (real-time news to quarterly economic indicators).

## API Characteristics

### 1. GDELT (Global Database of Events, Language, and Tone)

**Purpose**: Real-time global news/events monitoring
**Data Coverage**: 100+ languages, rolling 3-month window (DOC API), full archive via BigQuery

**Authentication**:
- DOC API: No authentication required (public)
- BigQuery: GCP credentials required

**Rate Limits**:
- DOC API: Rate-limited to protect ElasticSearch backend (specific limits not publicly disclosed)
- BigQuery: 1 TiB query processing per month (free tier), new projects default to 200 TiB daily limit (Sept 2025)
- DOC API: Max 250 results per query

**Update Frequency**: Real-time (15-minute lag typical)

**Data Format**: JSON (DOC API), structured tables (BigQuery)

**Python Libraries**:
- `gdeltPyR` (v0.1.10): Full GDELT 1.0/2.0 support, pandas integration
- `gdelt-doc-api`: Simplified DOC API wrapper
- Direct BigQuery access via `google-cloud-bigquery`

**Cost**: Free (DOC API), free tier for BigQuery queries

**Recommendation**: Use DOC API for recent data (3 months), BigQuery for historical analysis

---

### 2. FRED (Federal Reserve Economic Data)

**Purpose**: US economic indicators (inflation, GDP, employment, interest rates)
**Data Coverage**: 816,000+ time series from 109 sources

**Authentication**: API key (free registration required)

**Rate Limits**: Not publicly specified, described as "reasonable for most applications"

**Update Frequency**: Varies by series (daily/weekly/monthly/quarterly)

**Data Format**: JSON, XML

**Python Libraries**:
- `fredapi` (v0.5.2): Most popular, pandas integration, ALFRED support for data revisions
- `pyfredapi` (v0.7.1): Full FRED endpoint coverage, modern API
- `fedfred` (v0.1.5): Async support, rate limiting, caching, typed models

**Cost**: Free

**Recommendation**: Use `fredapi` for simplicity or `fedfred` for async/caching

---

### 3. UN Comtrade (International Trade Statistics)

**Purpose**: Global trade data by commodity, country, partner
**Data Coverage**: Monthly trade flows, 200+ countries, HS/SITC classification

**Authentication**:
- Free: No token required (500 records/call limit)
- Registered: API subscription key via email domain (500 calls/day, 100,000 records/call)

**Rate Limits**:
- Free: Unlimited calls/day, 500 records/call, 1 request/second
- Registered: 500 calls/day, 100,000 records/call, 100 requests/hour (legacy API)

**Update Frequency**: Monthly (2-6 month lag typical)

**Data Format**: JSON, CSV

**Python Libraries**:
- `comtradeapicall` (official): Python wrapper for UN Comtrade APIs
- GitHub: https://github.com/uncomtrade/comtradeapicall

**Cost**: Free (registered tier requires institutional email)

**Recommendation**: Register for higher limits, batch monthly queries

---

### 4. World Bank (Development Indicators)

**Purpose**: Development indicators (poverty, health, education, infrastructure)
**Data Coverage**: 1,600+ indicators, 200+ countries, 1960-present

**Authentication**: None required (public API)

**Rate Limits**: No strict limits, library auto-chunks large requests

**Update Frequency**: Quarterly/annual (varies by indicator)

**Data Format**: JSON, XML

**Python Libraries**:
- `wbgapi` (v1.0.14): Official library, extensive pandas support, queries databases individually
- `world-bank-data` (v0.1.3): Alternative wrapper

**Cost**: Free

**Recommendation**: Use `wbgapi` (official, modern, auto-handles pagination)

---

### 5. ReliefWeb (Humanitarian News/Reports)

**Purpose**: Humanitarian crises, disasters, reports from UN OCHA
**Data Coverage**: 800,000+ reports, real-time humanitarian updates

**Authentication**: Pre-approved appname required (form request, 1-day approval, effective Nov 1, 2025)

**Rate Limits**:
- Max 1,000 entries per API call
- Max 1,000 calls per day

**Update Frequency**: Continuous/daily (curated content)

**Data Format**: JSON (GET/POST supported)

**Python Libraries**:
- No official library
- Reference implementation: https://github.com/OCHA-DAP/dap-scrapers/blob/master/reliefweb-api.py
- Use `requests` library directly

**Cost**: Free

**Recommendation**: Custom wrapper using `requests`, implement retry logic

---

### 6. USITC (US International Trade Commission)

**Purpose**: US tariff data, trade statistics, injury investigations
**Data Coverage**: HTS codes, tariff rates, trade flows

**Authentication**: DataWeb account required (multifactor via Login.gov)

**Rate Limits**: Not publicly documented (account-restricted API)

**Update Frequency**: Irregular (tariff changes, investigation schedules)

**Data Format**: CSV, JSON (API documentation requires account access)

**Python Libraries**: None (custom integration required)

**Cost**: Free (account required)

**Recommendation**: DataWeb 5.0 launched Jan 16, 2025 with API improvements. Requires account for API docs.

**Note**: Most queries can be performed without login via web interface, but API access requires authentication. Lower priority due to account complexity.

---

### 7. Port Authorities (Shipping/Logistics)

**Purpose**: Vessel tracking, port calls, shipping data
**Data Coverage**: Global AIS data, port-specific APIs

**Authentication**: Varies by provider

**Commercial APIs**:
- **MarineTraffic**: Established AIS provider, tiered pricing, comprehensive coverage
- **VesselFinder**: Alternative AIS provider, API available
- **FleetMon**: Maritime tracking with API access

**Rate Limits**: Varies by pricing tier (commercial)

**Update Frequency**: Real-time AIS (minutes), port call data (daily)

**Data Format**: JSON, XML

**Python Libraries**: Provider-specific SDKs or `requests`

**Cost**: Commercial pricing (hundreds to thousands $/month depending on tier)

**Recommendation**:
- Venezuelan port data has opacity concerns (65% increase in ship-to-ship operations with smuggling risk indicators, April 2025)
- Consider SeaRates or ShipNext for aggregated port data
- Commercial APIs required for real-time vessel tracking
- Lower priority due to cost and data quality concerns

**Venezuela-Specific Context**: Strengthening Russia-Venezuela ties (May 2025 agreements), maritime domain growing more opaque. Use caution with direct port authority integrations.

---

## API Characteristics Summary Table

| API | Auth | Rate Limit | Update Freq | Format | Python Lib | Cost | Priority |
|-----|------|------------|-------------|--------|------------|------|----------|
| GDELT | None (DOC) | ~250 results/query | Real-time (15min) | JSON | gdeltPyR, gdelt-doc-api | Free | High |
| FRED | API key | Reasonable | Daily-Quarterly | JSON/XML | fredapi, fedfred | Free | High |
| UN Comtrade | API key (opt) | 500/day, 100K records | Monthly (2-6mo lag) | JSON/CSV | comtradeapicall | Free | Medium |
| World Bank | None | Auto-chunked | Quarterly-Annual | JSON/XML | wbgapi | Free | Medium |
| ReliefWeb | Appname | 1K/day, 1K entries | Daily | JSON | requests (custom) | Free | High |
| USITC | Account | Undisclosed | Irregular | CSV/JSON | requests (custom) | Free | Low |
| Port APIs | API key | Varies | Real-time-Daily | JSON/XML | Varies | $$$-$$$$ | Low |

---

## Task Queue Architecture

### Django Task Queue Comparison

#### Celery
**Description**: Enterprise-grade distributed task queue, de-facto standard

**Pros**:
- Battle-tested, massive ecosystem, extensive features
- Multiple broker support (Redis, RabbitMQ, SQS)
- Advanced scheduling (cron, intervals, ETAs)
- Task prioritization, routing, rate limiting
- Monitoring tools (Flower, Prometheus exporters)
- Canvas patterns (chains, groups, chords)

**Cons**:
- Complex configuration (broker + result backend)
- Operational overhead (managing workers, brokers)
- Steep learning curve
- Overkill for simple use cases

**Best For**: Large-scale distributed systems, complex workflows, high-volume tasks

**Broker Options**:
- Redis: Simplest, good performance, single point of failure
- RabbitMQ: Most robust, more complex, better for high reliability
- GCP: Not ideal (use Cloud Tasks instead)

---

#### Django-Q2 (Django-Q fork)
**Description**: Django-native task queue with ORM or Redis backend

**Pros**:
- Django integration (uses ORM for queue by default)
- Simple setup, minimal dependencies
- Scheduled tasks, cron support
- Admin interface integration
- Redis optional (can use PostgreSQL as queue)

**Cons**:
- Less mature than Celery
- Limited ecosystem
- ORM backend not ideal for high volume
- No canvas patterns

**Best For**: Small to medium Django apps, projects wanting minimal infrastructure

**Note**: Django-Q2 is the maintained fork (original Django-Q abandoned)

---

#### Huey
**Description**: Lightweight Redis-based task queue

**Pros**:
- Minimal code footprint, easy to learn
- Redis-backed (simple infrastructure)
- Scheduled tasks, cron support
- Automatic retry on failure
- Good balance of features vs complexity

**Cons**:
- Redis required (no broker choice)
- Limited advanced features
- Smaller community than Celery

**Best For**: Medium-sized apps needing background tasks without Celery complexity

---

### GCP Scheduling Options

#### Cloud Tasks
**Purpose**: Explicit task invocation with HTTP targets

**Features**:
- Guaranteed delivery (at-least-once)
- Rate limiting, deduplication
- Scheduled task execution (future ETA)
- Configurable retry policies
- 31-day task retention

**Use Case**: Asynchronous service-to-service calls, scheduled HTTP requests

**Django Integration**: `django-cloud-tasks` library

**Best For**: GCP-native architecture, Cloud Run/Cloud Functions targets

---

#### Cloud Scheduler
**Purpose**: Cron-like job scheduler

**Features**:
- Cron syntax for recurring schedules
- HTTP, Pub/Sub, App Engine targets
- Timezone support
- Automatic retries

**Use Case**: Recurring jobs (hourly reports, daily syncs)

**Best For**: Simple periodic tasks, complements Cloud Tasks

---

#### Pub/Sub
**Purpose**: Event-driven messaging, one-to-many patterns

**Features**:
- Decoupled publisher/subscriber model
- Message ordering, filtering
- Dead letter queues
- Global distribution

**Use Case**: Event-driven architecture, microservices communication

**Best For**: Multi-consumer patterns, service decoupling

---

### Recommendation: Celery + Redis + Cloud Scheduler

**Primary Task Queue**: Celery with Redis
- **Why**: VenezuelaWatch needs mixed latency handling (real-time to monthly), rate limiting, retry logic, and potential for complex workflows (e.g., chained tasks for event enrichment)
- **Redis**: Simplest broker, sufficient for single-instance use case, easy GCP deployment (Memorystore)
- **Workers**: Single worker instance sufficient for Phase 3 (7 data sources), horizontal scaling available later

**Scheduling**: GCP Cloud Scheduler + Celery Beat
- **Cloud Scheduler**: Trigger Celery tasks via HTTP endpoint (no dedicated Celery Beat process needed)
- **Celery Beat**: Alternative if self-hosting preferred, runs as separate process
- **Why Cloud Scheduler**: GCP-native, no additional process, easier ops, better for Cloud Run deployments

**Result Backend**: Django ORM (PostgreSQL)
- Store task results in database for debugging/audit trail
- Alternative: Redis (faster, no persistence)

**Rejected Alternatives**:
- Django-Q2: Too limited for multi-source rate limiting and complex retry logic
- Huey: No broker flexibility, smaller ecosystem
- Pure GCP (Tasks/Scheduler): No local dev parity, vendor lock-in for task logic
- Pure Celery Beat: Requires dedicated process, Cloud Scheduler cleaner for Cloud Run

---

## Ingestion Patterns by Latency

### Real-Time / High-Frequency (GDELT, ReliefWeb)

**Pattern**: Polling with exponential backoff

**Implementation**:
```python
@shared_task(bind=True, max_retries=3)
def ingest_gdelt_events(self):
    try:
        # Query last 15 minutes of data
        last_ingest = get_last_ingest_time('gdelt')
        events = gdelt_client.query(since=last_ingest)

        # Bulk insert with conflict handling
        Event.objects.bulk_create([
            Event(**normalize_event(e)) for e in events
        ], ignore_conflicts=True)

        update_last_ingest_time('gdelt')
    except APIRateLimitError as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

**Schedule**: Every 15-30 minutes (Cloud Scheduler cron)

**Rate Limiting**: Celery task rate limit decorator + tenacity retry

**Error Handling**: Store failed API responses in `FailedIngest` model for manual review

---

### Daily / Weekly (FRED, ReliefWeb)

**Pattern**: Daily batch with incremental updates

**Implementation**:
```python
@shared_task(rate_limit='10/m')  # FRED-friendly rate
def ingest_fred_series(series_id):
    last_date = get_latest_datapoint(series_id)
    data = fred.get_series(series_id, observation_start=last_date)

    # Upsert pattern (update or insert)
    for date, value in data.items():
        EconomicIndicator.objects.update_or_create(
            series_id=series_id,
            date=date,
            defaults={'value': value}
        )
```

**Schedule**: 1-2 AM daily (Cloud Scheduler)

**Optimization**: Parallel task dispatch for multiple series

---

### Monthly / Quarterly (UN Comtrade, World Bank)

**Pattern**: Monthly batch with chunked queries

**Implementation**:
```python
@shared_task
def ingest_comtrade_monthly():
    # Query previous month's data (accounts for lag)
    target_month = (datetime.now() - timedelta(days=60)).strftime('%Y%m')

    # Chunk by country to respect record limits
    countries = ['VE', 'US', 'CO', 'BR']  # Venezuela + partners
    for country in countries:
        ingest_comtrade_country.delay(target_month, country)

@shared_task(rate_limit='100/h')  # Comtrade limit
def ingest_comtrade_country(month, country_code):
    data = comtrade.get_data(
        reporter=country_code,
        period=month,
        max_records=100000
    )
    # Process and store...
```

**Schedule**: 1st of month, 3 AM (Cloud Scheduler)

**Backfill Strategy**: Separate task for historical data load

---

### Irregular / On-Demand (USITC, Port Data)

**Pattern**: Manual trigger + webhook-based updates (future)

**Implementation**:
```python
@shared_task
def ingest_usitc_tariffs():
    # Manual trigger via admin action or API endpoint
    # Lower priority, infrequent updates
    pass
```

**Schedule**: On-demand via Django admin action or API call

**Future**: Webhook listener for USITC notifications (if available)

---

## Error Handling & Retry Strategies

### Retry Library: Tenacity

**Why Tenacity**:
- Declarative retry configuration
- Multiple backoff strategies (exponential, random, jitter)
- Exception-based retry conditions
- Async support (future-proof)
- Better than custom retry logic or urllib3.Retry

**Installation**: `pip install tenacity`

**Example**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
    reraise=True
)
def fetch_api_data(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()
```

---

### Error Classification

**Transient Errors (Retry)**:
- Network timeouts
- HTTP 429 (rate limit)
- HTTP 503 (service unavailable)
- Connection errors

**Permanent Errors (Fail Fast)**:
- HTTP 401/403 (authentication)
- HTTP 404 (not found)
- Invalid API key
- Malformed request (HTTP 400)

---

### Retry Configuration by Source

| Source | Max Retries | Initial Backoff | Max Backoff | Jitter |
|--------|-------------|-----------------|-------------|--------|
| GDELT | 3 | 30s | 300s | Yes |
| FRED | 3 | 60s | 600s | Yes |
| UN Comtrade | 5 | 60s | 3600s | Yes (hourly limit) |
| World Bank | 3 | 30s | 300s | No (auto-chunks) |
| ReliefWeb | 3 | 60s | 600s | Yes |

**Jitter**: Add random 0-10s to prevent thundering herd

---

### Dead Letter Queue

**Pattern**: Store failed ingests for manual investigation

**Model**:
```python
class FailedIngest(models.Model):
    source = models.CharField(max_length=50)
    task_name = models.CharField(max_length=100)
    error_type = models.CharField(max_length=100)
    error_message = models.TextField()
    payload = models.JSONField()  # Original request
    timestamp = models.DateTimeField(auto_now_add=True)
    retry_count = models.IntegerField(default=0)
    resolved = models.BooleanField(default=False)
```

**Use Case**:
- Investigate API changes
- Debug authentication issues
- Manual retry after fixing issues

---

## Rate Limiting Approach

### Two-Layer Rate Limiting

**Layer 1: Celery Task Rate Limits**
```python
# Per-task rate limiting
@shared_task(rate_limit='10/m')  # Max 10 executions per minute
def ingest_fred_series(series_id):
    pass
```

**Layer 2: Tenacity Request Delays**
```python
# Per-request rate limiting within task
@retry(wait=wait_fixed(2))  # 2s between requests
def fetch_comtrade_batch(params):
    return requests.get(COMTRADE_API, params=params)
```

---

### Rate Limit Monitoring

**Celery Events**: Monitor task execution rates via Flower dashboard

**Custom Metrics**: Log API response headers (X-RateLimit-Remaining, Retry-After)

**Alerting**: Notify on sustained rate limit errors (indicates config issue)

---

## Architecture Diagrams

### Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                   GCP Cloud Scheduler                    │
│  (Cron: */15 * * * * → GDELT, 0 2 * * * → FRED, etc.)  │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP POST /api/tasks/trigger
                    ▼
┌─────────────────────────────────────────────────────────┐
│              Django (Cloud Run)                          │
│  ┌──────────────────────────────────────────┐          │
│  │  Task Dispatcher View                     │          │
│  │  → celery_app.send_task('ingest_gdelt')  │          │
│  └────────────────┬─────────────────────────┘          │
└───────────────────┼─────────────────────────────────────┘
                    │ Task → Redis
                    ▼
┌─────────────────────────────────────────────────────────┐
│              Redis (Memorystore)                         │
│                   Task Queue                             │
└───────────────────┬─────────────────────────────────────┘
                    │ Task ← Worker
                    ▼
┌─────────────────────────────────────────────────────────┐
│            Celery Worker (Cloud Run)                     │
│  ┌──────────────────────────────────────────┐          │
│  │  @shared_task                             │          │
│  │  def ingest_gdelt_events():               │          │
│  │    → External API (GDELT/FRED/etc.)       │          │
│  │    → tenacity retry logic                 │          │
│  │    → Event.objects.bulk_create()          │          │
│  └────────────────┬─────────────────────────┘          │
└───────────────────┼─────────────────────────────────────┘
                    │ Write events
                    ▼
┌─────────────────────────────────────────────────────────┐
│       PostgreSQL + TimescaleDB (Cloud SQL)               │
│  ┌──────────────────────────────────────────┐          │
│  │  Event Hypertable (partitioned by time)  │          │
│  │  EconomicIndicator Table                  │          │
│  │  FailedIngest Table (dead letter queue)  │          │
│  └──────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────┘
```

---

### Task Scheduling Matrix

| Source | Task Name | Schedule | Celery Rate Limit | Priority |
|--------|-----------|----------|-------------------|----------|
| GDELT | `ingest_gdelt_events` | */15 * * * * | None | High |
| ReliefWeb | `ingest_reliefweb_reports` | */30 * * * * | 1000/d | High |
| FRED | `ingest_fred_daily` | 0 2 * * * | 10/m | High |
| UN Comtrade | `ingest_comtrade_monthly` | 0 3 1 * * | 100/h | Medium |
| World Bank | `ingest_worldbank_quarterly` | 0 4 1 */3 * | None | Medium |
| USITC | `ingest_usitc_tariffs` | Manual | None | Low |
| Port Data | `ingest_port_data` | Future | N/A | Low |

---

## Don't Hand-Roll

**DO NOT custom-build these - use established solutions:**

1. **Task Queue**: Use Celery (not custom threading, not asyncio tasks)
2. **Retry Logic**: Use Tenacity (not custom try/except loops)
3. **HTTP Requests**: Use `requests` with `requests.Session()` (connection pooling)
4. **Rate Limiting**: Use Celery `rate_limit` decorator + Tenacity `wait` strategies
5. **JSON Parsing**: Use built-in `requests.json()` (not manual `json.loads()`)
6. **Date Parsing**: Use `dateutil.parser` or `pandas.to_datetime()` (not regex)
7. **API Wrappers**: Use official libraries (fredapi, wbgapi, gdeltPyR) when available
8. **CSV Parsing**: Use `pandas.read_csv()` (not csv module for large files)
9. **Scheduling**: Use Cloud Scheduler or Celery Beat (not cron + subprocess)
10. **Result Backend**: Use Celery's built-in backends (not custom status tracking)

**Libraries to Install**:
```
celery[redis]==5.3.6
redis==5.0.1
tenacity==8.2.3
requests==2.31.0
pandas==2.2.0
fredapi==0.5.2
wbgapi==1.0.14
gdeltPyR==0.1.10
comtradeapicall==0.1.0
django-celery-results==2.5.1
django-cloud-tasks==0.5.0  # Optional: GCP integration
flower==2.0.1  # Celery monitoring
```

---

## Common Pitfalls

### 1. Not Handling API Pagination
**Problem**: APIs return partial results, missing data
**Solution**: Check for `next_page` tokens, loop until exhausted

### 2. Ignoring Rate Limit Headers
**Problem**: Hitting rate limits unnecessarily
**Solution**: Parse `X-RateLimit-Remaining` and `Retry-After` headers

### 3. Synchronous Task Chains
**Problem**: Tasks wait for each other (slow ingestion)
**Solution**: Use Celery groups for parallel execution:
```python
from celery import group
job = group(ingest_fred_series.s(sid) for sid in series_ids)
job.apply_async()
```

### 4. No Idempotency
**Problem**: Re-running task duplicates data
**Solution**: Use `update_or_create()`, `bulk_create(ignore_conflicts=True)`, or unique constraints

### 5. Large Task Payloads
**Problem**: Passing huge datasets as Celery task args (Redis limits)
**Solution**: Pass IDs/queries, fetch data within task

### 6. No Result Expiration
**Problem**: Result backend fills up with old task results
**Solution**: Set `result_expires` in Celery config (e.g., 7 days)

### 7. Hardcoded API Keys
**Problem**: Secrets in code or environment variables
**Solution**: Use GCP Secret Manager, load at runtime

### 8. No Dead Letter Queue
**Problem**: Failed tasks disappear, no investigation possible
**Solution**: Implement `FailedIngest` model, catch exceptions and store

### 9. Timezone Confusion
**Problem**: UTC vs local time mismatches in scheduled tasks
**Solution**: Always use UTC in Celery, store timestamps as `timezone.now()` in Django

### 10. Worker Starvation
**Problem**: Long-running tasks block queue
**Solution**: Use separate queues for fast vs slow tasks:
```python
@shared_task(queue='fast')  # GDELT, ReliefWeb
@shared_task(queue='slow')   # UN Comtrade bulk loads
```

### 11. No Circuit Breaker
**Problem**: Hammering dead API repeatedly
**Solution**: Tenacity `stop_after_attempt`, check API status before retrying

### 12. Memory Leaks in Workers
**Problem**: Worker process grows unbounded
**Solution**: Set `CELERYD_MAX_TASKS_PER_CHILD=1000` to restart workers periodically

---

## Integration Patterns Summary

### High-Frequency Sources (GDELT, ReliefWeb)
- **Pattern**: Polling with small time windows (15-30min)
- **Optimization**: Incremental updates only (track last ingested timestamp)
- **Error Handling**: Aggressive retries (data is real-time sensitive)

### Daily/Weekly Sources (FRED)
- **Pattern**: Daily batch with series-level parallelization
- **Optimization**: Celery groups for concurrent series ingestion
- **Error Handling**: Retry failed series next day

### Monthly Sources (UN Comtrade, World Bank)
- **Pattern**: Monthly batch with country/indicator chunking
- **Optimization**: Respect monthly update cycles, query previous month
- **Error Handling**: Store failed months for manual backfill

### Irregular Sources (USITC, Port Data)
- **Pattern**: On-demand triggers, webhook listeners (future)
- **Optimization**: Low priority, manual review before ingestion
- **Error Handling**: Log errors, no automatic retry

---

## Key Decisions Summary

### Task Queue: Celery + Redis
- **Why**: Industry standard, mature, handles rate limiting and retries well
- **Alternative Rejected**: Django-Q2 (too limited), pure GCP (vendor lock-in)

### Scheduling: GCP Cloud Scheduler
- **Why**: GCP-native, no dedicated Beat process, easier Cloud Run deployment
- **Alternative**: Celery Beat (self-hosted, requires separate process)

### Retry Logic: Tenacity
- **Why**: Declarative, flexible backoff strategies, battle-tested
- **Alternative Rejected**: urllib3.Retry (less flexible), custom (error-prone)

### Result Backend: Django ORM (PostgreSQL)
- **Why**: Audit trail, no extra infrastructure, easier debugging
- **Alternative**: Redis (faster but no persistence)

### Rate Limiting: Two-Layer (Celery + Tenacity)
- **Why**: Coarse-grained task control + fine-grained request control
- **Alternative Rejected**: Single layer (insufficient control)

### Error Handling: Dead Letter Queue + FailedIngest Model
- **Why**: Debuggability, manual intervention for edge cases
- **Alternative Rejected**: Silent failures (data loss), logging only (no actionability)

---

## API Priority Ranking (Phase 3)

**Must-Have (Phase 3)**:
1. GDELT (real-time events)
2. FRED (economic indicators)
3. ReliefWeb (humanitarian updates)

**Should-Have (Phase 3 or 4)**:
4. UN Comtrade (trade data)
5. World Bank (development indicators)

**Nice-to-Have (Phase 4+)**:
6. USITC (tariff data, requires account)
7. Port Authorities (shipping data, commercial APIs, data quality concerns)

---

## Next Steps

Phase 3 will be split into 4 plans:
1. **03-01**: Celery + Redis setup, task infrastructure
2. **03-02**: GDELT + ReliefWeb real-time ingestion
3. **03-03**: FRED + economic data batch ingestion
4. **03-04**: UN Comtrade + World Bank monthly/quarterly ingestion

Each plan: 2-3 tasks, atomic implementation, tested with real API calls.

---

## Confidence Level

**Overall**: 85%

**High Confidence (90%+)**:
- API characteristics research (official docs + recent 2025 sources)
- Celery + Redis recommendation (industry standard, proven at scale)
- Tenacity for retry logic (widely adopted, better than alternatives)
- Two-layer rate limiting (matches real-world patterns)

**Medium Confidence (70-80%)**:
- Port data integration (commercial APIs, data quality concerns)
- USITC specifics (requires account, docs not fully accessible)
- Exact rate limits for GDELT/FRED (not publicly disclosed)

**Notes**:
- All major APIs (GDELT, FRED, UN Comtrade, World Bank, ReliefWeb) confirmed via official documentation and 2025 sources
- Task queue recommendation validated against 2025 Django community discussions
- GCP integration patterns verified against official GCP documentation
- Retry strategies based on industry best practices (exponential backoff with jitter)

**Risks**:
- GDELT DOC API rate limits not numerically specified (requires runtime testing)
- ReliefWeb appname requirement new as of Nov 2025 (watch for changes)
- UN Comtrade API transition from legacy to new API (verify which version in Phase 3)
- Port data costs could be prohibitive (defer until Phase 5+ if needed)
