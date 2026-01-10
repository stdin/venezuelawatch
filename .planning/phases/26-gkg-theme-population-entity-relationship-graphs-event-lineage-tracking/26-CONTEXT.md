# Phase 26: GKG Theme Population, Entity Relationship Graphs, Event Lineage Tracking - Context

**Gathered:** 2026-01-10 (Updated after Plans 26-01, 26-02)
**Status:** In progress - 2/4 plans complete

<vision>
## How This Should Work

This phase builds an **interactive entity relationship graph** that surfaces non-obvious intelligence patterns - indirect connections, sanctioned entity clusters, hidden networks. Users see a visual web of connections between people, companies, and governments with high-risk areas automatically highlighted.

**✅ COMPLETE (Plans 26-01, 26-02):**
- Interactive WebGL graph visualization with Reagraph
- Co-occurrence based relationships (3+ mentions threshold)
- Risk-based node colors (sanctions red, risk gradient)
- Directional weighted edges showing relationship strength
- Click-to-navigate entity profiles
- Louvain community detection clustering

**REMAINING WORK (Plans 26-03, 26-04):**

When you open the graph, it **automatically zooms to the largest high-risk cluster** - balancing both risk level AND cluster size to find the most important network. No manual searching needed - the system immediately frames the most critical intelligence.

**Progressive disclosure for pattern discovery:**
- Overview: See thematic clusters and main relationship patterns at a glance
- Click edges: LLM-generated narratives explain HOW entities connect through events
- Expand details: Full causal chains and comprehensive theme analysis for deep investigation
- Filter by themes: Focus on specific activity types (sanctions, trade, unrest)

**Event lineage tracking** reveals how events cascade over time - "Sanctions announcement → Port closure → Food shortage → Protests" - surfacing non-obvious cause-and-effect patterns.

**GKG themes** enable pattern discovery through categorical clustering - see which entities are connected by OIL_EXPORT events, SANCTIONS activities, or CIVIL_UNREST themes.

All capabilities work together for intelligence discovery: auto-focus surfaces critical networks, themes reveal activity patterns, narratives explain the connections, lineage shows causal chains.

</vision>

<essential>
## What Must Be Nailed

**PRIMARY: Pattern discovery** - Surface non-obvious intelligence through thematic clustering and causal event chains that aren't visible in individual events.

**Supporting capabilities:**
- **Auto-focus on largest high-risk cluster** - Balance risk level AND cluster size to immediately show the most important network
- **Progressive disclosure** - Start with scannable overview, expand to rich details when users dig deeper
- **Theme-based clustering** - Reveal activity patterns (which entities connect through sanctions, trade, unrest)
- **Event lineage** - Show temporal causal chains (A→B→C) to surface cascade effects

**Already nailed (26-01, 26-02):**
- ✅ Relationship quality - co-occurrence based, directional, weighted
- ✅ Interactive visualization - WebGL performance, click navigation
- ✅ Community detection - Louvain clustering operational

</essential>

<boundaries>
## What's Out of Scope

**Explicitly deferred to future phases:**
- **Time-based playback** - Animated graph showing network evolution over time (defer until core features mature)
- **Custom graph layouts** - User-configurable positioning, manual node placement (keep force-directed auto-layout)
- **Export capabilities** - Download graph as image/data files (defer until graph features stabilize)
- **Real-time updates** - Live graph updates as new events stream in (static snapshot for Phase 26)

**In scope for Phase 26:**
- Auto-focus camera on high-risk clusters
- Edge narratives (LLM-generated relationship stories)
- Theme filtering and clustering
- Event lineage view (causal chains)

</boundaries>

<specifics>
## Specific Ideas

**Auto-focus behavior (Plan 26-03):**
- Balance risk level AND cluster size to find "largest high-risk cluster"
- Camera automatically frames this network when graph loads
- Immediate intelligence delivery - no manual search required

**Progressive disclosure pattern:**
- **Overview:** Scannable theme clusters and main relationship patterns
- **Click edge:** Modal/panel with LLM narrative explaining connection
- **Expand details:** Full causal chain, comprehensive theme breakdown
- **Filter themes:** Show only entities connected by specific activity types

**Edge narratives (Plan 26-03):**
- LLM-generated stories: "Entity A sanctioned by US (Event 1) → Entity B lost financing (Event 2) → Project canceled (Event 3)"
- Click edge to see narrative modal
- List source events with links to verify

**Theme filtering (Plan 26-04):**
- Filter by GKG theme categories (SANCTIONS, ECON_TRADE, CIVIL_UNREST, etc.)
- Shows entities connected through that theme type
- Reveals activity-specific networks

**Event lineage view (Plan 26-04):**
- Temporal causal chains showing A→B→C progression
- Surface cascade effects and indirect impacts
- Timeline visualization of how events connect

**Already implemented (26-01, 26-02):**
- ✅ Reagraph WebGL visualization
- ✅ Risk-based node colors (sanctions red, risk gradient)
- ✅ Directional weighted edges (log-scale thickness)
- ✅ Click entities → navigate to profiles
- ✅ Community clustering (Louvain detection)

</specifics>

<notes>
## Additional Context

**Updated after Plans 26-01, 26-02 completion:**

The emphasis on **pattern discovery** emerged as the primary value - revealing non-obvious intelligence through thematic clustering and causal chains. This is more specific than generic "insight discovery" and guides remaining implementation.

**Relationship quality foundation is complete** (26-01):
- Co-occurrence threshold (3+ mentions) filters noise
- Louvain community detection groups related entities
- Weighted edges show relationship strength
- Backend returns high_risk_cluster for auto-focus

**Interactive visualization foundation is complete** (26-02):
- Reagraph WebGL handles 1K-5K nodes efficiently
- Risk-based colors, directional edges working
- Click handlers ready for narrative integration

**Remaining work (26-03, 26-04):**
1. Auto-focus camera on largest high-risk cluster
2. Edge click → LLM narrative modal explaining connections
3. Theme filters to show activity-specific networks
4. Event lineage view for temporal causal chains

**Progressive disclosure** is the UI pattern - overview first, rich details on demand - to balance scannability with deep investigation capability.

**Scope clarity:** Explicitly defer time-based playback, custom layouts, exports, and real-time updates. Keep Phase 26 focused on core pattern discovery features.

</notes>

---

*Phase: 26-gkg-theme-population-entity-relationship-graphs-event-lineage-tracking*
*Context gathered: 2026-01-10*
