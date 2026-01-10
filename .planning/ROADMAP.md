# Roadmap: VenezuelaWatch

## Overview

VenezuelaWatch begins with infrastructure and authentication, then builds a multi-source data pipeline with mixed latency requirements. The core value—risk intelligence—is implemented early (Phase 4), followed by the dashboard interface, entity tracking, and AI chat capabilities. This journey takes us from empty directory to a production SaaS platform providing real-time Venezuela intelligence to investors and operators.

## Domain Expertise

None

## Milestones

- ✅ **v1.0 MVP** - Phases 1-7 (shipped 2026-01-09)
- ✅ **v1.1 UI/UX Overhaul** - Phases 8-13 (shipped 2026-01-10)

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

### ✅ v1.1 UI/UX Overhaul (Shipped 2026-01-10)

**Milestone Goal:** Comprehensive UI/UX redesign with professional design system, improved component library, and enhanced user experience across all pages

#### Phase 8: Design System Foundation
**Goal**: Establish comprehensive design system with color palette, typography, spacing, and component tokens
**Depends on**: Phase 7 (v1.0 complete)
**Research**: Completed (08-RESEARCH.md)
**Research topics**: Design token systems, color theory for data visualization, typography scales, spacing/sizing systems, CSS architecture patterns
**Plans**: 2 plans

Plans:
- [x] 08-01: Design Token Foundation (typography, OKLCH colors, spacing)
- [x] 08-02: Storybook Interactive Style Guide

#### Phase 9: Component Library Rebuild
**Goal**: Rebuild core UI components (buttons, inputs, cards, modals, tables) with consistent design and accessibility
**Depends on**: Phase 8
**Research**: Completed (09-RESEARCH.md)
**Research topics**: Headless UI libraries, Radix UI primitives, ARIA patterns, component composition patterns
**Plans**: TBD

Plans:
- [x] 09-01: Foundation + Form Components (Button, Input)

#### Phase 10: Dashboard Redesign
**Goal**: Redesign Dashboard and Events Feed with improved layout, data visualization, and filtering UX
**Depends on**: Phase 9
**Research**: Completed (10-RESEARCH.md)
**Research topics**: Mantine Grid responsive patterns, Recharts data visualization, React Query data fetching, Mantine form components
**Plans**: 4 plans

Plans:
- [x] 10-01: Responsive Layout & Grid System
- [x] 10-02: Events Feed Redesign
- [x] 10-03: Data Visualization with Recharts
- [x] 10-04: Filter UX Enhancement

#### Phase 11: Entity Pages Redesign
**Goal**: Redesign entity leaderboard and profile pages with better information architecture and visualization
**Depends on**: Phase 9
**Research**: Unlikely (using established components and patterns from Phase 9)
**Plans**: 3/3 complete

Plans:
- [x] 11-01: Layout & Metric Toggles (Mantine Grid, SegmentedControl)
- [x] 11-02: EntityLeaderboard Redesign (Mantine Card, Badge, Skeleton loading)
- [x] 11-03: EntityProfile Redesign (Mantine Card sections, Alert for sanctions)

#### Phase 12: Chat Interface Polish
**Goal**: Polish chat interface with better message rendering, tool card design, and conversation UX
**Depends on**: Phase 9
**Research**: Unlikely (using established components and patterns from Phase 9)
**Plans**: TBD

Plans:
- [ ] 12-01: TBD

#### Phase 13: Responsive & Accessibility
**Goal**: Ensure mobile responsive design, keyboard navigation, ARIA labels, loading states, and error handling across all pages
**Depends on**: Phases 10, 11, 12
**Research**: Completed (13-RESEARCH.md)
**Research topics**: Mobile-first responsive design, WCAG 2.1 AA compliance, screen reader testing, keyboard navigation patterns, loading state patterns
**Plans**: 4/4 complete

Plans:
- [x] 13-01: Responsive Foundation & A11y Setup (Mantine breakpoints, Storybook a11y, skip links, ARIA landmarks)
- [x] 13-02: Dashboard Responsive & Keyboard Nav (mobile-first Grid, collapsible TrendsPanel, keyboard EventCards, ARIA labels)
- [x] 13-03: Entities & Chat Responsive (modal pattern, keyboard nav, ARIA labels, touch targets)
- [x] 13-04: Accessibility Verification & Documentation

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
