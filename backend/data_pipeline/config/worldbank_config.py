"""
Venezuela-relevant World Bank development indicators configuration.

Defines which indicators to track for Venezuela development metrics.
"""

# Venezuela Development Indicators Registry
# World Bank indicator codes for key economic, social, and infrastructure metrics
VENEZUELA_INDICATORS = {
    # Economic indicators
    'NY.GDP.MKTP.CD': {
        'name': 'GDP (current USD)',
        'category': 'economic',
        'description': 'Gross domestic product in current US dollars',
        'units': 'current USD',
        'priority': 'high',
    },
    'FP.CPI.TOTL.ZG': {
        'name': 'Inflation (CPI)',
        'category': 'economic',
        'description': 'Inflation as measured by consumer price index (annual %)',
        'units': 'percent',
        'priority': 'high',
    },
    'NY.GDP.PCAP.CD': {
        'name': 'GDP per capita',
        'category': 'economic',
        'description': 'GDP per capita in current US dollars',
        'units': 'current USD',
        'priority': 'high',
    },

    # Labor market
    'SL.UEM.TOTL.ZS': {
        'name': 'Unemployment rate',
        'category': 'labor',
        'description': 'Unemployment, total (% of total labor force)',
        'units': 'percent',
        'priority': 'medium',
    },

    # Social indicators
    'SI.POV.NAHC': {
        'name': 'Poverty headcount ratio',
        'category': 'social',
        'description': 'Poverty headcount ratio at national poverty lines (% of population)',
        'units': 'percent',
        'priority': 'high',
    },
    'SE.XPD.TOTL.GD.ZS': {
        'name': 'Education expenditure (% GDP)',
        'category': 'social',
        'description': 'Government expenditure on education, total (% of GDP)',
        'units': 'percent',
        'priority': 'medium',
    },
    'SH.XPD.CHEX.GD.ZS': {
        'name': 'Health expenditure (% GDP)',
        'category': 'social',
        'description': 'Current health expenditure (% of GDP)',
        'units': 'percent',
        'priority': 'medium',
    },

    # Infrastructure & services
    'EG.ELC.ACCS.ZS': {
        'name': 'Electricity access (%)',
        'category': 'infrastructure',
        'description': 'Access to electricity (% of population)',
        'units': 'percent',
        'priority': 'medium',
    },
    'IT.NET.USER.ZS': {
        'name': 'Internet users (%)',
        'category': 'infrastructure',
        'description': 'Individuals using the Internet (% of population)',
        'units': 'percent',
        'priority': 'low',
    },

    # Demographics
    'SP.POP.TOTL': {
        'name': 'Population total',
        'category': 'demographic',
        'description': 'Total population',
        'units': 'people',
        'priority': 'medium',
    },
}


def get_all_indicators():
    """
    Get list of all World Bank indicator codes to track.

    Returns:
        list of indicator code strings (e.g., ['NY.GDP.MKTP.CD', ...])
    """
    return list(VENEZUELA_INDICATORS.keys())


def get_indicator_config(indicator_id: str):
    """
    Get configuration for a specific indicator.

    Args:
        indicator_id: World Bank indicator code (e.g., 'NY.GDP.MKTP.CD')

    Returns:
        dict with indicator metadata, or None if not found
    """
    return VENEZUELA_INDICATORS.get(indicator_id)


def get_indicators_by_category(category: str):
    """
    Get all indicators in a specific category.

    Args:
        category: Category name (e.g., 'economic', 'social', 'infrastructure')

    Returns:
        dict of indicator codes and their configurations for that category
    """
    return {
        code: config
        for code, config in VENEZUELA_INDICATORS.items()
        if config.get('category') == category
    }


def get_priority_indicators(priority: str = 'high'):
    """
    Get indicators by priority level.

    Args:
        priority: Priority level ('high', 'medium', 'low')

    Returns:
        dict of indicator codes and their configurations for that priority
    """
    return {
        code: config
        for code, config in VENEZUELA_INDICATORS.items()
        if config.get('priority') == priority
    }
