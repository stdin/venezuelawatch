# Phase 25 Plan 01: Canonical Event Model & Category System Summary

**Implemented canonical data model with 10-category taxonomy across all sources**

## Accomplishments

- Extended BigQuery Event schema from 12 to 42 fields total (30+ canonical fields + legacy fields)
- Added 5 future-proof enhancement arrays: themes (GKG), quotations, gcam_scores, entity_relationships, related_events (initially empty, ready for Phase 26+)
- Implemented 10-category classification (POLITICAL, CONFLICT, ECONOMIC, TRADE, REGULATORY, INFRASTRUCTURE, HEALTHCARE, SOCIAL, ENVIRONMENTAL, ENERGY)
- Created CategoryClassifier with source-specific mapping logic (GDELT CAMEO, ACLED types, WB indicators, Trends terms, SEC keywords, FRED series, Comtrade codes)
- Updated adapters with canonical normalizers (GDELT GoldsteinScale→magnitude, AvgTone→tone, World Bank pct_change, Google Trends interest)
- BigQuery schema supports REPEATED/STRUCT for nested arrays (themes[], quotations[], relationships[])
- Validation enforces 10 categories, direction enum (POSITIVE/NEGATIVE/NEUTRAL), 0-1 normalized fields

## Files Created/Modified

- `backend/api/bigquery_models.py` - Extended Event dataclass to canonical schema (42 fields)
- `migrations/create_canonical_events_table.sql` - BigQuery DDL for canonical table with REPEATED/STRUCT support
- `backend/data_pipeline/services/category_classifier.py` - 10-category classification system for all 7 sources
- `backend/data_pipeline/adapters/gdelt_adapter.py` - Canonical normalizer for GDELT (GoldsteinScale, AvgTone, CAMEO codes)
- `backend/data_pipeline/adapters/world_bank_adapter.py` - Canonical normalizer for World Bank (percent_change, indicator prefixes)
- `backend/data_pipeline/adapters/google_trends_adapter.py` - Canonical normalizer for Google Trends (interest score, spike ratio)

## Decisions Made

- **Extensible schema architecture**: Added 5 enhancement arrays (themes, quotations, gcam_scores, entity_relationships, related_events) in Phase 25 even though they remain empty — enables Phase 26+ to populate without schema migration. This is not over-engineering; it's architecting for growth.

- **Schema extension (not migration)**: Kept existing Event fields (title, content, risk_score, severity) to avoid breaking current usage. Added canonical fields alongside legacy fields. Field name change: `mentioned_at` → `event_timestamp` for clarity (aligns with design doc terminology).

- **Subcategory stores source-specific code**: CAMEO code for GDELT, indicator ID for World Bank, search term for Google Trends. This preserves traceability to original source taxonomies.

- **Default fallbacks for unknown categories**:
  - POLITICAL for news/events when no mapping exists
  - ECONOMIC for data series when no mapping exists
  - Ensures every event gets a category

- **Phase 24 entity linking preserved**: `metadata.linked_entities` unchanged. Phase 26 will migrate to canonical `entity_relationships` array.

- **BigQuery REPEATED/STRUCT for arrays**: Native support for nested data, efficient queries, no JSON parsing overhead. Better than storing arrays as JSON strings.

- **Validation in __post_init__**: Event creation fails fast on invalid category, direction, or out-of-range normalized values. Prevents bad data from entering the system.

- **GKG data preserved in metadata**: Phase 25 stores GKG themes/quotations in `metadata.gkg_data` for backward compatibility. Phase 26 will migrate to canonical enhancement arrays (`themes`, `quotations`, `gcam_scores`).

- **Simplified actor classification for Phase 25**: Heuristic-based actor type classification (GOV→GOVERNMENT, MIL→MILITARY, BUS→CORPORATE). Phase 26+ will use LLM for better accuracy.

- **Commodity/sector extraction from GKG themes**: Simple keyword matching (OIL, GOLD, GAS) for Phase 25. Phase 26+ will use GKG theme taxonomy mapping for comprehensive coverage.

- **World Bank percent_change calculation**: For Phase 25, uses same-batch previous value. Phase 26+ will query BigQuery for accurate historical comparison.

- **Google Trends spike detection**: Baseline interest = 25 for Phase 25. Phase 26+ will query historical data for dynamic baselines.

## Issues Encountered

None

## Next Step

Ready for 25-02-PLAN.md (P1-P4 severity system and composite scoring)

---

## Technical Notes

**Event dataclass validation** (backend/api/bigquery_models.py:106-139):
- Category must be one of 10 valid categories
- Direction must be POSITIVE, NEGATIVE, or NEUTRAL
- magnitude_norm, tone_norm, confidence, source_credibility must be 0-1
- Raises ValueError on invalid values

**CategoryClassifier** (backend/data_pipeline/services/category_classifier.py):
- GDELT: CAMEO root code (01-20) → category mapping
- ACLED: event_type string → category mapping
- World Bank: indicator code prefix → category mapping
- Google Trends: search term keywords → category mapping
- SEC EDGAR: context text keywords → category mapping
- FRED: series ID patterns → category mapping
- UN Comtrade: commodity code (HS 2-digit) → category mapping

**GDELT normalizer** (backend/data_pipeline/adapters/gdelt_adapter.py:181-430):
- GoldsteinScale (-10 to +10) → magnitude_norm (0-1)
- AvgTone → tone_norm (inverted: negative tone → higher risk)
- Direction based on GoldsteinScale thresholds (-2, +2)
- Confidence = min(num_sources/10, 1.0) * 0.7
- Actor types from actor codes (heuristic-based)
- Commodities/sectors from GKG themes (keyword matching)

**World Bank normalizer** (backend/data_pipeline/adapters/world_bank_adapter.py:172-350):
- Percent change calculation from previous value
- magnitude_norm = min(abs(pct_change)/50, 1.0)
- Direction semantics: some indicators are "bad news" (inflation↑=NEGATIVE), others "good news" (GDP↑=POSITIVE)
- Source credibility 0.95 (World Bank is authoritative)

**Google Trends normalizer** (backend/data_pipeline/adapters/google_trends_adapter.py:112-311):
- Interest score 0-100 → magnitude_norm (0-1)
- Spike ratio calculation (interest / baseline)
- tone_norm = min(spike_ratio/5, 1.0)
- Direction always NEGATIVE (elevated attention = concern)
- Source credibility 0.8 (indirect signal)
- Event type: SEARCH_SPIKE if spike_ratio > 2, else SEARCH_LEVEL

**BigQuery schema** (migrations/create_canonical_events_table.sql):
- Partitioned by DATE(event_timestamp) for efficient time-series queries
- Indexes on category, severity, source, direction for fast filtering
- REPEATED fields for arrays (commodities, sectors, themes)
- STRUCT fields for nested objects (quotations, entity_relationships, related_events)
- JSON field for metadata (source-specific payloads)

**Enhancement arrays (Phase 26+ roadmap)**:
- `themes`: GKG V2Themes (2300+ categories), populated from metadata.gkg_data.themes
- `quotations`: {speaker, text, offset} from GKG quotations
- `gcam_scores`: {fear, anger, joy, sadness, surprise, disgust} from GKG GCAM
- `entity_relationships`: {entity1_id, entity2_id, relationship_type} from actor network analysis
- `related_events`: {event_id, relationship_type, timestamp} from narrative lineage tracking
