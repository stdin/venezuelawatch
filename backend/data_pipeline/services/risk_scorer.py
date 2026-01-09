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

    UPDATED: Now uses multi-dimensional risk aggregation via RiskAggregator
    for composite scores combining LLM risk, sanctions, sentiment, urgency,
    and supply chain dimensions.

    Legacy methods (calculate_risk_score with keyword/sentiment heuristics)
    maintained for backward compatibility.

    Generates risk scores from 0-100 based on weighted multi-dimensional
    aggregation of risk factors.
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
    def calculate_comprehensive_risk(cls, event: 'Event') -> float:
        """
        Calculate multi-dimensional risk score using RiskAggregator.

        This is the NEW risk scoring method that combines:
        - LLM base risk assessment
        - Sanctions screening results
        - Sentiment analysis
        - Urgency level
        - Supply chain impact

        Uses weighted aggregation with event-type-specific weights.

        Args:
            event: Event model instance with llm_analysis populated

        Returns:
            Composite risk score from 0-100

        Example:
            >>> from core.models import Event
            >>> event = Event.objects.filter(llm_analysis__isnull=False).first()
            >>> score = RiskScorer.calculate_comprehensive_risk(event)
            >>> assert 0 <= score <= 100
        """
        from data_pipeline.services.risk_aggregator import RiskAggregator
        from data_pipeline.services.sanctions_screener import SanctionsScreener

        try:
            # Extract LLM base risk (0.0-1.0)
            llm_risk = 0.5  # Default if no LLM analysis
            if event.llm_analysis:
                llm_risk = event.llm_analysis.get('risk', {}).get('score', 0.5)

            # Get sanctions screening score (0.0 or 1.0)
            # Check if event already has sanctions screening results
            if event.llm_analysis and 'sanctions_score' in event.llm_analysis:
                sanctions_score = event.llm_analysis['sanctions_score']
            else:
                # Screen entities if LLM analysis exists
                if event.llm_analysis and 'entities' in event.llm_analysis:
                    sanctions_score = SanctionsScreener.screen_event_entities(event)
                else:
                    sanctions_score = 0.0

            # Extract sentiment (-1.0 to 1.0)
            sentiment = event.sentiment if event.sentiment is not None else 0.0

            # Extract urgency (from LLM analysis or event field)
            urgency = event.urgency or 'medium'

            # Extract event type
            event_type = event.event_type or 'OTHER'

            # Extract themes (from LLM analysis or event field)
            themes = []
            if event.llm_analysis:
                themes = event.llm_analysis.get('themes', [])
            elif event.themes:
                themes = event.themes

            # Calculate composite risk using RiskAggregator
            composite_risk = RiskAggregator.calculate_composite_risk(
                llm_risk=llm_risk,
                sanctions_score=sanctions_score,
                sentiment=sentiment,
                urgency=urgency,
                event_type=event_type,
                themes=themes
            )

            logger.info(
                f"Event {event.id} comprehensive risk: {composite_risk:.2f} "
                f"(llm={llm_risk:.2f}, sanctions={sanctions_score:.2f}, "
                f"sentiment={sentiment:.2f}, urgency={urgency}, type={event_type})"
            )

            return composite_risk

        except Exception as e:
            logger.error(
                f"Failed to calculate comprehensive risk for Event {event.id}: {e}",
                exc_info=True
            )
            return 50.0  # Default to medium risk (50/100) on error

    @classmethod
    def calculate_risk_score(cls, event: 'Event') -> float:
        """
        Calculate risk score for an event.

        UPDATED: Now delegates to calculate_comprehensive_risk() which uses
        multi-dimensional RiskAggregator.

        Returns score scaled to 0-100 (not 0-1 like legacy version).

        Args:
            event: Event model instance

        Returns:
            Risk score from 0-100 (CHANGED from 0.0-1.0 in legacy version)
        """
        # Delegate to new comprehensive risk calculation
        return cls.calculate_comprehensive_risk(event)

    # ========================================================================
    # LEGACY METHODS - Kept for backward compatibility
    # These methods are no longer used by calculate_risk_score() but may be
    # referenced elsewhere. New code should use calculate_comprehensive_risk().
    # ========================================================================

    @classmethod
    def _calculate_event_type_risk(cls, event: 'Event') -> float:
        """Calculate base risk from event type. (LEGACY)"""
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
