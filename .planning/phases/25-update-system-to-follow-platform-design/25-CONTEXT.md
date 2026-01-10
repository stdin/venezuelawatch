# Phase 25: Update System to Follow Platform Design - Context

**Gathered:** 2026-01-10
**Status:** Ready for planning

<vision>
## How This Should Work

Transform the platform into a **premium data product** that commodity traders and investors would pay for. This means moving from basic event scraping to a professional-grade risk intelligence service with:

- **Rich, normalized data**: 30+ fields per event including actors, magnitude metrics, tone scores, commodities, sectors — the depth Bloomberg or Refinitiv provides, not just headlines
- **Consistent category taxonomy**: Every event from every source (GDELT, World Bank, Google Trends, SEC, etc.) maps to one of 10 categories (POLITICAL, CONFLICT, ECONOMIC, TRADE, REGULATORY, INFRASTRUCTURE, HEALTHCARE, SOCIAL, ENVIRONMENTAL, ENERGY) so cross-source analysis just works
- **Explainable scoring**: Risk scores show their work with component contributions (magnitude 30%, tone 20%, velocity 20%, attention 15%, persistence 15%) so analysts can trust and defend the numbers
- **Professional severity**: Industry-standard P1-P4 classification with deterministic auto-triggers for critical events (coups, nationalizations, 10+ fatalities)

This is the foundation for a premium service — rich canonical data that speaks a consistent language.

</vision>

<essential>
## What Must Be Nailed

- **Category consistency** - This is the cornerstone. The 10-category taxonomy must be rock-solid — every source maps correctly (GDELT CAMEO codes → categories, World Bank indicators → categories, Google Trends terms → categories), no ambiguity, no gaps. If categories are inconsistent, cross-source queries and correlation analysis fall apart.

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

</boundaries>

<specifics>
## Specific Ideas

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

**Design document as foundation:**
- Follow platform design formulas exactly (magnitude 30%, tone 20%, velocity 20%, attention 15%, persistence 15%)
- Use P1-P4 severity definitions (P1=CRITICAL with auto-triggers, P2=HIGH, P3=MODERATE, P4=LOW)
- Implement 10-category taxonomy from section 5.1
- Apply source-specific normalizers from section 5.2

</specifics>

<notes>
## Additional Context

**Premium data product vision** means this isn't just a technical migration — it's a quality bar. The canonical model should feel authoritative, the categories should be unambiguous, the scoring should be defensible to a skeptical analyst.

**Category consistency is non-negotiable** because it enables everything else: cross-source correlation, category sub-scores, daily composite scoring, filtered queries. If a GDELT protest event maps to SOCIAL but a similar ReliefWeb event maps to CONFLICT, the whole system breaks down.

**Venezuela context matters** because generic commodity trader weights don't reflect Venezuela's unique situation. Oil dominance means ENERGY events have outsized impact. Sanctions uncertainty means REGULATORY events are critical. Normalized violence means CONFLICT thresholds need adjustment.

**LLM as intelligent enhancement** (not replacement) preserves reliability while adding flexibility. Deterministic rules are fast, cheap, and predictable. LLM catches edge cases the rules miss and handles unstructured data gracefully.

</notes>

---

*Phase: 25-update-system-to-follow-platform-design*
*Context gathered: 2026-01-10*
