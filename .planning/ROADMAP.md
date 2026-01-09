# Roadmap: VenezuelaWatch

## Overview

VenezuelaWatch begins with infrastructure and authentication, then builds a multi-source data pipeline with mixed latency requirements. The core value—risk intelligence—is implemented early (Phase 4), followed by the dashboard interface, entity tracking, and AI chat capabilities. This journey takes us from empty directory to a production SaaS platform providing real-time Venezuela intelligence to investors and operators.

## Domain Expertise

None

## Phases

- [x] **Phase 1: Foundation & Infrastructure** - Django + React project setup, GCP infrastructure, database schema
- [x] **Phase 2: Authentication & User Management** - django-allauth integration, user accounts, frontend shell
- [x] **Phase 3: Data Pipeline Architecture** - Ingestion framework for 5 data sources with mixed latency
- [x] **Phase 4: Risk Intelligence Core** - Risk scoring engine for sanctions, political, supply chain disruptions
- [ ] **Phase 5: Dashboard & Events Feed** - Real-time event aggregation, filtering, search, sentiment
- [ ] **Phase 6: Entity Watch** - Track people/companies/governments with mentions, relationships, sanctions
- [ ] **Phase 7: AI Chat Interface** - assistant-ui integration for natural language queries and reports

## Phase Details

### Phase 1: Foundation & Infrastructure
**Goal**: Establish Django 5.2 + React 18 project structure on GCP with database and basic API framework
**Depends on**: Nothing (first phase)
**Research**: Likely (GCP setup, Django 5.2 + React 18 integration patterns)
**Research topics**: Django 5.2 best practices, django-ninja API patterns, GCP Cloud Run/Functions for Django, React 18 + Django integration, database choice for time-series event data
**Plans**: TBD

Plans:
- [ ] TBD during phase planning

### Phase 2: Authentication & User Management
**Goal**: Implement user authentication with django-allauth, user model supporting future teams
**Depends on**: Phase 1
**Research**: Likely (django-allauth configuration, team architecture planning)
**Research topics**: django-allauth with django-ninja, JWT vs session auth for React SPA, user model design supporting future teams
**Plans**: TBD

Plans:
- [ ] TBD during phase planning

### Phase 3: Data Pipeline Architecture
**Goal**: Build ingestion framework for 7 external APIs (GDELT, FRED, UN Comtrade, World Bank, ReliefWeb, USITC, Port Authorities) with mixed latency requirements
**Depends on**: Phase 1
**Research**: Completed (DISCOVERY.md)
**Research topics**: GDELT API, FRED API, UN Comtrade API, World Bank API, ReliefWeb API, USITC API, Port Authority APIs, GCP Pub/Sub vs Cloud Tasks for ingestion scheduling, rate limiting strategies
**Plans**: 4 plans (infrastructure, real-time, daily batch, monthly/quarterly)

Plans:
- [x] 03-01: Celery + Redis Infrastructure Setup (Celery, Redis, django-celery-results, GCP Memorystore, Secret Manager)
- [x] 03-02: Real-Time Ingestion - GDELT + ReliefWeb (15-min polling, daily updates, Celery Beat, Cloud Scheduler)
- [x] 03-03: Daily Batch Ingestion - FRED Economic Data (fredapi, economic indicators, threshold events)
- [x] 03-04: Monthly/Quarterly Ingestion - UN Comtrade + World Bank (trade flows, development indicators)

### Phase 4: Risk Intelligence Core
**Goal**: Implement risk scoring system for sanctions changes, political disruptions, supply chain events
**Depends on**: Phase 3
**Research**: Completed (04-RESEARCH.md)
**Research topics**: Risk scoring methodologies, OFAC sanctions list APIs, event impact classification, risk aggregation patterns
**Plans**: TBD

Plans:
- [x] 04-01: Sanctions Screening Integration (OpenSanctions/OFAC API, SanctionsMatch model, daily refresh task)
- [x] 04-02: Multi-Dimensional Risk Aggregation (RiskAggregator service, event-type-specific weights, comprehensive scoring)
- [x] 04-03: Event Severity Classification (ImpactClassifier, NCISS-style weighted criteria, SEV1-5 levels)
- [x] 04-04: Risk Intelligence API & Dashboard Integration (REST API endpoints, bulk operations, documentation)

### Phase 5: Dashboard & Events Feed
**Goal**: Build React dashboard with real-time event aggregation, filtering, search, and sentiment analysis
**Depends on**: Phase 4
**Research**: Unlikely (standard React patterns once data pipeline exists)
**Plans**: TBD

Plans:
- [ ] TBD during phase planning

### Phase 6: Entity Watch
**Goal**: Implement entity tracking for people, companies, governments with news mentions, relationships, sanctions status, and activities
**Depends on**: Phase 5
**Research**: Likely (entity extraction, relationship mapping)
**Research topics**: Named entity recognition for news, relationship graph modeling, sanctions list integration
**Plans**: TBD

Plans:
- [ ] TBD during phase planning

### Phase 7: AI Chat Interface
**Goal**: Integrate assistant-ui for natural language queries across data sources, event explanation, and report generation
**Depends on**: Phase 6
**Research**: Likely (assistant-ui integration, LLM provider choice)
**Research topics**: assistant-ui with React 18, Claude/OpenAI API integration, RAG patterns for querying aggregated data
**Plans**: TBD

Plans:
- [ ] TBD during phase planning

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Infrastructure | 4/4 | Complete | 2026-01-08 |
| 2. Authentication & User Management | 4/4 | Complete | 2026-01-09 |
| 3. Data Pipeline Architecture | 4/4 | Complete | 2026-01-08 |
| 4. Risk Intelligence Core | 4/4 | Complete | 2026-01-09 |
| 5. Dashboard & Events Feed | 0/TBD | Not started | - |
| 6. Entity Watch | 0/TBD | Not started | - |
| 7. AI Chat Interface | 0/TBD | Not started | - |
