# Risk Intelligence API Documentation

Phase 4 Risk Intelligence Core provides multi-dimensional risk analysis for Venezuela events.

## Features

### 1. Multi-Dimensional Risk Scoring (0-100)

Risk scores combine 5 dimensions:
- **LLM Base Risk** (25% weight): Claude's risk assessment from event content
- **Sanctions** (30% weight): Binary flag if event mentions sanctioned entities
- **Sentiment** (20% weight): Negative sentiment = higher risk
- **Urgency** (15% weight): Immediate > High > Medium > Low
- **Supply Chain** (10% weight): Keywords indicating trade/oil/export disruption

Weights vary by event type:
- Political events emphasize sanctions (40%)
- Trade events emphasize supply chain (25%)

### 2. Severity Classification (SEV 1-5)

NCISS-style multi-criteria assessment:
- **SEV1 - Critical**: International scope, permanent/long-term, irreversible, major economic impact
- **SEV2 - High**: National scope, months duration, difficult to reverse, significant impact
- **SEV3 - Medium**: National scope, weeks duration, moderate reversibility/impact
- **SEV4 - Low**: Local scope, days duration, easily reversed, minimal impact
- **SEV5 - Minimal**: Local scope, hours duration, negligible impact

Severity = impact magnitude (independent of probability)
Risk = probability × impact (composite score)

### 3. Sanctions Screening

- Automatic fuzzy matching against OpenSanctions/OFAC lists
- Matches threshold 0.7+ flagged as sanctioned
- Daily refresh to catch new sanctions additions
- Tracks: entity name, type (person/organization), sanctions list, match confidence

## API Endpoints

### GET /api/risk/events

Filter and retrieve events with risk intelligence.

**Query Parameters:**
- `severity` (string): Comma-separated SEV levels (e.g., "SEV1_CRITICAL,SEV2_HIGH")
- `min_risk_score` (float): Minimum risk score (0-100)
- `max_risk_score` (float): Maximum risk score (0-100)
- `has_sanctions` (boolean): Filter to events with sanctions matches
- `event_type` (string): Filter by event type
- `source` (string): Filter by data source
- `days_back` (int): Lookback period in days (default: 30)
- `limit` (int): Page size (default: 100, max: 1000)
- `offset` (int): Pagination offset (default: 0)

**Response:** Array of RiskIntelligenceEventSchema

**Example:**
```bash
# Get high-severity events with sanctions in last 7 days
curl "http://localhost:8000/api/risk/events?severity=SEV1_CRITICAL,SEV2_HIGH&has_sanctions=true&days_back=7"

# Get high-risk political events
curl "http://localhost:8000/api/risk/events?min_risk_score=70&event_type=POLITICAL"

# Get recent economic events sorted by risk
curl "http://localhost:8000/api/risk/events?event_type=ECONOMIC&days_back=14&limit=50"
```

**Response Schema:**
```json
[
  {
    "id": "uuid",
    "source": "GDELT",
    "event_type": "POLITICAL",
    "timestamp": "2026-01-08T12:00:00Z",
    "title": "Event title",
    "summary": "LLM-generated summary",
    "risk_score": 85.5,
    "severity": "SEV2_HIGH",
    "urgency": "high",
    "sentiment": -0.6,
    "themes": ["political_instability", "sanctions"],
    "sanctions_matches": [
      {
        "entity_name": "Example Entity",
        "entity_type": "organization",
        "sanctions_list": "OFAC-SDN",
        "match_score": 0.92
      }
    ],
    "entities": {
      "people": ["Person Name"],
      "organizations": ["Org Name"],
      "locations": ["Location"]
    }
  }
]
```

### GET /api/risk/sanctions-summary

Get aggregate statistics on sanctions matches.

**Query Parameters:**
- `days_back` (int): Lookback period (default: 30)

**Response:**
```json
{
  "total_events_with_sanctions": 15,
  "unique_sanctioned_entities": 8,
  "by_entity_type": {"person": 5, "organization": 3},
  "by_sanctions_list": {"OFAC-SDN": 6, "UN-1267": 2}
}
```

**Example:**
```bash
# Get sanctions summary for last 90 days
curl "http://localhost:8000/api/risk/sanctions-summary?days_back=90"
```

## Management Commands

### Recalculate Risk Scores

Update risk scores for events after model changes or backfilling.

```bash
# Recalculate last 30 days (default)
python manage.py recalculate_risk

# Recalculate last 90 days
python manage.py recalculate_risk --days 90

# Recalculate ALL events
python manage.py recalculate_risk --all
```

**Memory efficient:**
- Processes events in 100-event chunks using iterator()
- Updates only risk_score field, not entire model
- Shows progress every 100 events

### Classify Severity

Classify event severity using NCISS-style impact assessment.

```bash
# Classify events without severity (last 30 days)
python manage.py classify_all_severity

# Classify last 90 days
python manage.py classify_all_severity --days 90

# Reclassify events that already have severity
python manage.py classify_all_severity --force

# Classify ALL events
python manage.py classify_all_severity --all
```

