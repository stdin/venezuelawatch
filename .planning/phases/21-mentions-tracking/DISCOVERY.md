# Phase 21: Mentions Tracking - Discovery

**Date**: 2026-01-10
**Level**: Standard Research (Level 2)

## Overview

Phase 21 builds mention tracking infrastructure using GDELT's eventmentions_partitioned table (2.5B rows, 532GB) to detect narrative spikes and early warning signals.

## GDELT Mentions Table Schema

**Table**: `gdelt-bq.gdeltv2.eventmentions_partitioned`
- **Size**: 2,510,915,189 rows, 532.94 GB
- **Partitioning**: DAY on _PARTITIONTIME (critical for performance)

**Key Fields**:
- `GLOBALEVENTID` (INTEGER) - Links to events_partitioned table
- `EventTimeDate` (INTEGER) - When event actually occurred (YYYYMMDD format)
- `MentionTimeDate` (INTEGER) - When article mentioning event was published
- `MentionType` (INTEGER) - Type of mention (1=WEB, 2=CITATION, 3=CORE, etc.)
- `MentionSourceName` (STRING) - Source that published the mention
- `MentionIdentifier` (STRING) - URL or identifier for the article
- `Confidence` (INTEGER) - GDELT's confidence score (0-100)
- `MentionDocTone` (FLOAT) - Sentiment tone of the article
- `MentionDocLen` (INTEGER) - Document length in characters

## Time-Series Aggregation Patterns

### BigQuery Window Functions for Spike Detection

**Standard deviation and z-score calculation**:
```sql
WITH daily_counts AS (
  SELECT
    DATE(PARSE_TIMESTAMP('%Y%m%d', CAST(MentionTimeDate AS STRING))) AS mention_date,
    GLOBALEVENTID,
    COUNT(*) AS mention_count
  FROM `gdelt-bq.gdeltv2.eventmentions_partitioned`
  WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND GLOBALEVENTID IN (SELECT event_id FROM my_venezuela_events)
  GROUP BY mention_date, GLOBALEVENTID
),
stats_calc AS (
  SELECT
    mention_date,
    GLOBALEVENTID,
    mention_count,
    AVG(mention_count) OVER (
      PARTITION BY GLOBALEVENTID
      ORDER BY mention_date
      ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
    ) AS rolling_avg,
    STDDEV_POP(mention_count) OVER (
      PARTITION BY GLOBALEVENTID
      ORDER BY mention_date
      ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
    ) AS rolling_stddev
  FROM daily_counts
)
SELECT
  mention_date,
  GLOBALEVENTID,
  mention_count,
  rolling_avg,
  rolling_stddev,
  -- Calculate z-score
  CASE
    WHEN rolling_stddev > 0 THEN (mention_count - rolling_avg) / rolling_stddev
    ELSE 0
  END AS z_score
FROM stats_calc
WHERE mention_date >= CURRENT_DATE() - 7
ORDER BY mention_date DESC, z_score DESC;
```

**Key patterns**:
- Use `ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING` for 7-day lookback window (excludes current day to avoid inflating baseline)
- `STDDEV_POP` for population standard deviation over window
- `AVG` with window function for rolling average
- Partition filtering mandatory for 532GB table performance

## Statistical Spike Detection

### Z-Score Method

**Formula**: `z = (x - μ) / σ`
- `x` = current day mention count
- `μ` = rolling 7-day average (baseline)
- `σ` = rolling 7-day standard deviation

**Confidence thresholds**:
- `z >= 2.0` (95% confidence) = Medium spike
- `z >= 2.5` (98.8% confidence) = High spike
- `z >= 3.0` (99.7% confidence) = Critical spike

