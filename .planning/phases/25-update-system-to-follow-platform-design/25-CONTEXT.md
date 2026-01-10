# Phase 25: Update System to Follow Platform Design - Context

**Gathered:** 2026-01-10 (updated 2026-01-10)
**Status:** Ready for planning

<vision>
## How This Should Work

Transform the platform into a **premium data product** that commodity traders and investors would pay for. This means moving from basic event scraping to a professional-grade risk intelligence service with:

- **Rich, normalized data**: 30+ fields per event including actors, magnitude metrics, tone scores, commodities, sectors — the depth Bloomberg or Refinitiv provides, not just headlines
- **Consistent category taxonomy**: Every event from every source (GDELT, World Bank, Google Trends, SEC, etc.) maps to one of 10 categories (POLITICAL, CONFLICT, ECONOMIC, TRADE, REGULATORY, INFRASTRUCTURE, HEALTHCARE, SOCIAL, ENVIRONMENTAL, ENERGY) so cross-source analysis just works
- **Explainable scoring**: Risk scores show their work with component contributions (magnitude 30%, tone 20%, velocity 20%, attention 15%, persistence 15%) so analysts can trust and defend the numbers
- **Professional severity**: Industry-standard P1-P4 classification with deterministic auto-triggers for critical events (coups, nationalizations, 10+ fatalities)
- **Scalable architecture**: Extensible canonical model with future-proof hooks — GKG-ready metadata structure, relationship arrays, event lineage tracking — so we can add enhancements without schema migrations

This is the foundation for a premium service — rich canonical data that speaks a consistent language AND scales to handle sophisticated enhancements (GKG themes, entity relationships, temporal patterns) in future phases.

**Premium + Scalable** means we're not just building for today's 30-field model, we're architecting for tomorrow's relationship graphs and narrative tracking. The canonical schema has hooks for:
- GKG themes array (2300+ GDELT categories), quotations, GCAM emotional dimensions
- Entity relationships array (actor1 cooperates with actor2, corporate partnerships, government-military linkages)
- Event lineage array (related_events tracking protest → crackdown → policy change narrative arcs)
- Geographic precision (admin1/admin2 fields ready for Venezuelan state/city-level risk maps)

Phase 25 implements the core canonical model. Phase 26+ populates the enhancement hooks.

</vision>

<essential>
## What Must Be Nailed

- **Category consistency** - This is the cornerstone. The 10-category taxonomy must be rock-solid — every source maps correctly (GDELT CAMEO codes → categories, World Bank indicators → categories, Google Trends terms → categories), no ambiguity, no gaps. If categories are inconsistent, cross-source queries and correlation analysis fall apart.

- **Extensible schema design** - The canonical model must have clean, scalable hooks for future enhancements without breaking changes:
  - GKG-ready metadata structure (themes, quotations, GCAM fields can be added without schema migration)
  - Relationship arrays (empty for now, but typed and ready for Phase 26 entity graph work)
  - Event lineage tracking (related_events array for narrative analysis)
  - This isn't over-engineering — it's architecting for growth so Phase 26+ can enhance without retrofitting

- **Venezuela-tuned weights** - The design document has generic commodity trader weights, but Venezuela intelligence needs tuning:
  - ENERGY weight higher (15-20% vs 10%) — oil is Venezuela's lifeline
  - REGULATORY weight critical (15% vs 12%) — sanctions changes are make-or-break for investors
  - CONFLICT severity lower bar — protests and violence are common, so raise thresholds (maybe 5-9 fatalities is P3, not P2)

