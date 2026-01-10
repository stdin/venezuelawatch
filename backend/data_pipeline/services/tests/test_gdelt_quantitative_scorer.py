"""
Unit tests for GdeltQuantitativeScorer.

Tests all 4 scoring signals (Goldstein, tone, themes, intensity) with edge cases
and realistic GDELT metadata examples.
"""
import unittest
from data_pipeline.services.gdelt_quantitative_scorer import GdeltQuantitativeScorer


class TestGdeltQuantitativeScorer(unittest.TestCase):
    """Test suite for GDELT quantitative risk scoring."""

    def setUp(self):
        """Initialize scorer with default weights."""
        self.scorer = GdeltQuantitativeScorer()

    # ===== Weight Validation Tests =====

    def test_default_weights_sum_to_one(self):
        """Default weights should sum to 1.0."""
        weight_sum = sum(GdeltQuantitativeScorer.DEFAULT_WEIGHTS.values())
        self.assertAlmostEqual(weight_sum, 1.0, places=2)

    def test_custom_weights_valid(self):
        """Custom weights that sum to 1.0 should be accepted."""
        custom_weights = {
            'goldstein': 0.4,
            'tone': 0.3,
            'themes': 0.2,
            'intensity': 0.1
        }
        scorer = GdeltQuantitativeScorer(weights=custom_weights)
        self.assertEqual(scorer.weights, custom_weights)

    def test_invalid_weights_raise_error(self):
        """Weights that don't sum to 1.0 should raise ValueError."""
        invalid_weights = {
            'goldstein': 0.5,
            'tone': 0.3,
            'themes': 0.1,
            'intensity': 0.05  # Sum = 0.95
        }
        with self.assertRaises(ValueError) as context:
            GdeltQuantitativeScorer(weights=invalid_weights)
        self.assertIn("must sum to 1.0", str(context.exception))

    # ===== Goldstein Scale Scoring Tests =====

    def test_goldstein_negative_high_risk(self):
        """Negative Goldstein (conflict) should score high."""
        metadata = {'goldstein_scale': -10, 'avg_tone': 0}
        score = self.scorer.score_event(metadata)
        # Goldstein -10 inverted to +10 → 100 * 0.35 weight = 35 points
        # Tone 0 inverted to 0 → 50 * 0.25 = 12.5
        # Themes/intensity missing → 50 * 0.40 = 20
        # Total ≈ 67.5
        self.assertGreater(score, 60)

    def test_goldstein_positive_low_risk(self):
        """Positive Goldstein (cooperation) should score low."""
        metadata = {'goldstein_scale': 10, 'avg_tone': 0}
        score = self.scorer.score_event(metadata)
        # Goldstein +10 inverted to -10 → 0 * 0.35 = 0
        # Tone 0 inverted to 0 → 50 * 0.25 = 12.5
        # Themes/intensity missing → 50 * 0.40 = 20
        # Total ≈ 32.5
        self.assertLess(score, 40)

    def test_goldstein_zero_neutral(self):
        """Goldstein = 0 should score near middle."""
        metadata = {'goldstein_scale': 0, 'avg_tone': 0}
        score = self.scorer.score_event(metadata)
        # All signals neutral → should be around 50
        self.assertGreater(score, 45)
        self.assertLess(score, 55)

    def test_goldstein_missing_defaults_zero(self):
        """Missing Goldstein should default to 0 (neutral)."""
        metadata = {'avg_tone': 0}
        score = self.scorer.score_event(metadata)
        # Same as goldstein=0 case
        self.assertGreater(score, 45)
        self.assertLess(score, 55)

    # ===== Tone Scoring Tests =====

    def test_tone_negative_high_risk(self):
        """Negative tone (bad sentiment) should score high."""
        metadata = {'goldstein_scale': 0, 'avg_tone': -100}
        score = self.scorer.score_event(metadata)
        # Tone -100 inverted to +100 → 100 * 0.25 = 25 points
        # Goldstein 0 → 50 * 0.35 = 17.5
        # Themes/intensity → 50 * 0.40 = 20
        # Total ≈ 62.5
        self.assertGreater(score, 60)

    def test_tone_positive_low_risk(self):
        """Positive tone (good sentiment) should score low."""
        metadata = {'goldstein_scale': 0, 'avg_tone': 100}
        score = self.scorer.score_event(metadata)
        # Tone +100 inverted to -100 → 0 * 0.25 = 0
        # Goldstein 0 → 50 * 0.35 = 17.5
        # Themes/intensity → 50 * 0.40 = 20
        # Total ≈ 37.5
        self.assertLess(score, 40)

    def test_tone_zero_neutral(self):
        """Tone = 0 should contribute neutral score."""
        metadata = {'goldstein_scale': 0, 'avg_tone': 0}
        score = self.scorer.score_event(metadata)
        # All neutral → around 50
        self.assertGreater(score, 45)
        self.assertLess(score, 55)

    def test_tone_missing_defaults_zero(self):
        """Missing tone should default to 0 (neutral)."""
        metadata = {'goldstein_scale': 0}
        score = self.scorer.score_event(metadata)
        # Same as tone=0 case
        self.assertGreater(score, 45)
        self.assertLess(score, 55)

    # ===== GKG Theme Presence Tests =====

    def test_themes_crisis_high_risk(self):
        """CRISIS theme should score high (60 for 1 theme)."""
        metadata = {
            'goldstein_scale': 0,
            'avg_tone': 0,
            'gkg': {
                'themes': [{'name': 'CRISIS'}]
            }
        }
        score = self.scorer.score_event(metadata)
        # Themes = 60 * 0.25 = 15 (vs 50 * 0.25 = 12.5 for neutral)
        # So score should be higher than neutral (50)
        self.assertGreater(score, 50)

    def test_themes_multiple_risk_themes_high_score(self):
        """Multiple risk themes should score very high (80 for 2, 100 for 3+)."""
        metadata = {
            'goldstein_scale': 0,
            'avg_tone': 0,
            'gkg': {
                'themes': [
                    {'name': 'CRISIS'},
                    {'name': 'PROTEST'},
                    {'name': 'VIOLENCE'}
                ]
            }
        }
        score = self.scorer.score_event(metadata)
        # 3+ risk themes → 100 * 0.25 = 25 points from themes
        # Should push score significantly higher
        self.assertGreater(score, 55)

    def test_themes_no_risk_themes_low_score(self):
        """Non-risk themes should score low (20)."""
        metadata = {
            'goldstein_scale': 0,
            'avg_tone': 0,
            'gkg': {
                'themes': [
                    {'name': 'ECONOMY'},
                    {'name': 'TRADE'}
                ]
            }
        }
        score = self.scorer.score_event(metadata)
        # Themes = 20 * 0.25 = 5 (vs 50 * 0.25 = 12.5 for neutral)
        # Should be lower than neutral
        self.assertLess(score, 50)

    def test_themes_missing_gkg_neutral(self):
        """Missing GKG data should score neutral (50)."""
        metadata = {
            'goldstein_scale': 0,
            'avg_tone': 0
        }
        score = self.scorer.score_event(metadata)
        # All signals neutral → around 50
        self.assertGreater(score, 45)
        self.assertLess(score, 55)

    def test_themes_empty_list_neutral(self):
        """Empty themes list should score neutral (50)."""
        metadata = {
            'goldstein_scale': 0,
            'avg_tone': 0,
            'gkg': {'themes': []}
        }
        score = self.scorer.score_event(metadata)
        self.assertGreater(score, 45)
        self.assertLess(score, 55)

    def test_themes_string_format(self):
        """Themes as strings (not dicts) should work."""
        metadata = {
            'goldstein_scale': 0,
            'avg_tone': 0,
            'gkg': {
                'themes': ['CRISIS', 'PROTEST']
            }
        }
        score = self.scorer.score_event(metadata)
        # 2 risk themes → 80 * 0.25 = 20 points
        self.assertGreater(score, 50)

    def test_themes_case_insensitive(self):
        """Theme matching should be case-insensitive."""
        metadata = {
            'goldstein_scale': 0,
            'avg_tone': 0,
            'gkg': {
                'themes': [{'name': 'crisis'}]  # lowercase
            }
        }
        score = self.scorer.score_event(metadata)
        # Should match 'CRISIS' → score > neutral
        self.assertGreater(score, 50)

    # ===== Theme Intensity Tests =====

    def test_intensity_no_risk_mentions_low(self):
        """No risk theme mentions should score low (20)."""
        metadata = {
            'goldstein_scale': 0,
            'avg_tone': 0,
            'gkg': {
                'themes': [
                    {'name': 'ECONOMY'},
                    {'name': 'TRADE'}
                ]
            }
        }
        score = self.scorer.score_event(metadata)
        # Intensity = 20 * 0.15 = 3
        # Themes = 20 * 0.25 = 5
        # Total lower than neutral
        self.assertLess(score, 50)

    def test_intensity_few_mentions_moderate(self):
        """1-2 risk mentions should score moderate (50)."""
        metadata = {
            'goldstein_scale': 0,
            'avg_tone': 0,
            'gkg': {
                'themes': [
                    {'name': 'CRISIS'},
                    {'name': 'ECONOMY'}
                ]
            }
        }
        score = self.scorer.score_event(metadata)
        # 1 risk mention → intensity = 50
        # Should be near neutral overall
        self.assertGreater(score, 48)
        self.assertLess(score, 55)

    def test_intensity_many_mentions_high(self):
        """6+ risk mentions should score very high (100)."""
        metadata = {
            'goldstein_scale': 0,
            'avg_tone': 0,
            'gkg': {
                'themes': [
                    {'name': 'CRISIS'},
                    {'name': 'PROTEST'},
                    {'name': 'VIOLENCE'},
                    {'name': 'CONFLICT'},
                    {'name': 'WAR'},
                    {'name': 'TERRORISM'},
                    {'name': 'RIOT'}
                ]
            }
        }
        score = self.scorer.score_event(metadata)
        # 7 risk mentions → intensity = 100 * 0.15 = 15
        # 3+ unique themes → themes = 100 * 0.25 = 25
        # Total should be significantly elevated
        self.assertGreater(score, 60)

    # ===== End-to-End Integration Tests =====

    def test_high_risk_event_comprehensive(self):
        """High-risk event with all negative signals should score >= 70."""
        metadata = {
            'goldstein_scale': -8,    # Strong conflict
            'avg_tone': -6.5,         # Negative sentiment
            'gkg': {
                'themes': [
                    {'name': 'CRISIS'},
                    {'name': 'PROTEST'},
                    {'name': 'VIOLENCE'},
                    {'name': 'CONFLICT'}
                ]
            }
        }
        score = self.scorer.score_event(metadata)
        # Goldstein -8 → ~90 * 0.35 = 31.5
        # Tone -6.5 → ~53 * 0.25 = 13.25
        # Themes 3+ → 100 * 0.25 = 25
        # Intensity 4 → 75 * 0.15 = 11.25
        # Total ≈ 81
        self.assertGreaterEqual(score, 70)
        self.assertLessEqual(score, 100)

    def test_low_risk_event_comprehensive(self):
        """Low-risk event with all positive signals should score <= 40."""
        metadata = {
            'goldstein_scale': 7,     # Strong cooperation
            'avg_tone': 4.2,          # Positive sentiment
            'gkg': {
                'themes': [
                    {'name': 'ECONOMY'},
                    {'name': 'TRADE'},
                    {'name': 'DEVELOPMENT'}
                ]
            }
        }
        score = self.scorer.score_event(metadata)
        # Goldstein 7 → ~15 * 0.35 = 5.25
        # Tone 4.2 → ~48 * 0.25 = 12
        # Themes (no risk) → 20 * 0.25 = 5
        # Intensity 0 → 20 * 0.15 = 3
        # Total ≈ 25.25
        self.assertLessEqual(score, 40)
        self.assertGreaterEqual(score, 0)

    def test_mixed_signals_event(self):
        """Event with mixed signals should score in middle range."""
        metadata = {
            'goldstein_scale': -2,    # Slight conflict
            'avg_tone': 1.5,          # Slightly positive
            'gkg': {
                'themes': [
                    {'name': 'CRISIS'},
                    {'name': 'ECONOMY'}
                ]
            }
        }
        score = self.scorer.score_event(metadata)
        # Mixed signals → should be somewhere 40-60
        self.assertGreater(score, 40)
        self.assertLess(score, 70)

    def test_realistic_gdelt_metadata_protest(self):
        """Test with realistic GDELT protest event metadata."""
        metadata = {
            'goldstein_scale': -4.0,
            'avg_tone': -3.2,
            'num_mentions': 15,
            'num_sources': 8,
            'gkg': {
                'themes': [
                    {'name': 'PROTEST'},
                    {'name': 'UNREST'},
                    {'name': 'GOV_POLICY'}
                ],
                'persons': ['Nicolas Maduro', 'Opposition Leader'],
                'organizations': ['Government', 'Opposition Coalition']
            }
        }
        score = self.scorer.score_event(metadata)
        # Moderate conflict + negative tone + protest themes
        # Should score moderately high (60-80 range)
        self.assertGreater(score, 55)
        self.assertLess(score, 85)

    def test_realistic_gdelt_metadata_cooperation(self):
        """Test with realistic GDELT cooperation event metadata."""
        metadata = {
            'goldstein_scale': 5.2,
            'avg_tone': 2.8,
            'num_mentions': 5,
            'num_sources': 3,
            'gkg': {
                'themes': [
                    {'name': 'DIPLOMACY'},
                    {'name': 'TRADE'},
                    {'name': 'ECONOMY'}
                ],
                'persons': ['Foreign Minister'],
                'organizations': ['United Nations']
            }
        }
        score = self.scorer.score_event(metadata)
        # Cooperation + positive tone + no risk themes
        # Should score low (20-40 range)
        self.assertGreater(score, 15)
        self.assertLess(score, 45)

    # ===== Configurable Weights Tests =====

    def test_custom_weights_affect_score(self):
        """Custom weights should change final score."""
        metadata = {
            'goldstein_scale': -5,
            'avg_tone': -5,
            'gkg': {
                'themes': [{'name': 'CRISIS'}]
            }
        }

        # Default weights
        default_score = self.scorer.score_event(metadata)

        # Heavy Goldstein weighting
        heavy_goldstein = GdeltQuantitativeScorer(weights={
            'goldstein': 0.7,
            'tone': 0.1,
            'themes': 0.1,
            'intensity': 0.1
        })
        goldstein_score = heavy_goldstein.score_event(metadata)

        # Heavy theme weighting
        heavy_themes = GdeltQuantitativeScorer(weights={
            'goldstein': 0.1,
            'tone': 0.1,
            'themes': 0.7,
            'intensity': 0.1
        })
        themes_score = heavy_themes.score_event(metadata)

        # Scores should differ based on weights
        self.assertNotEqual(default_score, goldstein_score)
        self.assertNotEqual(default_score, themes_score)
        self.assertNotEqual(goldstein_score, themes_score)

    def test_equal_weights_balance(self):
        """Equal weights should balance all signals."""
        equal_weights = {
            'goldstein': 0.25,
            'tone': 0.25,
            'themes': 0.25,
            'intensity': 0.25
        }
        scorer = GdeltQuantitativeScorer(weights=equal_weights)

        metadata = {
            'goldstein_scale': -10,  # 100 score
            'avg_tone': 100,         # 0 score
            'gkg': {
                'themes': [{'name': 'CRISIS'}]  # 60 score
            }
            # intensity will be 50 (1 mention)
        }
        score = scorer.score_event(metadata)
        # (100 + 0 + 60 + 50) / 4 = 52.5
        self.assertGreater(score, 50)
        self.assertLess(score, 55)

    # ===== Edge Cases =====

    def test_score_clamped_to_range(self):
        """Score should always be 0-100 even with extreme values."""
        # Try to create scores outside range
        metadata_extreme_high = {
            'goldstein_scale': -10,
            'avg_tone': -100,
            'gkg': {
                'themes': [
                    {'name': 'CRISIS'},
                    {'name': 'WAR'},
                    {'name': 'TERRORISM'},
                    {'name': 'VIOLENCE'},
                    {'name': 'CONFLICT'}
                ]
            }
        }
        score = self.scorer.score_event(metadata_extreme_high)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

        metadata_extreme_low = {
            'goldstein_scale': 10,
            'avg_tone': 100,
            'gkg': {
                'themes': [{'name': 'PEACE'}, {'name': 'COOPERATION'}]
            }
        }
        score = self.scorer.score_event(metadata_extreme_low)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_empty_metadata(self):
        """Empty metadata should score neutral (around 50)."""
        score = self.scorer.score_event({})
        # All defaults to 0 → neutral
        self.assertGreater(score, 45)
        self.assertLess(score, 55)

    def test_none_values_handled(self):
        """None values should be treated as 0/missing."""
        metadata = {
            'goldstein_scale': None,
            'avg_tone': None,
            'gkg': None
        }
        score = self.scorer.score_event(metadata)
        # Should not crash, should score neutral
        self.assertGreater(score, 45)
        self.assertLess(score, 55)


if __name__ == '__main__':
    unittest.main()
