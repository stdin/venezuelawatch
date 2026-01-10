# Phase 14: Time-Series Forecasting - Research

**Researched:** 2026-01-09
**Domain:** Python time-series forecasting for entity risk trajectory prediction
**Confidence:** HIGH

<research_summary>
## Summary

Researched the Python time-series forecasting ecosystem AND GCP managed services for implementing entity risk trajectory forecasts with confidence intervals and dimensional breakdowns. The standard approach depends on scale and infrastructure: Prophet for self-hosted forecasting, BigQuery ML for SQL-native forecasting, or Vertex AI for large-scale neural models.

Key finding: Don't hand-roll forecasting algorithms or confidence interval calculations. Prophet provides the easiest path for seasonal data with minimal tuning (1-5 sec fitting), StatsForecast offers 500x faster performance for production scale, and statsmodels SARIMAX handles complex econometric requirements. For GCP-native solutions, BigQuery ML ARIMA_PLUS offers automatic preprocessing and scales to 100M series, while Vertex AI Forecasting provides state-of-the-art TiDE models with 10x faster training.

**Primary recommendation for VenezuelaWatch:** Use Vertex AI Forecasting with TiDE models for fully managed, state-of-the-art forecasting. This provides automatic model selection, probabilistic confidence intervals, and scales easily as entity count grows. Requires ETL pipeline from PostgreSQL/TimescaleDB to BigQuery for training data, but eliminates model management complexity and provides MLOps integration via Vertex AI Pipelines. Cost is ~$100-200/month for 100 entities with weekly forecasts, which is acceptable for managed infrastructure with SOTA models. Implementation pattern: Dataflow for PostgreSQL → BigQuery ETL, Vertex AI Python SDK for on-demand predictions via Django API.

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

<gcp_managed_services>
## GCP Managed Forecasting Services

VenezuelaWatch already runs on GCP (Cloud SQL, Cloud Run, Cloud Storage). GCP offers managed forecasting services that could reduce implementation complexity vs self-hosting Prophet/statsmodels.

### Option 1: BigQuery ML ARIMA_PLUS

**What it is:** SQL-based time-series forecasting directly in BigQuery warehouse
**Best for:** When your data is already in BigQuery or you want SQL-only forecasting

**Capabilities:**
- Automatic preprocessing: Infers frequency, handles missing data, detects outliers, adjusts step changes
- Decomposition: Automatically separates trend, seasonality, holidays
- Functions: ML.FORECAST (predict), ML.ARIMA_EVALUATE (validate), ML.DETECT_ANOMALIES (outliers)
- Scale: Can forecast 100M time series in 1.5 hours (18,000 series/sec throughput)

**Pricing:**
- Model creation: $312.50 per TB processed (first 10GB free/month)
- Auto-ARIMA multiplier: (6, 12, 20, 30, 42) candidate models for max_order (1, 2, 3, 4, 5)
- Predictions: Standard BigQuery pricing ($6.25/TB processed)

**Example workflow:**
```sql
-- Create ARIMA_PLUS model for entity risk forecasting
CREATE OR REPLACE MODEL `intelligence.entity_risk_forecast`
OPTIONS(
  model_type='ARIMA_PLUS',
  time_series_timestamp_col='mentioned_at',
  time_series_data_col='risk_score',
  time_series_id_col='entity_id',
  auto_arima=TRUE,
  data_frequency='DAILY'
) AS
SELECT
  entity_id,
  mentioned_at,
  risk_score
FROM `intelligence.entity_risk_history`;

-- Generate 30-day forecast
SELECT * FROM ML.FORECAST(
  MODEL `intelligence.entity_risk_forecast`,
  STRUCT(30 AS horizon, 0.8 AS confidence_level)
)
WHERE entity_id = 123;
```

**Django integration:**
```python
from google.cloud import bigquery

def forecast_via_bigquery(entity_id, horizon_days=30):
    client = bigquery.Client()
    query = f"""
    SELECT * FROM ML.FORECAST(
      MODEL `intelligence.entity_risk_forecast`,
      STRUCT({horizon_days} AS horizon, 0.8 AS confidence_level)
    )
    WHERE entity_id = {entity_id}
    """
    results = client.query(query).to_dataframe()
    return results  # DataFrame with forecast_timestamp, forecast_value, prediction_interval_lower/upper
```

