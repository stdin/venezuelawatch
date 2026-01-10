"""
GDELT quantitative risk scoring using tone, Goldstein scale, themes, and theme intensity.

Computes 0-100 risk score from GDELT signals with configurable weights.
"""
from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.preprocessing import MinMaxScaler


class GdeltQuantitativeScorer:
    """
    Compute quantitative risk score (0-100) from GDELT event signals.

    Uses 4 weighted signals:
    1. Goldstein scale: Event cooperation/conflict score (-10 to +10)
    2. Tone: GDELT sentiment analysis (-100 to +100)
    3. GKG themes: Presence of CRISIS, PROTEST, CONFLICT themes
    4. Theme intensity: Count/frequency of high-risk themes

    Attributes:
        weights (dict): Configurable signal weights (must sum to 1.0)
        high_risk_themes (set): GKG themes indicating elevated risk
    """

    # Default weights (can be overridden)
    DEFAULT_WEIGHTS = {
        'goldstein': 0.35,   # Primary conflict indicator
        'tone': 0.25,        # Sentiment signal
        'themes': 0.25,      # Categorical risk themes
        'intensity': 0.15    # Theme frequency
    }

    # High-risk GKG themes
    HIGH_RISK_THEMES = {
        'CRISIS', 'PROTEST', 'CONFLICT', 'VIOLENCE', 'WAR',
        'TERRORISM', 'RIOT', 'UNREST', 'SANCTIONS', 'EMBARGO'
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize scorer with configurable weights.

        Args:
            weights: Optional dict with keys: goldstein, tone, themes, intensity
                    Must sum to 1.0. Defaults to DEFAULT_WEIGHTS.

        Raises:
            ValueError: If weights don't sum to 1.0
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

        # Validate weights
        weight_sum = sum(self.weights.values())
        if not (0.99 <= weight_sum <= 1.01):  # Allow floating point tolerance
            raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")

        # Initialize scalers (fit on codebook ranges, not data)
        self.goldstein_scaler = MinMaxScaler(feature_range=(0, 100))
        self.goldstein_scaler.fit([[-10], [10]])

        self.tone_scaler = MinMaxScaler(feature_range=(0, 100))
        self.tone_scaler.fit([[-100], [100]])

    def score_event(self, event_metadata: dict) -> float:
        """
        Compute quantitative risk score from GDELT event metadata.

        Args:
            event_metadata: Event metadata dict with GDELT fields
                Expected fields: goldstein_scale, avg_tone, gkg (optional)

        Returns:
            Risk score (0-100), where 100 = highest risk
        """
        scores = []

        # 1. Goldstein scale (invert: negative values = higher risk)
        goldstein = event_metadata.get('goldstein_scale', 0) or 0
        goldstein_inverted = -goldstein  # -10 becomes +10 (high risk)
        goldstein_score = self.goldstein_scaler.transform([[goldstein_inverted]])[0][0]
        scores.append((goldstein_score, self.weights['goldstein']))

        # 2. Tone (invert: negative sentiment = higher risk)
        tone = event_metadata.get('avg_tone', 0) or 0
        tone_inverted = -tone  # -100 becomes +100 (high risk)
        tone_score = self.tone_scaler.transform([[tone_inverted]])[0][0]
        scores.append((tone_score, self.weights['tone']))

        # 3. GKG themes (categorical presence)
        themes_score = self._score_themes(event_metadata.get('gkg') or {})
        scores.append((themes_score, self.weights['themes']))

        # 4. Theme intensity (count/frequency)
        intensity_score = self._score_theme_intensity(event_metadata.get('gkg') or {})
        scores.append((intensity_score, self.weights['intensity']))

        # Weighted average
        values = [score for score, weight in scores]
        weights = [weight for score, weight in scores]
        final_score = float(np.average(values, weights=weights))

        # Clamp to 0-100 range
        return max(0.0, min(100.0, final_score))

    def _score_themes(self, gkg_data: dict) -> float:
        """
        Score based on presence of high-risk GKG themes.

        Args:
            gkg_data: Parsed GKG data with 'themes' key

        Returns:
            Score (0-100) based on theme presence
        """
        themes = gkg_data.get('themes', [])
        if not themes:
            return 50.0  # Neutral score when GKG data missing

        # Extract theme names (themes are dicts with 'name' key)
        theme_names = set()
        for theme in themes:
            if isinstance(theme, dict) and 'name' in theme:
                theme_names.add(theme['name'].upper())
            elif isinstance(theme, str):
                theme_names.add(theme.upper())

        # Count high-risk themes
        risk_themes_found = theme_names & self.HIGH_RISK_THEMES

        if not risk_themes_found:
            return 20.0  # Low risk if no concerning themes

        # Scale: 1 theme = 60, 2 themes = 80, 3+ themes = 100
        risk_count = len(risk_themes_found)
        if risk_count >= 3:
            return 100.0
        elif risk_count == 2:
            return 80.0
        else:
            return 60.0

    def _score_theme_intensity(self, gkg_data: dict) -> float:
        """
        Score based on frequency/intensity of high-risk themes.

        Args:
            gkg_data: Parsed GKG data with 'themes' key

        Returns:
            Score (0-100) based on theme intensity
        """
        themes = gkg_data.get('themes', [])
        if not themes:
            return 50.0  # Neutral score when GKG data missing

        # Count total high-risk theme mentions
        risk_mentions = 0
        for theme in themes:
            theme_name = ''
            if isinstance(theme, dict):
                theme_name = theme.get('name', '').upper()
            elif isinstance(theme, str):
                theme_name = theme.upper()

            if theme_name in self.HIGH_RISK_THEMES:
                risk_mentions += 1

        # Scale intensity: 0 mentions = 20, 1-2 = 50, 3-5 = 75, 6+ = 100
        if risk_mentions == 0:
            return 20.0
        elif risk_mentions <= 2:
            return 50.0
        elif risk_mentions <= 5:
            return 75.0
        else:
            return 100.0
