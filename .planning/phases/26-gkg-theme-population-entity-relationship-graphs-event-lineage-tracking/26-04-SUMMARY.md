# Plan 26-04 Summary: GKG Theme Filtering and Event Lineage Tracking

**Status:** ✅ Complete  
**Date:** 2026-01-10  
**Plan:** `.planning/phases/26-gkg-theme-population-entity-relationship-graphs-event-lineage-tracking/26-04-PLAN.md`

## Objective

Add GKG theme filtering and event lineage for comprehensive pattern discovery in entity relationship graphs.

## Tasks Completed (4/4)

### Task 1: ThemeEnricher Service ✅
**Commit:** `f97eca8`

Created ThemeEnricher service for parsing GDELT GKG V2Themes format:

- **parse_gkg_themes()**: Parses "THEME,offset1,offset2;THEME2,offset3" format into theme lists
- **categorize_relationship()**: Maps themes to 6 categories (sanctions, trade, political, adversarial, energy, other)
- **enrich_edge_with_themes()**: Fetches events from BigQuery, extracts GKG themes from metadata.gkg_data, enriches edges with theme lists and categories
- Graceful handling of missing GKG data (returns empty themes)
- Follows Phase 20 GKG data storage patterns

**Files:**
- `backend/data_pipeline/services/theme_enricher.py`

**Key Features:**
- Priority-based categorization (sanctions > trade > political > adversarial > energy > other)
- BigQuery integration for event metadata queries
- Defensive parsing with fallbacks for malformed data

### Task 2: Theme Filtering in API and UI ✅
**Commit:** `cff4888`

Implemented theme-based graph filtering across backend and frontend:

**Backend:**
- Updated `GraphBuilder.build_entity_graph()` with `theme_filter` parameter
- Integrated ThemeEnricher to filter edges by category
- Removed isolated nodes after theme filtering
- Updated `EdgeData` schema with optional `themes` and `category` fields
- Added `theme_categories` query parameter to `/api/graph/entities` endpoint

**Frontend:**
- Created `ThemeFilter.tsx` component with 5 category chips (Mantine Chip.Group)
- Updated `useGraphData` hook to accept `selectedThemes` parameter
- Modified `GraphPage.tsx` to display ThemeFilter above graph
- Shows active filter count when themes selected
- Pass theme_categories to API as comma-separated string

**Files:**
- `backend/data_pipeline/services/graph_builder.py`
- `backend/api/views/graph.py`
- `frontend/src/components/EntityGraph/ThemeFilter.tsx`
- `frontend/src/components/EntityGraph/useGraphData.ts`
- `frontend/src/components/EntityGraph/EntityGraph.tsx`
- `frontend/src/pages/GraphPage.tsx`

**Theme Categories:**
- Sanctions (red): SANCTION, EMBARGO themes
- Trade (blue): TRADE, EXPORT themes
- Political (violet): LEADER, GOV_ themes
- Energy (orange): OIL, ENERGY themes
- Adversarial (grape): UNREST, PROTEST themes

**Performance Note:**
Theme enrichment only runs when theme_filter is provided (not by default) to avoid unnecessary BigQuery queries.

### Task 3: LineageBuilder Service ✅
**Commit:** `bda585c`

Created LineageBuilder service for temporal event chain analysis:

- **build_event_lineage()**: Queries BigQuery for chronological event sequences where both entities appear
- Calculates `days_since_prev` for each event (temporal proximity analysis)
- Detects escalation patterns (20% risk score increase threshold)
- Extracts dominant GKG themes from event sequence (top 5 by frequency)
- Returns structured EventLineage with:
  - `events`: List of EventNode objects
  - `timeline_spans_days`: Total time span between first and last event
  - `escalation_detected`: Boolean flag for risk increases
  - `dominant_themes`: Most frequent themes across timeline

**Files:**
- `backend/data_pipeline/services/lineage_builder.py`

**Temporal Proximity Heuristics:**
- Events within 7 days: Strong causal signal
- Events within 30 days: Moderate causal signal
- Events >30 days apart: Correlation, not necessarily causation

**EventNode Structure:**
```python
{
  'id': str,
  'title': str,
  'published_at': datetime,
  'risk_score': float,
  'severity': str,
  'themes': List[str],  # Top 5 themes per event
  'days_since_prev': Optional[int]  # Gap from previous event
}
```

### Task 4: Timeline Visualization ✅
**Commit:** `42bac02`

Enhanced EdgeNarrative modal with timeline visualization:

