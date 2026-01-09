"""
Risk aggregation service for multi-dimensional risk scoring.

Combines multiple risk dimensions (LLM assessment, sanctions, sentiment,
urgency, supply chain) using weighted aggregation following ICRG/NCISS patterns.

Produces composite risk scores (0-100) that avoid score inflation and capture
nuanced risk across multiple domains.
"""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class RiskAggregator:
    """
    Multi-dimensional risk aggregation using weighted scoring.

    Follows NCISS/ICRG patterns for weighted arithmetic mean with
    strict weight normalization to prevent score inflation.

    Core principles:
    - Weights MUST sum to 1.0 exactly (avoids inflation)
    - Sanctions dimension highest weight (0.30-0.35) as binary flag
    - Event-type-specific weight distributions
    - Final score scaled to 0-100 for dashboard display
    """

    # Default weights (MUST sum to 1.0)
    DEFAULT_WEIGHTS = {
        'llm_base_risk': 0.25,      # LLM's risk assessment
        'sanctions': 0.30,           # Sanctions exposure (highest weight - binary)
        'sentiment': 0.20,           # Sentiment risk (negative = risky)
        'urgency': 0.15,             # Urgency level from LLM
        'supply_chain': 0.10,        # Supply chain impact
    }

    # Event-type-specific weight overrides
    EVENT_TYPE_WEIGHTS = {
        'TRADE': {
            'supply_chain': 0.25,    # Higher weight for trade events
            'sanctions': 0.35,
            'llm_base_risk': 0.20,
            'sentiment': 0.15,
            'urgency': 0.05,
        },
        'POLITICAL': {
            'sanctions': 0.40,       # Political events emphasize sanctions
            'llm_base_risk': 0.30,
            'sentiment': 0.20,
            'urgency': 0.10,
            'supply_chain': 0.00,    # Not relevant for pure political events
        },
        'HUMANITARIAN': {
            'urgency': 0.30,         # Humanitarian emphasizes urgency
            'sentiment': 0.25,
            'llm_base_risk': 0.25,
            'sanctions': 0.15,
            'supply_chain': 0.05,
        },
        'ECONOMIC': {
            'llm_base_risk': 0.30,
            'supply_chain': 0.25,
            'sanctions': 0.25,
            'sentiment': 0.15,
            'urgency': 0.05,
        },
        'CRISIS': {
            'urgency': 0.35,         # Crisis events emphasize urgency
            'llm_base_risk': 0.30,
            'sentiment': 0.20,
            'sanctions': 0.10,
            'supply_chain': 0.05,
        },
    }

    @classmethod
    def calculate_composite_risk(
        cls,
        llm_risk: float,
        sanctions_score: float,
        sentiment: float,
        urgency: str,
        event_type: str,
        themes: List[str]
    ) -> float:
        """
        Calculate composite risk score from multiple dimensions.

        Uses weighted aggregation with event-type-specific weights.
        All dimensions normalized to 0.0-1.0 before aggregation.

        Args:
            llm_risk: 0.0-1.0 from LLM analysis (risk.score field)
            sanctions_score: 0.0 or 1.0 from sanctions screening
            sentiment: -1.0 to 1.0 (negative = risky)
            urgency: 'low', 'medium', 'high', 'immediate'
            event_type: Event type for weight selection
            themes: List of themes for supply chain detection

        Returns:
            Risk score 0-100 (scaled from weighted 0.0-1.0)

        Example:
            >>> score = RiskAggregator.calculate_composite_risk(
            ...     llm_risk=0.7,
            ...     sanctions_score=1.0,
            ...     sentiment=-0.5,
            ...     urgency='high',
            ...     event_type='POLITICAL',
            ...     themes=['sanctions', 'arrest']
            ... )
            >>> assert 0 <= score <= 100
        """
        # Map urgency to risk score (0.0-1.0)
        urgency_map = {
            'low': 0.2,
            'medium': 0.5,
            'high': 0.8,
            'immediate': 1.0
        }
        urgency_risk = urgency_map.get(urgency.lower() if urgency else 'medium', 0.5)

        # Map sentiment to risk (absolute value, negative = risky)
        # Sentiment range: -1.0 (very negative) to +1.0 (very positive)
        # Risk interpretation: negative sentiment = higher risk
        if sentiment is not None:
            # Convert sentiment to risk: -1 -> 1.0, 0 -> 0.5, +1 -> 0.0
            sentiment_risk = 0.5 - (sentiment * 0.5)
            # Clamp to [0, 1]
            sentiment_risk = max(0.0, min(1.0, sentiment_risk))
        else:
            sentiment_risk = 0.5  # Neutral if no sentiment data

        # Calculate supply chain risk from themes
        supply_chain_risk = cls._calculate_supply_chain_risk(themes)

        # Get weights for this event type (or default)
        weights = cls.EVENT_TYPE_WEIGHTS.get(event_type, cls.DEFAULT_WEIGHTS)

        # Validate weights sum to 1.0 (critical for avoiding inflation)
        weight_sum = sum(weights.values())
        if abs(weight_sum - 1.0) > 0.001:  # Allow tiny floating point error
            logger.warning(
                f"Weights for {event_type} sum to {weight_sum:.4f}, not 1.0. "
                f"Normalizing to prevent score inflation."
            )
            # Normalize weights
            weights = {k: v / weight_sum for k, v in weights.items()}

        # Build dimensions dict
        dimensions = {
            'llm_base_risk': llm_risk,
            'sanctions': sanctions_score,
            'sentiment': sentiment_risk,
            'urgency': urgency_risk,
            'supply_chain': supply_chain_risk,
        }

        # Weighted aggregation
        composite = sum(
            dimensions[dim] * weights.get(dim, 0.0)
            for dim in dimensions
        )

        # Clamp to [0, 1] (should already be, but safety check)
        composite = max(0.0, min(1.0, composite))

        # Scale to 0-100
        final_score = round(composite * 100, 2)

        logger.debug(
            f"Composite risk: {final_score:.2f} "
            f"(llm={llm_risk:.2f}, sanctions={sanctions_score:.2f}, "
            f"sentiment={sentiment_risk:.2f}, urgency={urgency_risk:.2f}, "
            f"supply_chain={supply_chain_risk:.2f}, type={event_type})"
        )

        return final_score

    @classmethod
    def _calculate_supply_chain_risk(cls, themes: List[str]) -> float:
        """
        Detect supply chain risk from event themes.

        Checks for keywords indicating supply chain disruption,
        trade impacts, or commodity/energy concerns.

        Args:
            themes: List of event themes (from LLM analysis)

        Returns:
            Supply chain risk score 0.0-1.0

        Example:
            >>> themes = ['oil', 'sanctions', 'export']
            >>> risk = RiskAggregator._calculate_supply_chain_risk(themes)
            >>> assert risk >= 0.6  # High supply chain risk
        """
        if not themes:
            return 0.0

        # Supply chain keywords (lowercase)
        supply_chain_keywords = [
            'oil', 'export', 'trade', 'port', 'refinery', 'sanctions',
            'embargo', 'commodity', 'shipping', 'energy', 'petroleum',
            'imports', 'logistics', 'supply', 'disruption', 'blockade'
        ]

        # Convert themes to lowercase for matching
        themes_text = ' '.join(themes).lower()

        # Count keyword matches
        matches = sum(
            1 for keyword in supply_chain_keywords
            if keyword in themes_text
        )

        # Map match count to risk score
        if matches >= 3:
            return 0.8  # High supply chain risk
        elif matches >= 2:
            return 0.6  # Moderate-high risk
        elif matches >= 1:
            return 0.4  # Moderate risk
        else:
            return 0.0  # No supply chain risk detected

    @classmethod
    def validate_weights(cls) -> bool:
        """
        Validate that all weight configurations sum to 1.0.

        Returns:
            True if all weights valid, False otherwise
        """
        # Check default weights
        default_sum = sum(cls.DEFAULT_WEIGHTS.values())
        if abs(default_sum - 1.0) > 0.001:
            logger.error(
                f"DEFAULT_WEIGHTS sum to {default_sum:.4f}, not 1.0. "
                f"This will cause score inflation!"
            )
            return False

        # Check event-type weights
        for event_type, weights in cls.EVENT_TYPE_WEIGHTS.items():
            weight_sum = sum(weights.values())
            if abs(weight_sum - 1.0) > 0.001:
                logger.error(
                    f"EVENT_TYPE_WEIGHTS[{event_type}] sum to {weight_sum:.4f}, not 1.0. "
                    f"This will cause score inflation!"
                )
                return False

        logger.info("All weight configurations validated successfully")
        return True
