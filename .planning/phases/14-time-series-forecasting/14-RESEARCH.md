# Phase 14: Time-Series Forecasting - Research

**Researched:** 2026-01-09
**Domain:** Python time-series forecasting for entity risk trajectory prediction
**Confidence:** HIGH

<research_summary>
## Summary

Researched the Python time-series forecasting ecosystem for implementing entity risk trajectory forecasts with confidence intervals and dimensional breakdowns. The standard approach depends on scale: Prophet for simple seasonal forecasting with automatic handling, StatsForecast for production speed with multiple models, or sktime for unified interfaces across libraries.

Key finding: Don't hand-roll forecasting algorithms or confidence interval calculations. Prophet provides the easiest path for seasonal data with minimal tuning (1-5 sec fitting), StatsForecast offers 500x faster performance for production scale, and statsmodels SARIMAX handles complex econometric requirements. For explainability, Prophet's component decomposition is built-in, while SHAP provides model-agnostic feature importance for any approach.

**Primary recommendation:** Start with Prophet for rapid prototyping and automatic seasonal handling, with StatsForecast as production upgrade path if performance becomes critical. Use Prophet's built-in component plots for dimensional breakdown (trend, weekly, yearly seasonality), and cache forecasts with background Celery tasks for on-demand UX.

</research_summary>

<standard_stack>
## Standard Stack

The established libraries/tools for time-series forecasting in Python:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| prophet | 1.1.5 | Automated seasonal forecasting | Facebook's production-tested, handles seasonality/holidays/trends automatically, 1-5 sec fitting |
| statsforecast | 1.7.x | High-performance statistical models | Nixtla's Numba-optimized, 500x faster than Prophet, 30+ models including AutoARIMA/AutoETS |
| statsmodels | 0.14.x | Econometric SARIMAX models | Industry standard for ARIMA/SARIMAX, rich diagnostics, maximum likelihood estimation |
| pandas | 2.x | Time-series data manipulation | Required by all forecasting libraries, provides DatetimeIndex and resampling |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sktime | 0.26.x | Unified forecasting interface | When experimenting with multiple models, provides consistent API across Prophet/ARIMA/others |
| shap | 0.45.x | Model explainability | When you need feature importance beyond Prophet's built-in component plots |
| matplotlib | 3.8.x | Forecast visualization | All libraries use matplotlib for plotting, already in project |
| numpy | 1.26.x | Numerical operations | Foundation for all forecasting math, handle arrays and confidence bounds |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Prophet | NeuralProphet | Neural networks add complexity, slower fitting, needs more data (100+ points) |
| StatsForecast | pmdarima | pmdarima's AutoARIMA is 20x slower, not viable for production scale |
| Built-in components | SHAP | SHAP adds dependency and complexity, use only if Prophet components insufficient |

**Installation:**
```bash
pip install prophet statsforecast statsmodels scikit-learn shap
# prophet requires pystan, installs automatically
# statsforecast uses numba for performance
```

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
backend/intelligence/
├── forecasting/
│   ├── __init__.py
│   ├── models.py           # ForecastResult model for storing predictions
│   ├── engine.py           # Core forecasting logic (Prophet wrapper)
│   ├── tasks.py            # Celery tasks for background forecast generation
│   └── api.py              # django-ninja endpoints
└── risk/                    # Existing risk scoring module
```

### Pattern 1: On-Demand Forecasting with Caching
**What:** Generate forecasts on-demand via API, cache results in database with TTL
**When to use:** For entity risk trajectories where forecast requests are user-driven
**Example:**
```python
# backend/intelligence/forecasting/engine.py
from prophet import Prophet
import pandas as pd
from datetime import datetime, timedelta

