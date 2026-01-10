# Roadmap: VenezuelaWatch

## Overview

VenezuelaWatch begins with infrastructure and authentication, then builds a multi-source data pipeline with mixed latency requirements. The core value—risk intelligence—is implemented early (Phase 4), followed by the dashboard interface, entity tracking, and AI chat capabilities. This journey takes us from empty directory to a production SaaS platform providing real-time Venezuela intelligence to investors and operators.

## Domain Expertise

None

## Milestones

- ✅ **v1.0 MVP** - Phases 1-7 (shipped 2026-01-09)
- ✅ **v1.1 UI/UX Overhaul** - Phases 8-13 (shipped 2026-01-10)
- ✅ **v1.2 Advanced Analytics** - Phases 14-18 (shipped 2026-01-10, partial)
- 🚧 **v1.3 GDELT Intelligence** - Phases 19-24 (in progress)

## Completed Milestones

- ✅ [v1.2 Advanced Analytics](milestones/v1.2-Advanced-Analytics-ROADMAP.md) (Phases 14-18, partial) — SHIPPED 2026-01-10
- ✅ [v1.1 UI/UX Overhaul](milestones/v1.1-UI-UX-Overhaul-ROADMAP.md) (Phases 8-13) — SHIPPED 2026-01-10
- ✅ [v1.0 MVP](milestones/) (Phases 1-7) — SHIPPED 2026-01-09

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-7) - SHIPPED 2026-01-09</summary>

### Phase 1: Foundation & Infrastructure
**Goal**: Establish Django 5.2 + React 18 project structure on GCP with database and basic API framework
**Depends on**: Nothing (first phase)
**Research**: Likely (GCP setup, Django 5.2 + React 18 integration patterns)
**Research topics**: Django 5.2 best practices, django-ninja API patterns, GCP Cloud Run/Functions for Django, React 18 + Django integration, database choice for time-series event data
**Plans**: 4 plans

Plans:
- [x] 01-01: Django + React Project Setup
- [x] 01-02: GCP Infrastructure & Database
- [x] 01-03: Basic API Framework with django-ninja
- [x] 01-04: Event Model & TimescaleDB Integration

### Phase 2: Authentication & User Management
**Goal**: Implement user authentication with django-allauth, user model supporting future teams
**Depends on**: Phase 1
**Research**: Likely (django-allauth configuration, team architecture planning)
**Research topics**: django-allauth with django-ninja, JWT vs session auth for React SPA, user model design supporting future teams
**Plans**: 4 plans

Plans:
- [x] 02-01: Custom User Model & django-allauth Setup
- [x] 02-02: Session Authentication Integration
- [x] 02-03: Frontend Auth Shell & API Client
- [x] 02-04: User Registration & Login UI

### Phase 3: Data Pipeline Architecture
**Goal**: Build ingestion framework for 7 external APIs (GDELT, FRED, UN Comtrade, World Bank, ReliefWeb, USITC, Port Authorities) with mixed latency requirements
**Depends on**: Phase 1
**Research**: Completed (DISCOVERY.md)
**Research topics**: GDELT API, FRED API, UN Comtrade API, World Bank API, ReliefWeb API, USITC API, Port Authority APIs, GCP Pub/Sub vs Cloud Tasks for ingestion scheduling, rate limiting strategies
**Plans**: 4 plans

Plans:
- [x] 03-01: Celery + Redis Infrastructure Setup
- [x] 03-02: Real-Time Ingestion - GDELT + ReliefWeb
- [x] 03-03: Daily Batch Ingestion - FRED Economic Data
- [x] 03-04: Monthly/Quarterly Ingestion - UN Comtrade + World Bank

### Phase 4: Risk Intelligence Core
**Goal**: Implement risk scoring system for sanctions changes, political disruptions, supply chain events
**Depends on**: Phase 3
**Research**: Completed (04-RESEARCH.md)
**Research topics**: Risk scoring methodologies, OFAC sanctions list APIs, event impact classification, risk aggregation patterns
**Plans**: 4 plans

Plans:
- [x] 04-01: Sanctions Screening Integration
- [x] 04-02: Multi-Dimensional Risk Aggregation
- [x] 04-03: Event Severity Classification
- [x] 04-04: Risk Intelligence API & Dashboard Integration

### Phase 5: Dashboard & Events Feed
**Goal**: Build React dashboard with real-time event aggregation, filtering, search, and sentiment analysis
**Depends on**: Phase 4
**Research**: Unlikely (standard React patterns once data pipeline exists)
**Plans**: 4 plans

Plans:
- [x] 05-01: Event List Component with Real-Time Filtering
- [x] 05-02: Event Detail View with Risk Visualization
- [x] 05-03: Dashboard Layout Integration
- [x] 05-04: Trends Panel with Time-Series Risk Analysis

