"""
Category Sub-Scores and Daily Composite Calculation

Implements category-specific risk scoring from platform design (sections 7.2-7.3):
- Calculate sub-scores for 10 categories with severity weighting
- Compute daily composite score with Venezuela-tuned weights
- Apply P1 event boost to daily composite

Venezuela-tuned weights (adjusted from generic commodity trader weights):
- ENERGY: 18% (vs 10% generic) - oil is Venezuela's economic lifeline
- REGULATORY: 15% (vs 12% generic) - sanctions are make-or-break for investors
- POLITICAL: 14% (vs 15% generic)
- ECONOMIC: 14% (vs 15% generic)
- CONFLICT: 11% (vs 12% generic) - normalized violence requires adjusted thresholds
- TRADE: 11% (vs 12% generic)
- INFRASTRUCTURE: 7% (vs 8% generic)
- SOCIAL: 5% (vs 6% generic)
- HEALTHCARE: 4% (vs 5% generic)
- ENVIRONMENTAL: 4% (vs 5% generic)
"""

from typing import List, Dict, Any


class CategoryScoring:
    """
    Calculate category sub-scores and daily composite risk scores.
    """

    # 10 canonical categories
    CATEGORIES = [
        'POLITICAL',
        'CONFLICT',
        'ECONOMIC',
        'TRADE',
        'REGULATORY',
        'INFRASTRUCTURE',
        'HEALTHCARE',
        'SOCIAL',
        'ENVIRONMENTAL',
        'ENERGY',
    ]

    # Severity weights for category sub-score calculation (from design doc section 7.2)
    SEVERITY_WEIGHTS = {
        'P1': 4,
        'P2': 3,
        'P3': 2,
        'P4': 1,
    }

    # Venezuela-tuned category weights for daily composite (from 25-CONTEXT.md)
    # These reflect Venezuela's unique risk profile:
    # - Oil dependence → higher ENERGY weight (18% vs 10% generic)
    # - Sanctions uncertainty → higher REGULATORY weight (15% vs 12% generic)
    # - Normalized violence → lower CONFLICT weight (11% vs 12% generic)
    # - Infrastructure/healthcare/environmental less critical for commodity traders
    #
    # Weights sum to exactly 1.00 for proper normalization
    VENEZUELA_CATEGORY_WEIGHTS = {
        'score_political': 0.14,       # 14% (generic: 15%)
        'score_conflict': 0.11,        # 11% (generic: 12%, adjusted for normalized violence)
        'score_economic': 0.14,        # 14% (generic: 15%)
        'score_trade': 0.10,           # 10% (generic: 12%, reduced to balance)
        'score_regulatory': 0.15,      # 15% (generic: 12%, CRITICAL for sanctions)
        'score_infrastructure': 0.07,  # 7%  (generic: 8%)
        'score_healthcare': 0.04,      # 4%  (generic: 5%)
        'score_social': 0.05,          # 5%  (generic: 6%)
        'score_environmental': 0.02,   # 2%  (generic: 5%, reduced to balance)
        'score_energy': 0.18,          # 18% (generic: 10%, HIGHEST - oil is lifeline)
    }
    # Total: 1.00 exactly

    @classmethod
    def calculate_category_subscores(cls, events: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate sub-scores for each of the 10 categories.

        Aggregates all events for a given period, computes weighted average by severity,
        and applies event count boost.

        Args:
            events: List of event dicts with 'category', 'risk_score', 'severity' keys
                    Can be Event objects or dicts from BigQuery

        Returns:
            Dict with keys 'score_political', 'score_conflict', etc. (0-100 each)

        Formula (from design doc section 7.2):
            weighted_avg = sum(risk_score * severity_weight) / sum(severity_weight)
            event_count_factor = min(event_count / 10, 1.0)
            boosted_score = weighted_avg * (1 + 0.2 * event_count_factor)
            final_score = min(boosted_score, 100)
        """
        subscores = {}

        for category in cls.CATEGORIES:
            # Filter events for this category
            category_events = [
                e for e in events
                if (e.get('category') if isinstance(e, dict) else e.category) == category
            ]

            if not category_events:
                subscores[f'score_{category.lower()}'] = 0.0
                continue

            # Calculate weighted average by severity
            weighted_sum = 0.0
            weight_total = 0.0

            for event in category_events:
                # Get risk_score and severity (handle both dict and object)
                if isinstance(event, dict):
                    risk_score = event.get('risk_score', 0) or 0
                    severity = event.get('severity', 'P4') or 'P4'
                else:
                    risk_score = event.risk_score or 0
                    severity = event.severity or 'P4'

                severity_weight = cls.SEVERITY_WEIGHTS.get(severity, 1)
                weighted_sum += risk_score * severity_weight
                weight_total += severity_weight

            # Weighted average
            avg_score = weighted_sum / weight_total if weight_total > 0 else 0

            # Event count boost (up to 20% for 10+ events)
            event_count = len(category_events)
            event_count_factor = min(event_count / 10.0, 1.0)
            boosted_score = avg_score * (1 + 0.2 * event_count_factor)

            # Cap at 100
            subscores[f'score_{category.lower()}'] = min(round(boosted_score, 1), 100.0)

        return subscores

    @classmethod
    def calculate_daily_composite(
        cls,
        subscores: Dict[str, float],
        events: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate daily composite risk score from category sub-scores.

        Uses Venezuela-tuned category weights that reflect oil dependence and
        sanctions risk.

        Args:
            subscores: Dict with 'score_political', 'score_conflict', etc.
            events: List of all events (used for P1 boost calculation)

        Returns:
            Composite risk score 0-100

        Formula (from design doc section 7.3 + Venezuela tuning):
            composite = weighted_sum(subscores * category_weights)
            if any P1 events: composite = max(composite, 70)
            if p1_count > 0: composite *= (1 + 0.05 * min(p1_count, 5))
        """
        # Weighted sum using Venezuela-tuned weights
        weighted_sum = sum(
            subscores.get(cat, 0) * weight
            for cat, weight in cls.VENEZUELA_CATEGORY_WEIGHTS.items()
        )

        # Count P1 events
        p1_count = sum(
            1 for e in events
            if (e.get('severity') if isinstance(e, dict) else e.severity) == 'P1'
        )

        # Apply P1 boost
        if p1_count > 0:
            # Minimum score of 70 if any P1 events
            weighted_sum = max(weighted_sum, 70.0)

            # Boost by up to 25% (5% per P1, capped at 5 P1 events)
            boost_factor = 1 + 0.05 * min(p1_count, 5)
            weighted_sum *= boost_factor

        # Cap at 100 and round
        return min(round(weighted_sum, 1), 100.0)