- **LLM hybrid approach** - Blend deterministic rules with intelligent enhancement:
  - **Category disambiguation**: Use LLM when mapping is ambiguous (oil protests = ENERGY or SOCIAL?)
  - **Actor extraction**: LLM parses event text to populate actor1_name, actor1_type (GOVERNMENT/MILITARY/CORPORATE), actor2_name, actor2_type
  - **Severity validation**: Deterministic rules classify P1-P4, then LLM validates to catch false positives (e.g., "oil prices kill earnings" shouldn't trigger P1 on 'kill' keyword)

</essential>

<boundaries>
## What's Out of Scope

- **UI updates** - Dashboard and API will expose new fields (P1-P4, category sub-scores, canonical event data), but redesigning the UI to showcase them beautifully is a separate phase. Data model first, visualization enhancement later.

- **Data migration** - No existing data in the database, so this is a clean slate. No backfill, no dual-write period, no gradual rollover. New canonical model applies from day one.

- **Rolling window stats** - Velocity component needs historical baselines (7-day average, standard deviation), but we can default to 0.5 initially and add proper rolling window calculation in a future phase when we have history.

- **Persistence tracking** - Persistence score needs consecutive-day event tracking, but we can use metadata.persistence_days=1 for now and enhance with spike detection later.

- **Populating enhancement hooks** - Phase 25 creates the extensible schema with GKG/relationship/lineage arrays, but Phase 26+ will populate them:
  - GKG themes parsing and quotation extraction (Phase 26)
  - Entity relationship graph building (Phase 26 or 27)
  - Event lineage tracking and narrative analysis (Phase 27 or 28)
  - For now: arrays exist in schema, but remain empty. Clean separation of foundation vs enhancement.

</boundaries>

<specifics>
## Specific Ideas

**Extensible canonical schema (Phase 25):**
- Core 30 fields from design doc (actors, magnitude, tone, confidence, location, commodities, etc.)
- Enhancement arrays (initially empty, ready for Phase 26+):
  - `themes: Array<string>` for GKG V2Themes (2300+ categories)
  - `quotations: Array<{speaker, text, offset}>` for who-said-what tracking
  - `gcam_scores: Object` for GCAM emotional dimensions (fear, anger, joy, etc.)
  - `entity_relationships: Array<{entity1_id, entity2_id, relationship_type}>` for actor networks
  - `related_events: Array<{event_id, relationship_type, timestamp}>` for narrative arcs
- Metadata JSON extensible for source-specific richness
- BigQuery schema supports nested/repeated fields for efficient queries

**Venezuela-specific tuning:**
- ENERGY category weight: 15-20% (up from design doc's 10%)
- REGULATORY category weight: 15% (up from 12%)
- Sanctions keywords auto-trigger P1 severity
- CONFLICT severity thresholds adjusted for Venezuela violence patterns

**LLM enhancement flow:**
1. Deterministic rules classify event → P1/P2/P3/P4
2. LLM validates P1/P2 classifications to catch false positives
3. LLM extracts actors when source data lacks structured actor fields
4. LLM disambiguates category when source mapping is unclear

**Clean slate advantage:**
- No migration complexity
- No backward compatibility constraints
- Canonical model from day one
- Can optimize schema without legacy baggage
- Can add enhancement hooks without retrofitting

**Design document as foundation:**
- Follow platform design formulas exactly (magnitude 30%, tone 20%, velocity 20%, attention 15%, persistence 15%)
- Use P1-P4 severity definitions (P1=CRITICAL with auto-triggers, P2=HIGH, P3=MODERATE, P4=LOW)
- Implement 10-category taxonomy from section 5.1
- Apply source-specific normalizers from section 5.2
- Extend with future-proof arrays for GKG, relationships, lineage

</specifics>

<notes>
## Additional Context

**Premium + Scalable vision** means this isn't just a technical migration — it's laying foundation for a world-class risk intelligence platform. The canonical model should feel authoritative TODAY (rich 30-field data, P1-P4 classification, explainable scoring) AND enable sophisticated enhancements TOMORROW (GKG themes, entity graphs, narrative tracking) without schema surgery.

**Think outside the box = extensible schema**: Instead of just implementing the design doc's 30 fields, we're adding future-proof hooks (themes array, quotations array, entity_relationships array, related_events array). These stay empty in Phase 25, but Phase 26+ can populate them without migration pain. This is smart architecture, not over-engineering.

**Category consistency is non-negotiable** because it enables everything else: cross-source correlation, category sub-scores, daily composite scoring, filtered queries. If a GDELT protest event maps to SOCIAL but a similar ReliefWeb event maps to CONFLICT, the whole system breaks down.

**Venezuela context matters** because generic commodity trader weights don't reflect Venezuela's unique situation. Oil dominance means ENERGY events have outsized impact. Sanctions uncertainty means REGULATORY events are critical. Normalized violence means CONFLICT thresholds need adjustment.

**LLM as intelligent enhancement** (not replacement) preserves reliability while adding flexibility. Deterministic rules are fast, cheap, and predictable. LLM catches edge cases the rules miss and handles unstructured data gracefully.

**Enhancement roadmap** (Phase 26+):
- GKG themes parsing for 2300+ category tags per event
- Quotation extraction for who-said-what tracking
- GCAM emotional dimensions (fear, anger, joy) for sentiment nuance
- Entity relationship graph (cooperates, opposes, funds, reports-to)
- Event lineage tracking for narrative arcs (protest → crackdown → policy change)
- Geographic precision with Venezuelan state/city-level risk maps

</notes>

---

*Phase: 25-update-system-to-follow-platform-design*
*Context gathered: 2026-01-10*
