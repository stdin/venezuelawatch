# LLM & GCP Integration Architecture

## Overview

This document outlines the integration of LiteLLM/Claude and GCP-based solutions into VenezuelaWatch's intelligence platform.

## Current System Analysis

### Existing Intelligence Stack
- **Sentiment Analysis**: VADER (rule-based, no LLM)
- **Entity Extraction**: spaCy en_core_web_sm (ML, no LLM)
- **Risk Scoring**: Custom rule-based algorithm
- **ETL**: Celery + Redis on Cloud Run
- **Storage**: PostgreSQL + TimescaleDB on Cloud SQL
- **Scheduling**: Cloud Scheduler (cron jobs)

### Current Limitations
1. **VADER Limitations**: Rule-based sentiment doesn't understand nuanced political language or sarcasm
2. **spaCy Limitations**: Pre-trained model not optimized for Venezuela-specific entities (Maduro, PDVSA, etc.)
3. **No Summarization**: Events stored as-is without summarization for quick scanning
4. **No Reasoning**: Risk scores lack explainability
5. **No Relationships**: Entities extracted but relationships not mapped
6. **ETL Bottlenecks**: Sequential processing in Celery workers

---

## Part 1: LiteLLM & Claude Integration

### Why LiteLLM?

**Benefits:**
- Unified API for 100+ LLM providers (Claude, GPT-4, Gemini, etc.)
- Automatic fallbacks and load balancing
- Cost tracking and budget management
- Response caching to reduce costs
- Streaming support
- Function calling support

**Why Claude specifically:**
- Strong reasoning and analysis capabilities
- Good at following complex instructions
- Excellent context understanding (200K token context)
- Cost-effective for batch processing
- Anthropic's Constitutional AI for safer outputs

### LLM Integration Points

#### 1. **Enhanced Sentiment Analysis**
**Current**: VADER rule-based sentiment
**LLM Enhancement**: Claude-powered contextual sentiment

```python
# Use Case: Analyze political sentiment with nuance
Input: "Maduro's government claims victory despite international skepticism"
VADER Output: 0.0 (neutral)
Claude Output: -0.4 (negative - skepticism indicates doubt and criticism)
```

**Implementation:**
- Hybrid approach: Use VADER for quick baseline, Claude for complex cases
- Detect complex cases: political language, sarcasm, multiple entities
- Batch processing to reduce API costs

#### 2. **Event Summarization**
**New Feature**: Generate concise summaries for long reports

```python
# Use Case: Summarize ReliefWeb humanitarian report
Input: 5000-word report on food insecurity
Output: "Venezuela faces acute food shortages affecting 7.3M people.
         OCHA recommends immediate humanitarian intervention in
         Zulia and Táchira states."
```

**Benefits:**
- Quick scanning of large reports
- Executive summaries for dashboards
- Mobile-friendly content

#### 3. **Advanced Entity Extraction & Relationship Mapping**
**Current**: spaCy extracts entities (people, orgs, locations)
**LLM Enhancement**: Extract entities AND relationships

```python
# Use Case: Map entity relationships
Input: "Maduro met with Chinese President Xi Jinping to discuss
        PDVSA's oil exports to PetroChina"

Output:
{
  "entities": [
    {"name": "Nicolás Maduro", "type": "PERSON", "role": "President of Venezuela"},
    {"name": "Xi Jinping", "type": "PERSON", "role": "President of China"},
    {"name": "PDVSA", "type": "ORG", "role": "Venezuelan state oil company"},
    {"name": "PetroChina", "type": "ORG", "role": "Chinese state oil company"}
  ],
  "relationships": [
    {"subject": "Maduro", "predicate": "met_with", "object": "Xi Jinping"},
    {"subject": "PDVSA", "predicate": "exports_to", "object": "PetroChina"},
    {"subject": "Maduro", "predicate": "discussed", "object": "oil exports"}
  ]
}
```

