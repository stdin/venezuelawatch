# Phase 24: BigQuery Public Datasets - Context

**Gathered:** 2026-01-10
**Status:** Ready for research

<vision>
## How This Should Work

Expand VenezuelaWatch's intelligence by integrating 3 high-value BigQuery public datasets: Google Trends (search interest spikes), SEC EDGAR (US company exposure), and World Bank (economic fundamentals). The vision is **entity-centric multi-source intelligence**—when you look at an entity like PDVSA, you see ALL signals converged: GDELT news mentions, Google search trends, SEC filing mentions, World Bank economic data.

The real value is **cross-referencing signals**: Google Trends spike → Wikipedia surge → GDELT coverage → SEC filing mentions creates a complete intelligence picture. These correlations unlock early warning signals (search spikes often precede news coverage) and investment exposure tracking (which US companies are actually exposed to Venezuela risk).

**Architecture approach:** Extend the Phase 22 DataSourceAdapter pattern with new adapters for each BigQuery public dataset (GoogleTrendsAdapter, SecEdgarAdapter, WorldBankAdapter). Respect each data source's native update cadence (Google Trends: daily, SEC EDGAR: as-filed with hourly checks, World Bank: quarterly).

**Phase split:**
- **Phase 24:** Data ingestion + entity linking for 3 sources (foundation)
- **Phase 24.1:** Correlation engine + pattern detection (intelligence layer)

This phase focuses on getting data flowing and entities automatically linked across sources. Correlation logic comes in Phase 24.1.

</vision>

<essential>
## What Must Be Nailed

- **Entity linking across sources** - The critical challenge. Automatically link entities with high confidence across different data sources (PDVSA in SEC filings = Petróleos de Venezuela in World Bank data = "pdvsa" in Google Trends). This is what makes multi-source intelligence possible—without accurate linking, signals don't correlate to the same thing.

- **Research-driven entity matching** - Don't pick a linking approach arbitrarily. Research entity linking best practices thoroughly and implement what's considered best-in-class solution (could be fuzzy matching, entity registry, LLM-powered, hybrid—research determines the right approach).

- **Definition of done** - All 3 sources ingesting on schedule, entities automatically linked across sources, data available via API. No correlation logic yet (that's Phase 24.1), but the foundation must be solid.

</essential>

<boundaries>
## What's Out of Scope

- **UI changes for new data sources** - Don't redesign entity profiles or dashboards in this phase. Focus on backend infrastructure and making entity-linked data available via API. The existing UI already shows entity metadata, so no visual changes needed in Phase 24.

- **Correlation engine** - Pattern detection (temporal clusters, magnitude thresholds) is explicitly Phase 24.1, not Phase 24. This phase delivers the data foundation; Phase 24.1 builds the intelligence layer on top.

- **Historical backfill** - Start with real-time/recent data matching each source's natural cadence. Don't backfill years of historical data in Phase 24 (defer to future phases if needed).

- **All 6 data sources** - Only integrate Google Trends, SEC EDGAR, and World Bank in Phase 24 (top 3 highest-value). The other 3 sources from the original list (NOAA weather, Wikipedia pageviews, crypto) are deferred to future phases.

</boundaries>

<specifics>
## Specific Ideas

**Data sources (top 3):**
1. **bigquery-public-data.google_trends** - Search interest spikes for crisis terms ("Venezuela sanctions", "Venezuela blackout") as leading indicators
2. **bigquery-public-data.sec_edgar** - 10-K/10-Q filings mentioning Venezuela to track US public company exposure
3. **bigquery-public-data.world_bank_*** - GDP, inflation, FDI flows, trade balance, ease of doing business indicators

**Update cadence:**
- Google Trends: daily polling
- SEC EDGAR: hourly checks for new filings (as-filed)
- World Bank: quarterly ingestion

**Entity matching:** Research best practices thoroughly—candidates include:
- Extending Phase 6's RapidFuzz Jaro-Winkler matching (0.85 threshold)
- Building entity alias registry with exact matching
- LLM-powered entity resolution (Claude)
- Hybrid approach (exact → fuzzy → LLM escalation)

The research phase should evaluate accuracy, performance, and cost tradeoffs to determine the right approach.

**Architectural pattern:** Reuse Phase 22 DataSourceAdapter pattern for consistency (GoogleTrendsAdapter, SecEdgarAdapter, WorldBankAdapter classes).

</specifics>

<notes>
## Additional Context

**Why these 3 sources first:**
- **Google Trends:** Leading indicator (search spikes often precede news coverage)
- **SEC EDGAR:** Investment exposure tracking (which US companies are exposed to Venezuela risk)
- **World Bank:** Economic fundamentals (complement GDELT's political/social signals)

These 3 sources are diverse enough to prove the entity-linking architecture works across different data schemas before expanding to the other 3 sources (NOAA, Wikipedia, crypto).

**Phase 24.1 preview (correlation engine):**
Once entity-linked data is flowing, Phase 24.1 will build pattern detection for:
- **Temporal clusters:** Google Trends spike within 48hrs of SEC filing mention = high-confidence emerging risk
- **Magnitude thresholds:** Search interest >200% increase + World Bank indicator drop >10% = crisis signal

Correlation insights will be stored as structured metadata on entities/events so the existing UI already surfaces them without requiring UI changes.

**Why split Phase 24 and 24.1:**
Phase 24 is substantial: 3 data sources + entity linking + API integration. Splitting gives a clear checkpoint—prove entity linking works with real data before building correlation logic on top. If linking doesn't work well, correlation will be garbage.

</notes>

---

*Phase: 24-bigquery-public-datasets*
*Context gathered: 2026-01-10*
