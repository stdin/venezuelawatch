"""
Management command to analyze intelligence for existing events.

Applies sentiment analysis, risk scoring, and entity extraction to events that
are missing intelligence fields.

Usage:
    python manage.py analyze_intelligence
    python manage.py analyze_intelligence --source=GDELT
    python manage.py analyze_intelligence --reanalyze
    python manage.py analyze_intelligence --async --limit=1000
"""
import logging
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta

from core.models import Event
from data_pipeline.services.sentiment_analyzer import SentimentAnalyzer
from data_pipeline.services.risk_scorer import RiskScorer
from data_pipeline.services.entity_extractor import EntityExtractor
from data_pipeline.tasks.intelligence_tasks import batch_analyze_events

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Analyze intelligence (sentiment, risk, entities) for existing events'

    def add_arguments(self, parser):
        # Filtering options
        parser.add_argument(
            '--source',
            type=str,
            help='Filter by event source (e.g., GDELT, RELIEFWEB, FRED)'
        )
        parser.add_argument(
            '--event-type',
            type=str,
            help='Filter by event type (e.g., NEWS, HUMANITARIAN, ECONOMIC)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Only analyze events from last N days (default: 30)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Maximum number of events to process'
        )

        # Analysis options
        parser.add_argument(
            '--reanalyze',
            action='store_true',
            help='Re-analyze events that already have intelligence fields'
        )
        parser.add_argument(
            '--sentiment-only',
            action='store_true',
            help='Only update sentiment scores'
        )
        parser.add_argument(
            '--risk-only',
            action='store_true',
            help='Only update risk scores'
        )
        parser.add_argument(
            '--entities-only',
            action='store_true',
            help='Only update entity extraction'
        )

        # Execution options
        parser.add_argument(
            '--async',
            action='store_true',
            dest='use_async',
            help='Run analysis asynchronously using Celery workers'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be analyzed without actually running'
        )

    def handle(self, *args, **options):
        # Build query
        cutoff_date = timezone.now() - timedelta(days=options['days'])
        queryset = Event.objects.filter(timestamp__gte=cutoff_date)

        if options['source']:
            queryset = queryset.filter(source=options['source'])

        if options['event_type']:
            queryset = queryset.filter(event_type=options['event_type'])

        # Filter for events without intelligence (unless reanalyzing)
        if not options['reanalyze']:
            if options['sentiment_only']:
                queryset = queryset.filter(sentiment__isnull=True)
            elif options['risk_only']:
                queryset = queryset.filter(risk_score__isnull=True)
            elif options['entities_only']:
                queryset = queryset.filter(entities=[])
            else:
                # Default: events missing any intelligence field
                queryset = queryset.filter(sentiment__isnull=True)

        # Apply limit
        if options['limit']:
            queryset = queryset[:options['limit']]

        total_events = queryset.count()

        # Display analysis plan
        self.stdout.write(self.style.SUCCESS(f'\nIntelligence Analysis Plan:'))
        self.stdout.write(f'  Events to analyze: {total_events}')
        if options['source']:
            self.stdout.write(f'  Source filter: {options["source"]}')
        if options['event_type']:
            self.stdout.write(f'  Event type filter: {options["event_type"]}')
        self.stdout.write(f'  Days back: {options["days"]}')
        self.stdout.write(f'  Mode: {"Async (Celery)" if options["use_async"] else "Synchronous"}')
        if options['reanalyze']:
            self.stdout.write(f'  Reanalyze: Yes (including events with existing intelligence)')
        if options['sentiment_only']:
            self.stdout.write(f'  Analysis type: Sentiment only')
        elif options['risk_only']:
            self.stdout.write(f'  Analysis type: Risk scoring only')
        elif options['entities_only']:
            self.stdout.write(f'  Analysis type: Entity extraction only')
        else:
            self.stdout.write(f'  Analysis type: Full (sentiment + risk + entities)')

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No analysis will be performed'))
            return

        if total_events == 0:
            self.stdout.write(self.style.WARNING('\nNo events found matching filters'))
            return

        # Confirm execution for large batches
        if total_events > 100 and not options['use_async']:
            self.stdout.write(self.style.WARNING(
                f'\nThis will analyze {total_events} events synchronously. '
                'This may take a significant amount of time.'
            ))
            confirm = input('Continue? [y/N] ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.ERROR('Analysis cancelled'))
                return

        # Execute analysis
        self.stdout.write(self.style.SUCCESS('\nStarting intelligence analysis...\n'))

        if options['use_async']:
            # Dispatch async batch task
            result = batch_analyze_events.delay(
                source=options['source'],
                event_type=options['event_type'],
                days_back=options['days'],
                limit=options['limit'],
                reanalyze=options['reanalyze'],
            )

            self.stdout.write(
                self.style.SUCCESS(f'✓ Batch analysis task dispatched (ID: {result.id})')
            )
            self.stdout.write('\nMonitor task progress with:')
            self.stdout.write(f'  celery -A config.celery result {result.id}')

        else:
            # Run synchronously
            processed = 0
            updated = 0
            skipped = 0
            errors = 0

            for event in queryset.iterator(chunk_size=50):
                try:
                    needs_update = False

                    # Sentiment analysis
                    if options['sentiment_only'] or not any([
                        options['risk_only'],
                        options['entities_only']
                    ]):
                        if event.sentiment is None or options['reanalyze']:
                            event.sentiment = SentimentAnalyzer.analyze_event(event)
                            needs_update = True

                    # Risk scoring
                    if options['risk_only'] or not any([
                        options['sentiment_only'],
                        options['entities_only']
                    ]):
                        if event.risk_score is None or options['reanalyze']:
                            event.risk_score = RiskScorer.calculate_risk_score(event)
                            needs_update = True

                    # Entity extraction
                    if options['entities_only'] or not any([
                        options['sentiment_only'],
                        options['risk_only']
                    ]):
                        if not event.entities or options['reanalyze']:
                            entities = EntityExtractor.extract_event_entities(event)
                            event.entities = EntityExtractor.filter_relevant_entities(entities)
                            needs_update = True

                    if needs_update:
                        event.save(update_fields=['sentiment', 'risk_score', 'entities'])
                        updated += 1
                    else:
                        skipped += 1

                    processed += 1

                    # Progress update every 50 events
                    if processed % 50 == 0:
                        self.stdout.write(
                            f'  Processed {processed}/{total_events} events '
                            f'({updated} updated, {skipped} skipped, {errors} errors)'
                        )

                except Exception as e:
                    logger.error(f"Failed to analyze Event {event.id}: {e}", exc_info=True)
                    errors += 1

            # Display summary
            self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
            self.stdout.write(self.style.SUCCESS('Analysis Complete'))
            self.stdout.write(self.style.SUCCESS(f'{"="*60}\n'))

            self.stdout.write(f'Events processed: {processed}')
            self.stdout.write(f'  Updated: {updated}')
            self.stdout.write(f'  Skipped: {skipped}')
            self.stdout.write(f'  Errors: {errors}')

            if updated > 0:
                # Show sample of analyzed events
                sample_events = Event.objects.filter(
                    sentiment__isnull=False,
                    risk_score__isnull=False
                ).order_by('-timestamp')[:5]

                self.stdout.write('\nSample analyzed events:')
                for event in sample_events:
                    sentiment_label = SentimentAnalyzer.get_sentiment_label(event.sentiment)
                    risk_level = RiskScorer.get_risk_level(event.risk_score)

                    self.stdout.write(
                        f'  - {event.title[:60]}... '
                        f'[Sentiment: {sentiment_label} ({event.sentiment:.2f}), '
                        f'Risk: {risk_level} ({event.risk_score:.2f}), '
                        f'Entities: {len(event.entities)}]'
                    )

        self.stdout.write('')
