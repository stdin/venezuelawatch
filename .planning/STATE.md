# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-10)

**Core value:** Accurate risk intelligence that identifies sanctions changes, political disruptions, and trade opportunities before they impact investment decisions.
**Current focus:** v1.1 shipped — Ready for production deployment or v1.2 planning

## Current Position

Phase: 18 of 18 (GCP-Native Pipeline Migration)
Plan: 1 of 4 in current phase
Status: In progress
Last activity: 2026-01-10 - Completed 18-01-PLAN.md

Progress: ████████████████████████████░ 98%

## Performance Metrics

**Velocity:**
- Total plans completed: 54
- Average duration: 10 min
- Total execution time: 10.2 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 4 | 56 min | 14 min |
| 2 | 4 | 24 min | 6 min |
| 3 | 4 | 195 min | 49 min |
| 4 | 4 | 26 min | 7 min |
| 6 | 4 | 23 min | 6 min |
| 7 | 4 | 36 min | 9 min |
| 8 | 2 | 29 min | 15 min |
| 9 | 2 | 53 min | 27 min |
| 10 | 4 | 8 min | 2 min |
| 11 | 3 | 5 min | 2 min |
| 12 | 2 | 47 min | 24 min |
| 13 | 4 | 26 min | 7 min |
| 14 | 4 | 22 min | 6 min |
| 14.1 | 4 | 39 min | 10 min |
| 14.2 | 1 | 10 min | 10 min |
| 14.3 | 1 | 9 min | 9 min |
| 15 | 1 | 4 min | 4 min |
| 16 | 1 | 8 min | 8 min |
| 18 | 1 | 10 min | 10 min |