**Options:**
- `--days N`: Process events from last N days
- `--all`: Process all events (ignores --days)
- `--force`: Reclassify events with existing severity (default: skip)

### View Statistics

Display comprehensive risk intelligence statistics.

```bash
python manage.py intelligence_stats
```

**Output includes:**
- Overall coverage (% events with risk/severity/sanctions)
- Severity distribution (SEV1-5 breakdown)
- Risk score distribution (avg, min, max, stddev, percentiles)
- Sanctions statistics (total matches, unique entities, by type/list)
- Source-level data quality metrics

**Example output:**
```
============================================================
Risk Intelligence Statistics
============================================================
Overall Coverage
Total events: 4,523
Events with risk scores: 4,201 (92.9%)
Events with severity: 4,198 (92.8%)
Events with sanctions matches: 47 (1.0%)

------------------------------------------------------------
Severity Distribution
------------------------------------------------------------
SEV1_CRITICAL        23 events (  0.5%)
SEV2_HIGH           342 events (  8.1%)
SEV3_MEDIUM       2,104 events ( 50.1%)
SEV4_LOW          1,523 events ( 36.3%)
SEV5_MINIMAL        206 events (  4.9%)

------------------------------------------------------------
Risk Score Distribution
------------------------------------------------------------
Average:        42.15
Min:            5.20
Max:            94.80
Std Deviation:  18.43

Risk Score Ranges:
  Critical (75-100):     156 events
  High (50-74):        1,204 events
  Medium (25-49):      2,341 events
  Low (0-24):            500 events
```

## Dashboard Integration (Phase 5)

### Recommended Filters

1. **Crisis Dashboard**: severity=SEV1_CRITICAL,SEV2_HIGH + has_sanctions=true
2. **High Risk Feed**: min_risk_score=70 + days_back=7
3. **Sanctions Monitor**: has_sanctions=true + all event types
4. **Supply Chain Risk**: event_type=TRADE + min_risk_score=50

### Performance Notes

- `risk_score` and `severity` are indexed for fast filtering
- Use pagination (limit/offset) for large result sets
- Prefetch sanctions_matches included automatically to avoid N+1 queries
- Database-level filtering (ORM) ensures scalability to 1000s of events

### Example Dashboard Queries

**High-Priority Event Feed:**
```javascript
// Fetch critical/high severity events with sanctions in last 7 days
const response = await fetch('/api/risk/events?' + new URLSearchParams({
  severity: 'SEV1_CRITICAL,SEV2_HIGH',
  has_sanctions: true,
  days_back: 7,
  limit: 50
}));
const events = await response.json();
```

**Risk Score Chart Data:**
```javascript
// Fetch all events for risk score distribution chart
const response = await fetch('/api/risk/events?' + new URLSearchParams({
  days_back: 30,
  limit: 1000
}));
const events = await response.json();

// Group by risk score ranges for chart
const ranges = {
  critical: events.filter(e => e.risk_score >= 75).length,
  high: events.filter(e => e.risk_score >= 50 && e.risk_score < 75).length,
  medium: events.filter(e => e.risk_score >= 25 && e.risk_score < 50).length,
  low: events.filter(e => e.risk_score < 25).length
};
```

**Sanctions Exposure Widget:**
```javascript
// Fetch sanctions summary for last 30 days
const response = await fetch('/api/risk/sanctions-summary?days_back=30');
const summary = await response.json();

// Display total events with sanctions, unique entities, breakdowns
console.log(`${summary.total_events_with_sanctions} events flagged`);
console.log(`${summary.unique_sanctioned_entities} unique entities`);
```

## OpenAPI Documentation

Interactive API documentation is automatically generated and available at:

**Development:** http://localhost:8000/api/docs

The OpenAPI spec includes:
- Full request/response schemas
- Parameter descriptions and validation rules
- Example requests with curl commands
- Response status codes and error messages
- Try-it-out functionality for testing endpoints

## Risk Score Interpretation Guide

**Score Ranges:**
- **75-100 (Critical)**: Immediate attention required, potential major impact on investments
- **50-74 (High)**: Monitor closely, significant risk factors present
- **25-49 (Medium)**: Moderate risk, situational awareness needed
- **0-24 (Low)**: Informational, minimal direct investment impact

**Severity vs Risk:**
- **Severity** = Impact magnitude (how bad if it happens)
- **Risk Score** = Probability × Impact (how likely and how bad)

Example: A SEV1_CRITICAL event might have low risk score if probability is low.

## Data Freshness

- **Risk scores**: Updated on event ingestion and via manual recalculation
- **Severity**: Classified on event ingestion and via manual classification
- **Sanctions**: Refreshed daily at 4 AM UTC with 7-day rolling window
- **API data**: Real-time from database, no caching layer

## Future Enhancements

Tracked in .planning/ISSUES.md:
- Real-time sanctions alerts via webhooks
- Custom risk score weights per user/organization
- Historical risk score trending
- Sanctions entity detail pages with aliases/programs
- Export to CSV/JSON for offline analysis
