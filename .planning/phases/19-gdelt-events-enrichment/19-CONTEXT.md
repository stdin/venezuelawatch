# Phase 19: GDELT Events Enrichment - Context

**Gathered:** 2026-01-10
**Status:** Ready for planning

<vision>
## How This Should Work

This is a complete replacement — swap out the current 4 basic fields and rebuild everything around GDELT's full 61-field schema. We're not doing an additive enrichment or phased migration. It's a clean break.

The full schema is the point. Use all 61 fields:
- **Quotations**: Direct quotes from articles for sentiment without LLM processing
- **Themes**: Pre-categorized topics (ECON_CRISIS, TAX_FNCACT, etc) for instant event classification
- **Tone & Goldstein scale**: Built-in sentiment scores and conflict/cooperation metrics
- **Counts & mentions**: Article counts, mention frequency for trending/importance signals
- **Images & media**: Image URLs and media references for richer event presentation

The vision is source-specific schemas. GDELT gets its native 61-field structure. When we add other data sources later (FRED, ReliefWeb, etc.), they each keep their native fields too. Each source has its own schema, stored separately in BigQuery.

This isn't just about getting more GDELT data — it's about building the foundation so adding other source schemas is trivial later.

</vision>

<essential>
## What Must Be Nailed

- **Future-proof architecture** - Build this so adding other data sources with their own schemas is straightforward. The architecture is more important than the immediate feature set. Get the foundation right.

</essential>

<boundaries>
## What's Out of Scope

Nothing specific — use the new fields right away. Don't artificially limit what gets used. The full 61-field schema should be immediately available to:
- Intelligence pipeline (even though major intelligence rebuild is Phase 23)
- Dashboard/chat (even though UI updates might be needed)
- Any other part of the system that queries event data

</boundaries>

<specifics>
## Specific Ideas

No specific implementation requirements — open to the best approach for:
- BigQuery table structure
- Data type handling for GDELT's 61 fields
- Migration strategy from current 4-field to 61-field schema

Trust the builder to figure out the right implementation patterns.

</specifics>

<notes>
## Additional Context

The key insight is **scalability for multiple data sources**. This phase sets the pattern for how VenezuelaWatch handles diverse data with source-specific schemas, not forced into a unified event format.

GDELT is the first, but the architecture should make adding a new data source with 20 fields or 200 fields equally straightforward.

</notes>

---

*Phase: 19-gdelt-events-enrichment*
*Context gathered: 2026-01-10*