**Recent Trend:**
- Last 5 plans: 10min, 9min, 4min, 8min, 10min
- Trend: Fast (frontend visualization components)

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
- Phase 8: 1.25 modular ratio for typography scale (balanced for data scanning)
- Phase 8: OKLCH color space with hex fallbacks for progressive enhancement
- Phase 8: Risk-first semantic color naming (--color-risk-high) not visual naming
- Phase 8: Layered token system: primitives → semantic tokens for theme flexibility
- Phase 8: System font stacks for zero-latency rendering
- Phase 8: Storybook 10 API changes (imports from 'storybook/*' not '@storybook/*')
- Phase 8: preview.tsx instead of preview.ts for JSX support in decorators
- Phase 8: Border radius scale reduced by ~33% (md: 6px → 4px) for subtler rounding
- Phase 8: Theme decorator with useEffect for data-theme attribute switching
- Phase 8: Design token documentation pattern with visual examples and code tokens
- Phase 9: Mantine UI (28.1k stars, 500k+ weekly) for production-ready component library
- Phase 9: src/components/ui/ directory for base component library (separate from feature components)
- Phase 9: Mantine components wrapped with consistent API for project conventions
- Phase 9: MantineProvider in Storybook for proper CSS injection and theming
- Phase 9: Professional default styling with zero configuration required
- Phase 9: 120+ Mantine components available for future feature development
- Phase 10: Mantine Grid responsive layout pattern: span={{ base: 12, md: X }} for breakpoints
- Phase 10: Container fluid for full-width dashboard layouts
- Phase 10: React Query (@tanstack/react-query) for data fetching/caching in dashboards
- Phase 10: date-fns for date manipulation in time-series filtering
- Phase 10: Mantine Badge colors for risk scores: >70=red, 50-70=orange, <50=blue
- Phase 10: Mantine Badge colors for severity: SEV1=red, SEV2=orange, SEV3=yellow, SEV4=blue, SEV5=gray
- Phase 10: Skeleton loading pattern with 5 cards for perceived performance
- Phase 10: EventList component owns all loading states for separation of concerns
- Phase 10: RiskTrendChart as separate component for modularity and reusability
- Phase 10: Recharts ResponsiveContainer with width="100%" height={300} for fluid layouts
- Phase 10: Design token colors in charts (var(--color-risk-high), var(--mantine-color-blue-filled))
- Phase 10: Mantine Card wrapper pattern for all chart containers
- Phase 10: MultiSelect for multi-option filters (severity levels with searchable/clearable)
- Phase 10: NumberInput for numeric ranges (risk score min/max with validation)
- Phase 10: Select with clearable for single-choice filters (event type, time range)
- Phase 10: Mantine form component pattern across all filter controls
- Phase 11: Grid.Col span={{ base: 12, md: 5 }} for 40% width on desktop split-view
- Phase 11: SegmentedControl fullWidth for professional metric toggle UI
- Phase 11: Badge size="lg" circle for rank numbers in lists
- Phase 11: Entity type Badge colors: blue (Person), grape (Org), red (Gov), green (Location)
- Phase 11: Skeleton loading in component (not parent) for better encapsulation
- Phase 11: Loading prop pattern: loading && entities.length === 0 for initial fetch only
- Phase 11: MantineProvider at app root (main.tsx) required for all Mantine components
- Phase 11: Mantine Alert color='red' variant='filled' for sanctions warnings (high visibility)
- Phase 11: Profile sections in separate Cards (Overview, Risk Intelligence, Aliases, Events)
- Phase 11: React hooks must be called before any early returns (Rules of Hooks)
- Phase 12: Chat tool cards use compact Mantine sizing (size='sm' padding='xs') vs full Dashboard components
- Phase 12: Adaptive density pattern for chat: single items compact, lists use Stack gap='xs' spacing
- Phase 12: Badge colors consistent across chat/dashboard/entities for visual cohesion
- Phase 12: makeAssistantToolUI components must be rendered in JSX tree (not just imported) to register with AssistantRuntimeProvider
- Phase 12: Backend sends tool_result SSE chunks with structured data for tool UI rendering (hybrid: Claude commentary + visual cards)
- Phase 12: Real-time tool result updates during streaming (not after completion) for responsive UI
- Phase 13: Custom Mantine breakpoints in em units (xs: 36em, sm: 48em, md: 62em, lg: 75em, xl: 88em) for mobile-first responsive design
- Phase 13: Storybook a11y addon test mode set to 'error' to fail fast on accessibility violations
- Phase 13: Skip link pattern for keyboard navigation (positioned absolutely, visible on focus)
- Phase 13: ARIA landmarks with semantic HTML (nav with aria-label, main with role)
- Phase 13: TrendsPanel collapsed by default on mobile with expand button (not hidden entirely)
- Phase 13: Mantine's built-in focus styles used (meet WCAG 2.1 AA without custom CSS)
- Phase 13: role='feed' for EventList (not role='list') for better screen reader navigation of dynamic content
- Phase 13: ARIA live regions: assertive for errors, polite for loading/status announcements
- Phase 13: Entities mobile uses fullscreen modal for profile (not stacked below leaderboard)
- Phase 13: Chat composer 44px min-height and 16px font-size for WCAG touch targets and iOS zoom prevention
- Phase 13: Entity leaderboard uses role='feed' (not role='list') for dynamic content
- Phase 13: Arrow key navigation with querySelector and data-entity-index for focus management in virtualized lists
- Phase 14: BigQuery Federated Query over Dataflow for simplicity (no separate pipeline infrastructure)
- Phase 14: Daily 2 AM UTC ETL schedule for low-traffic period completion before business hours
- Phase 14: 90-day rolling window for sufficient training history without excessive storage costs
- Phase 14: Daily aggregation (vs hourly) aligns with Vertex AI recommended granularity
- Phase 14: DAY partitioning on mentioned_at for query performance and cost optimization
- Phase 14: TiDE model auto-selected by Vertex AI AutoML (10x faster training than previous models)
- Phase 14: 30-day forecast horizon for entity risk trajectory prediction
- Phase 14: n1-standard-4 machine type for TiDE inference (no GPU needed, cost-efficient)
- Phase 14: Autoscaling 1-10 replicas balances availability with cost (~$100/month minimum)
- Phase 14: 80/10/10 train/val/test split for robust forecasting model evaluation
- Phase 14: Training deferred until 60+ days historical data available in PostgreSQL
- Phase 14.1: Polyglot persistence architecture (PostgreSQL for transactional, BigQuery for time-series)
- Phase 14.1: STRING IDs in BigQuery (no AUTO_INCREMENT, generate UUIDs in Python)
- Phase 14.1: Streaming inserts for BigQuery (simpler than batch load jobs)
- Phase 14.1: GCP Application Default Credentials (ADC) for authentication
- Phase 14.1: Dataclasses with to_bigquery_row() for type-safe row generation
- Phase 14.1: Parameterized queries in BigQuery to prevent SQL injection
- Phase 14.1: TIME partitioning by DATE(mentioned_at) for query performance
- Phase 14.3: BigQuery DML UPDATE for intelligence analysis results (metadata, risk_score, severity fields)
- Phase 14.3: Intelligence results in metadata JSON field (sentiment, llm_analysis, entities, summary, relationships, themes, urgency, language, severity)
- Phase 14.3: PostgreSQL Event model retained for Django compatibility (not deleted via migrations)
- Phase 14.3: EntityMention and SanctionsMatch remain in PostgreSQL (reference data, not time-series)
- Phase 14.3: SimpleNamespace mock objects for service compatibility without full Event model instances
- Phase 14.3: Legacy batch tasks deprecated but kept for backward compatibility with warnings
- Phase 14.3: Processing logic preserved exactly (only data source changed, algorithms unchanged)
- Phase 15: scipy.stats.pearsonr/spearmanr for correlation (not custom formulas)
- Phase 15: Bonferroni correction (not FDR) for conservative multiple comparison control
- Phase 15: Default correlation thresholds: alpha=0.05, min_effect_size=0.7 for strong correlations
- Phase 15: ADF stationarity test with automatic differencing for time-series correlation
- Phase 15: Inner join for time-series alignment (drops dates missing from any variable)
- Phase 18: Cloud Functions Gen2 (not Gen1) for better performance and VPC connector support
- Phase 18: OIDC authentication (not API keys) for Cloud Scheduler security
- Phase 18: Standalone functions with no Django dependencies for serverless deployment
- Phase 18: Pub/Sub event publishing instead of Celery task dispatch
- Phase 18: 512MB-900MB memory allocation based on task complexity