#### 4. **Explainable Risk Assessment**
**Current**: Numeric risk score (0.0-1.0)
**LLM Enhancement**: Risk score + reasoning

```python
# Use Case: Risk assessment with explanation
Input: Event about sanctions
Output: {
  "risk_score": 0.75,
  "risk_level": "high",
  "reasoning": [
    "US sanctions directly impact oil revenue (60% of GDP)",
    "Mentions humanitarian crisis keywords",
    "Political instability indicators present",
    "Historical context: similar sanctions led to economic collapse"
  ],
  "mitigation_suggestions": [
    "Monitor humanitarian aid access",
    "Track oil export alternatives (China, Russia)"
  ]
}
```

#### 5. **Event Classification**
**New Feature**: Multi-label classification

```python
# Use Case: Classify event into multiple categories
Input: "Venezuela's oil production drops to 30-year low amid power outages"
Output: {
  "primary_category": "ECONOMIC",
  "secondary_categories": ["ENERGY", "INFRASTRUCTURE"],
  "themes": ["oil_production", "power_crisis", "economic_decline"],
  "urgency": "high",
  "confidence": 0.92
}
```

#### 6. **Trend Analysis & Anomaly Detection**
**New Feature**: Detect unusual patterns

```python
# Use Case: Identify anomalies in event stream
Query: "Analyze last 30 days of events for unusual patterns"
Output: {
  "anomalies": [
    {
      "type": "spike",
      "description": "300% increase in protest events in Zulia state",
      "significance": "High - indicates growing civil unrest",
      "timeframe": "Dec 1-15, 2024"
    }
  ],
  "trends": [
    {
      "type": "declining",
      "metric": "oil_exports",
      "change": "-45% over 90 days",
      "significance": "Critical economic indicator"
    }
  ]
}
```

#### 7. **Intelligence Q&A**
**New Feature**: Natural language queries over events

```python
# Use Case: Ask questions about collected intelligence
Query: "What are the top 3 humanitarian concerns in Venezuela this month?"
Answer: "Based on 47 humanitarian reports:
1. Food insecurity - affecting 7.3M people (up 12% from last month)
2. Healthcare collapse - 80% of hospitals lack basic supplies
3. Migration crisis - 1.2M people crossed borders in Q4 2024"
```

### LiteLLM Implementation Architecture

