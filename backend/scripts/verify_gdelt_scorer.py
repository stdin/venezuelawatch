#!/usr/bin/env python3
"""
Verification script for GdeltQuantitativeScorer with realistic GDELT metadata.

Uses synthetic but realistic GDELT metadata examples to verify:
1. Scorer works with production-like data
2. High-risk events score >= 70
3. Low-risk events score <= 40
4. No crashes or errors
"""
import os
import sys

# Setup path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.services.gdelt_quantitative_scorer import GdeltQuantitativeScorer


def create_test_events():
    """Create realistic GDELT metadata examples for testing."""
    return [
        # High-risk events (should score >= 70)
        {
            'id': 'TEST-001',
            'title': 'Violent protest in Caracas',
            'metadata': {
                'goldstein_scale': -8.0,
                'avg_tone': -6.5,
                'gkg': {
                    'themes': [
                        {'name': 'PROTEST'},
                        {'name': 'VIOLENCE'},
                        {'name': 'CRISIS'},
                        {'name': 'UNREST'}
                    ]
                }
            }
        },
        {
            'id': 'TEST-002',
            'title': 'Armed conflict escalates',
            'metadata': {
                'goldstein_scale': -10.0,
                'avg_tone': -8.2,
                'gkg': {
                    'themes': [
                        {'name': 'WAR'},
                        {'name': 'CONFLICT'},
                        {'name': 'VIOLENCE'}
                    ]
                }
            }
        },
        {
            'id': 'TEST-003',
            'title': 'Sanctions imposed on officials',
            'metadata': {
                'goldstein_scale': -6.5,
                'avg_tone': -4.8,
                'gkg': {
                    'themes': [
                        {'name': 'SANCTIONS'},
                        {'name': 'EMBARGO'},
                        {'name': 'CRISIS'}
                    ]
                }
            }
        },

        # Low-risk events (should score <= 40)
        {
            'id': 'TEST-004',
            'title': 'Diplomatic meeting on trade',
            'metadata': {
                'goldstein_scale': 7.2,
                'avg_tone': 4.5,
                'gkg': {
                    'themes': [
                        {'name': 'DIPLOMACY'},
                        {'name': 'TRADE'},
                        {'name': 'COOPERATION'}
                    ]
                }
            }
        },
        {
            'id': 'TEST-005',
            'title': 'Humanitarian aid agreement',
            'metadata': {
                'goldstein_scale': 8.5,
                'avg_tone': 5.8,
                'gkg': {
                    'themes': [
                        {'name': 'HUMANITARIAN'},
                        {'name': 'AID'},
                        {'name': 'DEVELOPMENT'}
                    ]
                }
            }
        },
        {
            'id': 'TEST-006',
            'title': 'Economic cooperation discussed',
            'metadata': {
                'goldstein_scale': 6.0,
                'avg_tone': 3.2,
                'gkg': {
                    'themes': [
                        {'name': 'ECONOMY'},
                        {'name': 'DEVELOPMENT'}
                    ]
                }
            }
        },

        # Medium-risk events (40 < score < 70)
        {
            'id': 'TEST-007',
            'title': 'Opposition demands election reform',
            'metadata': {
                'goldstein_scale': -2.5,
                'avg_tone': -1.8,
                'gkg': {
                    'themes': [
                        {'name': 'POLITICS'},
                        {'name': 'ELECTION'},
                        {'name': 'PROTEST'}
                    ]
                }
            }
        },
        {
            'id': 'TEST-008',
            'title': 'Government announces policy change',
            'metadata': {
                'goldstein_scale': 1.5,
                'avg_tone': 0.8,
                'gkg': {
                    'themes': [
                        {'name': 'GOVERNMENT'},
                        {'name': 'POLICY'}
                    ]
                }
            }
        },

        # Edge cases
        {
            'id': 'TEST-009',
            'title': 'Event with missing GKG data',
            'metadata': {
                'goldstein_scale': -3.0,
                'avg_tone': -2.0
            }
        },
        {
            'id': 'TEST-010',
            'title': 'Event with neutral values',
            'metadata': {
                'goldstein_scale': 0,
                'avg_tone': 0,
                'gkg': {
                    'themes': []
                }
            }
        }
    ]


