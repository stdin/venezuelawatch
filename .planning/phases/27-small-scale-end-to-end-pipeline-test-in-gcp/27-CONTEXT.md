# Phase 27: Small-Scale End-to-End Pipeline Test in GCP - Context

**Gathered:** 2026-01-10
**Status:** Ready for planning

<vision>
## How This Should Work

This is a full production simulation to prove the complete data flow works end-to-end in GCP: GDELT events → BigQuery → intelligence processing → entity graphs → API → frontend, all executing automatically without manual intervention.

The goal is confidence before production. We need to see the full pipeline run successfully from ingestion to frontend visualization, using real GDELT data, to know we can deploy to production without it breaking.

This is the final validation phase before going live - a staged approach where we start small (1-2 weeks of data), verify it works, then expand if successful.

</vision>

<essential>
## What Must Be Nailed

- **Prove it works** - The complete pipeline must execute successfully end-to-end, demonstrating that all components work together as designed
- **Data ingestion verified** - GDELT events successfully ingested and queryable in BigQuery
- **Intelligence processing verified** - Risk scores and severity levels computed by the intelligence pipeline

</essential>

<boundaries>
## What's Out of Scope

- **Performance optimization** - Not tuning for speed or cost efficiency - just verify it runs successfully
- **Scale testing** - Not testing with months of historical data or high concurrent load - keeping it small and manageable
- **Production launch** - This is a test environment validation, not the actual production deployment

</boundaries>

<specifics>
## Specific Ideas

**Test Data Scope:**
- Use 1-2 weeks of historical GDELT data
- Provides enough data to see patterns and entity relationships working
- Small enough to keep the test manageable and fast

**Verification Approach:**
- Check that events appear in BigQuery (raw ingestion successful)
- Verify risk scores are computed (intelligence pipeline operational)
- Confirm no errors in logs (pipeline completed cleanly)

**Post-Test Path:**
- If small test succeeds → expand to larger datasets
- Staged approach: start small, validate, then scale
- This is validation before expanding, not final production launch

</specifics>

<notes>
## Additional Context

Phase 27 is the final phase of the v1.3 GDELT Intelligence milestone. It validates that the entire polyglot persistence architecture + serverless GCP pipeline works together correctly.

The emphasis is on proving the flow works, not optimizing it. Performance tuning comes later - this is about confidence and bug discovery.

Success means seeing data flow from GDELT → BigQuery → processing → API → frontend with all intelligence features (risk scoring, entity graphs, severity classification) operational.

</notes>

---

*Phase: 27-small-scale-end-to-end-pipeline-test-in-gcp*
*Context gathered: 2026-01-10*