### Phase 6: Entity Watch
**Goal**: Implement entity tracking for people, companies, governments with news mentions, relationships, sanctions status, and activities
**Depends on**: Phase 5
**Research**: Likely (entity extraction, relationship mapping)
**Research topics**: Named entity recognition for news, relationship graph modeling, sanctions list integration
**Plans**: 4 plans

Plans:
- [x] 06-01: Entity Models & Fuzzy Matching Service
- [x] 06-02: Entity Extraction Celery Task
- [x] 06-03: Entity API & Trending Endpoints
- [x] 06-04: Frontend Entity Leaderboard & Profiles

### Phase 7: AI Chat Interface
**Goal**: Integrate assistant-ui for natural language queries across data sources, event explanation, and report generation
**Depends on**: Phase 6
**Research**: Likely (assistant-ui integration, LLM provider choice)
**Research topics**: assistant-ui with React 18, Claude/OpenAI API integration, RAG patterns for querying aggregated data
**Plans**: 4 plans

Plans:
- [x] 07-01: Backend Chat API with Claude Streaming
- [x] 07-02: assistant-ui React Integration
- [x] 07-03: Tool UI Components
- [x] 07-04: Chat Page UI & Navigation

</details>

<details>
<summary>✅ v1.1 UI/UX Overhaul (Phases 8-13) - SHIPPED 2026-01-10</summary>

See [milestones/v1.1-UI-UX-Overhaul-ROADMAP.md](milestones/v1.1-UI-UX-Overhaul-ROADMAP.md) for complete phase details.

**Key deliverables:**
- Professional design system with OKLCH colors, 1.25 modular typography, semantic tokens
- Storybook 10 interactive style guide with theme switcher
- Mantine UI component library (28.1k stars, 120+ components)
- Dashboard redesign with Recharts visualization and Mantine Grid layout
- Entity pages with leaderboard, metric toggles, and risk intelligence profiles
- Chat interface with compact tool cards and real-time streaming
- Mobile-responsive (320px-1440px+) with WCAG 2.1 AA accessibility
- Comprehensive documentation (1755 lines): responsive patterns and accessibility guidelines

</details>

<details>
<summary>✅ v1.2 Advanced Analytics (Phases 14-18, partial) - SHIPPED 2026-01-10</summary>

**Milestone Goal:** Add powerful intelligence capabilities with time-series forecasting, correlation analysis, custom reports, and enhanced data visualization.

- [x] Phase 14: Time-Series Forecasting (4/4 plans) — completed 2026-01-10
- [x] Phase 14.1: BigQuery Migration (4/4 plans, INSERTED) — completed 2026-01-10
- [x] Phase 14.2: GDELT Native BigQuery (1/1 plan, INSERTED) — completed 2026-01-10
- [x] Phase 14.3: Complete Event Migration to BigQuery (1/1 plan, INSERTED) — completed 2026-01-10
- [x] Phase 15: Correlation & Pattern Analysis (1/2 plans, partial) — backend complete 2026-01-10
- [x] Phase 16: Enhanced Data Visualization (1/1 plan) — completed 2026-01-09
- [ ] Phase 17: Custom Reports & Alerts (deferred to v1.3+)
- [x] Phase 18: GCP-Native Pipeline Migration (3/3 plans) — completed 2026-01-10

**Note:** Phase 15-02 (correlation UI) and Phase 17 deferred to future milestone. See [archive](milestones/v1.2-Advanced-Analytics-ROADMAP.md) for full details.

</details>

### 🚧 v1.3 GDELT Intelligence (In Progress)

**Milestone Goal:** Maximize value from free BigQuery GDELT data (61 fields vs current 4) - rebuild intelligence pipeline around rich GDELT signals to reduce LLM costs and improve risk scoring accuracy.

#### Phase 19: GDELT Events Enrichment

**Goal**: Migrate from 4 basic fields to all 61 GDELT BigQuery fields (quotations, themes, tone, images, Goldstein scale, counts)
**Depends on**: Phase 18 (GCP-Native Pipeline Migration)
**Research**: Likely (GDELT field schema, quotations parsing, Goldstein scale interpretation)
**Research topics**: GDELT 2.0 field definitions, quotation extraction patterns, Goldstein scale scoring, AvgTone normalization
**Plans**: TBD

Plans:
- [ ] 19-01: TBD (run /gsd:plan-phase 19 to break down)

#### Phase 20: GKG Integration

**Goal**: Integrate GDELT Global Knowledge Graph for richer entity extraction, location mapping, theme categorization, and people/org tracking
**Depends on**: Phase 19
**Research**: Likely (GKG table schema, GCAM scores, entity relationships)
**Research topics**: GKG V2 format, GCAM emotional dimensions, V2Themes taxonomy, entity relationship extraction
**Plans**: TBD