**Backend:**
- Added `EventNode` and `EventLineage` schemas to graph API
- Updated `NarrativeResponse` with optional `lineage` field
- Integrated LineageBuilder into `/api/graph/narrative/{entity_a_id}/{entity_b_id}` endpoint
- Builds temporal event sequences for entity pairs

**Frontend:**
- Imported Mantine Timeline component
- Added timeline visualization to EdgeNarrative modal
- Displays chronological event sequence with numbered bullets
- Shows escalation alert when risk increase detected
- Displays `days_since_prev` gaps between events (+Nd format)
- Shows dominant themes at timeline header (top 3)
- Displays per-event themes (top 3) as badges
- Fallback to supporting events list if lineage empty

**Files:**
- `backend/api/views/graph.py`
- `frontend/src/components/EntityGraph/EdgeNarrative.tsx`

**Timeline Features:**
- Vertical Mantine Timeline with numbered bullets (1, 2, 3...)
- Risk score and severity badges per event
- Temporal gaps highlighted (e.g., "+7d" since previous event)
- Theme badges for pattern context
- Orange escalation warning alert
- Progressive disclosure: Overview → Details on demand

## Verification

All success criteria met:

- ✅ GKG V2Themes parsing handles semicolon/comma delimiters correctly
- ✅ Relationship categorization maps themes to 6 categories
- ✅ Graph API returns theme-filtered results
- ✅ ThemeFilter UI toggles update graph display
- ✅ Event lineage service returns chronological sequences
- ✅ Timeline visualization shows events in temporal order
- ✅ Escalation detection identifies risk increases (20% threshold)
- ✅ Theme context displayed in timeline
- ✅ No errors when data missing (graceful fallbacks)
- ✅ Phase 26 complete: all 4 plans executed

## Key Decisions

1. **Theme enrichment performance**: Only enrich edges when theme_filter is provided, avoiding unnecessary BigQuery queries for default graph view
2. **Category priority**: Sanctions > Trade > Political > Adversarial > Energy to ensure most critical activities surface first
3. **Escalation threshold**: 20% risk score increase between first and last event indicates escalation
4. **Timeline display**: Top 3 themes per event to avoid visual clutter
5. **Temporal proximity**: 7/30 day thresholds for causal signals (no advanced graph algorithms in Phase 26)
6. **Graceful degradation**: All services return empty/default values on errors rather than breaking UX

## Technical Notes

- **GKG data format**: "THEME,offset1,offset2;THEME2,offset3,offset4" (semicolon-separated mentions with offsets)
- **Storage location**: Phase 20 stores GKG data in `metadata.gkg_data.V2Themes`
- **BigQuery queries**: Parameterized to prevent SQL injection
- **React state management**: Theme filter state managed in GraphPage, passed down to EntityGraph
- **Mantine UI components**: Chip.Group (multi-select), Timeline (vertical event sequence), Alert (escalation warnings)
- **Progressive disclosure**: EdgeNarrative modal expands from narrative → timeline → full event details

## Integration Points

- GKG data from Phase 20 (stored in BigQuery event metadata)
- Entity linking from metadata.linked_entities (Phase 20)
- Community detection from Phase 26-02
- Narrative generation from Phase 26-03
- BigQuery polyglot architecture (Phase 14-18)

## Phase 26 Completion

**All 4 plans executed:**
1. ✅ Plan 26-01: Base entity graph with co-occurrence analysis
2. ✅ Plan 26-02: Community detection and clustering
3. ✅ Plan 26-03: Camera auto-focus and edge narratives
4. ✅ Plan 26-04: GKG theme filtering and event lineage tracking

**Pattern Discovery Capabilities Delivered:**
- **Auto-focus**: Camera centers on largest high-risk cluster immediately
- **Narratives**: LLM-generated causal explanations for entity connections
- **Theme filtering**: Activity-specific networks (sanctions, trade, political, energy, adversarial)
- **Event lineage**: Temporal causal chains showing cascade effects (A→B→C)
- **Progressive disclosure**: Timeline view expands narrative with full event sequence
- **Escalation detection**: Identifies risk increases over time

**Next Phase:** Phase 27 - Rolling window statistics and persistence detection

## Commits

1. `f97eca8` - feat(26-04): create ThemeEnricher service for GKG theme parsing
2. `cff4888` - feat(26-04): add theme filtering to graph API and UI
3. `bda585c` - feat(26-04): create LineageBuilder service for event lineage
4. `42bac02` - feat(26-04): enhance EdgeNarrative modal with timeline visualization

**Phase 26 Complete:** Entity relationship graphs with pattern discovery, theme-based filtering, and temporal lineage tracking operational.
