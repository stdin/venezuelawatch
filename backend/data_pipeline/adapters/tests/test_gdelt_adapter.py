"""
Integration tests for GdeltAdapter.

Tests the full fetch -> transform -> validate cycle with real GDELT BigQuery data.
Requires GCP credentials to run.
"""
import os
import unittest
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone

from data_pipeline.adapters.gdelt_adapter import GdeltAdapter
from data_pipeline.adapters.base import DataSourceAdapter
from api.bigquery_models import Event as BigQueryEvent


@unittest.skipIf(
    not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
    "GCP credentials required for GDELT BigQuery integration tests"
)
class GdeltAdapterIntegrationTest(TestCase):
    """Integration tests for GdeltAdapter with real BigQuery."""

    def setUp(self):
        """Set up test adapter instance."""
        self.adapter = GdeltAdapter()

    def test_adapter_inheritance(self):
        """Test that GdeltAdapter inherits from DataSourceAdapter."""
        self.assertIsInstance(self.adapter, DataSourceAdapter)
        self.assertTrue(issubclass(GdeltAdapter, DataSourceAdapter))

    def test_adapter_class_attributes(self):
        """Test that adapter class attributes are set correctly."""
        self.assertEqual(GdeltAdapter.source_name, "GDELT")
        self.assertEqual(GdeltAdapter.schedule_frequency, "*/15 * * * *")
        self.assertEqual(GdeltAdapter.default_lookback_minutes, 15)

    def test_gdelt_adapter_full_pipeline(self):
        """
        Test full fetch -> transform -> validate cycle with real GDELT data.

        This is the key integration test that proves the adapter works end-to-end.
        Uses a 24-hour lookback window to ensure we get at least some Venezuela events.
        """
        # Fetch events from last 24 hours (small time window for fast test)
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=24)

        # Step 1: Fetch raw events
        raw_events = self.adapter.fetch(start_time, end_time, limit=10)

        self.assertIsInstance(raw_events, list)
        self.assertGreater(
            len(raw_events), 0,
            "Should fetch at least 1 Venezuela event in 24h window. "
            "If this fails, GDELT might have no recent Venezuela events."
        )

        # Verify raw event structure
        first_raw = raw_events[0]
        self.assertIn('GLOBALEVENTID', first_raw)
        self.assertIn('SOURCEURL', first_raw)
        self.assertIn('DATEADDED', first_raw)

        # Step 2: Transform to BigQuery schema
        bq_events = self.adapter.transform(raw_events)

        self.assertIsInstance(bq_events, list)
        self.assertEqual(len(bq_events), len(raw_events))

        # Verify all transformed events are BigQueryEvent instances
        for event in bq_events:
            self.assertIsInstance(event, BigQueryEvent)

        # Step 3: Validate first event
        first_event = bq_events[0]
        valid, error = self.adapter.validate(first_event)

        # Validation might fail due to duplicate (event exists from production sync)
        # That's acceptable for this test - we're testing the logic, not uniqueness
        if not valid:
            self.assertIn(
                "duplicate", error.lower(),
                f"Expected duplicate error, got: {error}"
            )

        # Step 4: Verify schema completeness
        self.assertIsNotNone(first_event.id)
        self.assertIsNotNone(first_event.source_url)
        self.assertIsNotNone(first_event.mentioned_at)
        self.assertIsNotNone(first_event.title)
        self.assertEqual(first_event.source_name, "GDELT")

        # Verify metadata contains GDELT-specific fields
        self.assertIn('goldstein_scale', first_event.metadata)
        self.assertIn('avg_tone', first_event.metadata)
        self.assertIn('quad_class', first_event.metadata)
        self.assertIn('actor1_name', first_event.metadata)
        self.assertIn('event_code', first_event.metadata)

        # If GKG enrichment worked, verify structured data
        if 'gkg' in first_event.metadata and first_event.metadata['gkg']:
            gkg = first_event.metadata['gkg']
            self.assertIn('themes', gkg)
            self.assertIn('tone', gkg)
            self.assertIsInstance(gkg['themes'], list)
            self.assertIsInstance(gkg['tone'], dict)

            # Log GKG data for visibility
            print(f"\n✓ GKG enrichment successful:")
            print(f"  - Themes: {len(gkg['themes'])}")
            print(f"  - Persons: {len(gkg.get('persons', []))}")
            print(f"  - Organizations: {len(gkg.get('organizations', []))}")

    def test_adapter_discovery(self):
        """Test that GdeltAdapter is discovered by the registry."""
        from data_pipeline.adapters.registry import adapter_registry

        # Check adapter is in registry
        adapters = adapter_registry.list_adapters()
        self.assertIn("GDELT", adapters)

        # Check we can get the adapter class
        gdelt_adapter_class = adapter_registry.get_adapter("GDELT")
        self.assertEqual(gdelt_adapter_class, GdeltAdapter)

        # Check metadata is correct
        metadata = adapter_registry.get_metadata("GDELT")
        self.assertEqual(metadata['schedule_frequency'], "*/15 * * * *")
        self.assertEqual(metadata['default_lookback_minutes'], 15)

    def test_validate_required_fields(self):
        """Test validation of required fields."""
        # Create event with missing required fields
        invalid_event = BigQueryEvent(
            id="",  # Missing
            source_url="",  # Missing
            mentioned_at=None,  # Missing
            created_at=timezone.now(),
            title="",  # Missing
            content="Test",
            source_name="GDELT"
        )

        valid, error = self.adapter.validate(invalid_event)
        self.assertFalse(valid)
        self.assertIsNotNone(error)
        self.assertIn("Missing required field", error)

    def test_fetch_with_limit(self):
        """Test that fetch respects the limit parameter."""
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=24)

        # Fetch with small limit
        raw_events = self.adapter.fetch(start_time, end_time, limit=5)

        self.assertIsInstance(raw_events, list)
        self.assertLessEqual(len(raw_events), 5)

    def test_transform_handles_missing_gkg(self):
        """Test that transform handles events without GKG enrichment."""
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=24)

        raw_events = self.adapter.fetch(start_time, end_time, limit=10)

        if raw_events:
            # Remove GKG data from first event to simulate missing enrichment
            first_event = raw_events[0].copy()
            if 'gkg_parsed' in first_event:
                del first_event['gkg_parsed']

            # Transform should still work
            bq_events = self.adapter.transform([first_event])

            self.assertEqual(len(bq_events), 1)
            self.assertIsInstance(bq_events[0], BigQueryEvent)

            # GKG field should be None
            self.assertIsNone(bq_events[0].metadata.get('gkg'))


@unittest.skipIf(
    not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
    "GCP credentials required"
)
class GdeltAdapterUnitTest(TestCase):
    """Unit tests for GdeltAdapter that don't require BigQuery."""

    def test_adapter_attributes(self):
        """Test adapter class attributes."""
        self.assertEqual(GdeltAdapter.source_name, "GDELT")
        self.assertEqual(GdeltAdapter.schedule_frequency, "*/15 * * * *")
        self.assertEqual(GdeltAdapter.default_lookback_minutes, 15)

    def test_adapter_methods_exist(self):
        """Test that all required methods are implemented."""
        adapter = GdeltAdapter()

        self.assertTrue(hasattr(adapter, 'fetch'))
        self.assertTrue(hasattr(adapter, 'transform'))
        self.assertTrue(hasattr(adapter, 'validate'))
        self.assertTrue(hasattr(adapter, 'publish_events'))

        self.assertTrue(callable(adapter.fetch))
        self.assertTrue(callable(adapter.transform))
        self.assertTrue(callable(adapter.validate))
        self.assertTrue(callable(adapter.publish_events))