Plans:
- [ ] 20-01: TBD

#### Phase 21: Mentions Tracking

**Goal**: Track narrative spread by monitoring how events are mentioned across articles over time for early warning signals
**Depends on**: Phase 20
**Research**: Complete
**Plans**: 1/3 complete
**Status**: In progress

Plans:
- [x] 21-01: Mentions tracking infrastructure (PostgreSQL spike model + BigQuery service)
- [ ] 21-02: TDD spike detection logic
- [ ] 21-03: Spike intelligence analysis

#### Phase 22: Data Source Architecture

**Goal**: Rebuild data source architecture with scalable adapter pattern (GDELT-first, plugin system for future integrations)
**Depends on**: Phase 21
**Research**: Unlikely (internal refactoring using established patterns from Phase 14.3)
**Plans**: TBD

Plans:
- [ ] 22-01: TBD

#### Phase 23: Intelligence Pipeline Rebuild

**Goal**: Redesign intelligence pipeline to use GDELT tone/sentiment scores, themes, and quote analysis as primary risk signals
**Depends on**: Phase 22
**Research**: Likely (GDELT-based risk scoring methodologies)
**Research topics**: Tone-based risk classification, theme-based severity mapping, quotation sentiment analysis
**Plans**: TBD

Plans:
- [ ] 23-01: TBD

#### Phase 24: LLM Optimization & UI

**Goal**: Implement selective Claude processing based on GDELT signals (high-priority themes/tone), batching, prompt caching, and dashboard updates
**Depends on**: Phase 23
**Research**: Likely (Claude prompt caching, batching strategies)
**Research topics**: Anthropic prompt caching API, batch processing patterns, token cost optimization
**Plans**: TBD

Plans:
- [ ] 24-01: TBD

#### Phase 25: Add More BigQuery Data Sources

**Goal**: [To be planned]
**Depends on**: Phase 24
**Plans**: 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 25 to break down)

**Details:**
[To be added during planning]

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation & Infrastructure | v1.0 | 4/4 | Complete | 2026-01-08 |
| 2. Authentication & User Management | v1.0 | 4/4 | Complete | 2026-01-09 |
| 3. Data Pipeline Architecture | v1.0 | 4/4 | Complete | 2026-01-08 |
| 4. Risk Intelligence Core | v1.0 | 4/4 | Complete | 2026-01-09 |
| 5. Dashboard & Events Feed | v1.0 | 4/4 | Complete | 2026-01-09 |
| 6. Entity Watch | v1.0 | 4/4 | Complete | 2026-01-09 |
| 7. AI Chat Interface | v1.0 | 4/4 | Complete | 2026-01-09 |
| 8. Design System Foundation | v1.1 | 2/2 | Complete | 2026-01-09 |
| 9. Component Library Rebuild | v1.1 | 2/2 | Complete | 2026-01-09 |
| 10. Dashboard Redesign | v1.1 | 4/4 | Complete | 2026-01-09 |
| 11. Entity Pages Redesign | v1.1 | 3/3 | Complete | 2026-01-09 |
| 12. Chat Interface Polish | v1.1 | 2/2 | Complete | 2026-01-09 |
| 13. Responsive & Accessibility | v1.1 | 4/4 | Complete | 2026-01-10 |
| 14. Time-Series Forecasting | v1.2 | 4/4 | Complete | 2026-01-10 |
| 14.1. BigQuery Migration (INSERTED) | v1.2 | 4/4 | Complete | 2026-01-10 |
| 14.2. GDELT Native BigQuery (INSERTED) | v1.2 | 1/1 | Complete | 2026-01-10 |
| 14.3. Complete Event Migration to BigQuery (INSERTED) | v1.2 | 1/1 | Complete | 2026-01-10 |
| 15. Correlation & Pattern Analysis | v1.2 | 1/2 | Partial | - |
| 16. Enhanced Data Visualization | v1.2 | 1/1 | Complete | 2026-01-09 |
| 18. GCP-Native Pipeline Migration | v1.2 | 3/3 | Complete | 2026-01-10 |
| 19. GDELT Events Enrichment | v1.3 | 1/? | In progress | 2026-01-10 |
| 20. GKG Integration | v1.3 | 2/? | In progress | 2026-01-10 |
| 21. Mentions Tracking | v1.3 | 0/? | Not started | - |
| 22. Data Source Architecture | v1.3 | 0/? | Not started | - |
| 23. Intelligence Pipeline Rebuild | v1.3 | 0/? | Not started | - |
| 24. LLM Optimization & UI | v1.3 | 0/? | Not started | - |
| 25. Add More BigQuery Data Sources | v1.3 | 0/? | Not started | - |
