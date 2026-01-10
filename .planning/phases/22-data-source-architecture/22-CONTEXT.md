# Phase 22: Data Source Architecture - Context

**Gathered:** 2026-01-09
**Status:** Ready for planning

<vision>
## How This Should Work

This phase is about creating a clean, extensible plugin architecture for data sources. The system should work like this:

**Plugin-style adapters:** Each data source (GDELT, future sources like ReliefWeb, World Bank, etc.) implements a common adapter interface with standardized methods: `fetch()`, `transform()`, `validate()`. The pipeline calls the same interface regardless of which source it's talking to.

**Convention-based discovery:** Drop a new adapter file in `data_pipeline/adapters/`, follow naming conventions (file: `source_adapter.py`, class: `SourceAdapter`), declare metadata as class attributes - and it's automatically discovered by the system. No manual registration, no touching existing code.

**GDELT as the gold standard:** The GDELT adapter is rewritten from scratch as a reference implementation - clean, well-documented, demonstrating best practices. When someone needs to add a new data source, they look at the GDELT adapter and immediately understand what to do.

**Decoupled data flow:** After an adapter validates data, it publishes events to Pub/Sub for async processing. The adapter's job ends at validation - downstream subscribers handle BigQuery insertion and intelligence pipeline triggering.

**Full observability:** The system knows what adapters exist, tracks their health metrics (last run, failure count, processing time), and allows manual triggering for testing or backfills.

</vision>

<essential>
## What Must Be Nailed

- **Clear path to add new sources** - The adapter pattern is so clean and well-documented that adding a future data source (like ReliefWeb or World Bank) is straightforward. This is the PRIMARY goal. The architecture should make it obvious how to extend the system.

- **Zero behavior change for GDELT** - While GDELT gets rewritten as a reference implementation, it must work EXACTLY as it does now. Same data, same frequency, same results. This is internal refactoring, not feature changes.

- **Reference implementation quality** - The GDELT adapter serves as the blueprint for all future adapters. It must have:
  - Clear docstrings on every method
  - Inline comments explaining GDELT-specific quirks vs what other adapters might do differently
  - Comprehensive type hints throughout

</essential>

<boundaries>
## What's Out of Scope

- **Performance optimization or caching** - Focus on architecture and extensibility, not performance improvements
- **Actually adding new data sources** - This phase only creates the architecture and migrates GDELT. Future sources (ReliefWeb, World Bank, etc.) come later
- **Advanced retry logic** - Keep error handling simple for now (partial success publishing, basic logging)

</boundaries>

<specifics>
## Specific Ideas

**Abstract Base Class pattern:**
- Use Python ABC with `abc.abstractmethod` decorators
- Forces implementations to define required methods
- Provides clear type contracts via comprehensive type hints

**Discovery conventions:**
- File location: `data_pipeline/adapters/`
- File naming: `{source}_adapter.py` (e.g., `gdelt_adapter.py`)
- Class naming: `{Source}Adapter` (e.g., `GdeltAdapter`)
- Metadata: Class attributes like `source_name`, `schedule_frequency`, `data_schema`

**Data flow architecture:**
- Adapter methods: `fetch()` → `transform()` → `validate()` → publish to Pub/Sub
- Each method has clear inputs/outputs defined by ABC
- Partial success publishing: if 100 events fetched but 1 fails validation, publish 99 and log the failure

**Integration points:**
- Cloud Functions use adapters for scheduled ingestion (like current GDELT sync function)
- Intelligence pipeline processes any adapter's output (source-agnostic)
- Admin/monitoring tools show adapter registry, health metrics, manual triggers

**Testing approach:**
- Integration test with real BigQuery for GDELT adapter
- Validates the full pipeline end-to-end as reference for future adapters

</specifics>

<notes>
## Additional Context

This architecture sets the foundation for Phase 25 (Add More BigQuery Data Sources) and any future data integrations. The key insight is that GDELT shouldn't be special-cased - it should be one implementation of a general pattern.

The rewrite of GDELT as a reference implementation is intentional: it's an investment in making the codebase more maintainable and extensible. Future contributors should be able to add a new data source by reading the GDELT adapter code and following the pattern.

The Pub/Sub integration maintains the existing serverless architecture from Phase 18 while providing clean decoupling between data ingestion and processing.

</notes>

---

*Phase: 22-data-source-architecture*
*Context gathered: 2026-01-09*
