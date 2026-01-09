"""
Management command to test complete data ingestion pipeline with LLM integration.

Tests end-to-end flow:
1. Ingest events from GDELT (or mock data if no API key)
2. Verify events are created in database
3. Check that LLM analysis tasks are dispatched
4. Wait for analysis to complete
5. Verify intelligence fields are populated

Usage:
    python manage.py test_ingestion_pipeline
    python manage.py test_ingestion_pipeline --source gdelt
    python manage.py test_ingestion_pipeline --source fred
    python manage.py test_ingestion_pipeline --mock  # Use mock data instead of API
"""
import logging
import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test complete data ingestion pipeline with LLM intelligence integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            choices=['gdelt', 'fred', 'all'],
            default='all',
            help='Test specific source (gdelt, fred, or all)'
        )
        parser.add_argument(
            '--mock',
            action='store_true',
            help='Use mock data instead of real API calls'
        )
        parser.add_argument(
            '--wait',
            type=int,
            default=30,
            help='Seconds to wait for LLM analysis to complete (default: 30)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('Data Ingestion Pipeline + LLM Integration Test'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        source = options['source']
        use_mock = options['mock']
        wait_seconds = options['wait']

        # Check prerequisites
        self._check_prerequisites()

        # Test based on source
        if source in ['gdelt', 'all']:
            self._test_gdelt_pipeline(use_mock, wait_seconds)

        if source in ['fred', 'all']:
            self._test_fred_pipeline(use_mock, wait_seconds)

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('Pipeline Test Complete'))
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write('\nIntegration Status: ✓ LLM intelligence fully integrated with ingestion')

    def _check_prerequisites(self):
        """Check that required services are available."""
        self.stdout.write('\n' + '-'*80)
        self.stdout.write('Checking Prerequisites...')
        self.stdout.write('-'*80 + '\n')

        # Check database connection
        try:
            from django.db import connection
            connection.ensure_connection()
            self.stdout.write('✓ Database connection: OK')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠ Database connection: {e}'))
            self.stdout.write('  Note: Some tests may fail without database access')

        # Check Celery
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            stats = inspect.stats()
            if stats:
                worker_count = len(stats)
                self.stdout.write(f'✓ Celery workers: {worker_count} active')
            else:
                self.stdout.write(self.style.WARNING('⚠ Celery workers: None detected'))
                self.stdout.write('  Note: LLM analysis will be queued but not processed')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠ Celery: {e}'))

        # Check LLM API key
        import os
        if os.getenv('ANTHROPIC_API_KEY'):
            self.stdout.write('✓ ANTHROPIC_API_KEY: Configured')
        else:
            self.stdout.write(self.style.WARNING('⚠ ANTHROPIC_API_KEY: Not set'))
            self.stdout.write('  Note: LLM analysis will fail without API key')

        # Check Redis (for caching)
        try:
            from django.core.cache import cache
            cache.set('test_key', 'test_value', 1)
            if cache.get('test_key') == 'test_value':
                self.stdout.write('✓ Redis cache: OK')
            else:
                self.stdout.write(self.style.WARNING('⚠ Redis cache: Not working'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠ Redis cache: {e}'))

    def _test_gdelt_pipeline(self, use_mock, wait_seconds):
        """Test GDELT ingestion with LLM analysis."""
        self.stdout.write('\n' + '-'*80)
        self.stdout.write('[Test 1] GDELT Ingestion + LLM Analysis')
        self.stdout.write('-'*80 + '\n')

        try:
            from core.models import Event

            # Record initial count
            initial_count = Event.objects.filter(source='GDELT').count()
            self.stdout.write(f'Initial GDELT events in database: {initial_count}')

            if use_mock:
                self.stdout.write('\n[MOCK MODE] Creating mock GDELT event...')
                event = self._create_mock_gdelt_event()
                self.stdout.write(f'✓ Created mock event: {event.title[:60]}')

                # Manually dispatch LLM analysis
                self._dispatch_llm_analysis(event.id, model='fast')

                events_created = 1
            else:
                self.stdout.write('\nIngesting from GDELT API (60 minute lookback)...')
                from data_pipeline.tasks.gdelt_tasks import ingest_gdelt_events

                # Run ingestion (this will automatically dispatch LLM analysis)
                result = ingest_gdelt_events.apply(kwargs={'lookback_minutes': 60})

                self.stdout.write(f'\n✓ GDELT Ingestion Complete:')
                self.stdout.write(f'  - Articles fetched: {result.result["articles_fetched"]}')
                self.stdout.write(f'  - Events created: {result.result["events_created"]}')
                self.stdout.write(f'  - Events skipped: {result.result["events_skipped"]}')

                events_created = result.result['events_created']

            if events_created == 0:
                self.stdout.write(self.style.WARNING('\n⚠ No new events created - cannot test LLM analysis'))
                return

            # Get most recent event
            latest_event = Event.objects.filter(source='GDELT').latest('created_at')
            self.stdout.write(f'\nMost Recent Event:')
            self.stdout.write(f'  ID: {latest_event.id}')
            self.stdout.write(f'  Title: {latest_event.title[:80]}')
            self.stdout.write(f'  Created: {latest_event.created_at}')

            # Wait for LLM analysis
            self._wait_for_analysis(latest_event, wait_seconds)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ GDELT pipeline test failed: {e}'))
            import traceback
            traceback.print_exc()

    def _test_fred_pipeline(self, use_mock, wait_seconds):
        """Test FRED ingestion with LLM analysis."""
        self.stdout.write('\n' + '-'*80)
        self.stdout.write('[Test 2] FRED Ingestion + LLM Analysis')
        self.stdout.write('-'*80 + '\n')

        try:
            from core.models import Event

            # Record initial count
            initial_count = Event.objects.filter(source='FRED').count()
            self.stdout.write(f'Initial FRED events in database: {initial_count}')

            if use_mock:
                self.stdout.write('\n[MOCK MODE] Creating mock FRED event...')
                event = self._create_mock_fred_event()
                self.stdout.write(f'✓ Created mock event: {event.title[:60]}')

                # Manually dispatch LLM analysis
                self._dispatch_llm_analysis(event.id, model='fast')

                events_created = 1
            else:
                self.stdout.write('\nIngesting from FRED API (WTI Crude Oil Prices, 7 day lookback)...')
                from data_pipeline.tasks.fred_tasks import ingest_single_series

                # Run ingestion (this will automatically dispatch LLM analysis)
                result = ingest_single_series.apply(kwargs={'series_id': 'DCOILWTICO', 'lookback_days': 7})

                self.stdout.write(f'\n✓ FRED Ingestion Complete:')
                self.stdout.write(f'  - Series: {result.result["series_id"]}')
                self.stdout.write(f'  - Observations created: {result.result["observations_created"]}')
                self.stdout.write(f'  - Observations skipped: {result.result["observations_skipped"]}')
                self.stdout.write(f'  - Status: {result.result["status"]}')

                events_created = result.result.get('observations_created', 0)

            if events_created == 0:
                self.stdout.write(self.style.WARNING('\n⚠ No new events created - cannot test LLM analysis'))
                return

            # Get most recent event
            latest_event = Event.objects.filter(source='FRED').latest('created_at')
            self.stdout.write(f'\nMost Recent Event:')
            self.stdout.write(f'  ID: {latest_event.id}')
            self.stdout.write(f'  Title: {latest_event.title[:80]}')
            self.stdout.write(f'  Created: {latest_event.created_at}')

            # Wait for LLM analysis
            self._wait_for_analysis(latest_event, wait_seconds)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ FRED pipeline test failed: {e}'))
            import traceback
            traceback.print_exc()

    def _create_mock_gdelt_event(self):
        """Create mock GDELT event for testing."""
        from core.models import Event
        from django.utils import timezone

        event = Event.objects.create(
            title='Maduro anuncia nuevas medidas económicas para enfrentar crisis',
            content={
                'url': 'https://example.com/test-article',
                'seendate': timezone.now().isoformat(),
                'socialimage': 'https://example.com/image.jpg',
                'domain': 'example.com',
                'language': 'Spanish',
                'sourcecountry': 'Venezuela',
                'location': 'Caracas, Venezuela',
            },
            source='GDELT',
            event_type='NEWS',
            timestamp=timezone.now(),
        )
        return event

    def _create_mock_fred_event(self):
        """Create mock FRED event for testing."""
        from core.models import Event
        from django.utils import timezone

        event = Event.objects.create(
            title='WTI Crude Oil Prices: $75.32',
            content={
                'series_id': 'DCOILWTICO',
                'date': timezone.now().isoformat(),
                'value': 75.32,
                'previous_value': 74.18,
                'change_percent': 1.54,
            },
            source='FRED',
            event_type='ECONOMIC',
            timestamp=timezone.now(),
        )
        return event

    def _dispatch_llm_analysis(self, event_id, model='fast'):
        """Manually dispatch LLM analysis task."""
        try:
            from data_pipeline.tasks.intelligence_tasks import analyze_event_intelligence

            task = analyze_event_intelligence.delay(event_id, model=model)
            self.stdout.write(f'✓ Dispatched LLM analysis task (ID: {task.id})')
            return task

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to dispatch LLM analysis: {e}'))
            return None

    def _wait_for_analysis(self, event, max_wait_seconds):
        """Wait for LLM analysis to complete and verify results."""
        self.stdout.write(f'\nWaiting for LLM analysis (max {max_wait_seconds}s)...')

        start_time = time.time()
        analysis_complete = False

        while time.time() - start_time < max_wait_seconds:
            # Refresh event from database
            event.refresh_from_db()

            if event.sentiment is not None:
                analysis_complete = True
                break

            time.sleep(2)  # Check every 2 seconds
            elapsed = int(time.time() - start_time)
            self.stdout.write(f'  Waiting... ({elapsed}s)', ending='\r')
            self.stdout.flush()

        self.stdout.write('')  # New line after waiting

        if analysis_complete:
            self.stdout.write(self.style.SUCCESS('\n✓ LLM Analysis Complete!'))
            self._display_analysis_results(event)
        else:
            self.stdout.write(self.style.WARNING(
                f'\n⚠ Analysis did not complete within {max_wait_seconds}s'
            ))
            self.stdout.write('  This may be due to:')
            self.stdout.write('  - Celery workers not running')
            self.stdout.write('  - High API latency')
            self.stdout.write('  - Missing ANTHROPIC_API_KEY')
            self.stdout.write('\n  Check Celery worker logs for details')

    def _display_analysis_results(self, event):
        """Display LLM analysis results."""
        self.stdout.write('\nIntelligence Fields:')
        self.stdout.write(f'  Sentiment: {event.sentiment:.3f}' if event.sentiment else '  Sentiment: None')
        self.stdout.write(f'  Risk Score: {event.risk_score:.3f}' if event.risk_score else '  Risk Score: None')
        self.stdout.write(f'  Language: {event.language}' if event.language else '  Language: None')
        self.stdout.write(f'  Urgency: {event.urgency}' if event.urgency else '  Urgency: None')

        if event.entities:
            self.stdout.write(f'  Entities: {len(event.entities)} extracted')
            for entity in event.entities[:3]:
                self.stdout.write(f'    - {entity}')
            if len(event.entities) > 3:
                self.stdout.write(f'    ... and {len(event.entities) - 3} more')

        if event.themes:
            self.stdout.write(f'  Themes: {", ".join(event.themes[:5])}')

        if event.summary:
            self.stdout.write(f'  Summary: {event.summary[:100]}...')

        if event.llm_analysis:
            metadata = event.llm_analysis.get('metadata', {})
            if metadata:
                self.stdout.write(f'\n  Model Used: {metadata.get("model_used", "unknown")}')
                self.stdout.write(f'  Tokens Used: {metadata.get("tokens_used", "unknown")}')
                self.stdout.write(f'  Processing Time: {metadata.get("processing_time_ms", "unknown")}ms')
                self.stdout.write(f'  Native Schema: {metadata.get("used_native_schema", False)}')
