"""
Management command to backfill historical UN Comtrade trade data.

Usage:
    python manage.py backfill_comtrade --months=12
    python manage.py backfill_comtrade --start=2023-01 --end=2024-12
    python manage.py backfill_comtrade --months=24 --commodity=2709
"""
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError

from data_pipeline.tasks.comtrade_tasks import ingest_comtrade_trade_data
from data_pipeline.config.comtrade_config import get_all_commodities, get_commodity_config

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Backfill historical UN Comtrade trade data for Venezuela'

    def add_arguments(self, parser):
        # Date range options
        parser.add_argument(
            '--months',
            type=int,
            default=12,
            help='Number of months to backfill (default: 12)'
        )
        parser.add_argument(
            '--start',
            type=str,
            help='Start period in YYYYMM format (overrides --months)'
        )
        parser.add_argument(
            '--end',
            type=str,
            help='End period in YYYYMM format (default: 3 months ago due to data lag)'
        )

        # Commodity filtering
        parser.add_argument(
            '--commodity',
            type=str,
            help='Specific commodity HS code to backfill (e.g., 2709). If not provided, all commodities will be backfilled.'
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Commodity category to backfill (e.g., energy, food, healthcare)'
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
        # Comtrade has 2-3 month lag, so default end is 3 months ago
        if options['end']:
            try:
                end_period = datetime.strptime(options['end'], '%Y%m')
            except ValueError:
                raise CommandError('Invalid end period format. Use YYYYMM')
        else:
            end_period = datetime.now() - timedelta(days=90)  # 3 months ago

        if options['start']:
            try:
                start_period = datetime.strptime(options['start'], '%Y%m')
            except ValueError:
                raise CommandError('Invalid start period format. Use YYYYMM')
        else:
            start_period = end_period - timedelta(days=30 * options['months'])

        # Generate list of periods (YYYYMM format)
        periods = []
        current = start_period
        while current <= end_period:
            periods.append(current.strftime('%Y%m'))
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        # Determine which commodities to backfill
        if options['commodity']:
            commodity_codes = [options['commodity']]
            commodity_config = get_commodity_config(options['commodity'])
            if not commodity_config:
                raise CommandError(f'Commodity {options["commodity"]} not found in configuration')
        else:
            commodity_codes = get_all_commodities()

        # Filter by category if specified
        if options['category']:
            from data_pipeline.config.comtrade_config import get_commodities_by_category
            category_commodities = get_commodities_by_category(options['category'])
            if not category_commodities:
                raise CommandError(f'Category {options["category"]} not found')
            commodity_codes = [code for code in commodity_codes if code in category_commodities]

        # Display backfill plan
        self.stdout.write(self.style.SUCCESS(f'\nComtrade Backfill Plan:'))
        self.stdout.write(f'  Period range: {periods[0]} to {periods[-1]}')
        self.stdout.write(f'  Total periods: {len(periods)} months')
        self.stdout.write(f'  Commodities: {len(commodity_codes)}')
        self.stdout.write(f'  Mode: {"Async (Celery)" if options["use_async"] else "Synchronous"}')
        self.stdout.write(f'\nCommodities to backfill:')
        for code in commodity_codes:
            config = get_commodity_config(code)
            name = config.get('name', code) if config else code
            self.stdout.write(f'  - {code}: {name}')

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No data will be ingested'))
            return

        # Confirm execution
        if not options['use_async']:
            self.stdout.write(self.style.WARNING(
                f'\nThis will ingest data for {len(periods)} periods x {len(commodity_codes)} commodities. '
                'This may take a significant amount of time.'
            ))
            confirm = input('Continue? [y/N] ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.ERROR('Backfill cancelled'))
                return

        # Execute backfill
        self.stdout.write(self.style.SUCCESS('\nStarting Comtrade backfill...\n'))

        results = []
        for period in periods:
            self.stdout.write(f'Processing period {period}...')

            try:
                if options['use_async']:
                    # Dispatch async task
                    result = ingest_comtrade_trade_data.delay(period=period, lookback_months=0)
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Task dispatched (ID: {result.id})')
                    )
                    results.append({'period': period, 'task_id': result.id, 'status': 'dispatched'})
                else:
                    # Run synchronously
                    result = ingest_comtrade_trade_data(period=period, lookback_months=0)
                    status_symbol = '✓' if result.get('trade_flows_created', 0) > 0 else '•'
                    status_style = self.style.SUCCESS if result.get('trade_flows_created', 0) > 0 else self.style.WARNING
                    self.stdout.write(
                        status_style(
                            f'  {status_symbol} {result["trade_flows_created"]} created, '
                            f'{result["trade_flows_skipped"]} skipped, '
                            f'${result["total_trade_value_usd"]/1_000_000:.1f}M total'
                        )
                    )
                    results.append(result)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Failed: {e}'))
                results.append({'period': period, 'status': 'error', 'error': str(e)})

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
            successful = sum(1 for r in results if r.get('trade_flows_created', 0) > 0)
            total_created = sum(r.get('trade_flows_created', 0) for r in results)
            total_skipped = sum(r.get('trade_flows_skipped', 0) for r in results)
            total_value = sum(r.get('total_trade_value_usd', 0) for r in results)

            self.stdout.write(f'Periods processed: {len(results)}')
            self.stdout.write(f'  With data: {successful}')
            self.stdout.write(f'\nTrade flows created: {total_created}')
            self.stdout.write(f'Trade flows skipped: {total_skipped}')
            self.stdout.write(f'Total trade value: ${total_value/1_000_000_000:.2f}B')

        self.stdout.write('')