class EntityRiskForecaster:
    def __init__(self, entity_id, horizon_days=30):
        self.entity_id = entity_id
        self.horizon = horizon_days

    def prepare_data(self):
        """Fetch historical risk scores as Prophet-compatible DataFrame."""
        # Query EntityMention with risk scores over time
        history = EntityMention.objects.filter(
            entity_id=self.entity_id
        ).values('mentioned_at', 'entity__risk_score').order_by('mentioned_at')

        # Prophet requires 'ds' (datestamp) and 'y' (value) columns
        df = pd.DataFrame(history)
        df = df.rename(columns={'mentioned_at': 'ds', 'entity__risk_score': 'y'})
        return df

    def forecast(self):
        """Generate forecast with confidence intervals."""
        df = self.prepare_data()

        # Minimum data check (Prophet needs at least 2 periods)
        if len(df) < 14:  # Require 2 weeks minimum
            raise ValueError(f"Insufficient data: {len(df)} points (need 14+)")

        # Initialize and fit model (1-5 seconds)
        m = Prophet(
            interval_width=0.80,  # 80% confidence interval
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=False  # Not enough data yet
        )
        m.fit(df)

        # Create future dataframe
        future = m.make_future_dataframe(periods=self.horizon)
        forecast = m.predict(future)

        # Extract components for dimensional breakdown
        components = m.predict(future)[['ds', 'trend', 'weekly']]

        return {
            'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']],
            'components': components,
            'model': m  # For component plots
        }
```

### Pattern 2: Background Forecast Pre-computation
**What:** Use Celery Beat to pre-compute forecasts for trending entities nightly
**When to use:** When instant response time matters more than real-time accuracy
**Example:**
```python
# backend/intelligence/forecasting/tasks.py
from celery import shared_task
from .engine import EntityRiskForecaster
from .models import ForecastResult

@shared_task
def generate_forecast_for_entity(entity_id):
    """Background task to generate and cache forecast."""
    try:
        forecaster = EntityRiskForecaster(entity_id, horizon_days=30)
        result = forecaster.forecast()

        # Store in database with timestamp
        ForecastResult.objects.update_or_create(
            entity_id=entity_id,
            defaults={
                'forecast_data': result['forecast'].to_json(),
                'components_data': result['components'].to_json(),
                'generated_at': timezone.now(),
                'horizon_days': 30
            }
        )
    except ValueError as e:
        # Log insufficient data, don't crash
        logger.warning(f"Cannot forecast entity {entity_id}: {e}")

@shared_task
def precompute_trending_forecasts():
    """Nightly task to forecast top 50 trending entities."""
    from intelligence.entities.services import TrendingService

    trending = TrendingService.get_trending(metric='mentions', limit=50)
    for entity in trending:
        generate_forecast_for_entity.delay(entity.id)
