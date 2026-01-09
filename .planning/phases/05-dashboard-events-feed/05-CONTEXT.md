# Phase 5: Dashboard & Events Feed - Context

**Gathered:** 2026-01-08
**Status:** Ready for planning

<vision>
## How This Should Work

This is an intelligence dashboard, not a news feed. Users experience it as a prioritized risk monitoring console - the highest risk events are immediately visible at the top, ordered by the risk scoring system built in Phase 4.

The dashboard uses a **split view layout** (inspired by Linear/modern SaaS design) with the event list on the left and a detail panel on the right. Users can quickly scan event cards showing moderate information (title, risk score, severity, timestamp, short summary, source, sentiment) and click to see full context without losing their place.

This is designed for **ongoing monitoring** - users keep the dashboard open throughout their workday for always-on awareness of emerging risks in Venezuela. Live updates appear with a notification badge when new events arrive, providing proactive awareness without disrupting their flow.

The interface is clean and minimal with plenty of whitespace, smooth interactions, and professional polish. It should feel trustworthy and calm, not overwhelming or cluttered.

</vision>

<essential>
## What Must Be Nailed

- **Risk prioritization accuracy** - Users must trust that the highest risk events are truly at the top. The intelligence value of this platform lives or dies on getting prioritization right.

- **Split view that maintains context** - Clicking into an event shows detail on the right, but the list stays visible on the left. Users never lose their place or context.

- **Performance for large volumes** - Virtual scrolling handles thousands of events efficiently. Always-on monitoring means users will accumulate large datasets, and the UI must stay responsive.

</essential>

<boundaries>
## What's Out of Scope

- **Custom dashboards or saved views** - Phase 5 delivers one well-designed default view. Personalization and custom layouts are future features.

- **Alerts and notifications** - No email/push notifications for high-risk events in this phase. Users interact with the dashboard directly for monitoring.

- **Entity tracking integration** - Phase 6 will add people, companies, relationships. For now, events stand alone without entity profiles or cross-references.

</boundaries>

<specifics>
## Specific Ideas

**Design inspiration:** Linear/modern SaaS aesthetic - clean, minimal, smooth interactions, professional without being corporate.

**Filtering capabilities (essential):**
- Risk dimension filters (sanctions, political, supply chain)
- Time range and date filters (last 24h, week, month, custom)
- Severity level filters (SEV1-5)

**Card content (moderate density):**
- Title
- Risk score (0-100)
- Severity level (SEV1-5)
- Timestamp
- Short summary
- Source
- Sentiment indicator (positive/neutral/negative)

**Detail view (comprehensive):**
- Full event description and source links
- Risk breakdown showing how score was calculated
- Related events from same source/topic
- All metadata (severity, sentiment, categories, tags)

**Real-time updates:**
- Live updates with notification badge showing count of new events
- Users see new events appear without manual refresh

**State persistence:**
- Filter preferences persist in URL/localStorage
- Users set filters once, they stick across sessions

**Visual trends:**
- Basic charts showing risk over time
- Events by category distribution
- Provides context for current risk snapshot

**Responsive:**
- Desktop-first design optimized for split view
- Mobile-readable as secondary priority (usable but not optimized)

</specifics>

<notes>
## Additional Context

The user workflow is **ongoing monitoring** rather than periodic check-ins. This affects design priorities:
- Performance matters more than completeness (but virtual scrolling handles both)
- Live updates are essential for awareness
- Persistence prevents re-configuring filters every session
- Split view keeps users oriented during investigation

The dashboard must support both **scan mode** (quick triage across many events) and **detail mode** (deep investigation of specific events). Moderate card density strikes the balance - users understand most events at a glance but can drill into full context when needed.

Both **risk score and sentiment** are visible indicators. Risk prioritizes the list, but sentiment adds important context about whether news is positive or negative.

Phase 4's risk intelligence system is the foundation - this phase is about making that intelligence accessible and actionable through an excellent interface.

</notes>

---

*Phase: 05-dashboard-events-feed*
*Context gathered: 2026-01-08*