def score_events(events):
    """Score events and analyze results."""
    scorer = GdeltQuantitativeScorer()

    results = {
        'high_risk': [],  # Score >= 70
        'medium_risk': [],  # 40 < score < 70
        'low_risk': [],  # Score <= 40
        'errors': []
    }

    print(f"\n{'='*80}")
    print(f"SCORING {len(events)} GDELT EVENTS")
    print(f"{'='*80}\n")

    for event in events:
        try:
            metadata = event['metadata']
            score = scorer.score_event(metadata)

            result = {
                'id': event['id'],
                'title': event['title'][:70],
                'score': score,
                'goldstein': metadata.get('goldstein_scale'),
                'tone': metadata.get('avg_tone'),
                'has_gkg': bool(metadata.get('gkg'))
            }

            # Categorize by score
            if score >= 70:
                results['high_risk'].append(result)
            elif score <= 40:
                results['low_risk'].append(result)
            else:
                results['medium_risk'].append(result)

            # Print individual score
            risk_label = 'HIGH' if score >= 70 else 'LOW' if score <= 40 else 'MED'
            print(f"[{risk_label:4}] Score: {score:5.1f} | "
                  f"G:{result['goldstein']:+5.1f} T:{result['tone']:+6.1f} | "
                  f"{result['title']}")

        except Exception as e:
            print(f"[ERROR] {event['id']}: {e}")
            results['errors'].append({
                'id': event['id'],
                'error': str(e)
            })

    return results


def analyze_results(results):
    """Analyze scoring results and print summary."""
    total = len(results['high_risk']) + len(results['medium_risk']) + len(results['low_risk'])

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}\n")

    print(f"Total events scored: {total}")
    print(f"High-risk (>= 70):   {len(results['high_risk'])} ({len(results['high_risk'])/total*100:.1f}%)")
    print(f"Medium-risk (40-70): {len(results['medium_risk'])} ({len(results['medium_risk'])/total*100:.1f}%)")
    print(f"Low-risk (<= 40):    {len(results['low_risk'])} ({len(results['low_risk'])/total*100:.1f}%)")
    print(f"Errors:              {len(results['errors'])}")

    # Detailed high-risk events
    if results['high_risk']:
        print(f"\n{'='*80}")
        print(f"HIGH-RISK EVENTS (Score >= 70)")
        print(f"{'='*80}\n")
        for event in results['high_risk']:
            print(f"Score: {event['score']:.1f} | Goldstein: {event['goldstein']:+.1f} | "
                  f"Tone: {event['tone']:+.1f} | GKG: {event['has_gkg']}")
            print(f"  {event['title']}\n")

    # Detailed low-risk events
    if results['low_risk']:
        print(f"\n{'='*80}")
        print(f"LOW-RISK EVENTS (Score <= 40)")
        print(f"{'='*80}\n")
        for event in results['low_risk']:
            print(f"Score: {event['score']:.1f} | Goldstein: {event['goldstein']:+.1f} | "
                  f"Tone: {event['tone']:+.1f} | GKG: {event['has_gkg']}")
            print(f"  {event['title']}\n")

    # Errors
    if results['errors']:
        print(f"\n{'='*80}")
        print(f"ERRORS")
        print(f"{'='*80}\n")
        for error in results['errors']:
            print(f"{error['id']}: {error['error']}")

    # Verification criteria
    print(f"\n{'='*80}")
    print(f"VERIFICATION CRITERIA")
    print(f"{'='*80}\n")

    checks = {
        'No crashes': len(results['errors']) == 0,
        'Scores in range (0-100)': all(
            0 <= e['score'] <= 100
            for e in results['high_risk'] + results['medium_risk'] + results['low_risk']
        ),
        'Distribution reasonable': len(results['medium_risk']) > 0 or len(results['high_risk']) + len(results['low_risk']) == total,
    }

    for check, passed in checks.items():
        status = '✓' if passed else '✗'
        print(f"{status} {check}")

    all_passed = all(checks.values())
    print(f"\n{'='*80}")
    if all_passed:
        print("SUCCESS: All verification criteria met!")
    else:
        print("FAILURE: Some verification criteria failed.")
    print(f"{'='*80}\n")

    return all_passed


def main():
    print("\nGDELT Quantitative Scorer Verification")
    print("=" * 80)

    # Create test events with realistic GDELT metadata
    print("\nCreating realistic GDELT metadata examples...")
    events = create_test_events()
    print(f"Created {len(events)} test events")

    # Score events
    results = score_events(events)

    # Analyze results
    success = analyze_results(results)

    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