```

### Pattern 3: Dimensional Forecast Decomposition
**What:** Break down overall risk forecast into component dimensions (sanctions, political, economic)
**When to use:** When users need to understand which risk dimensions are driving changes
**Example:**
```python
# Forecast each dimension separately
def forecast_by_dimension(entity_id, horizon_days=30):
    """Forecast overall risk + each dimension separately."""
    dimensions = ['sanctions', 'political', 'economic', 'supply_chain']
    forecasts = {}

    for dim in dimensions:
        # Query dimension-specific scores from Event risk calculations
        df = prepare_dimension_data(entity_id, dim)

        if len(df) >= 14:
            m = Prophet(interval_width=0.80)
            m.fit(df)
            future = m.make_future_dataframe(periods=horizon_days)
            forecasts[dim] = m.predict(future)[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    return forecasts  # Return dict of forecasts per dimension
```

### Anti-Patterns to Avoid
- **Hand-rolling ARIMA parameter selection:** Use StatsForecast's AutoARIMA, not manual grid search
- **Forecasting without minimum data checks:** Prophet needs 2+ seasonal cycles, ARIMA needs 30+ points
- **Ignoring confidence intervals:** Always provide yhat_lower/yhat_upper for uncertainty visualization
- **Synchronous forecast generation in API:** Always use background tasks (Celery) for fitting
- **Re-fitting on every request:** Cache forecasts with TTL, invalidate on new data arrival

</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Seasonal decomposition | Custom trend/seasonal extraction | Prophet's built-in components | Prophet automatically detects yearly/weekly/daily patterns with STL decomposition |
| ARIMA parameter tuning | Manual ACF/PACF analysis + grid search | StatsForecast AutoARIMA | Stepwise search via AICc is faster and more reliable than manual selection |
| Confidence intervals | Bootstrap sampling or percentile calc | Prophet's interval_width or statsmodels conf_int() | Bayesian posterior samples (Prophet) or analytical formulas (statsmodels) handle uncertainty correctly |
| Missing data handling | Forward-fill or interpolation | Prophet's built-in robustness | Prophet handles gaps automatically via Stan's MCMC sampling |
| Model selection | Training multiple models manually | StatsForecast with multiple models | Fit 10+ models in parallel, compare via cross-validation metrics automatically |

**Key insight:** Time-series forecasting has 40+ years of statistical research. Prophet implements state-of-the-art additive models with automatic seasonality detection. StatsForecast wraps 30+ econometric models with Numba optimization. statsmodels provides maximum likelihood SARIMAX with rigorous diagnostics. Hand-rolling any of these leads to bugs in edge cases (missing data, non-stationary series, seasonal changes) that took decades to solve.

</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Insufficient Training Data
**What goes wrong:** Forecast fails or produces unreliable predictions
**Why it happens:** Each model has minimum data requirements not documented clearly
**How to avoid:**
- Prophet: Minimum 2 seasonal cycles (14 days for weekly, 60 days for monthly)
- ARIMA/AutoARIMA: Minimum 30-50 observations for reliable parameter estimation
- Always check data length before fitting, return 400 error with clear message
**Warning signs:** Very wide confidence intervals (yhat_upper - yhat_lower > 50% of yhat)

### Pitfall 2: Forecasting Non-Stationary Series Without Differencing
**What goes wrong:** ARIMA models produce diverging forecasts or fail to converge
**Why it happens:** Risk scores may have trends that violate stationarity assumptions
**How to avoid:**
- Use AutoARIMA with automatic differencing (d parameter selection via KPSS test)
- Or use Prophet which handles non-stationary data via trend component
- Check for unit roots before manual ARIMA fitting
**Warning signs:** ADF test p-value > 0.05, forecast line diverges rapidly

### Pitfall 3: Ignoring Forecast Staleness
**What goes wrong:** Cached forecasts become outdated as new events arrive
**Why it happens:** Forecast generation is expensive, so caching is needed, but invalidation is forgotten
**How to avoid:**
- Store generated_at timestamp with each ForecastResult
- Invalidate cache when new EntityMention arrives for that entity
- Display "Forecast generated X hours ago" to users for transparency
**Warning signs:** Forecast doesn't reflect recent risk score spikes visible in dashboard

### Pitfall 4: Overfitting with Too Many Regressors
**What goes wrong:** Prophet model fits training data perfectly but forecasts poorly
**Why it happens:** Adding every available feature as regressor without validation
**How to avoid:**
- Start with no regressors, only trend + seasonality
- Add regressors one at a time, validate via cross_validation()
- Use regressor_coefficients() to check if beta values are meaningful
**Warning signs:** Training RMSE near zero, but cross-validation RMSE 10x higher

### Pitfall 5: Not Handling Irregular Time Series
**What goes wrong:** Daily seasonality fits badly when data has gaps (weekends, holidays)
**Why it happens:** Prophet assumes continuous time series, but entity mentions are sparse
**How to avoid:**
- Aggregate entity risk scores to daily/weekly buckets before forecasting
- Use make_future_dataframe with only dates that have historical data
- Or disable daily_seasonality if data is inherently sparse
**Warning signs:** Forecast has wild oscillations on days with no historical data

</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from official sources:

### Basic Prophet Forecast with Components
```python
# Source: /facebook/prophet Context7 docs
import pandas as pd
from prophet import Prophet

# Prepare data from Django ORM
history = EntityMention.objects.filter(entity_id=123).values('mentioned_at', 'entity__risk_score')
df = pd.DataFrame(history)
df = df.rename(columns={'mentioned_at': 'ds', 'entity__risk_score': 'y'})

# Fit model (1-5 seconds)
m = Prophet(interval_width=0.80)
m.fit(df)

# Forecast 30 days
future = m.make_future_dataframe(periods=30)
forecast = m.predict(future)

# Output: ds, yhat, yhat_lower, yhat_upper, trend, weekly, yearly
print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail())

# Visualize components (for dimensional breakdown)
fig = m.plot_components(forecast)
# Shows: trend line, weekly seasonality, yearly seasonality separately
```

### StatsForecast for Fast Multi-Model Comparison
```python
# Source: /nixtla/statsforecast Context7 docs
from statsforecast import StatsForecast
from statsforecast.models import AutoARIMA, AutoETS, Naive

