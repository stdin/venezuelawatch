"""
Correlation computation service with statistical significance testing.

Provides statistically rigorous correlation analysis with:
- Pearson (linear) and Spearman (monotonic) correlation methods
- Bonferroni correction for multiple comparisons
- Stationarity checks for time-series (ADF test with differencing)
- Effect size filtering (minimum |r| threshold)
"""

from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.stattools import adfuller
import pandas as pd
import numpy as np
from typing import List, Dict, Literal


def compute_pairwise_correlations(
    data_dict: Dict[str, np.ndarray],
    method: Literal['pearson', 'spearman'] = 'pearson',
    alpha: float = 0.05,
    min_effect_size: float = 0.7,
    check_stationarity: bool = True
) -> List[Dict]:
    """
    Compute pairwise correlations with statistical significance filtering.

    Statistical rigor:
    - Uses scipy.stats for correlation computation (not custom formulas)
    - Applies Bonferroni correction for multiple comparison problem
    - Checks stationarity with ADF test for time-series data
    - Filters to significant (p_adjusted < alpha) AND strong (|r| >= min_effect_size)

    Args:
        data_dict: {variable_name: time_series_array}
        method: 'pearson' (linear) or 'spearman' (monotonic)
        alpha: Significance level for Bonferroni correction (default 0.05)
        min_effect_size: Minimum |r| to report (default 0.7 for strong)
        check_stationarity: Apply ADF test for time-series (default True)

    Returns:
        List of {source, target, correlation, p_value, p_adjusted, significant, sample_size, warnings}
        Only returns correlations that are BOTH significant AND strong.
    """
    # Align all time series to common indices (inner join, drop NaN)
    df_all = pd.DataFrame(data_dict).dropna()

    if df_all.empty:
        return []

    variables = list(df_all.columns)
    n_vars = len(variables)

    if n_vars < 2:
        return []

    correlations = []

    # Compute all pairwise correlations
    for i in range(n_vars):
        for j in range(i + 1, n_vars):
            x = df_all[variables[i]].values
            y = df_all[variables[j]].values

            warnings = []

            # Stationarity check for time-series
            if check_stationarity and len(x) >= 12:  # Need minimum samples for ADF
                x, y, warnings = _check_and_difference(x, y, variables[i], variables[j], alpha)

            # Need minimum sample size after differencing
            if len(x) < 3:
                continue

            # Compute correlation
            try:
                if method == 'pearson':
                    r, p = stats.pearsonr(x, y)
                else:  # spearman
                    r, p = stats.spearmanr(x, y)

                correlations.append({
                    'source': variables[i],
                    'target': variables[j],
                    'correlation': float(r),
                    'p_value': float(p),
                    'sample_size': len(x),
                    'warnings': warnings
                })
            except (ValueError, RuntimeWarning):
                # Skip pairs with constant values or other issues
                continue

    # Apply Bonferroni correction for multiple comparisons
    if correlations:
        p_values = [c['p_value'] for c in correlations]
        rejected, p_adjusted, _, _ = multipletests(p_values, alpha=alpha, method='bonferroni')

        # Filter to significant AND strong correlations
        significant_correlations = []
        for corr, adj_p, is_sig in zip(correlations, p_adjusted, rejected):
            corr['p_adjusted'] = float(adj_p)
            corr['significant'] = bool(is_sig)
            # Only return if significant AND strong effect size
            if is_sig and abs(corr['correlation']) >= min_effect_size:
                significant_correlations.append(corr)

        return significant_correlations

    return []


def _check_and_difference(x: np.ndarray, y: np.ndarray, name_x: str, name_y: str, alpha: float):
    """
    Check stationarity with ADF test and apply differencing if needed.

    The ADF (Augmented Dickey-Fuller) test checks for unit roots:
    - Null hypothesis: Series has unit root (non-stationary)
    - p < alpha: Reject null, series is stationary
    - p >= alpha: Fail to reject, series is non-stationary (needs differencing)

    Returns:
        Tuple of (x_stationary, y_stationary, warnings)
    """
    warnings = []
    x_use = x.copy()
    y_use = y.copy()

    # ADF test for X (p < alpha means stationary)
    try:
        adf_x = adfuller(x, autolag='AIC')
        if adf_x[1] > alpha:  # Non-stationary
            x_use = np.diff(x)
            warnings.append(f'{name_x} was non-stationary (ADF p={adf_x[1]:.3f}), used first difference')
    except (ValueError, np.linalg.LinAlgError):
        # ADF can fail with constant series or numerical issues
        pass

    # ADF test for Y
    try:
        adf_y = adfuller(y, autolag='AIC')
        if adf_y[1] > alpha:  # Non-stationary
            y_use = np.diff(y)
            warnings.append(f'{name_y} was non-stationary (ADF p={adf_y[1]:.3f}), used first difference')
    except (ValueError, np.linalg.LinAlgError):
        pass

    # Align lengths after differencing
    min_len = min(len(x_use), len(y_use))
    x_use = x_use[-min_len:]
    y_use = y_use[-min_len:]

    return x_use, y_use, warnings
