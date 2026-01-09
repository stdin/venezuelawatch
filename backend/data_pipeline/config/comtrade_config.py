"""
Venezuela-relevant UN Comtrade commodity tracking configuration.

Defines which commodity codes to track and their metadata for trade flow analysis.
"""

# Venezuela Commodity Codes Registry
# HS (Harmonized System) codes for key imports/exports
VENEZUELA_COMMODITIES = {
    # Energy exports (Venezuela's primary export)
    '2709': {
        'name': 'Petroleum oils (crude)',
        'category': 'energy',
        'description': 'Crude petroleum and crude oils obtained from bituminous minerals',
        'priority': 'high',
    },
    '2710': {
        'name': 'Petroleum oils (refined)',
        'category': 'energy',
        'description': 'Petroleum oils (other than crude) and preparations containing petroleum',
        'priority': 'high',
    },

    # Food imports (critical due to food security issues)
    '1001': {
        'name': 'Wheat',
        'category': 'food',
        'description': 'Wheat and meslin',
        'priority': 'high',
    },
    '1005': {
        'name': 'Maize (corn)',
        'category': 'food',
        'description': 'Maize (corn)',
        'priority': 'high',
    },
    '0201': {
        'name': 'Beef (fresh/chilled)',
        'category': 'food',
        'description': 'Meat of bovine animals, fresh or chilled',
        'priority': 'medium',
    },

    # Healthcare imports
    '3004': {
        'name': 'Medicaments',
        'category': 'healthcare',
        'description': 'Medicaments consisting of mixed or unmixed products for therapeutic or prophylactic uses',
        'priority': 'high',
    },

    # Technology/Capital goods imports
    '8471': {
        'name': 'Computing machinery',
        'category': 'technology',
        'description': 'Automatic data processing machines and units thereof',
        'priority': 'medium',
    },
    '8517': {
        'name': 'Telephone/communication equipment',
        'category': 'technology',
        'description': 'Telephone sets, other apparatus for transmission or reception of voice, images or other data',
        'priority': 'medium',
    },

    # Total trade (for aggregate tracking)
    'TOTAL': {
        'name': 'All commodities',
        'category': 'total_trade',
        'description': 'Total trade across all commodity codes',
        'priority': 'high',
    },
}


# Trade flow thresholds
# Minimum USD value to create an Event (reduces noise from minor transactions)
MIN_TRADE_VALUE_USD = 10_000_000  # $10 million


def get_all_commodities():
    """
    Get list of all commodity codes to track.

    Returns:
        list of commodity code strings (e.g., ['2709', '2710', ...])
    """
    return list(VENEZUELA_COMMODITIES.keys())


def get_commodity_config(commodity_code: str):
    """
    Get configuration for a specific commodity code.

    Args:
        commodity_code: HS commodity code (e.g., '2709')

    Returns:
        dict with commodity metadata, or None if not found
    """
    return VENEZUELA_COMMODITIES.get(commodity_code)


def get_commodities_by_category(category: str):
    """
    Get all commodities in a specific category.

    Args:
        category: Category name (e.g., 'energy', 'food', 'healthcare')

    Returns:
        dict of commodity codes and their configurations for that category
    """
    return {
        code: config
        for code, config in VENEZUELA_COMMODITIES.items()
        if config.get('category') == category
    }


def get_priority_commodities(priority: str = 'high'):
    """
    Get commodities by priority level.

    Args:
        priority: Priority level ('high', 'medium', 'low')

    Returns:
        dict of commodity codes and their configurations for that priority
    """
    return {
        code: config
        for code, config in VENEZUELA_COMMODITIES.items()
        if config.get('priority') == priority
    }
