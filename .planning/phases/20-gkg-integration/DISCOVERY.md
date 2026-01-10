# Phase 20: GKG Integration Discovery

**Date:** 2026-01-10
**Discovery Level:** Level 1 (Quick Verification)
**Duration:** 10 minutes

## Objective

Understand GDELT Global Knowledge Graph (GKG) schema and join strategy to enrich Venezuela event data with themes, entities, locations, and tone analysis.

## GKG Schema Analysis

### Table Characteristics

- **Dataset:** `gdelt-bq.gdeltv2.gkg_partitioned`
- **Size:** 19.5 TB (55x larger than Events table at 351 GB)
- **Rows:** 1.76 billion records
- **Partitioning:** DAY partition on `_PARTITIONTIME`

### Key Fields (27 total)

**Entity Extraction:**
- `Persons`, `V2Persons` - Person entities extracted from articles
- `Organizations`, `V2Organizations` - Organization entities
- `AllNames` - All named entities combined

**Thematic Analysis:**
- `Themes`, `V2Themes` - Thematic categorization (e.g., CIVILIAN, CONFLICT, ECON_CURRENCY)
- `GCAM` - Global Content Analysis Measures (emotional dimensions)
- `V2Tone` - Sentiment/tone metrics

**Location Intelligence:**
- `Locations`, `V2Locations` - Enhanced location data with lat/long

**Content:**
- `Quotations` - Direct quotes from articles
- `Dates` - Temporal references in text
- `Amounts` - Numerical amounts mentioned

**Metadata:**
- `GKGRECORDID` - Unique identifier
- `DATE` - Event date (YYYYMMDDHHMMSS format)
- `DocumentIdentifier` - Source URL (join key)
- `SourceCommonName` - Publisher name

## Join Strategy

### Three-Table Relationship

```
Events → EventMentions → GKG
```

**Join Path:**
1. Events.GLOBALEVENTID → EventMentions.GLOBALEVENTID
2. EventMentions.MentionIdentifier → GKG.DocumentIdentifier

**Key Insight:** DocumentIdentifier is typically the source article URL, matching Events.SOURCEURL

### Recommended Approach for Venezuela Events

**Optimized strategy (avoid 3-table join):**
```sql
-- Filter Events first (already done in Phase 19)
-- Then fetch matching GKG records by DocumentIdentifier

SELECT gkg.*
FROM `gdelt-bq.gdeltv2.gkg_partitioned` gkg
WHERE gkg.DocumentIdentifier = @source_url
  AND _PARTITIONTIME >= @start_time
  AND _PARTITIONTIME < @end_time
```

This leverages our existing Venezuela event filtering (ActionGeo_CountryCode='VE') and avoids massive 3-table joins.

## Data Format

**STRING fields are delimited lists:**
- `V2Themes`: Semicolon-separated (e.g., "ECON_CURRENCY;CIVILIAN;PROTEST")
- `V2Persons`: Complex format with counts (e.g., "Person Name,Offset,Length;...")
- `V2Organizations`: Same format as Persons
- `V2Locations`: Includes lat/long (e.g., "2#Venezuela#VE#VE##-8#-66#VE#USVE#Venezuela;...")

**Parsing required** for all enrichment fields.

## Implementation Notes

**Performance Considerations:**
- GKG table is 55x larger than Events - query efficiency critical
- Use partition filtering on _PARTITIONTIME always
- Fetch GKG data only for Venezuela events (post-filter, not pre-join)
- Parse delimited strings in Python (not BigQuery) for flexibility

**Integration Pattern:**
1. Fetch Venezuela events (existing Phase 19 logic)
2. For each event with SOURCEURL, query GKG by DocumentIdentifier
3. Parse GKG fields (Themes, Persons, Orgs, Locations, V2Tone)
4. Store in event metadata JSON field (existing pattern)

**V2 vs V1 Fields:**
- Prefer V2 versions (V2Themes, V2Persons, etc.) - newer, richer format
- V1 fields can be ignored for new development

## References

- GDELT GKG Codebook: http://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf
- GDELT BigQuery Documentation: https://blog.gdeltproject.org/complex-queries-combining-events-eventmentions-and-gkg/
- Schema exploration: `backend/scripts/query_gdelt_schema.py`

## Decisions

1. **Join strategy:** Document Identifier-based lookup (not 3-table join) for performance
2. **Field selection:** Focus on V2 fields (Themes, Persons, Organizations, Locations, Tone)
3. **Parsing location:** Python-side parsing (not BigQuery STRING functions) for maintainability
4. **Storage pattern:** Extend existing metadata JSON field with gkg_* keys

## Next Steps

Phase 20 will implement:
1. GKG BigQuery service with DocumentIdentifier queries
2. GKG field parsers for delimited string formats
3. Integration with existing sync pipeline
4. Enhanced entity extraction using GKG Persons/Organizations data
