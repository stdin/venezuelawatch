#!/usr/bin/env python
"""
Verification script for hybrid GDELT + LLM intelligence scoring.

Tests the hybrid scoring system end-to-end with real GDELT events.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venezuelawatch.settings')
django.setup()

from data_pipeline.services.llm_intelligence import LLMIntelligence
from data_pipeline.services.gdelt_quantitative_scorer import GdeltQuantitativeScorer


def verify_hybrid_scoring():
    """Verify hybrid scoring with sample GDELT event."""
    print("=" * 80)
    print("HYBRID INTELLIGENCE SCORING VERIFICATION")
    print("=" * 80)
    print()

    # Sample high-risk GDELT event
    high_risk_event = {
        'title': 'Violent protests erupt in Caracas amid political crisis',
        'content': """
        Violent clashes between protesters and security forces erupted in Caracas today
        as political tensions in Venezuela reached a boiling point. Demonstrators demanding
        political change were met with tear gas and rubber bullets. Multiple injuries reported.
        Opposition leaders call for international intervention as the humanitarian crisis deepens.
        """,
        'context': {
            'source': 'GDELT',
            'event_type': 'PROTEST',
            'timestamp': '2026-01-10T12:00:00Z',
            'metadata': {
                'goldstein_scale': -8.5,  # Strong conflict indicator
                'avg_tone': -6.2,  # Very negative
                'themes': ['CRISIS', 'PROTEST', 'EPU_POLICY_UNCERTAINTY', 'GENERAL_GOVERNMENT'],
                'num_mentions': 12,
                'num_sources': 8,
                'num_articles': 25
            }
        }
    }

    #Sample low-risk GDELT event
    low_risk_event = {
        'title': 'Venezuela signs trade agreement with regional partner',
        'content': """
        Venezuela announced a new trade agreement with a regional partner today, signaling
        potential economic cooperation. The agreement focuses on agricultural products and
        technical exchange. Officials express optimism about improving economic relations
        and fostering mutual development. Details to be announced at upcoming summit.
        """,
        'context': {
            'source': 'GDELT',
            'event_type': 'DIPLOMATIC',
            'timestamp': '2026-01-10T14:00:00Z',
            'metadata': {
                'goldstein_scale': 4.0,  # Cooperation indicator
                'avg_tone': 2.8,  # Positive
                'themes': ['ECON_TRADE', 'DIPLOMACY'],
                'num_mentions': 3,
                'num_sources': 2,
                'num_articles': 5
            }
        }
    }

    print("\n" + "=" * 80)
    print("TEST 1: HIGH-RISK EVENT (Violent Protests)")
    print("=" * 80)
    test_event(high_risk_event, expected_severity=['SEV4', 'SEV5'])

    print("\n" + "=" * 80)
    print("TEST 2: LOW-RISK EVENT (Trade Agreement)")
    print("=" * 80)
    test_event(low_risk_event, expected_severity=['SEV1', 'SEV2'])

    print("\n" + "=" * 80)
    print("TEST 3: FALLBACK TO LLM-ONLY (No GDELT Metadata)")
    print("=" * 80)
    test_event({
        'title': 'Economic update from Venezuela',
        'content': 'Venezuela releases quarterly economic data showing mixed results...',
        'context': {'source': 'RSS'}  # No GDELT metadata
    }, expected_severity=None)

    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)


def test_event(event, expected_severity=None):
    """
    Test hybrid scoring on an event.

    Args:
        event: Event dict with title, content, context
        expected_severity: Expected severity range (list of strings)
    """
    print(f"\nEvent: {event['title']}")
    print(f"Source: {event['context'].get('source', 'Unknown')}")

    # Check if GDELT metadata present
    has_gdelt = 'metadata' in event['context']
    print(f"GDELT Metadata: {'Yes' if has_gdelt else 'No'}")

    if has_gdelt:
        # Show GDELT indicators
        metadata = event['context']['metadata']
        print(f"\nGDELT Indicators:")
        print(f"  Goldstein Scale: {metadata.get('goldstein_scale', 'N/A')}")
        print(f"  Avg Tone: {metadata.get('avg_tone', 'N/A')}")
        print(f"  Themes: {', '.join(metadata.get('themes', []))}")

        # Compute GDELT score
        scorer = GdeltQuantitativeScorer()
        gdelt_score = scorer.score_event(metadata)
        print(f"  → GDELT Quantitative Score: {gdelt_score:.2f}/100")

    print("\nRunning hybrid intelligence analysis...")
    try:
        result = LLMIntelligence.analyze_event_comprehensive(
            title=event['title'],
            content=event['content'],
            context=event['context'],
            model='fast'  # Use fast model for verification
        )

        print("\n✓ Analysis Complete!")
        print(f"\nRisk Scoring:")
        print(f"  GDELT Score: {result['risk'].get('gdelt_score', 'N/A')}")
        print(f"  LLM Score: {result['risk'].get('llm_score', 'N/A')}")
        print(f"  Hybrid Score: {result['risk'].get('hybrid_score', 'N/A')}/100")
        print(f"  Severity: {result['risk'].get('severity', 'N/A')}")
        print(f"  Scoring Method: {result['metadata'].get('scoring_method', 'N/A')}")

        print(f"\nSentiment:")
        print(f"  Score: {result['sentiment']['score']:.2f}")
        print(f"  Label: {result['sentiment']['label']}")

        print(f"\nSummary:")
        print(f"  {result['summary']['short']}")

        print(f"\nKey Points:")
        for i, point in enumerate(result['summary']['key_points'], 1):
            print(f"  {i}. {point}")

        print(f"\nRisk Analysis:")
        print(f"  Level: {result['risk']['level']}")
        print(f"  Reasoning: {result['risk']['reasoning']}")

        if result['risk'].get('factors'):
            print(f"  Factors:")
            for factor in result['risk']['factors']:
                print(f"    - {factor}")

        print(f"\nMetadata:")
        print(f"  Model: {result['metadata']['model_used']}")
        print(f"  Tokens: {result['metadata']['tokens_used']}")
        print(f"  Processing Time: {result['metadata']['processing_time_ms']}ms")

        # Verify expected severity
        if expected_severity:
            actual_severity = result['risk'].get('severity')
            if actual_severity in expected_severity:
                print(f"\n✓ PASS: Severity {actual_severity} is in expected range {expected_severity}")
            else:
                print(f"\n✗ WARN: Severity {actual_severity} not in expected range {expected_severity}")

        # Verify hybrid scoring worked
        if has_gdelt:
            if result['metadata'].get('scoring_method') == 'hybrid':
                print("✓ PASS: Hybrid scoring method confirmed")
            else:
                print(f"✗ FAIL: Expected hybrid scoring but got {result['metadata'].get('scoring_method')}")
        else:
            if result['metadata'].get('scoring_method') == 'llm_only':
                print("✓ PASS: LLM-only fallback confirmed")
            else:
                print(f"✗ WARN: Expected llm_only but got {result['metadata'].get('scoring_method')}")

    except Exception as e:
        print(f"\n✗ Analysis Failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    verify_hybrid_scoring()
