# Phase 18: GCP-Native Pipeline Migration - Context

**Gathered:** 2026-01-09
**Status:** Ready for planning

<vision>
## How This Should Work

Big bang cutover. Stop Celery completely, deploy GCP-native services, switch over. No parallel systems, no gradual migration workload-by-workload. Clean break.

The day after the switch, the primary win is **lower operational burden**. No more managing Redis instances, Celery workers, or monitoring queue depths. No more coordinating worker restarts when deploying code changes. GCP handles scaling automatically.

Specifically, this means:
- Delete Redis infrastructure entirely
- Remove all Celery worker deployments
- Let Cloud Run/Functions auto-scale without thinking about worker counts
- All logging unified in Cloud Logging (no more searching Celery logs + Django logs separately)
- Deploy functions independently without coordinating infrastructure changes

The research document (GCP-NATIVE-ORCHESTRATION-RESEARCH.md) already has the architectural blueprint. This phase is about executing that vision cleanly.

</vision>

<essential>
## What Must Be Nailed

**Zero data loss during cutover.**

Every GDELT event, every LLM analysis result, every entity extraction must complete successfully. No dropped events in the 15-minute GDELT polling window. No lost processing tasks during the transition.

This is non-negotiable — the pipeline feeds investment decisions, and missing data means missing risk signals.

</essential>

<boundaries>
## What's Out of Scope

- **Performance optimization beyond current baseline** - Match current ingestion speed and processing latency. Don't try to make it faster yet.
- **Cost optimization experiments** - Use sensible defaults from research (as documented). Don't spend time tuning Cloud Run memory settings or function timeout configurations.
- **Advanced GCP features (Workflows, Composer, Eventarc beyond basics)** - Keep it simple: Cloud Scheduler + Cloud Functions/Run + Pub/Sub + Cloud Tasks. Complex orchestration can come later.
- **New pipeline features or data sources** - Migrate existing workloads only (GDELT, ReliefWeb, FRED, UN Comtrade, World Bank, sanctions, LLM analysis, entity extraction). Don't add new sources during migration.

</boundaries>

<specifics>
## Specific Ideas

No specific implementation requirements — trust the research document to guide technical decisions.

The research already covers:
- Cloud Scheduler for cron jobs (replacing Celery Beat)
- Cloud Functions vs Cloud Run split (ingestion vs Django-dependent processing)
- Pub/Sub for event-driven patterns
- Cloud Tasks for queue management
- Cost analysis and architectural tradeoffs

Follow that blueprint with sensible defaults.

</specifics>

<notes>
## Additional Context

Migration priority is **operational simplicity over everything else**. The Celery infrastructure has served its purpose, but managing Redis, workers, and deployment coordination is overhead that doesn't scale.

GCP-native architecture means:
- Auto-scaling handles traffic spikes (no manual intervention)
- Unified observability (Cloud Logging, Error Reporting, Trace)
- Built-in retries and error handling
- Simpler deployment (no worker coordination)

This sets up the platform for future growth without operational complexity scaling linearly with features.

</notes>

---

*Phase: 18-gcp-native-pipeline-migration*
*Context gathered: 2026-01-09*
