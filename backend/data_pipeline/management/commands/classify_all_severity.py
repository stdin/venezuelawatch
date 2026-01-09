"""
Management command to classify event severity using impact classifier.

Useful for:
- Backfilling severity for events without classification
- Updating severity after model changes
- Fixing incorrect severity classifications
"""
from django.core.management.base import BaseCommand
from core.models import Event
from data_pipeline.services.impact_classifier import ImpactClassifier
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Classify event severity using NCISS-style impact assessment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Lookback period in days (default: 30)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Classify ALL events (ignores --days)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Reclassify events that already have severity (default: skip)'
        )

    def handle(self, *args, **options):
        if options['all']:
            queryset = Event.objects.all()
            self.stdout.write('Classifying severity for ALL events...')
        else:
            cutoff_date = timezone.now() - timedelta(days=options['days'])
            queryset = Event.objects.filter(created_at__gte=cutoff_date)
            self.stdout.write(f'Classifying severity for events in last {options["days"]} days...')

        # Skip events that already have severity unless --force
        if not options['force']:
            queryset = queryset.filter(severity__isnull=True)
            self.stdout.write('(Skipping events with existing severity - use --force to reclassify)')

        total = queryset.count()
        self.stdout.write(f'Found {total} events to process')

        if total == 0:
            self.stdout.write(self.style.WARNING('No events to process'))
            return

        classified = 0
        skipped = 0

        for event in queryset.iterator(chunk_size=100):
            old_severity = event.severity

            try:
                new_severity = ImpactClassifier.classify_severity(event)
                event.severity = new_severity
                event.save(update_fields=['severity'])
                classified += 1

                if classified % 100 == 0:
                    self.stdout.write(f'Progress: {classified}/{total}')

            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f'Failed to classify severity for Event {event.id}: {e}')
                )
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Classified {classified} events, skipped {skipped} due to errors'
            )
        )