```python
# Architecture Overview
┌─────────────────────────────────────────────────────────────┐
│                     VenezuelaWatch API                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           LiteLLM Service (Singleton)                │  │
│  │  - Provider: Claude (Anthropic)                      │  │
│  │  - Fallback: GPT-4 (OpenAI)                          │  │
│  │  - Budget: $100/month limit                          │  │
│  │  - Caching: Redis cache for repeated queries         │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           LLM-Enhanced Intelligence Services          │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  • Enhanced Sentiment Analyzer                       │  │
│  │  • Event Summarizer                                  │  │
│  │  • Relationship Extractor                            │  │
│  │  • Explainable Risk Scorer                           │  │
│  │  • Event Classifier                                  │  │
│  │  • Trend Analyzer                                    │  │
│  │  • Intelligence Q&A                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Hybrid Processing Strategy               │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  Fast Path (No LLM): Simple events, cached results   │  │
│  │  LLM Path: Complex events, new patterns              │  │
│  │  Batch Processing: Off-peak LLM calls for cost       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Cost Optimization Strategy

**Claude Pricing (Anthropic):**
- Claude 3.5 Sonnet: $3/million input tokens, $15/million output tokens
- Claude 3 Haiku: $0.25/million input tokens, $1.25/million output tokens

**Cost Reduction Tactics:**
1. **Hybrid Approach**: Use VADER/spaCy for simple cases, LLM for complex
2. **Batch Processing**: Process 100 events in single API call
3. **Response Caching**: Cache summaries and classifications (Redis)
4. **Model Selection**: Use Haiku for classification, Sonnet for reasoning
5. **Prompt Optimization**: Minimize token usage in prompts
6. **Budget Limits**: Set monthly caps ($100/month = ~6.6M input tokens on Haiku)

**Estimated Costs:**
- 10,000 events/month × 500 tokens avg = 5M tokens/month
- Using Haiku: $1.25/month for input
- Using Sonnet selectively: ~$5/month total

---

## Part 2: GCP ETL & Infrastructure Solutions

### Current vs. Proposed Architecture

#### Current Architecture (Celery-based)
```
Cloud Scheduler → Cloud Run API → Celery Queue (Redis) → Celery Workers → Cloud SQL
```

**Limitations:**
- Sequential processing (slow for large batches)
- Worker scaling requires manual configuration
- No event-driven triggers
- No streaming support
- Limited observability

#### Proposed Architecture (GCP-native)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Event Sources                                │
│  GDELT | ReliefWeb | FRED | Comtrade | World Bank                  │
└────────────────────────┬────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   Cloud Scheduler (Cron)                            │
│  - GDELT: Every 15 min                                              │
│  - ReliefWeb: Daily                                                 │
│  - FRED: Daily                                                      │
│  - Comtrade: Monthly                                                │
│  - World Bank: Quarterly                                            │
└────────────────────────┬────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                Cloud Functions (Ingestion)                          │
│  - Fetch data from external APIs                                   │
│  - Light transformation                                             │
│  - Publish to Pub/Sub topics                                       │
└────────────────────────┬────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│              Cloud Pub/Sub (Event Bus)                              │
│  Topics:                                                            │
│    • raw-events (from ingestion)                                   │
│    • analyzed-events (after processing)                            │
│    • high-risk-events (risk > 0.7)                                 │
│    • anomaly-events (detected anomalies)                           │
└────────────┬────────────────────────────────────────┬───────────────┘
             ↓                                        ↓
┌────────────────────────────────┐  ┌───────────────────────────────┐
│   Cloud Run (Real-time API)   │  │  Dataflow (Batch ETL)         │
│  - Event CRUD                  │  │  - Transform raw → structured │
│  - Intelligence analysis       │  │  - Enrich with LLM            │
│  - Query interface             │  │  - Deduplicate                │
│  - WebSocket updates           │  │  - Load to BigQuery + SQL     │
└────────────┬───────────────────┘  └───────────────┬───────────────┘
             ↓                                      ↓
┌────────────────────────────────────────────────────────────────────┐
│                      Storage Layer                                 │
├───────────────────────────────┬────────────────────────────────────┤
│  Cloud SQL (Operational)      │  BigQuery (Analytics)              │
│  - TimescaleDB                │  - Event warehouse                 │
│  - Real-time queries          │  - Trend analysis                  │
│  - Fast writes                │  - ML training data                │
│  - OLTP workload              │  - OLAP workload                   │
└───────────────────────────────┴────────────────────────────────────┘
             ↓                                      ↓
┌────────────────────────────────────────────────────────────────────┐
│                  Frontend / Dashboards                             │
│  - Next.js app (Vercel/Cloud Run)                                 │
│  - Real-time updates via Pub/Sub → WebSocket                      │
│  - Analytics from BigQuery                                         │
└────────────────────────────────────────────────────────────────────┘
```

### GCP Service Recommendations

#### 1. **Cloud Pub/Sub** (Event Bus)
**Use Case**: Decouple ingestion from processing

**Benefits:**
- Event-driven architecture
- Automatic scaling
- Message durability (7-day retention)
- Fan-out to multiple subscribers
- Dead letter queues for failed messages

**Topics Structure:**
```
raw-events          → Raw data from APIs
processed-events    → After intelligence analysis
high-risk-events    → Risk score > 0.7
humanitarian-events → Event type = HUMANITARIAN
anomaly-events      → Detected anomalies
```

