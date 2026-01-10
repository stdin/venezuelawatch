# TimescaleDB Migration: GCP Time-Series Database Decision

**Date:** 2026-01-09
**Issue:** TimescaleDB extension not available on Cloud SQL for PostgreSQL
**Status:** RESEARCH COMPLETE - RECOMMENDATION READY

## Problem Statement

The current architecture assumes TimescaleDB hypertables for time-series event data (Phase 1 decision). **TimescaleDB is not available as a Cloud SQL extension on GCP**, blocking production deployment.

**Current TimescaleDB usage:**
- Event model with `mentioned_at` timestamp for time-series queries
- EntityMention with `mentioned_at` for trending calculations
- FRED economic indicators with time-series data
- Phase 14 already uses BigQuery for forecasting ETL (90-day rolling window)

## GCP Time-Series Database Options

### Option 1: BigQuery (RECOMMENDED ✅)

**What it is:** Serverless data warehouse with SQL support, built-in time-series functions, and analytics optimization.

**Pros:**
- ✅ **Already using for Phase 14 forecasting** - consolidate infrastructure
- ✅ **SQL support** - familiar query language, easier than NoSQL
- ✅ **Built-in time-series functions** - TIMESTAMP_BUCKET, GAP_FILL, time-series ML
- ✅ **2025 transactional features** - DML (UPDATE/DELETE/MERGE), multi-statement transactions, ACID properties
- ✅ **Native PostgreSQL migration tools** - BigQuery Data Transfer Service, Datastream CDC
- ✅ **Scales automatically** - no capacity planning, handles petabytes
- ✅ **Cost-effective for analytics** - pay per query, cheap storage
- ✅ **Python client library** - `google-cloud-bigquery` integrates with Django services

**Cons:**
- ⚠️ **No Django ORM support** - need to use Python client library or SQLAlchemy (read-only)
- ⚠️ **Not optimized for high-frequency transactional writes** - but streaming inserts work fine for batch/polling ingestion
- ⚠️ **Query costs** - but predictable with proper optimization
- ⚠️ **Eventual consistency for DML** - but acceptable for analytics workloads

**Best for:** Analytics-heavy workloads (which VenezuelaWatch is)

**Migration complexity:** LOW-MEDIUM (tools exist, schema translation straightforward)

---

### Option 2: Cloud Bigtable

**What it is:** NoSQL wide-column database, optimized for low-latency, high-throughput time-series.

**Pros:**
- ✅ **Built specifically for time-series** - IoT, sensor data, financial ticks
- ✅ **Low latency** - single-digit millisecond reads/writes
- ✅ **High throughput** - millions of writes per second
- ✅ **Official time-series schema patterns** - well-documented

**Cons:**
- ❌ **NoSQL (no SQL)** - completely different data model, no JOINs
- ❌ **No Django ORM** - custom client code for everything
- ❌ **Wide-column schema** - requires application rewrite
- ❌ **More expensive** - minimum 3 nodes for production ($1,000+/month)
- ❌ **Overkill for this use case** - not doing millions of writes/sec

**Best for:** Real-time IoT sensor data, AdTech, high-frequency trading

**Migration complexity:** HIGH (complete application rewrite, different data model)

---

### Option 3: Cloud SQL PostgreSQL with pg_partman

**What it is:** Standard PostgreSQL with manual time-based partitioning using pg_partman extension.

**Pros:**
- ✅ **Keep Django ORM** - no application changes
- ✅ **PostgreSQL extensions available** - pg_partman supported on Cloud SQL
- ✅ **Time-based partitioning works** - can partition Event table by month/week

**Cons:**
- ❌ **Manual partition management** - no automatic partitioning like TimescaleDB
- ❌ **Won't scale as well** - Cloud SQL has instance size limits
- ❌ **Still need separate analytics database** - BigQuery for Phase 14 forecasting, correlation analysis
- ❌ **Higher ops burden** - Cloud Scheduler cron jobs for pg_partman maintenance
- ❌ **Doesn't solve the original problem** - just works around it

**Best for:** Small-scale time-series that fit on single PostgreSQL instance

**Migration complexity:** LOW (minimal changes, but adds ops complexity)

---

## Recommendation: Polyglot Persistence (PostgreSQL + BigQuery)

**Architecture:** Use the right database for the right job.

