"""
GDELT GKG field parsers for V2 enrichment data.

Parses delimited GKG string fields into structured Python data structures.
Focus on Venezuela-relevant themes and entities.
"""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Venezuela-relevant GKG themes (subset of 3000+ total themes)
VENEZUELA_RELEVANT_THEMES = {
    'ECON_CURRENCY',
    'ECON_INFLATION',
    'ECON_GDP',
    'CIVILIAN',
    'PROTEST',
    'LEADER',
    'GOVERNMENT',
    'ELECTIONS',
    'SANCTIONS',
    'REFUGEE',
    'HUMANITARIAN',
    'MIGRATION',
    'OIL',
    'ENERGY',
    'CORRUPTION',
    'HUMAN_RIGHTS',
    'DEMOCRACY',
    'AUTOCRACY',
    'TRADE',
    'DIPLOMACY',
}


def parse_v2_themes(themes_str: Optional[str]) -> List[str]:
    """
    Parse V2Themes semicolon-separated field into list of theme codes.

    Format: "THEME1;THEME2;THEME3"
    Example: "ECON_CURRENCY;CIVILIAN;PROTEST"

    Args:
        themes_str: Raw V2Themes string from GKG

    Returns:
        List of theme codes (empty list if None/empty)
    """
    if not themes_str:
        return []

    try:
        themes = [theme.strip() for theme in themes_str.split(';') if theme.strip()]
        return themes
    except Exception as e:
        logger.warning(f"Failed to parse V2Themes '{themes_str}': {e}")
        return []


def parse_v2_persons(persons_str: Optional[str]) -> List[str]:
    """
    Parse V2Persons field into list of person names.

    Format: "Name,Offset,Length;Name,Offset,Length;..."
    Example: "John Doe,0,8;Jane Smith,10,10"

    Extracts only names (ignores offsets).

    Args:
        persons_str: Raw V2Persons string from GKG

    Returns:
        Deduplicated list of person names (empty list if None/empty)
    """
    if not persons_str:
        return []

    try:
        names = []
        for person_entry in persons_str.split(';'):
            if not person_entry.strip():
                continue
            parts = person_entry.split(',')
            if parts:
                name = parts[0].strip()
                if name:
                    names.append(name)

        # Deduplicate while preserving order
        seen = set()
        unique_names = []
        for name in names:
            if name not in seen:
                seen.add(name)
                unique_names.append(name)

        return unique_names
    except Exception as e:
        logger.warning(f"Failed to parse V2Persons '{persons_str}': {e}")
        return []


def parse_v2_organizations(orgs_str: Optional[str]) -> List[str]:
    """
    Parse V2Organizations field into list of organization names.

    Format: Same as V2Persons - "Name,Offset,Length;Name,Offset,Length;..."
    Example: "United Nations,5,14;World Bank,25,10"

    Extracts only names (ignores offsets).

    Args:
        orgs_str: Raw V2Organizations string from GKG

    Returns:
        Deduplicated list of organization names (empty list if None/empty)
    """
    if not orgs_str:
        return []

    try:
        names = []
        for org_entry in orgs_str.split(';'):
            if not org_entry.strip():
                continue
            parts = org_entry.split(',')
            if parts:
                name = parts[0].strip()
                if name:
                    names.append(name)

        # Deduplicate while preserving order
        seen = set()
        unique_names = []
        for name in names:
            if name not in seen:
                seen.add(name)
                unique_names.append(name)

        return unique_names
    except Exception as e:
        logger.warning(f"Failed to parse V2Organizations '{orgs_str}': {e}")
        return []


def parse_v2_locations(locations_str: Optional[str]) -> List[Dict[str, Any]]:
    """
    Parse V2Locations field into list of location dicts with coordinates.

    Format: "Type#Name#CountryCode#ADM1#ADM2#Lat#Long#FeatureID#FullName#..."
    Example: "2#Venezuela#VE#VE##-8#-66#VE#USVE#Venezuela;..."

    Extracts: name, country_code, lat, long
    Skips entries missing lat/long.

    Args:
        locations_str: Raw V2Locations string from GKG

    Returns:
        List of dicts with keys: name, country_code, lat, long (empty list if None/empty)
    """
    if not locations_str:
        return []

    try:
        locations = []
        for location_entry in locations_str.split(';'):
            if not location_entry.strip():
                continue

            parts = location_entry.split('#')
            if len(parts) < 7:
                continue

            # Extract fields (Type#Name#CountryCode#ADM1#ADM2#Lat#Long#...)
            name = parts[1].strip() if len(parts) > 1 else None
            country_code = parts[2].strip() if len(parts) > 2 else None
            lat_str = parts[5].strip() if len(parts) > 5 else None
            long_str = parts[6].strip() if len(parts) > 6 else None

            # Skip if missing name or coordinates
            if not name or not lat_str or not long_str:
                continue

            try:
                lat = float(lat_str)
                long = float(long_str)

                locations.append({
                    'name': name,
                    'country_code': country_code,
                    'lat': lat,
                    'long': long,
                })
            except (ValueError, TypeError):
                # Invalid lat/long, skip entry
                continue

        return locations
    except Exception as e:
        logger.warning(f"Failed to parse V2Locations '{locations_str}': {e}")
        return []


def parse_v2_tone(tone_str: Optional[str]) -> Dict[str, Optional[float]]:
    """
    Parse V2Tone field into dict of tone metrics.

    Format: "tone,positive%,negative%,polarity,activity,self_refs,group_refs,word_count"
    Example: "-3.45,5.2,8.65,0.6,150.5,0.8,2.1,850"

    Args:
        tone_str: Raw V2Tone string from GKG

    Returns:
        Dict with tone metrics (None values for missing/invalid fields)
    """
    if not tone_str:
        return {
            'tone': None,
            'positive_pct': None,
            'negative_pct': None,
            'polarity': None,
            'activity_density': None,
            'self_refs': None,
            'group_refs': None,
            'word_count': None,
        }

    try:
        parts = tone_str.split(',')

        def safe_float(value: str) -> Optional[float]:
            """Convert string to float, return None if invalid."""
            try:
                return float(value.strip()) if value.strip() else None
            except (ValueError, AttributeError):
                return None

        return {
            'tone': safe_float(parts[0]) if len(parts) > 0 else None,
            'positive_pct': safe_float(parts[1]) if len(parts) > 1 else None,
            'negative_pct': safe_float(parts[2]) if len(parts) > 2 else None,
            'polarity': safe_float(parts[3]) if len(parts) > 3 else None,
            'activity_density': safe_float(parts[4]) if len(parts) > 4 else None,
            'self_refs': safe_float(parts[5]) if len(parts) > 5 else None,
            'group_refs': safe_float(parts[6]) if len(parts) > 6 else None,
            'word_count': safe_float(parts[7]) if len(parts) > 7 else None,
        }
    except Exception as e:
        logger.warning(f"Failed to parse V2Tone '{tone_str}': {e}")
        return {
            'tone': None,
            'positive_pct': None,
            'negative_pct': None,
            'polarity': None,
            'activity_density': None,
            'self_refs': None,
            'group_refs': None,
            'word_count': None,
        }
