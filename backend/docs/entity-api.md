# Entity Watch API Documentation

**Phase 6: Entity Watch**
**Last Updated:** 2026-01-09

## Overview

The Entity Watch API provides endpoints for tracking and analyzing entities (people, organizations, governments, locations) extracted from VenezuelaWatch event data. It powers the Entity Watch dashboard with trending leaderboards, entity profiles, and mention timelines.

## Base URL

```
http://localhost:8000/api/entities
```

Production: `https://venezuelawatch.com/api/entities`

## Authentication

All endpoints require authentication (inherited from django-ninja API configuration).

## Endpoints

### 1. GET /trending - Trending Entities Leaderboard

Get trending entities ranked by selected metric with time-decay scoring.

**Endpoint:** `GET /api/entities/trending`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `metric` | string | `mentions` | Ranking metric: `mentions`, `risk`, or `sanctions` |
| `limit` | integer | `50` | Maximum entities to return (1-100) |
| `entity_type` | string | `null` | Filter by type: `PERSON`, `ORGANIZATION`, `GOVERNMENT`, `LOCATION` |

**Metrics Explained:**

- **mentions**: Most mentioned entities using exponential time-decay (7-day half-life). Real-time scoring from Redis.
- **risk**: Highest risk entities based on average risk_score from linked events.
- **sanctions**: Entities with most sanctions matches (compliance focus).

**Response Schema:**

```json
[
  {
    "id": "uuid",
    "canonical_name": "Venezuela",
    "entity_type": "LOCATION",
    "mention_count": 42,
    "first_seen": "2026-01-01T00:00:00Z",
    "last_seen": "2026-01-09T06:25:00Z",
    "trending_score": 0.963,
    "trending_rank": 1
  }
]
```

**Example Requests:**

```bash
# Top 10 trending entities by mentions
curl "http://localhost:8000/api/entities/trending?metric=mentions&limit=10"

# Top 20 highest risk entities
curl "http://localhost:8000/api/entities/trending?metric=risk&limit=20"

# Trending organizations only
curl "http://localhost:8000/api/entities/trending?entity_type=ORGANIZATION&limit=15"
```

**Example Response:**

```json
[
  {
    "id": "6c13323a-1cf8-4fb8-99a3-83caa797a071",
    "canonical_name": "Venezuela",
    "entity_type": "LOCATION",
    "mention_count": 1,
    "first_seen": "2026-01-09T06:25:21.755Z",
    "last_seen": "2026-01-09T06:25:22.124Z",
    "trending_score": 0.9633792966815071,
    "trending_rank": 1
  },
  {
    "id": "b8f82ecd-5d4d-485f-94be-5cd5c8ff81b6",
    "canonical_name": "PDVSA",
    "entity_type": "ORGANIZATION",
    "mention_count": 1,
    "first_seen": "2026-01-09T06:25:19.957Z",
    "last_seen": "2026-01-09T06:25:20.326Z",
    "trending_score": 0.9338880946159187,
    "trending_rank": 2
  }
]
```

---

### 2. GET /{entity_id} - Entity Profile

Get detailed entity profile with sanctions status, risk score, and recent events.

**Endpoint:** `GET /api/entities/{entity_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_id` | UUID | Entity identifier |

**Response Schema:**

```json
{
  "id": "uuid",
  "canonical_name": "Venezuela",
  "entity_type": "LOCATION",
  "mention_count": 1,
  "first_seen": "2026-01-09T06:25:21.755Z",
  "last_seen": "2026-01-09T06:25:22.124Z",
  "trending_score": null,
  "trending_rank": 1,
  "aliases": ["República Bolivariana de Venezuela"],
  "metadata": {"location_type": "country"},
  "sanctions_status": false,
  "risk_score": 43.52,
  "recent_events": [
    {
      "id": "event-uuid",
      "title": "WTI Crude Oil Prices: $75.32",
      "source": "FRED",
      "event_type": "ECONOMIC",
      "risk_score": 43.52,
      "severity": "SEV2_HIGH",
      "timestamp": "2026-01-09T03:33:19.538328+00:00"
    }
  ]
}
```

**Example Request:**

```bash
curl "http://localhost:8000/api/entities/6c13323a-1cf8-4fb8-99a3-83caa797a071"
```

**Field Descriptions:**

- **aliases**: Known name variations from fuzzy matching
- **metadata**: Additional context extracted by LLM (roles, descriptions)
- **sanctions_status**: `true` if entity has any sanctions matches
- **risk_score**: Average risk score across all events mentioning this entity
- **recent_events**: Last 5 events mentioning the entity (sorted by timestamp DESC)

---

### 3. GET /{entity_id}/timeline - Entity Mention Timeline

Get chronological timeline of entity mentions over specified time range.

