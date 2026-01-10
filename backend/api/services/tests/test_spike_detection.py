"""
Tests for spike detection service using z-score statistical analysis.
"""
import datetime
import pytest
from api.services.spike_detection_service import SpikeDetectionService


class TestSpikeDetection:
    """Test suite for SpikeDetectionService.detect_spikes."""

    def test_normal_spike_detection(self):
        """Test spike detection with normal values - should detect CRITICAL spike."""
        mention_stats = [
            {
                'event_id': '1283174855',
                'mention_date': datetime.date(2026, 1, 10),
                'mention_count': 50,
                'rolling_avg': 10.0,
                'rolling_stddev': 8.0
            }
        ]

        spikes = SpikeDetectionService.detect_spikes(mention_stats)

        assert len(spikes) == 1
        spike = spikes[0]
        assert spike['event_id'] == '1283174855'
        assert spike['spike_date'] == datetime.date(2026, 1, 10)
        assert spike['mention_count'] == 50
        assert spike['baseline_avg'] == 10.0
        assert spike['baseline_stddev'] == 8.0
        assert spike['z_score'] == 5.0  # (50 - 10) / 8
        assert spike['confidence_level'] == 'CRITICAL'

    def test_critical_boundary(self):
        """Test z=3.0 boundary - should be CRITICAL (inclusive)."""
        mention_stats = [
            {
                'event_id': '123',
                'mention_date': datetime.date(2026, 1, 10),
                'mention_count': 25,
                'rolling_avg': 10.0,
                'rolling_stddev': 5.0
            }
        ]

        spikes = SpikeDetectionService.detect_spikes(mention_stats)

        assert len(spikes) == 1
        spike = spikes[0]
        assert spike['z_score'] == 3.0
        assert spike['confidence_level'] == 'CRITICAL'

    def test_high_confidence_boundary(self):
        """Test z=2.5 boundary - should be HIGH (inclusive)."""
        mention_stats = [
            {
                'event_id': '456',
                'mention_date': datetime.date(2026, 1, 10),
                'mention_count': 22.5,
                'rolling_avg': 10.0,
                'rolling_stddev': 5.0
            }
        ]

        spikes = SpikeDetectionService.detect_spikes(mention_stats)

        assert len(spikes) == 1
        spike = spikes[0]
        assert spike['z_score'] == 2.5
        assert spike['confidence_level'] == 'HIGH'

    def test_medium_confidence_boundary(self):
        """Test z=2.0 boundary - should be MEDIUM (inclusive)."""
        mention_stats = [
            {
                'event_id': '789',
                'mention_date': datetime.date(2026, 1, 10),
                'mention_count': 20,
                'rolling_avg': 10.0,
                'rolling_stddev': 5.0
            }
        ]

        spikes = SpikeDetectionService.detect_spikes(mention_stats)

        assert len(spikes) == 1
        spike = spikes[0]
        assert spike['z_score'] == 2.0
        assert spike['confidence_level'] == 'MEDIUM'

    def test_below_threshold_filtered_out(self):
        """Test z < 2.0 - should be filtered out (no spike)."""
        mention_stats = [
            {
                'event_id': '101',
                'mention_date': datetime.date(2026, 1, 10),
                'mention_count': 15,
                'rolling_avg': 10.0,
                'rolling_stddev': 5.0
            }
        ]

        spikes = SpikeDetectionService.detect_spikes(mention_stats)

        assert len(spikes) == 0  # z=1.0, below 2.0 threshold

    def test_zero_stddev_edge_case(self):
        """Test zero stddev - should return z=0 and be filtered out."""
        mention_stats = [
            {
                'event_id': '202',
                'mention_date': datetime.date(2026, 1, 10),
                'mention_count': 10,
                'rolling_avg': 10.0,
                'rolling_stddev': 0.0
            }
        ]

        spikes = SpikeDetectionService.detect_spikes(mention_stats)

        assert len(spikes) == 0  # z=0, below 2.0 threshold

    def test_missing_baseline_skipped(self):
        """Test None baseline values - should skip record."""
        mention_stats = [
            {
                'event_id': '303',
                'mention_date': datetime.date(2026, 1, 10),
                'mention_count': 50,
                'rolling_avg': None,
                'rolling_stddev': 8.0
            },
            {
                'event_id': '404',
                'mention_date': datetime.date(2026, 1, 10),
                'mention_count': 50,
                'rolling_avg': 10.0,
                'rolling_stddev': None
            }
        ]

        spikes = SpikeDetectionService.detect_spikes(mention_stats)

        assert len(spikes) == 0  # Both records skipped

    def test_negative_z_score_filtered_out(self):
        """Test negative z-score (decline, not spike) - should be filtered out."""
        mention_stats = [
            {
                'event_id': '505',
                'mention_date': datetime.date(2026, 1, 10),
                'mention_count': 5,
                'rolling_avg': 10.0,
                'rolling_stddev': 3.0
            }
        ]

        spikes = SpikeDetectionService.detect_spikes(mention_stats)

        assert len(spikes) == 0  # z=-1.67, negative means decline

    def test_multiple_spikes_with_mixed_confidence(self):
        """Test multiple events with different confidence levels."""
        mention_stats = [
            {
                'event_id': '601',
                'mention_date': datetime.date(2026, 1, 10),
                'mention_count': 50,
                'rolling_avg': 10.0,
                'rolling_stddev': 8.0  # z=5.0, CRITICAL
            },
            {
                'event_id': '602',
                'mention_date': datetime.date(2026, 1, 10),
                'mention_count': 22.5,
                'rolling_avg': 10.0,
                'rolling_stddev': 5.0  # z=2.5, HIGH
            },
            {
                'event_id': '603',
                'mention_date': datetime.date(2026, 1, 10),
                'mention_count': 15,
                'rolling_avg': 10.0,
                'rolling_stddev': 5.0  # z=1.0, filtered out
            }
        ]

        spikes = SpikeDetectionService.detect_spikes(mention_stats)

        assert len(spikes) == 2  # Only first two pass threshold
        assert spikes[0]['confidence_level'] == 'CRITICAL'
        assert spikes[1]['confidence_level'] == 'HIGH'
