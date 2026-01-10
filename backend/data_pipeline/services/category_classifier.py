"""
Category Classification System

Implements 10-category taxonomy from platform design:
POLITICAL, CONFLICT, ECONOMIC, TRADE, REGULATORY, INFRASTRUCTURE,
HEALTHCARE, SOCIAL, ENVIRONMENTAL, ENERGY

Maps source-specific codes/patterns to canonical categories:
- GDELT: CAMEO root codes (01-20)
- ACLED: event_type strings
- World Bank: indicator code prefixes
- Google Trends: search term keywords
- SEC EDGAR: filing context keywords
- FRED: series ID patterns
- UN Comtrade: commodity codes (HS 2-digit)
"""

from typing import Tuple, Dict, Any, Optional


class CategoryClassifier:
    """
    Classify events into 10-category taxonomy based on source data.
    """

    # GDELT CAMEO root codes → Category (from design doc section 5.1)
    GDELT_CATEGORY_MAP = {
        "01": "POLITICAL",      # Make public statement
        "02": "POLITICAL",      # Appeal
        "03": "POLITICAL",      # Express intent to cooperate
        "04": "POLITICAL",      # Consult
        "05": "POLITICAL",      # Diplomatic cooperation
        "06": "ECONOMIC",       # Material cooperation
        "07": "ECONOMIC",       # Provide aid
        "08": "POLITICAL",      # Yield
        "09": "POLITICAL",      # Investigate
        "10": "POLITICAL",      # Demand
        "11": "POLITICAL",      # Disapprove
        "12": "POLITICAL",      # Reject
        "13": "CONFLICT",       # Threaten
        "14": "SOCIAL",         # Protest (changed from CONFLICT to SOCIAL per design)
        "15": "REGULATORY",     # Exhibit force posture
        "16": "ECONOMIC",       # Reduce relations
        "17": "CONFLICT",       # Coerce
        "18": "CONFLICT",       # Assault
        "19": "CONFLICT",       # Fight
        "20": "CONFLICT",       # Use unconventional mass violence
    }

    # ACLED event types → Category
    ACLED_CATEGORY_MAP = {
        "Battles": "CONFLICT",
        "Explosions/Remote violence": "CONFLICT",
        "Violence against civilians": "CONFLICT",
        "Protests": "SOCIAL",
        "Riots": "CONFLICT",
        "Strategic developments": "POLITICAL",
    }

    # World Bank indicator prefixes → Category
    # Match on prefix (NY.GDP, FP.CPI, etc.)
    WORLD_BANK_CATEGORY_MAP = {
        "NY.GDP": "ECONOMIC",       # GDP indicators
        "FP.CPI": "ECONOMIC",       # Inflation
        "BX.KLT": "ECONOMIC",       # Foreign direct investment
        "NE.EXP": "TRADE",          # Exports
        "NE.IMP": "TRADE",          # Imports
        "SH.": "HEALTHCARE",        # Health indicators
        "EG.": "ENERGY",            # Energy indicators
        "SP.POP": "SOCIAL",         # Population
        "SE.": "SOCIAL",            # Education
        "EN.": "ENVIRONMENTAL",     # Environment
        "IS.": "INFRASTRUCTURE",    # Infrastructure (roads, etc.)
    }

    # Google Trends terms → Category (lowercase matching)
    GOOGLE_TRENDS_CATEGORY_MAP = {
        "venezuela sanctions": "REGULATORY",
        "venezuela oil": "ENERGY",
        "venezuela crisis": "POLITICAL",
        "venezuela inflation": "ECONOMIC",
        "venezuela protests": "SOCIAL",
        "pdvsa": "ENERGY",
        "maduro": "POLITICAL",
        "guaido": "POLITICAL",
        "oil": "ENERGY",
        "sanctions": "REGULATORY",
        "inflation": "ECONOMIC",
        "protests": "SOCIAL",
        "blackout": "INFRASTRUCTURE",
        "gold": "TRADE",
        "citgo": "ENERGY",
        "military": "CONFLICT",
    }

    # SEC EDGAR keywords → Category (substring matching)
    SEC_EDGAR_CATEGORY_MAP = {
        "sanction": "REGULATORY",
        "nationalization": "REGULATORY",
        "expropriation": "REGULATORY",
        "currency": "ECONOMIC",
        "hyperinflation": "ECONOMIC",
        "oil": "ENERGY",
        "pdvsa": "ENERGY",
        "default": "ECONOMIC",
        "debt": "ECONOMIC",
    }

    # FRED series patterns → Category (prefix matching)
    FRED_CATEGORY_MAP = {
        "EXVZUS": "ECONOMIC",       # Exchange rate
        "VENEZUEL": "ECONOMIC",     # Various indicators
    }

    # UN Comtrade commodity codes (HS 2-digit) → Category
    UN_COMTRADE_CATEGORY_MAP = {
        "27": "ENERGY",             # Mineral fuels, oils (includes crude oil)
        "71": "TRADE",              # Precious stones, metals (gold)
        "26": "TRADE",              # Ores, slag, ash
        "default": "TRADE",         # All other commodities default to TRADE
    }

    @classmethod
    def classify(cls, source: str, source_data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """
        Classify event into category and subcategory based on source data.

        Args:
            source: Source name ('gdelt', 'acled', 'world_bank', etc.)
            source_data: Raw source data dict

        Returns:
            (category, subcategory) tuple where:
            - category is one of 10 canonical categories
            - subcategory is source-specific code/identifier (CAMEO code, indicator ID, etc.)

        Examples:
            >>> CategoryClassifier.classify('gdelt', {'EventCode': '14'})
            ('SOCIAL', '14')

            >>> CategoryClassifier.classify('world_bank', {'indicator_code': 'NY.GDP.MKTP.CD'})
            ('ECONOMIC', 'NY.GDP.MKTP.CD')
        """

        if source == "gdelt":
            return cls._classify_gdelt(source_data)
        elif source == "acled":
            return cls._classify_acled(source_data)
        elif source == "world_bank":
            return cls._classify_world_bank(source_data)
        elif source == "google_trends":
            return cls._classify_google_trends(source_data)
        elif source == "sec_edgar":
            return cls._classify_sec_edgar(source_data)
        elif source == "fred":
            return cls._classify_fred(source_data)
        elif source == "un_comtrade":
            return cls._classify_un_comtrade(source_data)
        else:
            # Unknown source: default to POLITICAL for events, ECONOMIC for data
            return ("POLITICAL", None)

    @classmethod
    def _classify_gdelt(cls, data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """Classify GDELT event using CAMEO code."""
        event_code = data.get("EventCode", "")
        if not event_code:
            return ("POLITICAL", None)

        # Extract root code (first 2 digits)
        cameo_root = str(event_code)[:2]
        category = cls.GDELT_CATEGORY_MAP.get(cameo_root, "POLITICAL")
        return (category, event_code)

    @classmethod
    def _classify_acled(cls, data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """Classify ACLED event using event_type."""
        event_type = data.get("event_type", "")
        category = cls.ACLED_CATEGORY_MAP.get(event_type, "CONFLICT")
        return (category, event_type)

    @classmethod
    def _classify_world_bank(cls, data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """Classify World Bank indicator using code prefix."""
        indicator_code = data.get("indicator_code", "")
        if not indicator_code:
            return ("ECONOMIC", None)

        # Match on prefix
        for prefix, category in cls.WORLD_BANK_CATEGORY_MAP.items():
            if indicator_code.startswith(prefix):
                return (category, indicator_code)

        # Default to ECONOMIC for unmatched indicators
        return ("ECONOMIC", indicator_code)

    @classmethod
    def _classify_google_trends(cls, data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """Classify Google Trends using search term keywords."""
        term = data.get("term", "").lower()
        if not term:
            return ("POLITICAL", None)

        # Exact match
        if term in cls.GOOGLE_TRENDS_CATEGORY_MAP:
            return (cls.GOOGLE_TRENDS_CATEGORY_MAP[term], term)

        # Substring match
        for keyword, category in cls.GOOGLE_TRENDS_CATEGORY_MAP.items():
            if keyword in term:
                return (category, term)

        # Default to POLITICAL
        return ("POLITICAL", term)

    @classmethod
    def _classify_sec_edgar(cls, data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """Classify SEC filing using context text keywords."""
        context_text = data.get("context_text", "").lower()
        filing_type = data.get("filing_type", "")

        if not context_text:
            return ("REGULATORY", filing_type)

        # Substring match on context
        for keyword, category in cls.SEC_EDGAR_CATEGORY_MAP.items():
            if keyword in context_text:
                return (category, filing_type)

        # Default to REGULATORY for SEC filings
        return ("REGULATORY", filing_type)

    @classmethod
    def _classify_fred(cls, data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """Classify FRED series using series ID patterns."""
        series_id = data.get("series_id", "")
        if not series_id:
            return ("ECONOMIC", None)

        # Prefix match
        for prefix, category in cls.FRED_CATEGORY_MAP.items():
            if series_id.startswith(prefix):
                return (category, series_id)

        # Default to ECONOMIC
        return ("ECONOMIC", series_id)

    @classmethod
    def _classify_un_comtrade(cls, data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """Classify UN Comtrade using commodity code (HS 2-digit)."""
        commodity_code = str(data.get("commodity_code", ""))
        if not commodity_code:
            return ("TRADE", None)

        # Extract HS 2-digit code
        hs2 = commodity_code[:2] if len(commodity_code) >= 2 else commodity_code

        category = cls.UN_COMTRADE_CATEGORY_MAP.get(hs2, "TRADE")
        return (category, commodity_code)
