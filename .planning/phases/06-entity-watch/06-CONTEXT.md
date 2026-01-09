# Phase 6: Entity Watch - Context

**Gathered:** 2026-01-08
**Status:** Ready for research

<vision>
## How This Should Work

The system automatically discovers and surfaces the most important entities (people, companies, government organizations) from the event stream. Users don't need to know who to look for — Entity Watch tells them who's important right now.

The core is an entity leaderboard showing trending entities with different metric toggles: "Most mentioned this week," "Highest risk," "Recently sanctioned." Users can switch between these lenses to understand importance from different angles.

This lives as a separate "Entities" tab in the navigation — a distinct view from the events feed. Users can switch between event-centric view (Phase 5) and entity-centric view (Phase 6) depending on what they're investigating.

When someone clicks an entity from the leaderboard, they see a basic profile card with quick summary info: entity type, sanctions status, risk score, mention count, and recent events mentioning them.

</vision>

<essential>
## What Must Be Nailed

- **Discovery & trending** - Surfacing who's important right now is the core value. Users shouldn't have to know who to look for. The system identifies key entities automatically from the event stream.
- **Metric toggles** - Different lenses on importance (most mentioned, highest risk, recently sanctioned) let users explore entities from multiple angles.
- **Auto-discovery only** - Entities appear because they're mentioned in events, not because users manually added them. The intelligence emerges from the data.

</essential>

<boundaries>
## What's Out of Scope

- **Manual entity creation** - Users cannot manually add entities to track. Only system-discovered entities appear on the leaderboard.
- **Relationship graphs** - No network visualization showing connections between entities. That's too complex for Phase 6.
- **Historical timelines** - No full timeline/history view for entities. Focus on recent mentions and current status only.
- **Entity search bar** - Discovery-only interface. However, basic filtering or clicking through from events is acceptable.

</boundaries>

<specifics>
## Specific Ideas

- Entity leaderboard with metric toggles: "Most mentioned," "Highest risk," "Recently sanctioned"
- Treat all entity types equally (people, companies, government entities)
- Basic profile card on click showing: entity type, sanctions status, risk score, mention count, recent events
- Separate tab/page in navigation (e.g., "Entities" alongside "Events")
- Lightweight and scannable — like a sports leaderboard

</specifics>

<notes>
## Additional Context

The key differentiator from Phase 5 is the shift from event-centric to entity-centric intelligence. Phase 5 shows "what happened," Phase 6 shows "who's important."

Entity Watch builds on existing Phase 4 risk intelligence (sanctions screening, risk scores) and Phase 5 event data. The challenge is extraction and aggregation — identifying entities from unstructured event text and rolling up their mentions, sanctions status, and risk signals into meaningful profiles.

Users are investors and operators who need to know: "Who should I be watching right now?" The answer should be immediate and data-driven, not dependent on users already knowing the Venezuela landscape.

</notes>

---

*Phase: 06-entity-watch*
*Context gathered: 2026-01-08*
