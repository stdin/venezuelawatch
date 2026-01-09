"""
Risk scoring service for events.

Calculates risk scores based on event characteristics including:
- Event type and source
- Sentiment analysis
- Content indicators (keywords, themes)
- Economic/trade/development metrics
"""
import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


class RiskScorer:
    """
    Risk assessment engine for Venezuela intelligence events.

    Generates risk scores from 0.0 (low risk) to 1.0 (high risk) based on
    multiple factors including event type, sentiment, keywords, and metrics.
    """

    # Event type risk weights (base risk multipliers)
    EVENT_TYPE_WEIGHTS = {
        'CONFLICT': 0.8,
        'CRISIS': 0.8,
        'POLITICAL': 0.7,
        'HUMANITARIAN': 0.7,
        'PROTEST': 0.6,
        'ECONOMIC': 0.5,
        'TRADE': 0.4,
        'DEVELOPMENT_INDICATOR': 0.3,
        'NEWS': 0.3,
        'OTHER': 0.2,
    }

    # Source reliability multipliers
    SOURCE_RELIABILITY = {
        'RELIEFWEB': 0.9,    # UN humanitarian updates (high reliability)
        'FRED': 0.9,          # Federal Reserve economic data (high reliability)
        'WORLD_BANK': 0.9,    # World Bank indicators (high reliability)
        'COMTRADE': 0.8,      # UN trade statistics (reliable)
        'GDELT': 0.6,         # News aggregator (variable quality)
    }

    # High-risk keywords (presence increases risk score)
    HIGH_RISK_KEYWORDS = [
        # Political instability
        'crisis', 'collapse', 'coup', 'dictatorship', 'authoritarian',
        'regime', 'oppression', 'crackdown', 'arrest', 'detention',
        # Violence and conflict
        'violence', 'attack', 'killed', 'death', 'massacre', 'clashes',
        'military', 'armed', 'weapon', 'gunfire', 'explosion',
        # Humanitarian crisis
        'famine', 'starvation', 'malnutrition', 'epidemic', 'outbreak',
        'refugee', 'displacement', 'shortage', 'scarcity', 'emergency',
        # Economic collapse
        'hyperinflation', 'default', 'sanctions', 'embargo', 'recession',
        'unemployment', 'poverty', 'bankruptcy', 'debt', 'crisis',
        # Social unrest
        'protest', 'riot', 'strike', 'unrest', 'demonstration',
        'uprising', 'rebellion', 'revolt', 'resistance',
    ]

    # Economic indicator thresholds (for FRED data)
    ECONOMIC_THRESHOLDS = {
        'inflation_high': 50.0,         # >50% inflation = high risk
        'oil_price_drop': -20.0,        # >20% oil price drop = high risk
        'currency_devaluation': -30.0,  # >30% currency drop = high risk
    }

    @classmethod
    def calculate_risk_score(cls, event: 'Event') -> float:
        """
        Calculate comprehensive risk score for an event.

        Args:
            event: Event model instance

        Returns:
            Risk score from 0.0 (low risk) to 1.0 (high risk)
        """
        try:
            risk_components = []

            # 1. Base risk from event type (20% weight)
            event_type_risk = cls._calculate_event_type_risk(event)
            risk_components.append((event_type_risk, 0.20))

            # 2. Source reliability adjustment (10% weight)
            source_risk = cls._calculate_source_risk(event)
            risk_components.append((source_risk, 0.10))

            # 3. Sentiment-based risk (30% weight)
            sentiment_risk = cls._calculate_sentiment_risk(event)
            risk_components.append((sentiment_risk, 0.30))

            # 4. Keyword presence risk (25% weight)
            keyword_risk = cls._calculate_keyword_risk(event)
            risk_components.append((keyword_risk, 0.25))

            # 5. Metric-based risk for economic events (15% weight)
            metric_risk = cls._calculate_metric_risk(event)
            risk_components.append((metric_risk, 0.15))

            # Calculate weighted risk score
            total_risk = sum(
                risk * weight
                for risk, weight in risk_components
            )

            # Clamp to [0.0, 1.0]
            total_risk = max(0.0, min(1.0, total_risk))

            logger.info(
                f"Event {event.id} risk score: {total_risk:.3f} "
                f"(type={event_type_risk:.2f}, source={source_risk:.2f}, "
                f"sentiment={sentiment_risk:.2f}, keywords={keyword_risk:.2f}, "
                f"metrics={metric_risk:.2f})"
            )

            return round(total_risk, 4)

        except Exception as e:
            logger.error(f"Failed to calculate risk score for Event {event.id}: {e}", exc_info=True)
            return 0.5  # Default to medium risk on error

    @classmethod
    def _calculate_event_type_risk(cls, event: 'Event') -> float:
        """Calculate base risk from event type."""
        event_type = event.event_type or 'OTHER'
        return cls.EVENT_TYPE_WEIGHTS.get(event_type, 0.2)

    @classmethod
    def _calculate_source_risk(cls, event: 'Event') -> float:
        """Calculate risk adjustment based on source reliability."""
        source = event.source
        reliability = cls.SOURCE_RELIABILITY.get(source, 0.5)

        # Convert reliability to risk (inverse relationship)
        # High reliability (0.9) → low risk contribution (0.1)
        # Low reliability (0.5) → medium risk contribution (0.5)
        return 1.0 - reliability

    @classmethod
    def _calculate_sentiment_risk(cls, event: 'Event') -> float:
        """
        Calculate risk from sentiment score.

        Negative sentiment → higher risk
        Neutral sentiment → medium risk
        Positive sentiment → lower risk
        """
        sentiment = event.sentiment

        if sentiment is None:
            # No sentiment data available - use neutral risk
            return 0.5

        # Map sentiment [-1, +1] to risk [0.8, 0.2]
        # sentiment = -1 (very negative) → risk = 0.8
        # sentiment = 0 (neutral) → risk = 0.5
        # sentiment = +1 (very positive) → risk = 0.2
        risk = 0.5 - (sentiment * 0.3)

        return max(0.0, min(1.0, risk))

    @classmethod
    def _calculate_keyword_risk(cls, event: 'Event') -> float:
        """
        Calculate risk from presence of high-risk keywords.

        Checks title and content for keywords indicating instability,
        violence, crisis, or economic collapse.
        """
        # Collect all text to analyze
        text_parts = []

        if event.title:
            text_parts.append(event.title.lower())

        content_dict = event.content if isinstance(event.content, dict) else {}
        for field in ['description', 'summary', 'text', 'body']:
            if field in content_dict and content_dict[field]:
                text_parts.append(str(content_dict[field]).lower())

        combined_text = ' '.join(text_parts)

        if not combined_text:
            return 0.0

        # Count keyword matches
        keyword_matches = sum(
            1 for keyword in cls.HIGH_RISK_KEYWORDS
            if re.search(r'\b' + re.escape(keyword) + r'\b', combined_text)
        )

        # Calculate risk based on keyword density
        # 0 keywords → 0.0 risk
        # 1-2 keywords → 0.3 risk
        # 3-4 keywords → 0.6 risk
        # 5+ keywords → 0.9 risk
        if keyword_matches == 0:
            return 0.0
        elif keyword_matches <= 2:
            return 0.3
        elif keyword_matches <= 4:
            return 0.6
        else:
            return 0.9

    @classmethod
    def _calculate_metric_risk(cls, event: 'Event') -> float:
        """
        Calculate risk from economic/trade metrics.

        Applies to FRED, Comtrade, and World Bank events.
        """
        source = event.source
        content = event.content if isinstance(event.content, dict) else {}

        # FRED economic data risk
        if source == 'FRED':
            return cls._calculate_fred_risk(content)

        # Comtrade trade data risk
        elif source == 'COMTRADE':
            return cls._calculate_comtrade_risk(content)

        # World Bank development indicators risk
        elif source == 'WORLD_BANK':
            return cls._calculate_worldbank_risk(content)

        # Other sources - no metric-based risk
        return 0.0

    @classmethod
    def _calculate_fred_risk(cls, content: Dict[str, Any]) -> float:
        """Calculate risk from FRED economic observations."""
        value = content.get('value')
        series_id = content.get('series_id', '')

        if value is None:
            return 0.0

        # Oil price series - significant drops increase risk
        if 'POIL' in series_id or 'WTI' in series_id or 'BRENT' in series_id:
            # Check for price drops (simplified - would need historical context)
            if value < 40:  # Oil below $40/barrel
                return 0.7
            elif value < 60:
                return 0.4
            else:
                return 0.2

        # Exchange rate series - devaluation increases risk
        elif 'DEXUS' in series_id or 'VES' in series_id:
            # High exchange rates indicate devaluation
            if value > 30:
                return 0.8
            elif value > 20:
                return 0.5
            else:
                return 0.2

        # Default for other series
        return 0.3

    @classmethod
    def _calculate_comtrade_risk(cls, content: Dict[str, Any]) -> float:
        """Calculate risk from Comtrade trade flow data."""
        flow_type = content.get('flow_type', '')
        trade_value = content.get('trade_value_usd', 0)
        commodity_category = content.get('commodity_category', '')

        # Very low trade values may indicate economic isolation
        if trade_value < 50_000_000:  # < $50M
            return 0.6

        # Food/healthcare imports indicate humanitarian need
        if flow_type == 'imports' and commodity_category in ['food', 'healthcare']:
            return 0.5

        # Energy export dependence
        if flow_type == 'exports' and commodity_category == 'energy':
            # High energy export dependence = moderate risk
            return 0.4

        return 0.2

    @classmethod
    def _calculate_worldbank_risk(cls, content: Dict[str, Any]) -> float:
        """Calculate risk from World Bank development indicators."""
        indicator_id = content.get('indicator_id', '')
        value = content.get('value')

        if value is None:
            return 0.0

        # GDP decline
        if 'GDP' in indicator_id:
            # Negative GDP growth or very low GDP
            if value < 0 or value < 1_000_000_000:  # < $1B GDP
                return 0.8
            return 0.3

        # High inflation
        if 'CPI' in indicator_id or 'INFL' in indicator_id:
            if value > 100:  # >100% inflation
                return 0.9
            elif value > 50:
                return 0.7
            elif value > 20:
                return 0.5
            return 0.2

        # High unemployment
        if 'UEM' in indicator_id:
            if value > 20:
                return 0.7
            elif value > 10:
                return 0.5
            return 0.3

        # High poverty
        if 'POV' in indicator_id:
            if value > 50:  # >50% poverty rate
                return 0.8
            elif value > 30:
                return 0.6
            return 0.3

        return 0.3

    @classmethod
    def get_risk_level(cls, score: float) -> str:
        """
        Convert risk score to human-readable level.

        Args:
            score: Risk score from 0.0 to 1.0

        Returns:
            Risk level: 'low', 'medium', 'high', or 'critical'
        """
        if score >= 0.75:
            return 'critical'
        elif score >= 0.50:
            return 'high'
        elif score >= 0.25:
            return 'medium'
        else:
            return 'low'
