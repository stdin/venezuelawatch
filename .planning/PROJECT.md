# VenezuelaWatch

## What This Is

VenezuelaWatch is a SaaS intelligence platform that aggregates real-time data from multiple sources to provide actionable risk intelligence about political, economic, and trade events in Venezuela. It helps investors and operators (oil & energy companies, commodity traders, private equity funds) make informed decisions about Venezuela exposure, trade opportunities, and competitive positioning.

## Core Value

Accurate risk intelligence that identifies sanctions changes, political disruptions, and trade opportunities before they impact investment decisions.

## Requirements

### Validated

- ✓ Dashboard with real-time event aggregation from 7 data sources (GDELT, FRED, UN Comtrade, World Bank, ReliefWeb) — v1.0
- ✓ News/Events feed with filtering, search, and sentiment analysis — v1.0, enhanced UX in v1.1
- ✓ Risk scoring system for sanctions, political changes, supply chain disruptions — v1.0
- ✓ Entity Watch for tracking people, companies, and governments with news mentions, sanctions monitoring, and trending metrics — v1.0, enhanced UI in v1.1
- ✓ AI chat interface for natural language queries, event explanation, and tool-based data access — v1.0, polished UI in v1.1
- ✓ Individual user authentication and accounts — v1.0
- ✓ Architecture supporting future team features (user model designed for teams) — v1.0
- ✓ Mobile-responsive design (320px-1440px+) — v1.1
- ✓ WCAG 2.1 AA accessibility (keyboard navigation, ARIA labels, screen reader support) — v1.1
- ✓ Professional design system with comprehensive component library — v1.1

### Active

- [ ] Trade opportunity identification (arbitrage, supply chain shifts, new routes)
- [ ] Competitive intelligence tracking (what key players are doing)
- [ ] USITC and Port Authorities data source integration (deferred from v1.0)
- [ ] Team workspaces with role-based permissions
- [ ] Proactive alerting and notifications
- [ ] Deep historical analysis beyond 3-6 months

### Out of Scope

- Mobile apps (iOS/Android native) — web-only for v1, mobile apps require separate development effort
- Multi-country coverage — Venezuela focus only, regional expansion adds complexity without validating core value first
- Predictive models / AI forecasting — descriptive and analytical features first, forecasting requires significant ML infrastructure
- Proactive alerting / notifications — passive dashboard for v1, alerts add notification infrastructure complexity
- Deep historical analysis — focus on real-time and recent data (last 3-6 months), historical deep dives not critical for current decision-making

## Context

**Current Venezuela Situation (January 2026):**
- Major political upheaval: US military operation arrested President Maduro (January 3, 2026), taken to New York on drug/arms trafficking charges
- Sanctions remain in full effect on Venezuelan oil, government, Central Bank, and PDVSA
- Oil production at ~800k barrels/day (down from 3.5M peak in late 1990s)
- China buys ~80% of Venezuelan oil exports at steep discounts
- Venezuela holds 303 billion barrels of oil reserves (17% of global total)
- US oil companies (Chevron, Exxon, ConocoPhillips) positioning for potential re-entry
- Analysts estimate 10+ years and $100B+ needed to rebuild oil infrastructure

**Target Users:**
- Oil & energy companies evaluating Venezuela re-entry or operations
- Commodity traders dealing with Venezuela-related products (oil, minerals, agriculture)
- Private equity and investment funds assessing Venezuela exposure and infrastructure opportunities

**Key Use Cases:**
- Risk assessment: Quantify exposure to sanctions, political changes, supply disruptions
- Trade opportunities: Identify arbitrage, supply chain shifts, new routes opening
- Competitive intelligence: Track what competitors, governments, and key players are doing

**Data freshness requirements (mixed by source):**
- Critical sources (GDELT news): 5-15 minute updates for breaking events
- Economic indicators (FRED, World Bank): Hourly or daily updates acceptable
- Trade data (UN Comtrade, USITC): Daily or weekly updates acceptable
- Emergency alerts (ReliefWeb): 5-15 minute updates
- Port data: Hourly updates

## Constraints

- **Tech Stack**: React 18 (frontend), Django 5.2 (backend), GCP (infrastructure), assistant-ui (AI chat interface), django-allauth (authentication), django-ninja (API framework) — chosen for modern web development with good ecosystem support for data ingestion, real-time updates, and AI features
- **Data Sources**: Must integrate with 7 specified external APIs/services (GDELT, FRED, UN Comtrade, World Bank, ReliefWeb, USITC, Port Authorities) — each has different API patterns, rate limits, and data formats
- **Latency**: Mixed update frequency required - breaking news must be near real-time (5-15 min), economic/trade data can be hourly/daily — impacts data pipeline architecture
- **User Model**: Start with individual users but architecture must support future team features — affects data modeling and permissions design from the start

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| React 18 + Django 5.2 on GCP | Modern stack with strong ecosystem for data ingestion, real-time updates, and AI features. Django for robust backend/API, React for dynamic frontend, GCP for scalable infrastructure | — Pending |
| Risk intelligence as core value | Given January 2026 Venezuela crisis (Maduro arrest, sanctions uncertainty), users need risk assessment most urgently over other features | — Pending |
| No mobile apps in v1 | Web-first validates core value with less development overhead, can add mobile later if demand exists | — Pending |
| Mixed latency by data source | Breaking news/alerts need near-real-time, economic data can be slower - optimizes cost and complexity while meeting user needs | — Pending |
| Individual users with team architecture | Simpler v1 while avoiding costly refactor later when teams are needed | — Pending |

## Current State (v1.1)

**Shipped:** v1.0 MVP (2026-01-09) + v1.1 UI/UX Overhaul (2026-01-10)

**Tech Stack:**
- Frontend: React 19, TypeScript, Mantine UI, Recharts, @tanstack/react-query, assistant-ui, Vite
- Backend: Django 5.2, Celery, Redis, TimescaleDB/PostgreSQL, django-ninja, django-allauth
- Infrastructure: GCP (Cloud SQL, Cloud Storage, Secret Manager)
- Testing: Storybook 10 with a11y addon, Vitest
- Total LOC: ~7,709 frontend TypeScript/TSX

**Current Features:**
- Multi-source data pipeline (GDELT, FRED, UN Comtrade, World Bank, ReliefWeb)
- Risk intelligence with sanctions screening and severity classification
- Real-time events dashboard with Recharts visualization and Mantine filters
- Entity tracking with leaderboard, trending metrics, and detailed profiles
- AI chat with Claude streaming and custom tool UI components
- Mobile-responsive design (xs: 576px → xl: 1408px breakpoints)
- WCAG 2.1 AA accessible with keyboard navigation and screen reader support
- Professional design system with OKLCH colors and semantic tokens
- Comprehensive documentation (responsive design + accessibility patterns)

**User Feedback Themes:**
(No user testing yet - ready for beta)

**Known Issues/Technical Debt:**
- TypeScript errors in Modal.stories.tsx (pre-existing, non-blocking)
- Consider Mantine v8.x upgrade when stable
- Potential virtualized list performance optimization for 1000+ entities

---
*Last updated: 2026-01-10 after v1.1 milestone*
