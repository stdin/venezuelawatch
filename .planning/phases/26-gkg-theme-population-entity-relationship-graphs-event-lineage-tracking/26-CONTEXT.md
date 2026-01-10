# Phase 26: GKG Theme Population, Entity Relationship Graphs, Event Lineage Tracking - Context

**Gathered:** 2026-01-10
**Status:** Ready for planning

<vision>
## How This Should Work

This phase builds an **interactive entity relationship graph** that surfaces non-obvious intelligence patterns - indirect connections, sanctioned entity clusters, hidden networks. Users see a visual web of connections between people, companies, and governments with high-risk areas automatically highlighted.

When you open the graph, it **automatically focuses on high-risk clusters** - no manual searching needed. The system identifies the most interesting networks and puts them front and center.

**Event lineage tracking** creates the story behind the connections. Click on any relationship edge in the graph and you see an **LLM-generated narrative** explaining how these entities are connected through specific events - "After US sanctions on Person A were announced, this led to Company B's bankruptcy, which triggered supply chain disruptions in Country C."

**GKG themes** enrich this intelligence by providing categorical context (ECON_TRADE, SANCTIONS, CIVIL_UNREST) and identifying entity clusters based on thematic patterns. Themes help you understand not just WHO is connected, but WHAT types of activities connect them.

All three capabilities work together: themes provide context, graphs show networks, narratives explain the connections.

</vision>

<essential>
## What Must Be Nailed

- **Insight discovery** - The graph must surface patterns that aren't obvious from individual events alone. Non-obvious connections, hidden networks, indirect relationships.

- **Relationship quality** - Connections must be real and meaningful, based on:
  - **Repeated co-occurrence** across multiple events over time (not one-off mentions)
  - **Directional and weighted** relationships with strength indicators
  - **Verifiable from sources** - every edge traces back to specific events/articles

- **Narratives as edge annotations** - When users click relationships, they get LLM-generated stories explaining HOW and WHY entities are connected through event sequences

- **Auto-surface high-risk clusters** - Graph immediately shows the most critical intelligence without requiring manual search

</essential>

<boundaries>
## What's Out of Scope

**Nothing explicitly excluded** - all three capabilities (GKG themes, relationship graphs, event lineage) are in scope for Phase 26 as named.

However, defer complexity where possible:
- Start with core relationship types (sanctions, employment, trade, adversarial)
- Basic graph interactivity first, advanced features (filtering, time ranges) can evolve
- Focus on getting insight discovery working, then refine performance

</boundaries>

<specifics>
## Specific Ideas

**Graph entry point:** Auto-focus on high-risk clusters when opening the visualization - put the most important intelligence front and center immediately.

**Relationship criteria:**
- Repeated co-occurrence signals persistent relationships
- Directional edges (A sanctioned B, not just "A and B are related")
- Weighted by strength of evidence
- Verifiable - click through to source events

**Event lineage:** LLM-generated narratives that explain causal chains - "Sanctions announcement → Port closure → Food shortage → Protests"

**Theme roles:**
- Enrich event context in narratives (categorize what happened)
- Clustering signal to identify thematic entity groups (all entities in OIL_EXPORT events)

**Interactive graph:** Click on entities to explore, click on edges to see narratives, visual indicators for risk levels and relationship types

</specifics>

<notes>
## Additional Context

The emphasis on **insight discovery** means the graph should reveal patterns invisible in individual events - this is the core value proposition.

**Relationship quality** was a key concern - not just co-mentions, but evidence-based connections users can verify and trust.

Integration vision: Themes and lineage both support the graph - themes cluster and contextualize, lineage narratives explain the connections.

All three capabilities (themes, graphs, lineage) should ship together in Phase 26 to deliver the complete intelligence experience.

</notes>

---

*Phase: 26-gkg-theme-population-entity-relationship-graphs-event-lineage-tracking*
*Context gathered: 2026-01-10*