### PostgreSQL (Cloud SQL) for:
- ✅ **User accounts, authentication** - django.contrib.auth, allauth sessions
- ✅ **Entity metadata** - Entity model (id, name, entity_type, aliases)
- ✅ **Reference data** - Static configuration, lookup tables
- ✅ **Transactional operations** - Things that need ACID, Django ORM

### BigQuery for:
- ✅ **Event time-series data** - Event model with mentioned_at timestamp
- ✅ **EntityMention time-series** - Entity mentions with mentioned_at for trending
- ✅ **FRED economic indicators** - Time-series economic data
- ✅ **UN Comtrade, World Bank data** - Historical trade and development indicators
- ✅ **Analytics queries** - Aggregations, time-series analysis, correlations
- ✅ **Phase 14 forecasting** - Already using BigQuery for this
- ✅ **Phase 15 correlation analysis** - Perfect fit for BigQuery

**Why this works:**
1. **VenezuelaWatch is an analytics platform, not a transactional system** - optimizing for read-heavy analytics queries
2. **Event ingestion is batch/polling** - GDELT every 15 min, FRED daily, UN Comtrade monthly (not millions of writes/sec)
3. **Already using BigQuery for Phase 14** - consolidate instead of adding another database
4. **Django ORM isn't critical for time-series queries** - these are complex analytics queries anyway, not ORM-friendly
5. **Separation of concerns** - operational data (users, entities) separate from analytical data (events, mentions)

**This is a standard "polyglot persistence" pattern** used by Netflix, Uber, Airbnb, etc.

---

## Migration Strategy

### Phase 1: Set Up BigQuery Schema

```sql
-- Events table in BigQuery
CREATE TABLE `project.dataset.events` (
    id STRING NOT NULL,
    title STRING,
    content STRING,
    source_url STRING NOT NULL,
    source_name STRING,
    event_type STRING,
    location STRING,
    risk_score FLOAT64,
    severity STRING,
    mentioned_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    metadata JSON
)
PARTITION BY DATE(mentioned_at)
CLUSTER BY event_type, source_name;

-- EntityMentions table in BigQuery
CREATE TABLE `project.dataset.entity_mentions` (
    id STRING NOT NULL,
    entity_id STRING NOT NULL,
    event_id STRING NOT NULL,
    mentioned_at TIMESTAMP NOT NULL,
    context STRING
)
PARTITION BY DATE(mentioned_at)
CLUSTER BY entity_id;

-- FRED economic indicators
CREATE TABLE `project.dataset.fred_indicators` (
    series_id STRING NOT NULL,
    date DATE NOT NULL,
    value FLOAT64,
    series_name STRING,
    units STRING
)
PARTITION BY date
CLUSTER BY series_id;
```

**Key design choices:**
- **PARTITION BY DATE(mentioned_at)** - time-based partitioning for query performance and cost optimization
- **CLUSTER BY** - co-locate related data for faster scans (entity_id, event_type)
- **STRING for IDs** - BigQuery doesn't have SERIAL/AUTO_INCREMENT, use UUIDs

### Phase 2: Update Django Models

**Keep in Cloud SQL PostgreSQL:**
```python
# backend/api/models.py - STAYS IN POSTGRESQL

class User(AbstractUser):
    """User model - PostgreSQL (transactional)"""
    # No changes needed
    pass

class Entity(models.Model):
    """Entity metadata - PostgreSQL (transactional)"""
    # Keep this in PostgreSQL for ORM, foreign keys, etc.
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=50)
    aliases = models.JSONField(default=list)
    sanctions_status = models.BooleanField(default=False)
    # NO time-series data here
```

**Move to BigQuery (remove Django models):**
```python
# backend/api/bigquery_models.py - NEW FILE

"""
BigQuery models (not Django models, just dataclasses/schemas)
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class Event:
    """Event schema for BigQuery"""
    title: str
    content: str
    source_url: str
    source_name: str
    event_type: str
    location: Optional[str]
    risk_score: float
    severity: str
    mentioned_at: datetime
    metadata: dict
    id: str = None  # Generated if not provided

    def to_bigquery_row(self):
        """Convert to BigQuery insert format"""
        return {
            'id': self.id or str(uuid.uuid4()),
            'title': self.title,
            'content': self.content,
            'source_url': self.source_url,
            'source_name': self.source_name,
            'event_type': self.event_type,
            'location': self.location,
            'risk_score': self.risk_score,
            'severity': self.severity,
            'mentioned_at': self.mentioned_at.isoformat(),
            'metadata': self.metadata
        }

@dataclass
class EntityMention:
    """EntityMention schema for BigQuery"""
    entity_id: str
    event_id: str
    mentioned_at: datetime
    context: str
    id: str = None

    def to_bigquery_row(self):
        return {
            'id': self.id or str(uuid.uuid4()),
            'entity_id': self.entity_id,
            'event_id': self.event_id,
            'mentioned_at': self.mentioned_at.isoformat(),
            'context': self.context
        }
```