**Advantages**:
- Statistical rigor (probability-based)
- Self-calibrating (adapts to each event's normal pattern)
- Filters noise (random variance doesn't trigger spikes)

**Implementation**: BigQuery calculates z-scores, Python service classifies confidence levels

## Architecture Decisions

### BigQuery for Aggregation, PostgreSQL for Spike Metadata

**Pattern**: Similar to Phase 14.3 event migration
- BigQuery: Time-series aggregation (fast windowed queries over 2.5B rows)
- PostgreSQL: Store detected spikes for quick lookup (Django ORM, trending queries, risk scoring)

**Flow**:
1. BigQuery aggregates daily mention counts with rolling stats
2. Python service fetches results, calculates z-scores
3. Spikes (z >= 2.0) stored in PostgreSQL `MentionSpike` model
4. Future phases query PostgreSQL for spike signals

### Spike Response Strategy

**Multi-stage response based on confidence**:

| Z-Score | Confidence | Action |
|---------|-----------|--------|
| < 2.0 | Low | Store baseline data only, no spike record |
| 2.0 - 2.5 | Medium | Store spike metadata (z-score, mention_count, baseline_avg) |
| 2.5 - 3.0 | High | Store spike + flag for risk score recalculation trigger (Phase 23) |
| >= 3.0 | Critical | Store spike + flag for immediate human review |

**Rationale**: Phases 23/24 will consume spike signals for risk scoring. Store all meaningful spikes (z >= 2.0) to build training data.

### Lookback Windows

**7-day rolling baseline**: Balance between:
- Too short (< 5 days): Overly sensitive to short-term variance
- Too long (> 14 days): Misses genuine escalations, stale baseline
- 7 days: Captures weekly patterns, responsive to trends

**30-day query window**: Fetch mentions for last 30 days to calculate 7-day windows for all recent events

## Performance Considerations

### Partition Filtering

**CRITICAL**: Always filter by `_PARTITIONTIME` to avoid full table scans

```sql
-- GOOD: Partition filter limits scan to 30 days
WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)

-- BAD: Scans entire 532GB table
WHERE MentionTimeDate >= 20251211
```

### Event ID Filtering

**Pattern**: Filter by Venezuela event IDs from BigQuery events table
- Join on `GLOBALEVENTID` after partition filtering
- Use subquery with Venezuela event ID list from events_partitioned
- Typical result: 50-200 Venezuela events per day × 30 days = 1500-6000 events to track

### Batch Processing

**Strategy**: Process in daily batches
- Query mentions for last 30 days once per day
- Calculate spikes for all tracked events in single query
- Store new spikes in PostgreSQL batch insert

**Why not real-time**: Mention counts stabilize 6-12 hours after event (articles propagate). Daily batch is sufficient for early warning (vs hourly churn).

## Data Model

### PostgreSQL Schema

```python
class MentionSpike(models.Model):
    """Detected mention count spike for a Venezuela event."""

    event_id = models.CharField(max_length=50, db_index=True)  # GLOBALEVENTID
    spike_date = models.DateField(db_index=True)
    mention_count = models.IntegerField()
    baseline_avg = models.FloatField()  # 7-day rolling average
    baseline_stddev = models.FloatField()  # 7-day rolling std dev
    z_score = models.FloatField(db_index=True)
    confidence_level = models.CharField(
        max_length=10,
        choices=[
            ('MEDIUM', 'Medium (z >= 2.0)'),
            ('HIGH', 'High (z >= 2.5)'),
            ('CRITICAL', 'Critical (z >= 3.0)')
        ]
    )
    detected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['event_id', 'spike_date']]
        indexes = [
            models.Index(fields=['spike_date', '-z_score']),
            models.Index(fields=['confidence_level', 'spike_date'])
        ]
```

**Rationale**:
- `event_id` links to BigQuery event (not ForeignKey, polyglot architecture)
- Indexes support: "Recent critical spikes" query, "Spikes for event X" query
- `unique_together` prevents duplicate spike records

## Standard Stack

### BigQuery Client (google-cloud-bigquery)
**Already in use** (Phase 14.1+)
- Parameterized queries for SQL injection prevention
- Window functions for rolling statistics
- Partition filtering for performance

### scipy.stats (z-score validation)
**Already in use** (Phase 15)
- Use `scipy.stats.zscore` for validation/testing
- Production: BigQuery calculates z-scores (faster at scale)
- Python: Classification logic only

### Django ORM
**Already in use** (all phases)
- MentionSpike model with custom indexes
- Bulk insert for batch spike storage

## Don't Hand-Roll

**❌ Custom statistical functions**: Use BigQuery window functions (STDDEV_POP, AVG)
**❌ Manual partition selection**: Use `_PARTITIONTIME >= TIMESTAMP_SUB()` pattern
**❌ Event-by-event queries**: Batch all events in single windowed query
**❌ Real-time streaming**: Daily batch sufficient for early warning use case

## Common Pitfalls

1. **Forgetting partition filter**: Full 532GB scan = expensive + slow. Always filter `_PARTITIONTIME`.

2. **Including current day in baseline**: Rolling window must exclude current day (`ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING`) to avoid inflating baseline with the spike you're trying to detect.

3. **Zero stddev edge case**: New events with flat mention counts have stddev=0. Handle division by zero (return z=0, not error).

4. **Confidence threshold tuning**: Start conservative (z >= 2.5) to avoid false positives. Phase 23 analysis will inform optimal thresholds.

5. **MentionTimeDate vs EventTimeDate**: Use `MentionTimeDate` (when article published) for spike detection, not `EventTimeDate` (when event occurred). Mentions spike when media picks up story.

## Code Examples

### BigQuery Service Pattern (from Phase 20)

```python
class GDELTMentionsService:
    def __init__(self):
        self.client = bigquery.Client(project=settings.GCP_PROJECT_ID)
        self.gdelt_project = "gdelt-bq"
        self.gdelt_dataset = "gdeltv2"

    def get_mention_stats(self, event_ids: List[str], lookback_days: int = 30):
        """Calculate daily mention counts with rolling stats for spike detection."""
        query = f"""
        WITH daily_counts AS (
          SELECT
            GLOBALEVENTID,
            DATE(PARSE_TIMESTAMP('%Y%m%d', CAST(MentionTimeDate AS STRING))) AS mention_date,
            COUNT(*) AS mention_count
          FROM `{self.gdelt_project}.{self.gdelt_dataset}.eventmentions_partitioned`
          WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @lookback_days DAY)
          AND GLOBALEVENTID IN UNNEST(@event_ids)
          GROUP BY GLOBALEVENTID, mention_date
        ),
        stats_calc AS (
          SELECT
            GLOBALEVENTID,
            mention_date,
            mention_count,
            AVG(mention_count) OVER (
              PARTITION BY GLOBALEVENTID
              ORDER BY mention_date
              ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
            ) AS rolling_avg,
            STDDEV_POP(mention_count) OVER (
              PARTITION BY GLOBALEVENTID
              ORDER BY mention_date
              ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
            ) AS rolling_stddev
          FROM daily_counts
        )
        SELECT
          GLOBALEVENTID AS event_id,
          mention_date,
          mention_count,
          rolling_avg,
          rolling_stddev
        FROM stats_calc
        WHERE mention_date >= CURRENT_DATE() - 7
        ORDER BY mention_date DESC, mention_count DESC
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('lookback_days', 'INT64', lookback_days),
                bigquery.ArrayQueryParameter('event_ids', 'INT64', [int(eid) for eid in event_ids])
            ]
        )

        results = self.client.query(query, job_config=job_config).result()
        return [dict(row) for row in results]
```

### Spike Detection Service

```python
def detect_spikes(mention_stats: List[dict]) -> List[dict]:
    """Calculate z-scores and classify spikes from mention statistics."""
    spikes = []

    for stat in mention_stats:
        # Skip if insufficient baseline data
        if stat['rolling_stddev'] is None or stat['rolling_avg'] is None:
            continue

        # Handle zero stddev edge case
        if stat['rolling_stddev'] == 0:
            z_score = 0.0
        else:
            z_score = (stat['mention_count'] - stat['rolling_avg']) / stat['rolling_stddev']

        # Classify confidence level
        if z_score >= 3.0:
            confidence = 'CRITICAL'
        elif z_score >= 2.5:
            confidence = 'HIGH'
        elif z_score >= 2.0:
            confidence = 'MEDIUM'
        else:
            continue  # No spike

        spikes.append({
            'event_id': stat['event_id'],
            'spike_date': stat['mention_date'],
            'mention_count': stat['mention_count'],
            'baseline_avg': stat['rolling_avg'],
            'baseline_stddev': stat['rolling_stddev'],
            'z_score': z_score,
            'confidence_level': confidence
        })

    return spikes
```

## Success Criteria

- GDELT Mentions table schema understood
- BigQuery window function patterns for rolling statistics validated
- Z-score spike detection methodology defined with confidence thresholds
- PostgreSQL data model designed for spike storage
- Partition filtering pattern established for 532GB table performance
- Batch processing strategy defined (daily, 30-day window)

---

*Discovery completed: 2026-01-10*
*Ready for phase planning*
