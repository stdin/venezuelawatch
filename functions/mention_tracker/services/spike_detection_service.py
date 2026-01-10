"""
Spike detection service using z-score statistical analysis.

Detects mention spikes by calculating z-scores from rolling baseline statistics
and classifying confidence levels based on statistical significance thresholds.
"""
from typing import List


class SpikeDetectionService:
    """Detects mention spikes using z-score statistical analysis."""

    @staticmethod
    def detect_spikes(mention_stats: List[dict]) -> List[dict]:
        """
        Calculate z-scores and classify spikes from mention statistics.

        Args:
            mention_stats: List of dicts with event_id, mention_date, mention_count,
                          rolling_avg, rolling_stddev from GDELTMentionsService

        Returns:
            List of spike dicts with z_score and confidence_level for spikes >= 2.0

        Example:
            >>> stats = [{
            ...     'event_id': '123',
            ...     'mention_date': date(2026, 1, 10),
            ...     'mention_count': 50,
            ...     'rolling_avg': 10.0,
            ...     'rolling_stddev': 8.0
            ... }]
            >>> spikes = SpikeDetectionService.detect_spikes(stats)
            >>> spikes[0]['z_score']
            5.0
            >>> spikes[0]['confidence_level']
            'CRITICAL'
        """
        spikes = []

        for stat in mention_stats:
            # Skip if insufficient baseline data
            if stat['rolling_avg'] is None or stat['rolling_stddev'] is None:
                continue

            # Handle zero stddev edge case (flat baseline)
            if stat['rolling_stddev'] == 0:
                z_score = 0.0
            else:
                z_score = (
                    stat['mention_count'] - stat['rolling_avg']
                ) / stat['rolling_stddev']

            # Only detect positive spikes (z >= 2.0)
            if z_score < 2.0:
                continue

            # Classify confidence level
            if z_score >= 3.0:
                confidence = 'CRITICAL'
            elif z_score >= 2.5:
                confidence = 'HIGH'
            else:  # z >= 2.0
                confidence = 'MEDIUM'

            spikes.append({
                'event_id': stat['event_id'],
                'spike_date': stat['mention_date'],
                'mention_count': stat['mention_count'],
                'baseline_avg': stat['rolling_avg'],
                'baseline_stddev': stat['rolling_stddev'],
                'z_score': z_score,
                'confidence_level': confidence
            })

        return spikes


# Singleton instance for consistent service pattern
spike_detection_service = SpikeDetectionService()