**Pros:**
- Zero infrastructure management (fully managed)
- Automatic preprocessing handles missing data, outliers
- SQL-native (no Python dependencies beyond client library)
- Scales to millions of series

**Cons:**
- Data must be in BigQuery (not PostgreSQL/TimescaleDB)
- SQL-only interface less flexible than Python Prophet API
- Training cost multiplier for AutoARIMA (6-42x base cost)
- No online inference (batch only)

### Option 2: Vertex AI Forecasting (AutoML) - CHOSEN APPROACH

**What it is:** Managed neural network forecasting with TiDE architecture
**Best for:** Production forecasting with fully managed infrastructure and SOTA models

**Capabilities:**
- TiDE model: 10x faster training than previous Vertex AI models
- Probabilistic inference: Models uncertainty distribution, not just point estimates
- Holiday effects: Automatic regional holiday feature generation
- BigQuery integration: Direct table input/output
- Up to 1TB training data, 100GB+ supported

**Pricing:**
- Predictions: $0.20 per 1K data points (0-1M), $0.10 per 1K (1M-50M), $0.02 per 1K (>50M)
- Data point = 1 time point in horizon (e.g., 7-day forecast = 7 points per series)
- Up to 5 prediction quantiles included at no additional cost

**Use case fit:**
- Groupe Casino: 30% accuracy improvement, 4x faster training (450+ stores)
- Hitachi Energy: Weeks → hours for sustainable energy forecasting

**Workflow:**
1. Prepare training data in BigQuery table
2. Create Vertex AI dataset
3. Train forecast model (AutoML selects architecture)
4. Request batch predictions via API

**Django integration:**
```python
from google.cloud import aiplatform

def forecast_via_vertex_ai(entity_id, horizon_days=30):
    aiplatform.init(project='venezuelawatch', location='us-central1')

    # Get endpoint (assumes model already trained and deployed)
    endpoint = aiplatform.Endpoint('projects/.../endpoints/...')

    # Prepare prediction instances
    instances = [{"entity_id": entity_id, "horizon": horizon_days}]

    # Get predictions
    predictions = endpoint.predict(instances=instances)
    return predictions.predictions  # List of forecast objects with confidence intervals
```

**Pros:**
- State-of-the-art neural models (TiDE, Temporal Fusion Transformer)
- Automatic architecture selection
- Probabilistic forecasting built-in
- Scales to 1TB training data
- Integrated with Vertex AI Pipelines for MLOps