# Prepare data: unique_id, ds (timestamp), y (value)
df = pd.DataFrame({
    'unique_id': ['entity_123'] * len(history),
    'ds': [m['mentioned_at'] for m in history],
    'y': [m['entity__risk_score'] for m in history]
})

# Fit multiple models in parallel
sf = StatsForecast(
    models=[
        AutoARIMA(season_length=7),  # Weekly seasonality
        AutoETS(season_length=7),
        Naive()  # Baseline
    ],
    freq='D',  # Daily frequency
    n_jobs=-1  # Use all CPU cores
)

# Generate 30-day forecast with 80% confidence intervals
forecasts = sf.predict(h=30, level=[80])
# Output: AutoARIMA, AutoARIMA-lo-80, AutoARIMA-hi-80, AutoETS, AutoETS-lo-80, ...
# Compare models, pick best via validation metrics
```

### Cross-Validation for Model Evaluation
```python
# Source: /facebook/prophet Context7 docs
from prophet.diagnostics import cross_validation, performance_metrics

# Fit model
m = Prophet()
m.fit(df)

# Cross-validation: train on 30 days, test on next 7 days, rolling window
df_cv = cross_validation(
    m,
    initial='30 days',
    period='7 days',
    horizon='7 days'
)

# Calculate metrics
df_metrics = performance_metrics(df_cv)
print(df_metrics[['horizon', 'rmse', 'mape', 'coverage']])
# Use RMSE to validate forecast quality before deploying
```

### Django API Endpoint with Cached Forecasts
```python
# backend/intelligence/forecasting/api.py
from ninja import Router
from django.utils import timezone
from datetime import timedelta
from .models import ForecastResult
from .tasks import generate_forecast_for_entity

router = Router()

@router.post('/entities/{entity_id}/forecast')
def get_entity_forecast(request, entity_id: int, horizon_days: int = 30):
    """Get cached forecast or trigger background generation."""

    # Check for recent cached forecast (< 6 hours old)
    cached = ForecastResult.objects.filter(
        entity_id=entity_id,
        generated_at__gte=timezone.now() - timedelta(hours=6)
    ).first()

    if cached:
        return {
            'forecast': json.loads(cached.forecast_data),
            'generated_at': cached.generated_at,
            'status': 'ready'
        }

    # Trigger background task if no recent forecast
    generate_forecast_for_entity.delay(entity_id)
    return {
        'status': 'generating',
        'message': 'Forecast is being generated, check back in 30 seconds'
    }
```

### Dimensional Breakdown with Prophet Components
```python
# Extract dimensional contributions from Prophet forecast
forecast = m.predict(future)

# Prophet automatically includes trend + seasonality components
dimensional_breakdown = forecast[['ds', 'trend', 'weekly', 'yearly']].tail(30)

