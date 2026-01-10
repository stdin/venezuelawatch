# Phase 21: Mentions Tracking - Context

**Gathered:** 2026-01-10
**Status:** Ready for research

<vision>
## How This Should Work

Track how events get mentioned across articles over time to detect early warning signals. When a Venezuela-related event suddenly goes from 5 mentions per day to 50, that spike signals escalation — something important is brewing.

The system monitors mention patterns and uses statistical significance thresholds (like z-scores) to assign confidence scores to spike detection. Not just "spike detected" but "85% confidence this matters" — filtering out noise to surface only meaningful escalations.

When a high-confidence spike is detected, the system responds with a multi-stage approach:
1. Store spike metadata for later analysis (Phases 23/24 will use it for risk scoring)
2. Trigger immediate risk score updates for the event
3. Flag high-confidence spikes for human review/attention

This creates an early warning system where investors see brewing crises before they fully materialize.
</vision>

<essential>
## What Must Be Nailed

All three components are equally essential and must work together:

- **Accurate mention counting over time** - Getting the time-series data right so we can see real trends without noise
- **Spike detection that actually matters** - Statistical filtering to only alert on meaningful escalations, not random variance
- **Fast lookback for recent trends** - Being able to quickly see "what's heating up in the last 24-48 hours"

The core value is early warning: detecting when narrative momentum is building before it becomes obvious to everyone.
</essential>

<boundaries>
## What's Out of Scope

- **UI/dashboard visualization** - This phase builds the data pipeline only. UI comes in Phase 24
- Sentiment analysis across individual mentions (tracking counts, not analyzing tone)
- Cross-language mention tracking (focus on patterns, not translation)
- Historical mention analysis beyond recent lookback windows

Phase 21 is pure backend infrastructure — collecting mention data, detecting spikes, and storing signals for future phases to consume.
</boundaries>

<specifics>
## Specific Ideas

**Confidence scoring with statistical significance:**
- Use z-scores or similar statistical measures to determine if a mention spike is meaningful
- Not just binary "spike/no spike" but quantified confidence (e.g., 85% confidence)
- Thresholds filter out noise from random variance

**Multi-stage spike response:**
- Low confidence: Store metadata only
- Medium confidence: Trigger risk score recalculation
- High confidence: Flag for human review/attention
- All spikes contribute to future risk scoring in Phase 23

**Time-series foundation:**
- Need accurate baseline to detect deviations
- Fast queries for recent windows (24h, 7d lookback)
- Foundation for narrative tracking across the platform
</specifics>

<notes>
## Additional Context

This phase builds the foundation for the intelligence pipeline rebuild in Phase 23. The mention patterns and spike signals captured here will become primary risk indicators.

Focus is on statistical rigor — better to miss a few real spikes than to flood users with false positives. Confidence scoring is key to maintaining signal-to-noise ratio.

GDELT Mentions table provides the raw data. Phase 21 transforms it into actionable early warning signals.
</notes>

---

*Phase: 21-mentions-tracking*
*Context gathered: 2026-01-10*
