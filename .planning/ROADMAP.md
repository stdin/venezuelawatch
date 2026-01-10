# Roadmap: VenezuelaWatch

## Overview

VenezuelaWatch begins with infrastructure and authentication, then builds a multi-source data pipeline with mixed latency requirements. The core value—risk intelligence—is implemented early (Phase 4), followed by the dashboard interface, entity tracking, and AI chat capabilities. This journey takes us from empty directory to a production SaaS platform providing real-time Venezuela intelligence to investors and operators.

## Domain Expertise

None

## Milestones

- ✅ **v1.0 MVP** - Phases 1-7 (shipped 2026-01-09)
- ✅ **v1.1 UI/UX Overhaul** - Phases 8-13 (shipped 2026-01-10)
- 🚧 **v1.2 Advanced Analytics** - Phases 14-17 (in progress)

## Completed Milestones

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

### 🚧 v1.2 Advanced Analytics (In Progress)

**Milestone Goal:** Add powerful intelligence capabilities with time-series forecasting, correlation analysis, custom reports, and enhanced data visualization.

#### Phase 14: Time-Series Forecasting
**Goal**: Predict risk trends, economic indicators, and event patterns using statistical models
**Depends on**: Phase 13 (previous milestone complete)
**Research**: Completed (14-RESEARCH.md)
**Research topics**: Python forecasting libraries (Prophet, statsmodels, scikit-learn), model selection for time-series data, integration with existing TimescaleDB data
**Plans**: 4 plans

Plans:
- [x] 14-01: BigQuery ETL Setup
- [x] 14-02: Vertex AI Training Infrastructure
- [ ] 14-03: Forecast API Integration
- [ ] 14-04: Frontend Forecast Visualization

#### Phase 15: Correlation & Pattern Analysis
**Goal**: Discover relationships between events, entities, and economic data with visual correlation matrices
**Depends on**: Phase 14
**Research**: Likely (statistical correlation methods, graph algorithms)
**Research topics**: Correlation analysis methods for mixed data types, pattern detection algorithms, network analysis for entity relationships
**Plans**: TBD

Plans:
- [ ] 15-01: TBD

#### Phase 16: Custom Reports & Export
**Goal**: User-defined report templates, PDF generation, CSV/Excel export, scheduled reports
**Depends on**: Phase 15
**Research**: Likely (PDF generation libraries, scheduling)
**Research topics**: Python PDF libraries (ReportLab, WeasyPrint), Excel generation (openpyxl, xlsxwriter), report scheduling patterns
**Plans**: TBD

Plans:
- [ ] 16-01: TBD

#### Phase 17: Enhanced Data Visualization
**Goal**: Interactive charts, heatmaps, network graphs, custom dashboards, visualization library expansion
**Depends on**: Phase 16
**Research**: Unlikely (extending existing Recharts patterns)
**Plans**: TBD

Plans:
- [ ] 17-01: TBD

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
| 14. Time-Series Forecasting | v1.2 | 2/4 | In progress | - |
| 15. Correlation & Pattern Analysis | v1.2 | 0/? | Not started | - |
| 16. Custom Reports & Export | v1.2 | 0/? | Not started | - |
| 17. Enhanced Data Visualization | v1.2 | 0/? | Not started | - |
