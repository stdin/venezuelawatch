# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-08)

**Core value:** Accurate risk intelligence that identifies sanctions changes, political disruptions, and trade opportunities before they impact investment decisions.
**Current focus:** Phase 4 — Risk Intelligence Core

## Current Position

Phase: 4 of 7 (Risk Intelligence Core)
Plan: 3 of TBD in current phase
Status: In progress
Last activity: 2026-01-08 — Completed 04-03-PLAN.md (Event Severity Classification)

Progress: ███████░░░ 68%

## Performance Metrics

**Velocity:**
- Total plans completed: 15
- Average duration: 18 min
- Total execution time: 4.54 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 4 | 56 min | 14 min |
| 2 | 4 | 24 min | 6 min |
| 3 | 4 | 195 min | 49 min |
| 4 | 3 | 19 min | 6 min |

**Recent Trend:**
- Last 5 plans: 50min, 9min, 5min, 5min
- Trend: Very fast (leveraging Phase 3/4 infrastructure)

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Phase 1: django-ninja for REST API (auto OpenAPI docs, type safety)
- Phase 1: Router pattern for API organization (scalable by domain)
- Phase 1: CORS for Vite dev server at localhost:5173
- Phase 1: Vite proxy to Django backend for seamless API calls
- Phase 1: Typed API client pattern with TypeScript interfaces
- Phase 1: TimescaleDB hypertables for time-series event data
- Phase 1: Event model with JSONField for flexible content
- Phase 1: GCP Cloud SQL for production database (db-custom-1-3840)
- Phase 1: Cloud Storage for static files with public read access
- Phase 1: Secret Manager for secure credential storage
- Phase 2: django-allauth headless for SPA authentication (not dj-rest-auth)
- Phase 2: Custom User model NOW to avoid migration pain for future teams
- Phase 2: JWT in httpOnly cookies via djangorestframework-simplejwt
- Phase 2: CORS_ALLOW_CREDENTIALS=True for cross-origin cookie authentication
- Phase 2: Email verification set to optional for Phase 2 (can be enabled later)
- Phase 2: PostgreSQL with TimescaleDB required for ArrayField in Event model
- Phase 2: Email as primary authentication method (username auto-generated)
- Phase 2: 15-minute access token, 7-day refresh token for security/UX balance
- Phase 2: Console email backend for development
- Phase 2: Email verification disabled for development (ACCOUNT_EMAIL_VERIFICATION='none')
- Phase 2: Session-based authentication via django_auth (not JWT tokens)
- Phase 3: Celery + Redis for async task queue (don't hand-roll)
- Phase 3: django-celery-results for ORM result backend in PostgreSQL
- Phase 3: GCP Secret Manager with environment variable fallback for API credentials
- Phase 3: Tenacity for exponential backoff retry strategy (not custom)
- Phase 3: Token bucket RateLimiter for API rate limit compliance
- Phase 3: GDELT 15-minute polling for real-time event detection
- Phase 3: ReliefWeb daily polling for humanitarian crisis updates
- Phase 3: Celery Beat for local development, Cloud Scheduler for production
- Phase 3: HTTP trigger endpoints for Cloud Scheduler integration
- Phase 3: Deduplication by URL/ID using JSONField queries
- Phase 3: FRED daily batch ingestion for 6 key Venezuela economic series
- Phase 3: Parallel series fetching using Celery group for performance
- Phase 3: Threshold-based economic event generation (oil > 10%, inflation > 5%)
- Phase 3: UN Comtrade monthly ingestion for trade flows (oil, food, medicine, machinery)
- Phase 3: World Bank quarterly ingestion for 10 development indicators
- Phase 3: Backfill management commands for historical data ingestion
- Phase 4: OFAC SDN API for sanctions screening (free, no authentication)
- Phase 4: Levenshtein distance for fuzzy name matching (threshold 0.6-0.7)
- Phase 4: Binary sanctions scoring (0.0=clean, 1.0=sanctioned)
- Phase 4: 7-day rolling window for daily sanctions refresh (4 AM UTC)
- Phase 4: OpenSanctions premium API optional upgrade path
- Phase 4: Weighted aggregation with strict normalization (weights sum to 1.0)
- Phase 4: Event-type-specific weight distributions for risk scoring
- Phase 4: Sanctions dimension highest weight (0.30-0.40) as binary flag
- Phase 4: Risk score scale changed from 0-1 to 0-100 for dashboard
- Phase 4: Supply chain risk detection from LLM theme keywords
- Phase 4: NCISS-style severity classification with weighted criteria (scope, duration, reversibility, economic_impact)
- Phase 4: Severity independent of risk score (severity=impact, risk=probability×impact)
- Phase 4: LLM for context-aware severity criteria extraction (not keyword matching)
- Phase 4: SEV1-5 string choices for self-documenting severity levels
- Phase 4: Fallback to medium severity (0.5) on LLM errors for resilience

### Deferred Issues

None yet.

### Blockers/Concerns

**Phase 1 Manual Steps Required:**
- TimescaleDB extension setup (requires psql client)
- Django migrations application to Cloud SQL
- See backend/README.md for detailed instructions

## Session Continuity

Last session: 2026-01-08
Stopped at: Completed 04-03-PLAN.md (Event Severity Classification)
Resume file: None

Note: Phase 4 intelligence core nearly complete - severity classification complements risk scoring
