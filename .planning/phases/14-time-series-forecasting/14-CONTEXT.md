# Phase 14: Time-Series Forecasting - Context

**Gathered:** 2026-01-09
**Status:** Ready for research

<vision>
## How This Should Work

Users can forecast entity risk trajectories on-demand through contextual widgets that appear where they're most useful - on entity profile pages and in risk intelligence views. When users click to forecast, they see a visual chart with historical data extending into a forecasted trajectory line with shaded confidence bands (like weather forecasts).

The forecast shows both the overall risk score trajectory and dimensional breakdowns - "Overall risk: 65→75, driven by sanctions risk: 40→80, political risk stable" - so users understand where the risk is coming from. Each forecast includes contextual benchmarks like "Forecast vs average sanctioned entity trajectory" or "vs typical political disruption pattern" to provide meaningful context.

Forecasts are explained in plain language with contributing factors: "Rising mentions (↑40%), Similar to sanctioned entity Y (match: 0.85), Economic indicator correlation" rather than technical model details. Users see WHY the model predicts this trend, with a simple timestamp showing "Forecast generated 2 hours ago" for freshness.

</vision>

<essential>
## What Must Be Nailed

- **Explainability over accuracy** - Users must understand WHY the forecast predicts a certain trajectory. Show contributing factors in plain language (mentions increasing, similar patterns to known entities, correlating indicators) rather than technical model details. Trust comes from transparency about reasoning.

- **Visual trajectory with confidence** - Chart-based forecast showing historical data + predicted line extending into future with shaded confidence bands. Users need to see both the direction and the uncertainty visually.

- **Dimensional breakdown** - Don't just forecast overall risk score - show which dimensions are driving the change (sanctions risk increasing vs political risk stable). Users need to know where the risk is coming from.

</essential>

<boundaries>
## What's Out of Scope

- **Forecasting all metrics** - Phase 14 focuses on entity risk trajectories only. Not forecasting economic indicators, event patterns, or other time-series data yet.

- **Custom user models** - Users can't train their own models or adjust parameters. They use the platform's forecasts. No model tuning or configuration interface.

- **Historical backtesting UI** - No interface to test "what would the model have predicted 6 months ago." Just forward-looking predictions, not retrospective validation.

</boundaries>

<specifics>
## Specific Ideas

- **Contextual forecast widgets** - Forecast options appear contextually rather than in a dedicated page. Entity profiles show "Predict this entity's trajectory" button. Forecasts feel integrated into existing workflows.

- **Visual forecast presentation** - Chart with historical data + forecasted line extending into future with shaded confidence band. Similar to weather forecast visualizations - intuitive and familiar.

- **Model transparency: "Just the why"** - Show contributing factors and plain language explanations. Hide technical details like algorithm names, feature weights, model parameters. Focus on what's driving the forecast, not how the model works internally.

- **Timestamp freshness** - Simple "Forecast generated 2 hours ago" timestamp. No complex staleness warnings or color-coding. Users trust it's based on latest available data at that time.

- **Error handling: Disabled with explanation** - When not enough data or confidence too low, show grayed-out forecast button with tooltip: "Need 30 days of history" or "Confidence too low for reliable prediction." Don't hide the button entirely, but make limitations clear.

- **Always-visible disclaimer** - Every forecast shows subtle disclaimer text: "Directional indicator based on historical patterns." Consistent expectations across all forecasts.

- **Dimensional forecasts shown** - Default view shows overall risk score forecast PLUS dimensional breakdown. No progressive disclosure or "show breakdown" button - make the detail visible upfront.

- **Contextual benchmarks** - Include relevant benchmark comparison: "Forecast vs average sanctioned entity trajectory" or "vs typical political disruption pattern." Provide context without requiring user to select comparison entities.

</specifics>

<notes>
## Additional Context

User wants forecasting to be actionable for investment decisions - entity risk trajectories help answer "Is this exposure getting riskier?" The emphasis on explainability reflects need for trust in predictions when making portfolio decisions.

The contextual widget approach (vs dedicated forecast page) shows preference for integrating forecasting into existing workflows rather than treating it as separate analytics tool.

Dimensional breakdown is critical - users don't just want to know risk is increasing, they want to know if it's sanctions-driven, political instability, or economic factors. This specificity drives different actions.

Always-visible disclaimers and disabled-with-explanation error handling show thoughtful approach to setting realistic expectations while maintaining transparency.

</notes>

---

*Phase: 14-time-series-forecasting*
*Context gathered: 2026-01-09*
