"""
Management command to recalculate risk scores for events.

Useful for:
- Updating scores after risk model changes
- Backfilling scores for old events
- Fixing incorrect risk calculations
"""
from django.core.management.base import BaseCommand
from core.models import Event
from data_pipeline.services.risk_scorer import RiskScorer
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Recalculate risk scores for events using multi-dimensional model'

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
            help='Recalculate ALL events (ignores --days)'
        )

    def handle(self, *args, **options):
        if options['all']:
            queryset = Event.objects.filter(llm_analysis__isnull=False)
            self.stdout.write('Recalculating risk for ALL events with LLM analysis...')
        else:
            cutoff_date = timezone.now() - timedelta(days=options['days'])
            queryset = Event.objects.filter(
                created_at__gte=cutoff_date,
                llm_analysis__isnull=False
            )
            self.stdout.write(f'Recalculating risk for events in last {options["days"]} days...')

        total = queryset.count()
        self.stdout.write(f'Found {total} events to process')

        if total == 0:
            self.stdout.write(self.style.WARNING('No events to process'))
            return

        updated = 0
        skipped = 0

        for event in queryset.iterator(chunk_size=100):
            old_score = event.risk_score

            try:
                new_score = RiskScorer.calculate_comprehensive_risk(event)
                event.risk_score = new_score
                event.save(update_fields=['risk_score'])
                updated += 1

                if updated % 100 == 0:
                    self.stdout.write(f'Progress: {updated}/{total}')

            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f'Failed to recalculate risk for Event {event.id}: {e}')
                )
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Updated {updated} events, skipped {skipped} due to errors'
            )
        )