### Phase 3: Create BigQuery Service Layer

```python
# backend/api/services/bigquery_service.py - NEW FILE

"""
BigQuery service for time-series queries
"""
from google.cloud import bigquery
from django.conf import settings
from typing import List, Dict, Any
from datetime import datetime, timedelta

class BigQueryService:
    def __init__(self):
        self.client = bigquery.Client(project=settings.GCP_PROJECT_ID)
        self.dataset = settings.BIGQUERY_DATASET

    def insert_events(self, events: List['Event']) -> None:
        """
        Insert events into BigQuery (streaming insert)
        """
        table_id = f"{self.dataset}.events"
        rows = [event.to_bigquery_row() for event in events]

        errors = self.client.insert_rows_json(table_id, rows)
        if errors:
            raise Exception(f"BigQuery insert errors: {errors}")

    def get_recent_events(
        self,
        start_date: datetime,
        end_date: datetime,
        event_type: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query recent events with filters
        """
        query = f"""
        SELECT
            id,
            title,
            content,
            source_url,
            source_name,
            event_type,
            location,
            risk_score,
            severity,
            mentioned_at,
            metadata
        FROM `{self.dataset}.events`
        WHERE mentioned_at BETWEEN @start_date AND @end_date
        {f"AND event_type = @event_type" if event_type else ""}
        ORDER BY mentioned_at DESC
        LIMIT {limit}
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date),
                bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", end_date),
            ]
        )

        if event_type:
            job_config.query_parameters.append(
                bigquery.ScalarQueryParameter("event_type", "STRING", event_type)
            )

        results = self.client.query(query, job_config=job_config)
        return [dict(row) for row in results]

    def get_entity_trending(
        self,
        metric: str = 'mentions',
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Calculate trending entities (replaces Phase 6 trending logic)
        """
        # Time-decay trending using BigQuery time functions
        query = f"""
        WITH recent_mentions AS (
            SELECT
                entity_id,
                mentioned_at,
                TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), mentioned_at, HOUR) as hours_ago
            FROM `{self.dataset}.entity_mentions`
            WHERE mentioned_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        )
        SELECT
            entity_id,
            COUNT(*) as mention_count,
            -- Exponential time decay: score = mentions * exp(-hours_ago / 168)
            -- 168 hours = 7 days half-life
            SUM(EXP(-hours_ago / 168.0)) as trending_score
        FROM recent_mentions
        GROUP BY entity_id
        ORDER BY trending_score DESC
        LIMIT {limit}
        """

        results = self.client.query(query)
        return [dict(row) for row in results]

    def get_risk_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        bucket_size: str = 'DAY'
    ) -> List[Dict[str, Any]]:
        """
        Time-bucketed risk trend aggregation
        """
        query = f"""
        SELECT
            TIMESTAMP_BUCKET(mentioned_at, INTERVAL 1 {bucket_size}) as time_bucket,
            AVG(risk_score) as avg_risk,
            MAX(risk_score) as max_risk,
            COUNT(*) as event_count
        FROM `{self.dataset}.events`
        WHERE mentioned_at BETWEEN @start_date AND @end_date
        GROUP BY time_bucket
        ORDER BY time_bucket
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date),
                bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", end_date),
            ]
        )

        results = self.client.query(query, job_config=job_config)
        return [dict(row) for row in results]


# Singleton instance
bigquery_service = BigQueryService()
```

### Phase 4: Update Celery Ingestion Tasks

