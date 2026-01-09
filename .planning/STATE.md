# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-08)

**Core value:** Accurate risk intelligence that identifies sanctions changes, political disruptions, and trade opportunities before they impact investment decisions.
**Current focus:** v1.1 — UI/UX Overhaul

## Current Position

Phase: 8 of 13 (Design System Foundation)
Plan: Not started
Status: Ready to plan
Last activity: 2026-01-09 — Milestone v1.1 UI/UX Overhaul created

Progress: ░░░░░░░░░░ 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 24
- Average duration: 13 min
- Total execution time: 5.6 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 4 | 56 min | 14 min |
| 2 | 4 | 24 min | 6 min |
| 3 | 4 | 195 min | 49 min |
| 4 | 4 | 26 min | 7 min |
| 6 | 4 | 23 min | 6 min |
| 7 | 4 | 36 min | 9 min |

**Recent Trend:**
- Last 5 plans: 8min, 2min, 15min, 8min, 11min
- Trend: Very fast (mature infrastructure)

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
- Phase 6: RapidFuzz JaroWinkler for fuzzy name matching (10x faster than FuzzyWuzzy)
- Phase 6: Jaro-Winkler threshold 0.85 for real-time entity deduplication (0.90 for batch)
- Phase 6: Unicode NFC normalization to handle accent variations in entity names
- Phase 6: Denormalized mentioned_at in EntityMention for efficient trending queries
- Phase 6: Exponential time-decay trending with 7-day half-life (168 hours)
- Phase 6: Redis Sorted Sets for O(log N) trending operations (not PostgreSQL materialized views)
- Phase 6: Three trending metrics: mentions (time-decay), risk (avg score), sanctions (count)
- Phase 6: timezone.now() not datetime.utcnow() for timezone-aware datetime calculations
- Phase 6: Bulk Entity fetch in trending queries to avoid N+1 problem
- Phase 6: Metric toggle pattern for trending (mentions/risk/sanctions in single endpoint)
- Phase 6: Profile aggregation on-the-fly (no denormalization for sanctions/risk)
- Phase 6: OpenAPI automatic documentation for entity endpoints
- Phase 6: Split-view layout (40% leaderboard, 60% profile) for entity dashboard
- Phase 6: Metric toggle pattern with radio-style buttons for UI controls
- Phase 6: Entity type badge colors (Person=blue, Organization=purple, Government=red, Location=green)
- Phase 6: React Router for SPA navigation with tab-style UI
- Phase 6: Virtualized leaderboard using @tanstack/react-virtual for performance
- Phase 7: Anthropic Claude (claude-3-5-sonnet-20241022) for LLM provider
- Phase 7: Server-Sent Events (SSE) for streaming responses (not WebSockets)
- Phase 7: Tool calling loop: stream text → detect tool_use → execute → add results → re-stream
- Phase 7: Four tools for data access: search_events, get_entity_profile, get_trending_entities, analyze_risk_trends
- Phase 7: Fuzzy entity matching in get_entity_profile using RapidFuzz (threshold 0.75)
- Phase 7: Tool results passed back to Claude as JSON in conversation context
- Phase 7: SSE format: 'data: {json}\n\n' for each chunk with type field (content, tool_use, done, error)
- Phase 7: useExternalStoreRuntime pattern for custom Django backend (not Vercel AI SDK)
- Phase 7: fetch() with ReadableStream for SSE parsing (not EventSource API)
- Phase 7: Accumulate text chunks in single assistant message (not separate messages)
- Phase 7: ChatProvider wraps AssistantRuntimeProvider with custom runtime
- Phase 7: makeAssistantToolUI pattern for custom tool rendering tied to backend tool names
- Phase 7: Expand-in-place pattern (not navigation) for preview card interactions
- Phase 7: Compact inline display optimized for chat context (smaller than dashboard components)
- Phase 7: Visual indicators: risk score colors, severity badges, entity type badges, trend arrows
- Phase 7: Sanctions alert badge with pulse animation for high visibility
- Phase 7: Perplexity-style center-focused layout (max-width: 44rem) for research-oriented feel
- Phase 7: Suggestion chips on welcome screen with example queries for user guidance
- Phase 7: Chat as separate /chat route (peer to Dashboard and Entities)
- Phase 7: ThreadPrimitive components from assistant-ui for message rendering

### Deferred Issues

None yet.

### Blockers/Concerns

**Phase 1 Manual Steps Required:**
- TimescaleDB extension setup (requires psql client)
- Django migrations application to Cloud SQL
- See backend/README.md for detailed instructions

### Roadmap Evolution

- v1.0 MVP shipped 2026-01-09: Complete SaaS platform with data pipeline, risk intelligence, dashboard, entity tracking, and AI chat (Phases 1-7)
- v1.1 UI/UX Overhaul created 2026-01-09: Comprehensive UI/UX redesign with design system, component library, and responsive design (Phases 8-13)

## Session Continuity

Last session: 2026-01-09
Stopped at: Milestone v1.1 UI/UX Overhaul created
Resume file: None

Note: v1.0 MVP shipped (7 phases complete). Starting v1.1 UI/UX Overhaul milestone (6 phases: design system, component library, page redesigns, responsive & accessibility).