### Deferred Issues

None yet.

### Blockers/Concerns

**Phase 14.3 Complete:**
- Full polyglot persistence architecture operational (PostgreSQL + BigQuery)
- All processing tasks migrated to BigQuery (entity extraction, intelligence, sanctions)
- PostgreSQL Event model deprecated with comprehensive documentation
- Phase 15 correlation analysis unblocked (all event data in BigQuery)
- TODO: Adapt RiskScorer and ImpactClassifier for dict-based events (currently using LLM risk directly)

### Roadmap Evolution

- v1.0 MVP shipped 2026-01-09: Complete SaaS platform with data pipeline, risk intelligence, dashboard, entity tracking, and AI chat (Phases 1-7)
- v1.1 UI/UX Overhaul shipped 2026-01-10: Comprehensive UI/UX redesign with design system, component library, and responsive design (Phases 8-13)
- Milestone v1.2 Advanced Analytics created: Time-series forecasting, correlation analysis, custom reports, enhanced visualization (Phases 14-17)
- **Phase 14.1 inserted after Phase 14 (2026-01-09):** BigQuery Migration - TimescaleDB not available on Cloud SQL, migrate to polyglot persistence (PostgreSQL + BigQuery) - URGENT infrastructure fix blocking production deployment (COMPLETE 2026-01-10)
- **Phase 14.2 inserted after Phase 14.1 (2026-01-10):** GDELT Native BigQuery - Migrate from custom GDELT DOC API polling to native BigQuery dataset (gdelt-bq.gdeltv2) for richer data and simpler architecture - Unlocks 2,300+ themes/emotions, 65 languages, historical access (COMPLETE 2026-01-10)
- **Phase 14.3 inserted after Phase 14.2 (2026-01-10):** Complete Event Migration to BigQuery - Migrate all remaining event ingestion (ReliefWeb, FRED, UN Comtrade, World Bank) and API views from PostgreSQL to BigQuery for unified time-series analytics - URGENT architectural prerequisite for Phase 15 correlation analysis
- **Phase 18 added to v1.2 (2026-01-10):** GCP-Native Pipeline Migration - Comprehensive migration from Celery to GCP-native serverless orchestration (Cloud Scheduler, Cloud Run, Pub/Sub, Cloud Tasks) for auto-scaling, observability, and operational simplicity - Research complete (GCP-NATIVE-ORCHESTRATION-RESEARCH.md)

## Session Continuity

Last session: 2026-01-10
Stopped at: Completed 18-01-PLAN.md (Ingestion Layer Migration - code ready, deployment pending)
Resume file: None