**Endpoint:** `GET /api/entities/{entity_id}/timeline`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_id` | UUID | Entity identifier |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | integer | `30` | Lookback period in days (1-365) |

**Response Schema:**

```json
{
  "entity_id": "uuid",
  "canonical_name": "Venezuela",
  "total_mentions": 1,
  "mentions": [
    {
      "id": "mention-uuid",
      "raw_name": "Venezuela",
      "match_score": 1.0,
      "relevance": 0.98,
      "mentioned_at": "2026-01-09T03:33:19.538Z",
      "event_summary": {
        "id": "event-uuid",
        "title": "WTI Crude Oil Prices: $75.32",
        "source": "FRED",
        "event_type": "ECONOMIC",
        "risk_score": 43.52,
        "severity": "SEV2_HIGH",
        "timestamp": "2026-01-09T03:33:19.538328+00:00"
      }
    }
  ],
  "time_range": {
    "start": "2025-12-10T06:32:36.363494+00:00",
    "end": "2026-01-09T06:32:36.437328+00:00"
  }
}
```

**Example Requests:**

```bash
# Last 30 days (default)
curl "http://localhost:8000/api/entities/6c13323a-1cf8-4fb8-99a3-83caa797a071/timeline"

# Last 7 days
curl "http://localhost:8000/api/entities/6c13323a-1cf8-4fb8-99a3-83caa797a071/timeline?days=7"
```

**Field Descriptions:**

- **raw_name**: Exact entity name as extracted from event
- **match_score**: Fuzzy match confidence (0.0-1.0) from RapidFuzz JaroWinkler
- **relevance**: LLM relevance score for entity in event context
- **mentioned_at**: Denormalized timestamp for efficient trending queries

---

## Performance Notes

### Redis Caching

- **Trending scores** stored in Redis Sorted Sets for O(log N) operations
- **Time-decay** applied with 7-day half-life (score = weight × e^(-age_hours / 168))
- **Sync frequency**: Redis synced to PostgreSQL every 15 minutes (Celery Beat task)

### Database Optimization

- **Prefetch relationships**: `select_related('event')` on EntityMention queries
- **Bulk fetching**: Trending endpoint fetches all entities in single query
- **Indexed fields**: `mention_count`, `last_seen`, `mentioned_at` for fast sorting

### Query Performance Benchmarks

- **Trending leaderboard**: ~10ms (Redis)
- **Entity profile**: ~50ms (1 entity + 5 events)
- **Timeline (30 days)**: ~100ms (avg 20 mentions)

---

## Frontend Integration Guide

### Phase 6 Dashboard Integration

**1. Trending Leaderboard Component**

```typescript
// Fetch trending entities with metric toggle
const fetchTrending = async (metric: 'mentions' | 'risk' | 'sanctions') => {
  const response = await fetch(
    `/api/entities/trending?metric=${metric}&limit=50`
  );
  return response.json();
};

// Example: Display top 10 by mentions
const entities = await fetchTrending('mentions');
// Render EntityCard for each entity
```

**2. Entity Profile Card Component**

```typescript
// Fetch entity profile
const fetchProfile = async (entityId: string) => {
  const response = await fetch(`/api/entities/${entityId}`);
  return response.json();
};

// Display: name, type, sanctions badge, risk score, recent events
```

**3. Entity Timeline Component**

```typescript
// Fetch mention timeline
const fetchTimeline = async (entityId: string, days: number = 30) => {
  const response = await fetch(
    `/api/entities/${entityId}/timeline?days=${days}`
  );
  return response.json();
};

// Render chronological mention list with event summaries
```

---

## Error Responses

### 404 Not Found

```json
{
  "detail": "Not Found"
}
```

Returned when entity_id does not exist.

### 400 Bad Request

```json
{
  "detail": "Invalid metric: invalid. Must be 'mentions', 'risk', or 'sanctions'"
}
```

Returned when invalid query parameters provided.

---

## OpenAPI Documentation

Interactive API documentation available at:

- **Swagger UI**: http://localhost:8000/api/docs
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

All Entity Watch endpoints tagged as "Entity Watch" in OpenAPI spec.

---

## Related Documentation

- **Risk Intelligence API**: `./risk-intelligence-api.md`
- **Entity Extraction Pipeline**: `../data_pipeline/services/entity_service.py`
- **Trending Service**: `../data_pipeline/services/trending_service.py`
- **Entity Models**: `../core/models.py` (Entity, EntityMention)

---

## Future Enhancements

**Phase 7+ Roadmap:**

- [ ] Entity relationship graphs (Neo4j integration)
- [ ] Historical trending charts (time-series data)
- [ ] Entity search endpoint (full-text search)
- [ ] User-defined entity watchlists
- [ ] Real-time WebSocket updates for trending changes

---

**Last Updated:** 2026-01-09
**Phase:** 6 (Entity Watch)
**Status:** Production Ready
