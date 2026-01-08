# VenezuelaWatch

## What This Is

VenezuelaWatch is a SaaS intelligence platform that aggregates real-time data from multiple sources to provide actionable risk intelligence about political, economic, and trade events in Venezuela. It helps investors and operators (oil & energy companies, commodity traders, private equity funds) make informed decisions about Venezuela exposure, trade opportunities, and competitive positioning.

## Core Value

Accurate risk intelligence that identifies sanctions changes, political disruptions, and trade opportunities before they impact investment decisions.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Dashboard with real-time event aggregation from 7 data sources (GDELT, FRED, UN Comtrade, World Bank, ReliefWeb, USITC, Port Authorities)
- [ ] News/Events feed with filtering, search, and sentiment analysis
- [ ] Risk scoring system for sanctions, political changes, supply chain disruptions
- [ ] Entity Watch for tracking people, companies, and governments with:
  - News mentions and sentiment tracking
  - Network relationship mapping
  - Sanctions and legal status monitoring
  - Activities and transactions tracking
- [ ] AI chat interface for:
  - Natural language queries across all data sources
  - Event explanation and impact analysis
  - Custom report generation
- [ ] Trade opportunity identification (arbitrage, supply chain shifts, new routes)
- [ ] Competitive intelligence tracking (what key players are doing)
- [ ] Individual user authentication and accounts
- [ ] Architecture supporting future team features (shared workspaces, permissions)

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

---
*Last updated: 2026-01-08 after initialization*