**Pricing:**
- First 10 GB/month: Free
- $40/TB after free tier
- Estimated: ~$5/month for 100K events

#### 2. **Cloud Functions** (Serverless Ingestion)
**Use Case**: Replace Celery workers for ingestion

**Benefits:**
- Auto-scaling (0 to N instances)
- Pay-per-invocation (no idle cost)
- Built-in HTTP triggers
- Native Pub/Sub integration
- Max 60 min timeout (vs Celery's indefinite)

**Functions:**
```
ingest-gdelt        → Fetch GDELT, publish to Pub/Sub
ingest-reliefweb    → Fetch ReliefWeb, publish to Pub/Sub
ingest-fred         → Fetch FRED, publish to Pub/Sub
analyze-event       → Subscribe to raw-events, analyze, publish to processed-events
detect-anomalies    → Subscribe to processed-events, check for anomalies
```

**Pricing:**
- First 2M invocations/month: Free
- $0.40 per million invocations after
- Estimated: ~$2/month for 100K events

#### 3. **Cloud Dataflow** (Apache Beam ETL)
**Use Case**: Large-scale batch processing and streaming

**Benefits:**
- Unified batch + streaming
- Auto-scaling workers
- Built-in windowing and aggregations
- SQL-like transforms
- Direct BigQuery integration

**Pipelines:**
```
Batch Pipeline (Daily):
  Read from Cloud SQL
    ↓
  Transform & Enrich
    ↓
  Deduplicate
    ↓
  Write to BigQuery

Streaming Pipeline (Real-time):
  Read from Pub/Sub
    ↓
  Windowed Aggregations (5 min windows)
    ↓
  Anomaly Detection
    ↓
  Write to BigQuery + Pub/Sub
```

**When to Use:**
- Large-scale data transformation (>10K events/hour)
- Complex aggregations
- Real-time streaming analytics
- ML feature engineering

**Pricing:**
- $0.056 per vCPU hour
- $0.003557 per GB RAM hour
- Estimated: $50-100/month for continuous streaming

**Alternative**: For smaller scale (<10K events/hour), stick with Cloud Run + Pub/Sub

#### 4. **BigQuery** (Data Warehouse)
**Use Case**: Analytics, reporting, ML training

**Benefits:**
- Serverless (no infrastructure)
- Petabyte-scale queries
- Built-in ML (BQML)
- Cost-effective storage ($0.02/GB/month)
- Fast queries with column-based storage

**Schema Design:**
```sql
-- events table
CREATE TABLE venezuelawatch.events (
  event_id STRING,
  source STRING,
  event_type STRING,
  timestamp TIMESTAMP,
  title STRING,
  content JSON,
  sentiment FLOAT64,
  risk_score FLOAT64,
  entities ARRAY<STRING>,
  ingestion_timestamp TIMESTAMP
)
PARTITION BY DATE(timestamp)
CLUSTER BY source, event_type;

-- aggregations table (materialized view)
CREATE MATERIALIZED VIEW venezuelawatch.daily_metrics AS
SELECT
  DATE(timestamp) as date,
  source,
  event_type,
  COUNT(*) as event_count,
  AVG(sentiment) as avg_sentiment,
  AVG(risk_score) as avg_risk,
  ARRAY_AGG(DISTINCT entity ORDER BY entity LIMIT 10) as top_entities
FROM venezuelawatch.events
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
GROUP BY date, source, event_type;
```

**Use Cases:**
- Trend analysis (sentiment over time)
- Risk heatmaps by region/type
- Entity co-occurrence graphs
- ML model training data
- Executive dashboards

**Pricing:**
- Storage: $0.02/GB/month (first 10GB free)
- Queries: $5/TB processed (first 1TB free)
- Estimated: ~$10/month for 100K events

#### 5. **Cloud Run** (API & Realtime)
**Current Use**: Django API
**Enhanced Use**: WebSocket support for real-time updates

**Enhancements:**
- Add WebSocket endpoint for live event streaming
- Subscribe to Pub/Sub topics
- Push updates to connected clients
- Horizontal auto-scaling (0-1000 instances)

**Pricing:**
- First 2M requests/month: Free
- $0.40 per million requests after
- Current usage: Likely within free tier

#### 6. **Vertex AI** (ML & LLM Hosting)
**Use Case**: Self-hosted LLM for cost optimization (optional)

**Benefits:**
- Host open-source LLMs (Llama 3, Mixtral)
- Fine-tune models on Venezuela-specific data
- Lower cost than API calls for high volume
- Data privacy (no data leaves GCP)

**Cost Comparison:**
```
Claude API (100K events/month):
  - $5/month via LiteLLM

Vertex AI (self-hosted Llama 3):
  - Instance: $200/month (1x A100 GPU)
  - Cost-effective at >4M tokens/month

Recommendation: Start with Claude API, migrate to Vertex AI if volume justifies
```

#### 7. **Cloud Composer** (Airflow for Orchestration)
**Use Case**: Complex ETL workflows with dependencies

**Benefits:**
- Managed Apache Airflow
- Visual DAG editor
- Task dependencies and retries
- Monitoring and alerting

**Example DAG:**
```python
# Daily intelligence pipeline
ingest_gdelt >> ingest_reliefweb >> merge_events >> analyze_events >>
  generate_summary >> export_to_bigquery >> send_alerts
```

**When to Use:**
- Complex multi-step workflows
- Task dependencies
- SLA monitoring
- Backfill capabilities

**Pricing:**
- $0.074/vCPU hour (small environment: $300/month)
- Alternative: Use Cloud Scheduler + Pub/Sub for simple workflows (current approach)

### Recommended GCP Architecture (Pragmatic)

For VenezuelaWatch's current scale, recommend:

1. **Keep**: Cloud Run (Django API), Cloud SQL (PostgreSQL), Cloud Scheduler
2. **Add**: Cloud Pub/Sub for event-driven processing
3. **Add**: BigQuery for analytics (sync events daily)
4. **Consider**: Cloud Functions for ingestion (vs Celery)
5. **Skip for now**: Dataflow (overkill for current scale), Composer (too expensive)

**Migration Path:**
- **Phase 1** (Current): Cloud Run + Celery + Cloud SQL
- **Phase 2**: Add Pub/Sub + BigQuery
- **Phase 3**: Replace Celery with Cloud Functions (optional)
- **Phase 4**: Add Dataflow if streaming needs grow

---

## Implementation Plan

### Phase 1: LiteLLM Integration (Week 1-2)
1. Install LiteLLM + Anthropic SDK
2. Create LLM service wrapper
3. Implement enhanced sentiment analysis
4. Add event summarization
5. Test with 100 sample events

### Phase 2: Advanced LLM Features (Week 3-4)
1. Relationship extraction
2. Explainable risk scoring
3. Event classification
4. Q&A interface

### Phase 3: GCP Pub/Sub Integration (Week 5-6)
1. Set up Pub/Sub topics
2. Modify ingestion to publish to Pub/Sub
3. Create Pub/Sub → Cloud SQL subscriber
4. Add real-time WebSocket updates

### Phase 4: BigQuery Analytics (Week 7-8)
1. Create BigQuery dataset
2. Daily sync from Cloud SQL → BigQuery
3. Build analytics queries
4. Create materialized views

### Cost Estimate (Monthly)
- LiteLLM/Claude: $5-10
- Pub/Sub: $5
- BigQuery: $10
- Cloud Functions (if migrate): $2
- **Total Additional**: ~$25/month

### Success Metrics
- LLM accuracy: >85% on sentiment vs human labels
- Processing latency: <5s per event with LLM
- Cost per event: <$0.001
- BigQuery query performance: <5s for 90-day aggregations