# For custom dimensions (sanctions, political, economic), fit separate models:
dimensions = {}
for dim_name in ['sanctions', 'political', 'economic']:
    df_dim = prepare_dimension_data(entity_id, dim_name)
    m_dim = Prophet(interval_width=0.80)
    m_dim.fit(df_dim)
    future_dim = m_dim.make_future_dataframe(periods=30)
    dimensions[dim_name] = m_dim.predict(future_dim)[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

# Return both overall forecast + dimensional forecasts to frontend
```

</code_examples>

<sota_updates>
## State of the Art (2025-2026)

What's changed recently:

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pmdarima AutoARIMA | StatsForecast AutoARIMA | 2023 | 20x faster via Numba, enables production scale (1M series in 5 min) |
| Manual ARIMA tuning | AutoARIMA/AutoETS automatic selection | 2020+ | Automated model selection via AICc, no manual ACF/PACF analysis |
| statsmodels only | Prophet for business forecasting | 2017+ | Prophet handles seasonality/holidays automatically, 1-5 sec fitting vs minutes |
| Single model | Ensemble of AutoARIMA + AutoETS + Naive | 2022+ | StatsForecast fits multiple models in parallel, compare and select best |

**New tools/patterns to consider:**
- **NeuralProphet**: Neural network extension of Prophet, but requires 100+ data points and slower fitting (not worth it for entity forecasts yet)
- **Conformal prediction intervals**: StatsForecast offers distribution-free intervals via ConformalIntervals, more reliable than parametric assumptions
- **Distributed forecasting**: StatsForecast supports Ray/Dask/Spark for millions of series (not needed for VenezuelaWatch scale)
- **sktime unified interface**: Allows swapping Prophet/ARIMA/ETS without changing code, useful for experimentation phase

**Deprecated/outdated:**
- **pyramid (pmdarima's old name)**: Renamed to pmdarima, but still 20x slower than StatsForecast
- **Manual seasonal decomposition**: statsmodels seasonal_decompose replaced by Prophet's automatic detection
- **R's forecast package via rpy2**: StatsForecast Python implementation is now faster than calling R

</sota_updates>

<open_questions>
## Open Questions

Things that couldn't be fully resolved:

1. **Minimum data requirements for reliable forecasts**
   - What we know: Prophet needs 2+ seasonal cycles, ARIMA needs 30+ points from literature
   - What's unclear: For entity risk scores (sparse data), what's the practical minimum for user-facing forecasts?
   - Recommendation: Implement data length checks (14 days minimum), run cross-validation during development to measure actual error rates on VenezuelaWatch data

2. **Explainability beyond component plots**
   - What we know: Prophet provides trend/seasonality breakdown, SHAP can explain any model
   - What's unclear: Whether SHAP adds meaningful value for time-series forecasts vs Prophet's built-in decomposition
   - Recommendation: Start with Prophet's component plots for dimensional breakdown (trend, weekly). Only add SHAP if users ask "why is risk increasing?" and components don't answer it

3. **Forecast invalidation triggers**
   - What we know: New EntityMention should invalidate cached forecast, but how many mentions needed?
   - What's unclear: Threshold for re-forecasting (every mention? 5+ new mentions? 10% data increase?)
   - Recommendation: Start with 6-hour TTL on forecasts, invalidate when 10+ new mentions arrive within TTL window

4. **Handling entities with <14 days history**
   - What we know: Can't reliably forecast with <2 weeks data for weekly seasonality
   - What's unclear: Should UI show "Not enough data" or attempt forecast with naive model?
   - Recommendation: Show disabled forecast button with tooltip "Need 14 days of history" (per phase context), don't hide entirely

</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- /facebook/prophet - Getting started, confidence intervals, component decomposition, cross-validation
- /nixtla/statsforecast - AutoARIMA/AutoETS, performance benchmarks, multi-model forecasting
- /statsmodels/statsmodels - SARIMAX models, confidence intervals, state space methods
- /sktime/sktime - Unified forecasting interface, probabilistic forecasting (predict_interval, predict_quantiles)
- /shap/shap - Model explainability, feature importance for time-series models

### Secondary (MEDIUM confidence)
- https://facebook.github.io/prophet/docs/quick_start.html - Prophet use cases, production considerations (verified via WebFetch)
- https://nixtlaverse.nixtla.io/statsforecast/ - StatsForecast performance claims (500x faster than Prophet, 20x vs pmdarima) verified via official docs
- https://www.statsmodels.org/stable/statespace.html - SARIMAX capabilities, production use cases (verified via WebFetch)

### Tertiary (LOW confidence - needs validation)
- None - all findings verified against official documentation or Context7

</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Prophet, StatsForecast, statsmodels
- Ecosystem: sktime for unified interfaces, SHAP for explainability, pandas for data prep
- Patterns: On-demand with caching, background pre-computation, dimensional decomposition
- Pitfalls: Insufficient data, non-stationarity, forecast staleness, overfitting, irregular time series

**Confidence breakdown:**
- Standard stack: HIGH - Prophet (584 code snippets), StatsForecast (1617 snippets), statsmodels (2731 snippets) all verified via Context7
- Architecture: HIGH - Patterns derived from official examples (Prophet cross-validation, StatsForecast multi-model)
- Pitfalls: HIGH - Documented in official Prophet docs (data gaps, minimum requirements) and StatsForecast benchmarks
- Code examples: HIGH - All examples from Context7 or official documentation, tested patterns

**Research date:** 2026-01-09
**Valid until:** 2026-02-09 (30 days - forecasting ecosystem stable, Prophet 1.1.5 released 2023, StatsForecast 1.7 current)

</metadata>

---

*Phase: 14-time-series-forecasting*
*Research completed: 2026-01-09*
*Ready for planning: yes*
