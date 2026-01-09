"""
Venezuela-relevant FRED economic series registry.

Defines which economic indicators to track, their metadata, and alert thresholds.
"""

# Venezuela Economic Series Registry
# Organized by category with threshold values for event generation
VENEZUELA_ECONOMIC_SERIES = {
    'oil_prices': {
        'DCOILWTICO': {
            'name': 'WTI Crude Oil Price',
            'units': 'USD/barrel',
            'frequency': 'daily',
            'threshold_low': 50.0,  # Generate alert if < $50/barrel
            'threshold_high': 100.0,  # Generate alert if > $100/barrel
            'description': 'West Texas Intermediate crude oil spot price - key indicator for Venezuela\'s oil-dependent economy',
        },
        'DCOILBRENTEU': {
            'name': 'Brent Crude Oil Price',
            'units': 'USD/barrel',
            'frequency': 'daily',
            'threshold_low': 55.0,
            'threshold_high': 105.0,
            'description': 'Brent crude oil spot price - European benchmark often closer to Venezuelan heavy crude pricing',
        },
    },
    'venezuela_macro': {
        'FPCPITOTLZGVEN': {
            'name': 'Venezuela CPI Inflation (YoY)',
            'units': 'percent',
            'frequency': 'annual',
            'threshold_high': 100.0,  # Hyperinflation alert at 100% YoY
            'description': 'Venezuela Consumer Price Index Year-over-Year change - tracks hyperinflation',
        },
        'NYGDPPCAPKDVEN': {
            'name': 'Venezuela GDP per Capita',
            'units': 'constant 2015 USD',
            'frequency': 'annual',
            'description': 'Venezuela GDP per capita in constant 2015 US dollars - economic output per person',
        },
    },
    'exchange_rates': {
        'DEXVZUS': {
            'name': 'Venezuela Bolivar / USD Exchange Rate',
            'units': 'VEF/USD',
            'frequency': 'daily',
            'note': 'Series may be discontinued due to hyperinflation. Handle gracefully if unavailable.',
            'description': 'Official Venezuela Bolivar to US Dollar exchange rate',
        },
    },
    'reserves': {
        'TRESEGVEA634N': {
            'name': 'Venezuela Total Reserves',
            'units': 'USD millions',
            'frequency': 'monthly',
            'threshold_low': 10_000.0,  # Alert if reserves drop below $10B
            'description': 'Total reserves excluding gold for Venezuela - foreign currency reserves',
        },
    },
}


def get_all_series_ids():
    """
    Get list of all FRED series IDs to monitor.

    Returns:
        list of series IDs (e.g., ['DCOILWTICO', 'DCOILBRENTEU', ...])
    """
    series_ids = []
    for category, series_dict in VENEZUELA_ECONOMIC_SERIES.items():
        series_ids.extend(series_dict.keys())
    return series_ids


def get_series_config(series_id: str):
    """
    Get configuration for a specific series ID.

    Args:
        series_id: FRED series identifier (e.g., 'DCOILWTICO')

    Returns:
        dict with series metadata and thresholds, or None if not found
    """
    for category, series_dict in VENEZUELA_ECONOMIC_SERIES.items():
        if series_id in series_dict:
            config = series_dict[series_id].copy()
            config['category'] = category
            config['series_id'] = series_id
            return config
    return None


def get_series_by_category(category: str):
    """
    Get all series in a specific category.

    Args:
        category: Category name (e.g., 'oil_prices', 'venezuela_macro')

    Returns:
        dict of series configurations for that category
    """
    return VENEZUELA_ECONOMIC_SERIES.get(category, {})
