"""
Integration tests for hybrid GDELT + LLM intelligence scoring.

Tests the complete hybrid scoring pipeline:
- GDELT quantitative scoring
- LLM qualitative analysis with GDELT context
- Weighted average hybrid score calculation
- Severity derivation (SEV1-5)
- Fallback to LLM-only when GDELT unavailable
"""
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings

from data_pipeline.services.llm_intelligence import LLMIntelligence


class HybridIntelligenceTests(TestCase):
    """Test hybrid GDELT + LLM intelligence scoring."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample GDELT metadata for high-risk event
        self.high_risk_metadata = {
            'goldstein_scale': -8.5,  # Conflict
            'avg_tone': -6.2,  # Very negative
            'themes': ['CRISIS', 'PROTEST', 'GENERAL_GOVERNMENT'],
            'num_mentions': 5,
            'num_sources': 3,
            'num_articles': 10
        }

        # Sample GDELT metadata for low-risk event
        self.low_risk_metadata = {
            'goldstein_scale': 3.0,  # Cooperation
            'avg_tone': 2.5,  # Positive
            'themes': ['ECON_TRADE', 'DIPLOMACY'],
            'num_mentions': 2,
            'num_sources': 1,
            'num_articles': 3
        }

        # Mock LLM response for high-risk event
        self.mock_llm_high_risk = {
            'content': {
                'sentiment': {
                    'score': -0.7,
                    'label': 'negative',
                    'confidence': 0.9,
                    'reasoning': 'Event describes violent protest',
                    'nuances': ['anger', 'urgency']
                },
                'summary': {
                    'short': 'Protests turn violent in Caracas',
                    'key_points': [
                        'Protests against government',
                        'Police clash with demonstrators',
                        'Multiple injuries reported'
                    ]
                },
                'entities': {
                    'people': [],
                    'organizations': [],
                    'locations': [
                        {'name': 'Caracas', 'type': 'city', 'relevance': 1.0}
                    ]
                },
                'relationships': [],
                'risk': {
                    'score': 0.85,  # LLM scores 85/100
                    'level': 'critical',
                    'reasoning': 'Violence and civil unrest pose high risk',
                    'factors': ['violence', 'government response', 'escalation'],
                    'mitigation': ['monitor situation', 'avoid area']
                },
                'themes': ['political_instability', 'civil_unrest'],
                'urgency': 'high',
                'language': 'en'
            },
            'model': 'claude-3-5-sonnet-20241022',
            'usage': {'total_tokens': 500}
        }

        # Mock LLM response for low-risk event
        self.mock_llm_low_risk = {
            'content': {
                'sentiment': {
                    'score': 0.3,
                    'label': 'positive',
                    'confidence': 0.8,
                    'reasoning': 'Trade agreement signals cooperation',
                    'nuances': ['optimism']
                },
                'summary': {
                    'short': 'Venezuela signs trade agreement',
                    'key_points': [
                        'New trade deal with neighboring country',
                        'Economic cooperation expected',
                        'Details to be announced'
                    ]
                },
                'entities': {
                    'people': [],
                    'organizations': [],
                    'locations': [
                        {'name': 'Venezuela', 'type': 'country', 'relevance': 1.0}
                    ]
                },
                'relationships': [],
                'risk': {
                    'score': 0.15,  # LLM scores 15/100
                    'level': 'low',
                    'reasoning': 'Positive economic development',
                    'factors': [],
                    'mitigation': []
                },
                'themes': ['economic_cooperation'],
                'urgency': 'low',
                'language': 'en'
            },
            'model': 'claude-3-5-sonnet-20241022',
            'usage': {'total_tokens': 400}
        }

    @patch('data_pipeline.services.llm_intelligence.LLMClient._call_llm_structured')
    def test_hybrid_scoring_high_risk_event(self, mock_llm):
        """Test hybrid scoring for high-risk event."""
        mock_llm.return_value = self.mock_llm_high_risk

        result = LLMIntelligence.analyze_event_comprehensive(
            title="Protests turn violent in Caracas",
            content="Violent clashes between protesters and police in Caracas...",
            context={
                'source': 'GDELT',
                'metadata': self.high_risk_metadata
            },
            model='standard'
        )

        # Verify GDELT score was computed
        self.assertIsNotNone(result['risk']['gdelt_score'])
        gdelt_score = result['risk']['gdelt_score']

        # GDELT should score high due to negative indicators
        self.assertGreater(gdelt_score, 50, "GDELT should score high-risk event above 50")

        # Verify LLM score extracted
        self.assertEqual(result['risk']['llm_score'], 85.0)

        # Verify hybrid score is weighted average
        expected_hybrid = 0.3 * gdelt_score + 0.7 * 85.0  # Default weights
        self.assertAlmostEqual(
            result['risk']['hybrid_score'],
            expected_hybrid,
            places=1
        )

        # Verify severity derived correctly (should be SEV4 or SEV5)
        self.assertIn(result['risk']['severity'], ['SEV4', 'SEV5'])

        # Verify scoring method tracked
        self.assertEqual(result['metadata']['scoring_method'], 'hybrid')

    @patch('data_pipeline.services.llm_intelligence.LLMClient._call_llm_structured')
    def test_hybrid_scoring_low_risk_event(self, mock_llm):
        """Test hybrid scoring for low-risk event."""
        mock_llm.return_value = self.mock_llm_low_risk

        result = LLMIntelligence.analyze_event_comprehensive(
            title="Venezuela signs trade agreement",
            content="Venezuela announces new trade agreement with neighboring country...",
            context={
                'source': 'GDELT',
                'metadata': self.low_risk_metadata
            },
            model='standard'
        )

        # Verify GDELT score was computed
        self.assertIsNotNone(result['risk']['gdelt_score'])
        gdelt_score = result['risk']['gdelt_score']

        # GDELT should score low due to positive indicators
        self.assertLess(gdelt_score, 50, "GDELT should score low-risk event below 50")

        # Verify LLM score extracted
        self.assertEqual(result['risk']['llm_score'], 15.0)

        # Verify hybrid score is weighted average
        expected_hybrid = 0.3 * gdelt_score + 0.7 * 15.0  # Default weights
        self.assertAlmostEqual(
            result['risk']['hybrid_score'],
            expected_hybrid,
            places=1
        )

        # Verify severity derived correctly (should be SEV1 or SEV2)
        self.assertIn(result['risk']['severity'], ['SEV1', 'SEV2'])

        # Verify scoring method tracked
        self.assertEqual(result['metadata']['scoring_method'], 'hybrid')

    @patch('data_pipeline.services.llm_intelligence.LLMClient._call_llm_structured')
    def test_gdelt_score_included_in_llm_prompt(self, mock_llm):
        """Test that GDELT score is included in LLM prompt for context."""
        mock_llm.return_value = self.mock_llm_high_risk

        LLMIntelligence.analyze_event_comprehensive(
            title="Test event",
            content="Test content",
            context={'source': 'GDELT', 'metadata': self.high_risk_metadata},
            model='standard'
        )

        # Verify LLM was called
        self.assertTrue(mock_llm.called)

        # Extract user prompt from call
        call_args = mock_llm.call_args
        messages = call_args[1]['messages']
        user_prompt = messages[1]['content']

        # Verify GDELT score is in prompt
        self.assertIn('GDELT Risk Score:', user_prompt)
        self.assertIn('GDELT Quantitative Signals', user_prompt)
        self.assertIn('Goldstein scale', user_prompt)

    @patch('data_pipeline.services.llm_intelligence.LLMClient._call_llm_structured')
    def test_fallback_to_llm_only_when_gdelt_unavailable(self, mock_llm):
        """Test fallback to LLM-only scoring when GDELT metadata missing."""
        mock_llm.return_value = self.mock_llm_high_risk

        result = LLMIntelligence.analyze_event_comprehensive(
            title="Test event",
            content="Test content",
            context={'source': 'RSS'},  # No metadata
            model='standard'
        )

        # Verify GDELT score is None
        self.assertIsNone(result['risk']['gdelt_score'])

        # Verify hybrid score equals LLM score (fallback)
        self.assertEqual(result['risk']['hybrid_score'], 85.0)
        self.assertEqual(result['risk']['llm_score'], 85.0)

        # Verify scoring method is llm_only
        self.assertEqual(result['metadata']['scoring_method'], 'llm_only')

    @patch('data_pipeline.services.llm_intelligence.LLMClient._call_llm_structured')
    def test_severity_derivation_all_levels(self, mock_llm):
        """Test severity derivation for all SEV1-5 levels."""
        test_cases = [
            (5.0, 'SEV1'),    # 0-19: Minimal
            (25.0, 'SEV2'),   # 20-39: Low
            (45.0, 'SEV3'),   # 40-59: Medium
            (65.0, 'SEV4'),   # 60-79: High
            (85.0, 'SEV5'),   # 80-100: Critical
        ]

        for llm_score, expected_severity in test_cases:
            # Create mock response with specific score
            mock_response = {
                'content': {
                    **self.mock_llm_low_risk['content'],
                    'risk': {
                        **self.mock_llm_low_risk['content']['risk'],
                        'score': llm_score / 100
                    }
                },
                'model': 'claude-3-5-sonnet-20241022',
                'usage': {'total_tokens': 400}
            }
            mock_llm.return_value = mock_response

            result = LLMIntelligence.analyze_event_comprehensive(
                title="Test event",
                content="Test content",
                context={'source': 'RSS'},  # No GDELT metadata (LLM-only)
                model='standard'
            )

            self.assertEqual(
                result['risk']['severity'],
                expected_severity,
                f"LLM score {llm_score} should map to {expected_severity}"
            )

    @override_settings(HYBRID_SCORING={
        'weights': {'gdelt': 0.5, 'llm': 0.5},  # Equal weights
        'gdelt_weights': {
            'goldstein': 0.35,
            'tone': 0.25,
            'themes': 0.25,
            'intensity': 0.15,
        },
        'severity_thresholds': {
            'SEV5': 80, 'SEV4': 60, 'SEV3': 40, 'SEV2': 20, 'SEV1': 0,
        }
    })
    @patch('data_pipeline.services.llm_intelligence.LLMClient._call_llm_structured')
    def test_configurable_weights_affect_hybrid_score(self, mock_llm):
        """Test that weight configuration changes affect hybrid score."""
        mock_llm.return_value = self.mock_llm_high_risk

        # Clear cached scorer to pick up new weights
        LLMIntelligence._gdelt_scorer = None

        result = LLMIntelligence.analyze_event_comprehensive(
            title="Test event",
            content="Test content",
            context={'source': 'GDELT', 'metadata': self.high_risk_metadata},
            model='standard'
        )

        # With 50/50 weights
        gdelt_score = result['risk']['gdelt_score']
        expected_hybrid = 0.5 * gdelt_score + 0.5 * 85.0

        self.assertAlmostEqual(
            result['risk']['hybrid_score'],
            expected_hybrid,
            places=1,
            msg="50/50 weights should produce equal contribution from GDELT and LLM"
        )

    @patch('data_pipeline.services.llm_intelligence.LLMClient._call_llm_structured')
    @patch('data_pipeline.services.llm_intelligence.GdeltQuantitativeScorer.score_event')
    def test_gdelt_scoring_failure_fallback(self, mock_scorer, mock_llm):
        """Test graceful fallback when GDELT scoring fails."""
        # Make GDELT scorer raise exception
        mock_scorer.side_effect = Exception("GDELT scoring failed")
        mock_llm.return_value = self.mock_llm_high_risk

        result = LLMIntelligence.analyze_event_comprehensive(
            title="Test event",
            content="Test content",
            context={'source': 'GDELT', 'metadata': self.high_risk_metadata},
            model='standard'
        )

        # Should fallback to LLM-only
        self.assertIsNone(result['risk']['gdelt_score'])
        self.assertEqual(result['risk']['hybrid_score'], 85.0)
        self.assertEqual(result['metadata']['scoring_method'], 'llm_only')

    @patch('data_pipeline.services.llm_intelligence.LLMClient._call_llm_structured')
    def test_hybrid_fields_present_in_response(self, mock_llm):
        """Test that all hybrid scoring fields are present in response."""
        mock_llm.return_value = self.mock_llm_high_risk

        result = LLMIntelligence.analyze_event_comprehensive(
            title="Test event",
            content="Test content",
            context={'source': 'GDELT', 'metadata': self.high_risk_metadata},
            model='standard'
        )

        # Verify all hybrid fields present
        self.assertIn('hybrid_score', result['risk'])
        self.assertIn('gdelt_score', result['risk'])
        self.assertIn('llm_score', result['risk'])
        self.assertIn('severity', result['risk'])
        self.assertIn('scoring_method', result['metadata'])

        # Verify data types
        self.assertIsInstance(result['risk']['hybrid_score'], float)
        self.assertIsInstance(result['risk']['severity'], str)

    @patch('data_pipeline.services.llm_intelligence.LLMClient._call_llm_structured')
    def test_backward_compatibility_risk_score_field(self, mock_llm):
        """Test that risk.score field still exists for backward compatibility."""
        mock_llm.return_value = self.mock_llm_high_risk

        result = LLMIntelligence.analyze_event_comprehensive(
            title="Test event",
            content="Test content",
            context={'source': 'GDELT', 'metadata': self.high_risk_metadata},
            model='standard'
        )

        # Original risk.score field should still exist
        self.assertIn('score', result['risk'])

        # Should be 0-1 normalized version of hybrid_score
        expected_score = result['risk']['hybrid_score'] / 100
        self.assertAlmostEqual(
            result['risk']['score'],
            expected_score,
            places=2
        )