```python
# backend/api/tasks.py - UPDATE

from api.services.bigquery_service import bigquery_service
from api.bigquery_models import Event

@celery.task
def ingest_gdelt_events():
    """
    GDELT ingestion - write to BigQuery instead of PostgreSQL
    """
    # Fetch from GDELT API (no changes)
    gdelt_data = fetch_gdelt_api()

    # Transform to Event dataclass
    events = []
    for item in gdelt_data:
        event = Event(
            title=item['title'],
            content=item['content'],
            source_url=item['url'],
            source_name='GDELT',
            event_type='political',
            location=item.get('location'),
            risk_score=calculate_risk_score(item),
            severity=classify_severity(item),
            mentioned_at=item['published_date'],
            metadata=item.get('metadata', {})
        )
        events.append(event)

    # Write to BigQuery (instead of Django ORM)
    bigquery_service.insert_events(events)

    logger.info(f"Ingested {len(events)} GDELT events to BigQuery")
```

### Phase 5: Update Django Views

```python
# backend/api/views.py - UPDATE

from ninja import Router
from datetime import datetime, timedelta
from api.services.bigquery_service import bigquery_service

router = Router()

@router.get("/events/")
def list_events(
    request,
    start_date: datetime = None,
    end_date: datetime = None,
    event_type: str = None,
    limit: int = 100
):
    """
    List events from BigQuery (not Django ORM)
    """
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    events = bigquery_service.get_recent_events(
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        limit=limit
    )

    return {"events": events}

@router.get("/entities/trending/")
def trending_entities(request, metric: str = 'mentions', limit: int = 20):
    """
    Trending entities from BigQuery (replaces Redis trending)
    """
    trending = bigquery_service.get_entity_trending(metric=metric, limit=limit)

    # Fetch Entity metadata from PostgreSQL (still using ORM)
    from api.models import Entity
    entity_ids = [t['entity_id'] for t in trending]
    entities = Entity.objects.filter(id__in=entity_ids)
    entity_map = {str(e.id): e for e in entities}

    # Merge BigQuery trending scores with PostgreSQL metadata
    results = []
    for trend in trending:
        entity = entity_map.get(trend['entity_id'])
        if entity:
            results.append({
                'entity': {
                    'id': entity.id,
                    'name': entity.name,
                    'entity_type': entity.entity_type,
                    'sanctions_status': entity.sanctions_status
                },
                'mention_count': trend['mention_count'],
                'trending_score': trend['trending_score']
            })

    return {"trending": results}
```

### Phase 6: Data Migration (One-Time)

**Option A: Export/Import (for initial migration)**

```bash
# 1. Export existing PostgreSQL data to CSV
psql -h <cloud-sql-ip> -U postgres -d venezuelawatch \
  -c "COPY (SELECT * FROM api_event) TO STDOUT WITH CSV HEADER" \
  > events.csv

# 2. Upload to Cloud Storage
gsutil cp events.csv gs://venezuelawatch-migration/events.csv

# 3. Load into BigQuery
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --autodetect \
  venezuelawatch_dataset.events \
  gs://venezuelawatch-migration/events.csv
```

**Option B: Datastream CDC (for ongoing sync during transition)**

1. Set up Datastream connection from Cloud SQL to BigQuery
2. Enable CDC on Cloud SQL PostgreSQL
3. Datastream replicates changes in near real-time
4. Cut over once confident BigQuery has all data

**Recommended:** Option A (one-time export/import) since you're early in development.

---

## Impact on Existing Phases

### Phase 1: Foundation & Infrastructure ✅
- **Change:** Remove TimescaleDB hypertable setup
- **Update:** Add BigQuery dataset creation
- **Effort:** LOW (1-2 hours)

### Phase 3: Data Pipeline ✅
- **Change:** Celery tasks write to BigQuery instead of PostgreSQL
- **Update:** Use `bigquery_service.insert_events()` instead of Django ORM
- **Effort:** MEDIUM (4-6 hours, update all ingestion tasks)

### Phase 4: Risk Intelligence ✅
- **Change:** Risk scoring queries from BigQuery
- **Update:** Risk aggregation uses BigQuery SQL instead of Django ORM aggregates
- **Effort:** MEDIUM (4-6 hours)

### Phase 6: Entity Watch ✅
- **Change:** Trending calculation moves from Redis to BigQuery
- **Update:** Use BigQuery time-decay trending query
- **Benefit:** Simpler architecture (no Redis Sorted Sets)
- **Effort:** MEDIUM (4-6 hours)

### Phase 7: AI Chat ✅
- **Change:** Tool functions query BigQuery instead of PostgreSQL
- **Update:** `search_events` tool uses `bigquery_service`
- **Effort:** LOW (2-3 hours)

### Phase 14: Forecasting ✅
- **Change:** NONE (already using BigQuery!)
- **Benefit:** No longer need ETL from PostgreSQL to BigQuery
- **Effort:** ZERO

