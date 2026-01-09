"""
Management command to backfill historical FRED economic data.

Usage:
    python manage.py backfill_fred --days=90
    python manage.py backfill_fred --days=365 --series=DCOILWTICO
    python manage.py backfill_fred --start=2023-01-01 --end=2024-01-01
"""
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from data_pipeline.tasks.fred_tasks import ingest_single_series
from data_pipeline.config.fred_series import get_all_series_ids, get_series_config

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Backfill historical FRED economic data for Venezuela series'

    def add_arguments(self, parser):
        # Date range options
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to backfill (default: 90)'
        )
        parser.add_argument(
            '--start',
            type=str,
            help='Start date in YYYY-MM-DD format (overrides --days)'
        )
        parser.add_argument(
            '--end',
            type=str,
            help='End date in YYYY-MM-DD format (default: today)'
        )

        # Series filtering
        parser.add_argument(
            '--series',
            type=str,
            help='Specific series ID to backfill (e.g., DCOILWTICO). If not provided, all series will be backfilled.'
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Series category to backfill (e.g., oil_prices, venezuela_macro)'
        )

        # Execution options
        parser.add_argument(
            '--async',
            action='store_true',
            dest='use_async',
            help='Run backfill asynchronously using Celery workers'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be backfilled without actually running'
        )

    def handle(self, *args, **options):
        # Parse date range
        if options['start']:
            try:
                start_date = datetime.strptime(options['start'], '%Y-%m-%d')
            except ValueError:
                raise CommandError('Invalid start date format. Use YYYY-MM-DD')
        else:
            start_date = datetime.now() - timedelta(days=options['days'])

        if options['end']:
            try:
                end_date = datetime.strptime(options['end'], '%Y-%m-%d')
            except ValueError:
                raise CommandError('Invalid end date format. Use YYYY-MM-DD')
        else:
            end_date = datetime.now()

        # Calculate lookback days
        lookback_days = (end_date - start_date).days

        # Determine which series to backfill
        if options['series']:
            series_ids = [options['series']]
            series_config = get_series_config(options['series'])
            if not series_config:
                raise CommandError(f'Series {options["series"]} not found in configuration')
        else:
            series_ids = get_all_series_ids()

        # Filter by category if specified
        if options['category']:
            from data_pipeline.config.fred_series import get_series_by_category
            category_series = get_series_by_category(options['category'])
            if not category_series:
                raise CommandError(f'Category {options["category"]} not found')
            series_ids = [sid for sid in series_ids if sid in category_series]

        # Display backfill plan
        self.stdout.write(self.style.SUCCESS(f'\nFRED Backfill Plan:'))
        self.stdout.write(f'  Date range: {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}')
        self.stdout.write(f'  Lookback: {lookback_days} days')
        self.stdout.write(f'  Series: {len(series_ids)} series')
        self.stdout.write(f'  Mode: {"Async (Celery)" if options["use_async"] else "Synchronous"}')
        self.stdout.write(f'\nSeries to backfill:')
        for series_id in series_ids:
            config = get_series_config(series_id)
            name = config.get('name', series_id) if config else series_id
            self.stdout.write(f'  - {series_id}: {name}')

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No data will be ingested'))
            return

        # Confirm execution
        if not options['use_async']:
            self.stdout.write(self.style.WARNING(
                f'\nThis will ingest data for {len(series_ids)} series synchronously. '
                'This may take several minutes.'
            ))
            confirm = input('Continue? [y/N] ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.ERROR('Backfill cancelled'))
                return

        # Execute backfill
        self.stdout.write(self.style.SUCCESS('\nStarting FRED backfill...\n'))

        results = []
        for series_id in series_ids:
            self.stdout.write(f'Processing {series_id}...')

            try:
                if options['use_async']:
                    # Dispatch async task
                    result = ingest_single_series.delay(series_id, lookback_days)
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Task dispatched (ID: {result.id})')
                    )
                    results.append({'series_id': series_id, 'task_id': result.id, 'status': 'dispatched'})
                else:
                    # Run synchronously
                    result = ingest_single_series(series_id, lookback_days)
                    status_symbol = '✓' if result['status'] == 'success' else '✗'
                    status_style = self.style.SUCCESS if result['status'] == 'success' else self.style.WARNING
                    self.stdout.write(
                        status_style(
                            f'  {status_symbol} {result["observations_created"]} created, '
                            f'{result["observations_skipped"]} skipped ({result["status"]})'
                        )
                    )
                    results.append(result)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Failed: {e}'))
                results.append({'series_id': series_id, 'status': 'error', 'error': str(e)})

        # Display summary
        self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
        self.stdout.write(self.style.SUCCESS('Backfill Complete'))
        self.stdout.write(self.style.SUCCESS(f'{"="*60}\n'))

        if options['use_async']:
            self.stdout.write(f'Dispatched {len(results)} tasks')
            self.stdout.write('\nMonitor task progress with:')
            self.stdout.write('  celery -A venezuelawatch inspect active')
            self.stdout.write('  celery -A venezuelawatch result <task_id>')
        else:
            successful = sum(1 for r in results if r.get('status') == 'success')
            failed = sum(1 for r in results if r.get('status') == 'failed')
            no_data = sum(1 for r in results if r.get('status') == 'no_data')
            total_created = sum(r.get('observations_created', 0) for r in results)
            total_skipped = sum(r.get('observations_skipped', 0) for r in results)

            self.stdout.write(f'Series processed: {len(results)}')
            self.stdout.write(f'  Successful: {successful}')
            self.stdout.write(f'  Failed: {failed}')
            self.stdout.write(f'  No data: {no_data}')
            self.stdout.write(f'\nObservations created: {total_created}')
            self.stdout.write(f'Observations skipped: {total_skipped}')

        self.stdout.write('')