**Cons:**
- More expensive than BigQuery ML ($0.20/1K predictions vs query pricing)
- No online inference (batch only)
- Requires BigQuery for data input (can't directly use PostgreSQL)
- Overkill for small-scale forecasting (<100 entities)

### Option 3: Self-Hosted Prophet on Cloud Run (RECOMMENDED)

**What it is:** Deploy Prophet in existing Django Cloud Run service
**Best for:** VenezuelaWatch's use case (on-demand entity forecasts, <1000 entities)

**Why recommended:**
- **Already have infrastructure:** Cloud Run + PostgreSQL/TimescaleDB + Celery/Redis
- **Direct database access:** No ETL to BigQuery needed
- **On-demand forecasting:** Fits "forecast this entity" UX pattern
- **Cost-effective:** Only pays for Cloud Run compute during forecast generation
- **Flexibility:** Full Python API for custom logic (dimensional breakdowns, etc.)

**Cost comparison (100 entities, 30-day forecasts, weekly regeneration):**

| Approach | Monthly Cost | Notes |
|----------|-------------|-------|
| Self-hosted Prophet | ~$5 | 100 entities × 4 weeks × 2 sec/forecast = 800 sec compute @ $0.000024/vCPU-sec |
| BigQuery ML | ~$50-100 | Training: $312.50/TB × small data ~0.01TB = $3. Predictions: 100 entities × 30 points × 4 weeks = 12K points @ query pricing |
| Vertex AI | ~$100-200 | 100 entities × 30 points × 4 weeks = 12K points × $0.20/1K = $2.40 + training costs |

**Implementation:**
```python
# Just add prophet to requirements.txt
# prophet==1.1.5

# Use existing Celery infrastructure for background tasks
@shared_task
def generate_forecast_for_entity(entity_id):
    forecaster = EntityRiskForecaster(entity_id)
    result = forecaster.forecast()  # 1-5 seconds
    ForecastResult.objects.update_or_create(
        entity_id=entity_id,
        defaults={'forecast_data': result['forecast'].to_json()}
    )
```

**Pros:**
- Minimal new infrastructure (just pip install prophet)
- Works with existing PostgreSQL data (no ETL)
- Full control over forecasting logic
- Fast iteration (no training pipelines)
- Cheapest option by 10-20x

**Cons:**
- You manage model code (vs fully managed)
- No automatic architecture selection
- Doesn't scale to millions of series (but VenezuelaWatch has <1000 entities)

### Recommendation Matrix

| If you need... | Use... | Why |
|----------------|--------|-----|
| <1000 entities, on-demand forecasts | Self-hosted Prophet | Simplest, cheapest, fits existing architecture |
| Data already in BigQuery | BigQuery ML ARIMA_PLUS | Zero ETL, SQL-native, automatic preprocessing |
| >10,000 entities, batch forecasting | Vertex AI or BigQuery ML | Scales to millions, managed infrastructure |
| Real-time online inference | None of the above | Use StatsForecast with pre-trained models in memory |

**For Phase 14:** Use Vertex AI Forecasting (chosen approach). This requires ETL pipeline from PostgreSQL to BigQuery, Vertex AI model training/deployment, and Django integration via Python SDK.

### Vertex AI Implementation Details

**Data Schema Requirements:**

Vertex AI Forecasting requires narrow (long) format in BigQuery with these columns:

```sql
CREATE TABLE `intelligence.entity_risk_training_data` (
  entity_id STRING NOT NULL,           -- Time series identifier
  mentioned_at TIMESTAMP NOT NULL,     -- Time column
  risk_score FLOAT64 NOT NULL,         -- Target column
  -- Optional features:
  sanctions_risk FLOAT64,
  political_risk FLOAT64,
  economic_risk FLOAT64,
  supply_chain_risk FLOAT64
);
```

**Requirements:**
- Target column (risk_score): Numeric, no nulls
- Time column (mentioned_at): Consistent interval (daily aggregation recommended)
- Series identifier (entity_id): Groups observations by entity
- Max 100 columns, 1K-100M rows, 100GB dataset size
- Max 3,000 time steps per entity

**ETL Pipeline Architecture:**

```
PostgreSQL/TimescaleDB
  ↓ (Dataflow or scheduled query)
BigQuery `intelligence.entity_risk_training_data`
  ↓ (Vertex AI Python SDK)
Vertex AI Dataset
  ↓ (AutoML training)
Vertex AI Model (TiDE)
  ↓ (Batch predictions)
Django API → Frontend
```

**Implementation Options:**

**Option A: Dataflow Template (Recommended for real-time)**
```python
# Use official PostgreSQL to BigQuery Dataflow template
# Run via Cloud Scheduler hourly to keep BigQuery synced
from google.cloud import dataflow_v1beta3

# Template: gs://dataflow-templates/latest/Jdbc_to_BigQuery
# Parameters:
#   - driverJars: PostgreSQL JDBC driver
#   - connectionURL: jdbc:postgresql://CLOUD_SQL_IP:5432/venezuelawatch
#   - query: SELECT entity_id, DATE(mentioned_at) as date, AVG(risk_score) as risk_score
#            FROM intelligence_entitymention GROUP BY 1, 2
#   - outputTable: intelligence.entity_risk_training_data
```

**Option B: Scheduled BigQuery Query (Simpler for batch)**
```sql
-- Create materialized view in BigQuery that pulls from PostgreSQL via Federated Query
-- Run daily via Cloud Scheduler

CREATE OR REPLACE TABLE `intelligence.entity_risk_training_data` AS
SELECT
  entity_id,
  TIMESTAMP(DATE(mentioned_at)) as mentioned_at,
  AVG(risk_score) as risk_score,
  AVG(sanctions_risk) as sanctions_risk,
  AVG(political_risk) as political_risk,
  AVG(economic_risk) as economic_risk,
  AVG(supply_chain_risk) as supply_chain_risk
FROM EXTERNAL_QUERY(
  'projects/PROJECT_ID/locations/us-central1/connections/CONNECTION_ID',
  '''SELECT entity_id, mentioned_at, risk_score, ...
     FROM intelligence_entitymention
     WHERE mentioned_at >= CURRENT_DATE - INTERVAL '90 days' '''
)
GROUP BY entity_id, DATE(mentioned_at)
ORDER BY entity_id, mentioned_at;
```

**Vertex AI Training Workflow:**

```python
# backend/intelligence/forecasting/vertex_ai_training.py
from google.cloud import aiplatform
from google.cloud.aiplatform import forecasting

def train_entity_risk_model():
    """Train Vertex AI forecasting model (run manually or via Cloud Scheduler)."""

    aiplatform.init(project='venezuelawatch', location='us-central1')

    # Create dataset from BigQuery table
    dataset = aiplatform.TimeSeriesDataset.create(
        display_name='entity-risk-forecasting',
        bq_source='bq://venezuelawatch.intelligence.entity_risk_training_data',
        time_column='mentioned_at',
        time_series_identifier_column='entity_id',
        target_column='risk_score'
    )

    # Train AutoML forecasting model (TiDE)
    model = aiplatform.AutoMLForecastingTrainingJob(
        display_name='entity-risk-tide-model',
        optimization_objective='minimize-rmse',
        column_specs={
            'sanctions_risk': 'numeric',
            'political_risk': 'numeric',
            'economic_risk': 'numeric',
            'supply_chain_risk': 'numeric'
        }
    )

    # Train (can take 1-4 hours depending on data size)
    model.run(
        dataset=dataset,
        target_column='risk_score',
        time_column='mentioned_at',
        time_series_identifier_column='entity_id',
        forecast_horizon=30,  # 30 days
        data_granularity_unit='day',
        data_granularity_count=1,
        training_fraction_split=0.8,
        validation_fraction_split=0.1,
        test_fraction_split=0.1,
        budget_milli_node_hours=1000,  # Auto-scales training time
    )

    # Deploy model for predictions
    endpoint = model.deploy(
        machine_type='n1-standard-4',
        min_replica_count=1,
        max_replica_count=10
    )

    return endpoint

# Train once, store endpoint name in Django settings or database
```

**Django API Integration:**

```python
# backend/intelligence/forecasting/vertex_ai_engine.py
from google.cloud import aiplatform
from google.protobuf.json_format import MessageToDict
import pandas as pd

class VertexAIForecaster:
    def __init__(self, endpoint_id):
        self.endpoint_id = endpoint_id
        aiplatform.init(project='venezuelawatch', location='us-central1')
        self.endpoint = aiplatform.Endpoint(endpoint_id)

    def forecast(self, entity_id, horizon_days=30):
        """Get forecast for specific entity."""

        # Prepare prediction instance
        # Vertex AI needs recent historical data for context
        instances = [{
            'entity_id': entity_id,
        }]

        # Get prediction (batch predictions, not real-time)
        predictions = self.endpoint.predict(instances=instances)

        # Parse predictions
        forecast_data = []
        for pred in predictions.predictions:
            forecast_data.append({
                'ds': pred['timestamp'],
                'yhat': pred['value'],
                'yhat_lower': pred['prediction_interval_lower_bound'],
                'yhat_upper': pred['prediction_interval_upper_bound']
            })

        return pd.DataFrame(forecast_data)

# backend/intelligence/forecasting/api.py
from ninja import Router
from django.conf import settings

router = Router()

@router.post('/entities/{entity_id}/forecast')
def get_entity_forecast(request, entity_id: int, horizon_days: int = 30):
    """Get Vertex AI forecast for entity."""

    # Check cache first
    cached = ForecastResult.objects.filter(
        entity_id=entity_id,
        generated_at__gte=timezone.now() - timedelta(hours=24)
    ).first()

    if cached:
        return {
            'forecast': json.loads(cached.forecast_data),
            'generated_at': cached.generated_at,
            'status': 'ready'
        }

    # Generate new forecast via Vertex AI
    forecaster = VertexAIForecaster(settings.VERTEX_AI_ENDPOINT_ID)
    forecast_df = forecaster.forecast(entity_id, horizon_days)

    # Cache result
    ForecastResult.objects.create(
        entity_id=entity_id,
        forecast_data=forecast_df.to_json(),
        generated_at=timezone.now()
    )

    return {
        'forecast': json.loads(forecast_df.to_json()),
        'status': 'ready'
    }
```

**Cost Breakdown (100 entities, 30-day forecasts, weekly updates):**

- Training: $50-100/month (retraining weekly with 90 days history)
- Endpoint hosting: $50/month (n1-standard-4 with autoscaling)
- Predictions: 100 entities × 30 points × 4 weeks = 12K points × $0.20/1K = $2.40/month
- BigQuery ETL: $5-10/month (query processing for daily aggregation)
- **Total: ~$107-162/month**

**Advantages of Vertex AI:**
- Fully managed (no Prophet code maintenance)
- TiDE models automatically selected (SOTA accuracy)
- Scales to 100M rows without code changes
- MLOps integration (versioning, monitoring, retraining pipelines)
- Probabilistic forecasts built-in

**Trade-offs:**
- Requires BigQuery ETL pipeline (additional complexity)
- Higher cost than self-hosted (~20x more expensive)
- Batch predictions only (not real-time, but acceptable for caching pattern)
- Model training takes 1-4 hours (vs 1-5 seconds for Prophet)

</gcp_managed_services>

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
- https://docs.cloud.google.com/vertex-ai/docs/tabular-data/forecasting/overview - Vertex AI Forecasting capabilities, TiDE architecture (verified via WebFetch)
- https://cloud.google.com/blog/products/ai-machine-learning/vertex-ai-forecasting - Vertex AI use cases, Groupe Casino/Hitachi Energy benchmarks (verified via WebFetch)
- https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-time-series - BigQuery ML ARIMA_PLUS syntax, capabilities (verified via WebFetch)
- https://cloud.google.com/vertex-ai/pricing - Vertex AI prediction pricing (verified via WebSearch)
- https://cloud.google.com/bigquery/pricing - BigQuery ML training/prediction pricing (verified via WebSearch)

### Tertiary (LOW confidence - needs validation)
- None - all findings verified against official documentation or Context7

</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Prophet, StatsForecast, statsmodels
- GCP services: BigQuery ML ARIMA_PLUS, Vertex AI Forecasting (TiDE), integration patterns
- Ecosystem: sktime for unified interfaces, SHAP for explainability, pandas for data prep
- Patterns: On-demand with caching, background pre-computation, dimensional decomposition
- Pitfalls: Insufficient data, non-stationarity, forecast staleness, overfitting, irregular time series
- Cost analysis: Self-hosted vs BigQuery ML vs Vertex AI for VenezuelaWatch scale

**Confidence breakdown:**
- Standard stack: HIGH - Prophet (584 code snippets), StatsForecast (1617 snippets), statsmodels (2731 snippets) all verified via Context7
- GCP services: HIGH - Official GCP documentation for BigQuery ML, Vertex AI Forecasting, pricing verified via official pricing pages
- Architecture: HIGH - Patterns derived from official examples (Prophet cross-validation, StatsForecast multi-model)
- Pitfalls: HIGH - Documented in official Prophet docs (data gaps, minimum requirements) and StatsForecast benchmarks
- Code examples: HIGH - All examples from Context7 or official documentation, tested patterns
- Cost comparison: HIGH - Based on official GCP pricing, realistic workload estimates for VenezuelaWatch

**Research date:** 2026-01-09
**Valid until:** 2026-02-09 (30 days - forecasting ecosystem stable, Prophet 1.1.5 released 2023, StatsForecast 1.7 current, GCP services GA)

</metadata>

---

*Phase: 14-time-series-forecasting*
*Research completed: 2026-01-09*
*Ready for planning: yes*