### Phase 15: Correlation Analysis ✅
- **Change:** NONE (BigQuery is perfect for this!)
- **Benefit:** All time-series data already in BigQuery
- **Effort:** ZERO

---

## Cost Analysis

### Current Architecture (with TimescaleDB if it worked):
- Cloud SQL PostgreSQL: ~$200/month (db-custom-1-3840, 4 vCPU, 15GB RAM)
- Cloud Storage: ~$20/month
- **Total: ~$220/month**

### Recommended Architecture (PostgreSQL + BigQuery):
- Cloud SQL PostgreSQL (smaller instance): ~$100/month (db-custom-1-1920, 2 vCPU, 7.5GB RAM)
  - Only storing users, entities, reference data (much less data)
- BigQuery storage: ~$20/month (assuming 100GB events @ $0.02/GB)
- BigQuery queries: ~$50/month (assuming 1TB scanned @ $5/TB, with partitioning)
- Cloud Storage: ~$20/month
- **Total: ~$190/month**

**Savings: $30/month (~15% cheaper) + infinite scalability**

**Cost optimization tips:**
- Use PARTITION BY DATE for time-series queries (only scan relevant dates)
- Use CLUSTER BY for entity/event_type queries (co-locate related data)
- Use BigQuery BI Engine for cached queries (first 1GB free)
- Use streaming inserts for ingestion (free up to 1GB/day)

---

## Timeline

| Phase | Task | Effort | Dependencies |
|-------|------|--------|--------------|
| 1 | Create BigQuery dataset and schema | 2 hours | - |
| 2 | Create `bigquery_service.py` | 4 hours | Phase 1 |
| 3 | Update Celery ingestion tasks (Phase 3) | 6 hours | Phase 2 |
| 4 | Update API views (Phase 4, 6, 7) | 8 hours | Phase 2 |
| 5 | Migrate existing data (export/import) | 2 hours | Phase 3-4 |
| 6 | Update tests | 4 hours | Phase 3-4 |
| 7 | Deploy and validate | 2 hours | All above |
| **TOTAL** | | **28 hours (~3.5 days)** | |

**Recommendation:** Do this migration NOW (before Phase 15) since Phase 15 correlation analysis benefits hugely from BigQuery.

---

## Decision

**RECOMMENDED: Option 1 - Polyglot Persistence (PostgreSQL + BigQuery)**

**Rationale:**
1. ✅ VenezuelaWatch is an analytics platform - BigQuery is purpose-built for this
2. ✅ Already using BigQuery for Phase 14 - consolidate infrastructure
3. ✅ Event ingestion is batch/polling - not high-frequency transactional writes
4. ✅ Separation of concerns - operational data in PostgreSQL, analytical data in BigQuery
5. ✅ Future-proof - scales to billions of events without re-architecture
6. ✅ Cost-effective - ~15% cheaper than current architecture
7. ✅ Phase 15 correlation analysis - perfect fit for BigQuery time-series functions

**Next steps:**
1. Create `TIMESCALEDB-MIGRATION-PLAN.md` with specific tasks for each phase
2. Update Phase 1, 3, 4, 6, 7 plans to remove TimescaleDB references
3. Create new plan: "Phase 0.5: BigQuery Migration" (or integrate into Phase 1)
4. Execute migration (~3.5 days effort)

---

## References

**Official Documentation:**
- [BigQuery time-series functions](https://cloud.google.com/bigquery/docs/working-with-time-series)
- [BigQuery transactions (2025)](https://cloud.google.com/bigquery/docs/transactions)
- [Datastream PostgreSQL to BigQuery](https://cloud.google.com/datastream/docs/quickstart-replication-to-bigquery)
- [Bigtable time-series schema design](https://cloud.google.com/bigtable/docs/schema-design-time-series)
- [Cloud SQL supported extensions](https://cloud.google.com/sql/docs/postgres/extensions)

**Research Sources:**
- Sprinkle Data "Bigtable vs BigQuery" (2024)
- Hevo Data "PostgreSQL to BigQuery" (2024)
- Google Cloud Blog "Bigtable vs BigQuery" (official)
- Estuary "BigQuery ETL Best Practices" (2025)

**Confidence:** HIGH - Based on official GCP documentation and production use cases

---

*Document created: 2026-01-09*
*Author: Claude Code*
*Status: READY FOR DECISION*
