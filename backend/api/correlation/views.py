"""
Django REST API endpoints for statistical correlation analysis.

Provides POST /api/correlation/compute/ endpoint for computing pairwise correlations
between time-series variables with Bonferroni correction and effect size filtering.
"""

from ninja import Router, Schema
from typing import List, Literal, Optional
from datetime import date
from google.cloud import bigquery
from api.correlation.compute import compute_pairwise_correlations
from api.services.bigquery_service import BigQueryService
import pandas as pd

router = Router()


class CorrelationRequest(Schema):
    """Request schema for correlation computation."""
    variables: List[str]  # e.g., ["entity_123_risk", "oil_price", "sanctions_count"]
    start_date: date
    end_date: date
    method: Literal['pearson', 'spearman'] = 'pearson'
    min_effect_size: float = 0.7
    alpha: float = 0.05


class CorrelationResult(Schema):
    """Individual correlation result."""
    source: str
    target: str
    correlation: float
    p_value: float
    p_adjusted: float
    significant: bool
    sample_size: int
    warnings: List[str]


class CorrelationResponse(Schema):
    """Response schema with correlation results and metadata."""
    correlations: List[CorrelationResult]
    n_tested: int
    n_significant: int
    method: str
    bonferroni_threshold: float


@router.post("/compute/", response=CorrelationResponse)
def compute_correlations(request, payload: CorrelationRequest):
    """
    Compute pairwise correlations between selected variables with statistical rigor.

    Statistical methodology:
    - Computes Pearson (linear) or Spearman (monotonic) correlation with p-values
    - Applies Bonferroni correction for multiple comparisons problem
    - Filters to significant (p < alpha/n_tests) AND strong (|r| >= min_effect_size)
    - Checks stationarity for time-series data with ADF test

    Variable naming conventions:
    - Entity risk: "entity_{id}_risk" (e.g., "entity_123_risk")
    - FRED indicators: "oil_price", "inflation", "gdp", "exchange_rate"
    - Event counts: "{type}_count" (e.g., "sanctions_count", "political_count")

    Returns:
        Only correlations meeting BOTH significance AND effect size thresholds.
        Empty list if no strong + significant correlations found.
    """
    bq_service = BigQueryService()
    data_dict = {}

    # Extract time-series data for each variable
    for var in payload.variables:
        if var.startswith('entity_'):
            # Entity risk score time series
            # Parse entity_id from variable name (e.g., "entity_123_risk" -> "123")
            parts = var.split('_')
            if len(parts) >= 2:
                entity_id = parts[1]

                # Query BigQuery: entity_mentions joined with events for risk scores
                # Aggregate by date for time-series
                query = f"""
                SELECT
                    DATE(em.mentioned_at) as date,
                    AVG(e.risk_score) as risk_score
                FROM `{bq_service.project_id}.{bq_service.dataset_id}.entity_mentions` em
                JOIN `{bq_service.project_id}.{bq_service.dataset_id}.events` e ON em.event_id = e.id
                WHERE em.entity_id = @entity_id
                  AND DATE(em.mentioned_at) >= @start_date
                  AND DATE(em.mentioned_at) <= @end_date
                GROUP BY date
                ORDER BY date
                """
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("entity_id", "STRING", entity_id),
                        bigquery.ScalarQueryParameter("start_date", "DATE", payload.start_date),
                        bigquery.ScalarQueryParameter("end_date", "DATE", payload.end_date)
                    ]
                )
                df = bq_service.client.query(query, job_config=job_config).to_dataframe()
                if not df.empty:
                    data_dict[var] = df.set_index('date')['risk_score']

        elif var in ['oil_price', 'inflation', 'gdp', 'exchange_rate']:
            # FRED economic indicators
            # Map variable name to FRED series ID
            series_map = {
                'oil_price': 'DCOILWTICO',  # WTI Crude Oil Price
                'inflation': 'FPCPITOTLZGVEN',  # Venezuela inflation
                'gdp': 'NYGDPMKTPCDVZB',  # GDP per capita
                'exchange_rate': 'DEXVZUS'  # Venezuela exchange rate
            }

            query = f"""
            SELECT
                date,
                value
            FROM `{bq_service.project_id}.{bq_service.dataset_id}.fred_indicators`
            WHERE series_id = @series_id
              AND date >= @start_date
              AND date <= @end_date
            ORDER BY date
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("series_id", "STRING", series_map[var]),
                    bigquery.ScalarQueryParameter("start_date", "DATE", payload.start_date),
                    bigquery.ScalarQueryParameter("end_date", "DATE", payload.end_date)
                ]
            )
            df = bq_service.client.query(query, job_config=job_config).to_dataframe()
            if not df.empty:
                data_dict[var] = df.set_index('date')['value']

        elif var.endswith('_count'):
            # Event count aggregates (e.g., sanctions_count, political_count)
            # Extract event type from variable name (e.g., "sanctions_count" -> "sanctions")
            event_type = var.replace('_count', '')

            query = f"""
            SELECT
                DATE(mentioned_at) as date,
                COUNT(*) as count
            FROM `{bq_service.project_id}.{bq_service.dataset_id}.events`
            WHERE event_type = @event_type
              AND DATE(mentioned_at) >= @start_date
              AND DATE(mentioned_at) <= @end_date
            GROUP BY date
            ORDER BY date
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("event_type", "STRING", event_type),
                    bigquery.ScalarQueryParameter("start_date", "DATE", payload.start_date),
                    bigquery.ScalarQueryParameter("end_date", "DATE", payload.end_date)
                ]
            )
            df = bq_service.client.query(query, job_config=job_config).to_dataframe()
            if not df.empty:
                data_dict[var] = df.set_index('date')['count']

    # Align all time series to common dates (inner join, drops NaN)
    df_all = pd.DataFrame(data_dict).dropna()
    data_arrays = {col: df_all[col].values for col in df_all.columns}

    # Compute correlations with significance testing
    correlations = compute_pairwise_correlations(
        data_arrays,
        method=payload.method,
        alpha=payload.alpha,
        min_effect_size=payload.min_effect_size,
        check_stationarity=True  # Always check for time-series data
    )

    # Calculate total tests for reporting
    n_vars = len(payload.variables)
    n_total_tests = (n_vars * (n_vars - 1)) // 2

    return {
        'correlations': correlations,
        'n_tested': n_total_tests,
        'n_significant': len(correlations),
        'method': payload.method,
        'bonferroni_threshold': payload.alpha / n_total_tests if n_total_tests > 0 else payload.alpha
    }
