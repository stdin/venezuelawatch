"""
Composite Risk Scoring System

Implements 5-component explainable risk scoring from platform design (section 7.1):
- Magnitude (30%): Normalized event magnitude (0-1)
- Tone (20%): Normalized tone/sentiment (0-1, higher = more negative)
- Velocity (20%): Z-score vs rolling category average
- Attention (15%): Number of sources reporting (more sources = higher attention)
- Persistence (15%): Consecutive days with elevated signals

Final score is base_score * confidence_modifier with severity floors:
- P1 events: minimum score 70
- P2 events: minimum score 50
"""

import math
from typing import Dict, Any
from api.bigquery_models import Event


class CompositeRiskScorer:
    """
    Calculate composite risk scores with 5-component weighting and confidence modifiers.
    """

    # Component weights (from design doc section 7.1)
    MAGNITUDE_WEIGHT = 0.30
    TONE_WEIGHT = 0.20
    VELOCITY_WEIGHT = 0.20
    ATTENTION_WEIGHT = 0.15
    PERSISTENCE_WEIGHT = 0.15

    # Severity floors (from design doc section 7.1)
    P1_MINIMUM_SCORE = 70
    P2_MINIMUM_SCORE = 50

    @classmethod
    def calculate_risk_score(cls, event: Event, rolling_stats: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate composite risk score for an event.

        Args:
            event: Canonical Event instance with magnitude, tone, confidence fields
            rolling_stats: Rolling window statistics dict with keys:
                - {category}_avg: Rolling average magnitude for category (default 0.5)
                - {category}_std: Rolling standard deviation for category (default 0.2)
                Empty dict {} is acceptable for Phase 25 (uses defaults)

        Returns:
            Dict with:
            - risk_score: Final 0-100 risk score
            - magnitude_contrib: Magnitude component contribution (0-30)
            - tone_contrib: Tone component contribution (0-20)
            - velocity_contrib: Velocity component contribution (0-20)
            - attention_contrib: Attention component contribution (0-15)
            - persistence_contrib: Persistence component contribution (0-15)
            - confidence_mod: Confidence modifier (0.5-1.0)
            - base_score: Pre-confidence base score (0-100)

        Formula (from design doc section 7.1):
            base_score = (0.30*magnitude + 0.20*tone + 0.20*velocity + 0.15*attention + 0.15*persistence) * 100
            confidence_mod = 0.5 + 0.5 * (0.4*source_diversity + 0.3*source_credibility + 0.3*corroboration)
            risk_score = base_score * confidence_mod
            if severity == P1: risk_score = max(risk_score, 70)
            if severity == P2: risk_score = max(risk_score, 50)
        """

        # ============ COMPONENT SCORES (0-1 each) ============

        # Magnitude (30% weight) - already normalized 0-1 by adapters
        magnitude_norm = event.magnitude_norm if event.magnitude_norm is not None else 0.0

        # Tone (20% weight) - already normalized 0-1 by adapters
        tone_norm = event.tone_norm if event.tone_norm is not None else 0.0

        # Velocity (20% weight) - compare to rolling category average
        category = event.category or 'POLITICAL'
        category_avg = rolling_stats.get(f"{category}_avg", 0.5)
        category_std = rolling_stats.get(f"{category}_std", 0.2)

        if category_std > 0:
            z_score = (magnitude_norm - category_avg) / category_std
            velocity_norm = cls._sigmoid(z_score, k=1.0)
        else:
            velocity_norm = 0.5  # Neutral if no std dev

        # Attention (15% weight) - based on number of sources
        num_sources = event.num_sources if event.num_sources is not None else 1
        attention_norm = min(num_sources / 10.0, 1.0)

        # Persistence (15% weight) - consecutive days with elevated signals
        # Populated from metadata.persistence_days (spike tracking from Phase 21)
        persistence_days = event.metadata.get('persistence_days', 1) if event.metadata else 1
        persistence_norm = min(persistence_days / 7.0, 1.0)  # 7+ days = max persistence

        # ============ BASE SCORE ============
        base_score = (
            cls.MAGNITUDE_WEIGHT * magnitude_norm +
            cls.TONE_WEIGHT * tone_norm +
            cls.VELOCITY_WEIGHT * velocity_norm +
            cls.ATTENTION_WEIGHT * attention_norm +
            cls.PERSISTENCE_WEIGHT * persistence_norm
        ) * 100

        # ============ CONFIDENCE MODIFIER ============
        # Range: 0.5 to 1.0 (from design doc section 7.1)

        # Source diversity (0-1)
        source_diversity = min(num_sources / 5.0, 1.0)

        # Source credibility (0-1, from event)
        source_credibility = event.source_credibility if event.source_credibility is not None else 0.7

        # Corroboration (0-1, from cross-source matching)
        # Phase 25: defaults to 0.5, Phase 26+ will compute from multi-source analysis
        corroboration = event.metadata.get('corroboration_score', 0.5) if event.metadata else 0.5

        confidence_mod = 0.5 + 0.5 * (
            0.4 * source_diversity +
            0.3 * source_credibility +
            0.3 * corroboration
        )

        # ============ FINAL SCORE ============
        risk_score = base_score * confidence_mod

        # Apply severity floor
        severity = event.severity
        if severity == 'P1':
            risk_score = max(risk_score, cls.P1_MINIMUM_SCORE)
        elif severity == 'P2':
            risk_score = max(risk_score, cls.P2_MINIMUM_SCORE)

        # Return detailed breakdown for explainability
        return {
            'risk_score': round(risk_score, 1),
            'magnitude_contrib': round(magnitude_norm * cls.MAGNITUDE_WEIGHT * 100, 1),
            'tone_contrib': round(tone_norm * cls.TONE_WEIGHT * 100, 1),
            'velocity_contrib': round(velocity_norm * cls.VELOCITY_WEIGHT * 100, 1),
            'attention_contrib': round(attention_norm * cls.ATTENTION_WEIGHT * 100, 1),
            'persistence_contrib': round(persistence_norm * cls.PERSISTENCE_WEIGHT * 100, 1),
            'confidence_mod': round(confidence_mod, 3),
            'base_score': round(base_score, 1),
        }

    @staticmethod
    def _sigmoid(x: float, k: float = 1.0) -> float:
        """
        Sigmoid normalization function. Maps any value to 0-1.

        Args:
            x: Input value (typically z-score)
            k: Steepness parameter (default 1.0)

        Returns:
            Value in range 0-1
        """
        return 1.0 / (1.0 + math.exp(-k * x))
