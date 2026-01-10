"""
GDELT field reference utilities for CAMEO codes and geographic types.

Provides human-readable descriptions for GDELT codes without exhaustive tables.
Focus on Venezuela-relevant codes and common patterns.
"""
from typing import Optional

# Common CAMEO Actor Codes (Venezuela-relevant subset)
CAMEO_ACTOR_CODES = {
    'GOV': 'Government',
    'MIL': 'Military',
    'REB': 'Rebel/Opposition',
    'JUD': 'Judiciary',
    'LEG': 'Legislature',
    'COP': 'Police',
    'CVL': 'Civilian',
    'BUS': 'Business',
    'MED': 'Media',
    'EDU': 'Education',
    'NGO': 'NGO',
    'IGO': 'International Govt Org',
    # Add more as needed for Venezuela context
}

# CAMEO Event Code Categories (root codes)
CAMEO_EVENT_CODES = {
    '01': 'Make Public Statement',
    '02': 'Appeal',
    '03': 'Express Intent to Cooperate',
    '04': 'Consult',
    '05': 'Engage in Diplomatic Cooperation',
    '06': 'Engage in Material Cooperation',
    '07': 'Provide Aid',
    '08': 'Yield',
    '09': 'Investigate',
    '10': 'Demand',
    '11': 'Disapprove',
    '12': 'Reject',
    '13': 'Threaten',
    '14': 'Protest',
    '15': 'Exhibit Force Posture',
    '16': 'Reduce Relations',
    '17': 'Coerce',
    '18': 'Assault',
    '19': 'Fight',
    '20': 'Use Unconventional Mass Violence',
}

# Geographic Type Codes
GEO_TYPE_CODES = {
    1: 'Country',
    2: 'State/Province',
    3: 'City/District',
    4: 'Landmark',
    5: 'Coordinate',
}

# QuadClass Descriptions
QUAD_CLASS_NAMES = {
    1: 'Verbal Cooperation',
    2: 'Material Cooperation',
    3: 'Verbal Conflict',
    4: 'Material Conflict',
}


def decode_actor_code(code: Optional[str]) -> str:
    """Get human-readable description for CAMEO actor code."""
    if not code:
        return 'Unknown'

    # Check first 3 characters for standard codes
    prefix = code[:3] if len(code) >= 3 else code
    return CAMEO_ACTOR_CODES.get(prefix, code)


def decode_event_code(code: Optional[str]) -> str:
    """Get human-readable description for CAMEO event code."""
    if not code:
        return 'Unknown Event'

    # Use root code (first 2 digits)
    root = code[:2] if len(code) >= 2 else code
    return CAMEO_EVENT_CODES.get(root, f'Event {code}')


def get_geo_type_name(geo_type: Optional[int]) -> str:
    """Get geographic resolution type name."""
    if geo_type is None:
        return 'Unknown'
    return GEO_TYPE_CODES.get(geo_type, f'Type {geo_type}')


def get_quad_class_name(quad_class: Optional[int]) -> str:
    """Get QuadClass category name."""
    if quad_class is None:
        return 'Unknown'
    return QUAD_CLASS_NAMES.get(quad_class, f'Class {quad_class}')
