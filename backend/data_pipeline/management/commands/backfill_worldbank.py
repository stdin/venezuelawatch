"""
Management command to backfill historical World Bank development indicators.

Usage:
    python manage.py backfill_worldbank --years=5
    python manage.py backfill_worldbank --start=2015 --end=2023
    python manage.py backfill_worldbank --years=10 --indicator=NY.GDP.MKTP.CD
"""
import logging
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from data_pipeline.services.worldbank_client import WorldBankClient
from data_pipeline.services.event_mapper import map_worldbank_to_event
from data_pipeline.config.worldbank_config import (
    VENEZUELA_INDICATORS,
    get_indicator_config,
    get_indicators_by_category,
    get_priority_indicators,
)
from core.models import Event
from django.db import transaction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Backfill historical World Bank development indicators for Venezuela'

    def add_arguments(self, parser):
        # Date range options
        parser.add_argument(
            '--years',
            type=int,
            default=5,
            help='Number of years to backfill (default: 5)'
        )
        parser.add_argument(
            '--start',
            type=int,
            help='Start year (overrides --years)'
        )
        parser.add_argument(
            '--end',
            type=int,
            help='End year (default: current year - 1 due to data lag)'
        )

        # Indicator filtering
        parser.add_argument(
            '--indicator',
            type=str,
            help='Specific indicator ID to backfill (e.g., NY.GDP.MKTP.CD). If not provided, all indicators will be backfilled.'
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Indicator category to backfill (e.g., economic, social, infrastructure)'
        )
        parser.add_argument(
            '--priority',
            type=str,
            choices=['high', 'medium', 'low'],
            help='Backfill only indicators with specific priority level'
        )

        # Execution options
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be backfilled without actually running'
        )

    def handle(self, *args, **options):
        # Parse year range
        # World Bank data typically has 1-2 year lag
        if options['end']:
            end_year = options['end']
        else:
            end_year = datetime.now().year - 1  # Previous year

        if options['start']:
            start_year = options['start']
        else:
            start_year = end_year - options['years'] + 1

        if start_year > end_year:
            raise CommandError('Start year must be before or equal to end year')

        # Determine which indicators to backfill
        if options['indicator']:
            indicator_ids = {options['indicator']: VENEZUELA_INDICATORS.get(options['indicator'])}
            if not indicator_ids[options['indicator']]:
                raise CommandError(f'Indicator {options["indicator"]} not found in configuration')
        elif options['category']:
            indicator_ids = get_indicators_by_category(options['category'])
            if not indicator_ids:
                raise CommandError(f'Category {options["category"]} not found or has no indicators')
        elif options['priority']:
            indicator_ids = get_priority_indicators(options['priority'])
            if not indicator_ids:
                raise CommandError(f'No indicators found with priority {options["priority"]}')
        else:
            indicator_ids = VENEZUELA_INDICATORS

        # Display backfill plan
        self.stdout.write(self.style.SUCCESS(f'\nWorld Bank Backfill Plan:'))
        self.stdout.write(f'  Year range: {start_year} to {end_year}')
        self.stdout.write(f'  Total years: {end_year - start_year + 1} years')
        self.stdout.write(f'  Indicators: {len(indicator_ids)}')
        self.stdout.write(f'\nIndicators to backfill:')
        for indicator_id, config in indicator_ids.items():
            self.stdout.write(f'  - {indicator_id}: {config["name"]} ({config["priority"]} priority)')

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No data will be ingested'))
            return

        # Confirm execution
        self.stdout.write(self.style.WARNING(
            f'\nThis will fetch data for {len(indicator_ids)} indicators over {end_year - start_year + 1} years.'
        ))
        confirm = input('Continue? [y/N] ')
        if confirm.lower() != 'y':
            self.stdout.write(self.style.ERROR('Backfill cancelled'))
            return

        # Execute backfill
        self.stdout.write(self.style.SUCCESS('\nStarting World Bank backfill...\n'))

        # Initialize client
        client = WorldBankClient()

        results = []
        total_created = 0
        total_skipped = 0
        indicators_with_data = 0
        indicators_no_data = 0

        for indicator_id, indicator_config in indicator_ids.items():
            self.stdout.write(f'Processing {indicator_id}: {indicator_config["name"]}...')

            try:
                # Fetch indicator data
                result = client.get_indicator(
                    indicator_id=indicator_id,
                    country='VE',
                    start_year=start_year,
                    end_year=end_year,
                )

                data_points = result.get('data', [])

                if not data_points:
                    self.stdout.write(self.style.WARNING(f'  • No data available for {indicator_id}'))
                    indicators_no_data += 1
                    results.append({'indicator_id': indicator_id, 'status': 'no_data'})
                    continue

                created_count = 0
                skipped_count = 0

                # Process each observation
                for data_point in data_points:
                    year = data_point['year']
                    value = data_point['value']

                    # Check for duplicate
                    existing = Event.objects.filter(
                        source='WORLD_BANK',
                        content__indicator_id=indicator_id,
                        content__year=year,
                    ).exists()

                    if existing:
                        skipped_count += 1
                        continue

                    # Create Event
                    try:
                        indicator_data = {
                            'indicator_id': indicator_id,
                            'year': year,
                            'value': value,
                        }
                        event = map_worldbank_to_event(indicator_data, indicator_config)

                        with transaction.atomic():
                            event.save()
                            created_count += 1

                    except Exception as e:
                        logger.error(f"Failed to create event for {indicator_id} {year}: {e}", exc_info=True)
                        skipped_count += 1

                status_symbol = '✓' if created_count > 0 else '•'
                status_style = self.style.SUCCESS if created_count > 0 else self.style.WARNING
                self.stdout.write(
                    status_style(
                        f'  {status_symbol} {created_count} created, {skipped_count} skipped '
                        f'(found {len(data_points)} observations)'
                    )
                )

                total_created += created_count
                total_skipped += skipped_count
                indicators_with_data += 1 if created_count > 0 or skipped_count > 0 else 0
                results.append({
                    'indicator_id': indicator_id,
                    'status': 'success',
                    'created': created_count,
                    'skipped': skipped_count,
                })

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Failed: {e}'))
                results.append({'indicator_id': indicator_id, 'status': 'error', 'error': str(e)})

        # Display summary
        self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
        self.stdout.write(self.style.SUCCESS('Backfill Complete'))
        self.stdout.write(self.style.SUCCESS(f'{"="*60}\n'))

        self.stdout.write(f'Indicators processed: {len(results)}')
        self.stdout.write(f'  With data: {indicators_with_data}')
        self.stdout.write(f'  No data: {indicators_no_data}')
        self.stdout.write(f'\nObservations created: {total_created}')
        self.stdout.write(f'Observations skipped: {total_skipped}')

        self.stdout.write('')
