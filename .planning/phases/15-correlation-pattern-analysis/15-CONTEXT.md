# Phase 15: Correlation & Pattern Analysis - Context

**Gathered:** 2026-01-10
**Status:** Ready for research

<vision>
## How This Should Work

Users can interactively explore relationships between entities, events, and economic data through a network graph visualization. This is a self-service exploration tool — users select the variables they want to analyze (entity risk scores, economic indicators like oil prices or inflation, event counts), and the system computes and visualizes correlations as a network graph.

The graph uses a force-directed layout (like D3.js force simulations) where nodes represent variables and edges represent correlation strengths. Nodes repel each other, edges attract, creating organic clustering of related variables. Users can interact with the graph — dragging nodes, filtering by correlation strength, clicking to see details.

This is about **discovering relationships**, not proving causation. Users explore patterns to inform their investment decisions: "When oil prices drop, which entities see risk score increases?" or "How do sanctions events correlate with humanitarian crisis indicators?"

</vision>

<essential>
## What Must Be Nailed

- **Statistical accuracy** — Correlations must be mathematically sound and statistically rigorous. This is paramount. Show p-values, ensure significance testing, and require both:
  1. **Statistical significance (p-value < 0.05)** to filter out chance correlations
  2. **Strong effect size** (correlation coefficient |r| > threshold like 0.5 or 0.7) so only meaningful relationships appear

- **Meaningful correlations only** — Don't show weak or insignificant correlations. Better to show fewer high-quality insights than overwhelm users with statistical noise.

</essential>

<boundaries>
## What's Out of Scope

- **No causation analysis** — We show correlation, not causation. Not trying to prove X causes Y (correlation ≠ causation)
- **No predictive modeling** — Not using correlations to forecast future events. That's what Phase 14 forecasting is for. This phase is about understanding relationships in historical data.
- **No AI/ML pattern discovery** — Not using machine learning to automatically discover hidden patterns. Too complex for this phase. Users manually select variables to correlate.
- **No real-time correlation updates** — Correlations computed on-demand or in batch jobs, not streaming/real-time as new data arrives.

</boundaries>

<specifics>
## Specific Ideas

- **Force-directed graph layout** — Like D3.js force simulations. Nodes repel, edges attract based on correlation strength, creating natural clustering of related variables.

- **Interactive exploration** — Users can drag nodes, zoom, pan. Click nodes to see variable details. Click edges to see correlation details (r-value, p-value, sample size, time period).

- **Variables available for correlation:**
  1. **Entity-level metrics** — Individual entity risk scores, sanctions status, mention frequency, trending velocity
  2. **Economic indicators** — FRED data like oil prices, inflation, GDP, exchange rates (from Phase 3 ingestion)
  3. **Event aggregates** — Daily/weekly event counts by type (political, sanctions, supply chain, humanitarian)

- **Filtering controls** — Users can adjust thresholds to show only correlations above certain strength (e.g., |r| > 0.7) to reduce visual clutter.

</specifics>

<notes>
## Additional Context

**Statistical rigor is non-negotiable.** Users are making investment decisions based on these insights. False correlations or spurious relationships could lead to bad decisions. Better to be conservative and show only high-confidence patterns.

**Focus on time-series correlations** — Most value comes from understanding how variables move together over time (e.g., "When oil prices dropped 20% in Q3 2024, sanctions event counts increased 35%"). Cross-sectional correlations (comparing entities at one point in time) are lower priority.

**Interactive tool, not automatic insights** — Users drive the exploration. We provide the statistical engine and visualization, they choose what to investigate. This gives them ownership of discoveries and builds trust in the analysis.

</notes>

---

*Phase: 15-correlation-pattern-analysis*
*Context gathered: 2026-01-10*
