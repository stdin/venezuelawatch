"""
Management command for entity extraction and trending score sync.

Usage:
    python manage.py extract_entities [--days 30] [--sync-trending] [--all]
"""

import argparse
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Entity, EntityMention, Event
from data_pipeline.tasks.entity_extraction import backfill_entities
from data_pipeline.services.trending_service import TrendingService


class Command(BaseCommand):
    help = 'Extract entities from events and update trending scores'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Process events from last N days (default: 30)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Process all events with entities (overrides --days)'
        )
        parser.add_argument(
            '--sync-trending',
            action='store_true',
            help='Sync trending scores from EntityMention records after extraction'
        )

    def handle(self, *args, **options):
        days = options['days']
        process_all = options['all']
        sync_trending = options['sync_trending']

        self.stdout.write(self.style.SUCCESS('=== Entity Extraction Command ===\n'))

        # Show current stats before processing
        self.stdout.write('Current state:')
        self.stdout.write(f'  Entities: {Entity.objects.count()}')
        self.stdout.write(f'  Entity mentions: {EntityMention.objects.count()}')
        self.stdout.write(f'  Events with entities: {Event.objects.filter(entities__len__gt=0).count()}\n')

        # Queue extraction tasks
        if process_all:
            self.stdout.write(self.style.WARNING('Queuing ALL events for entity extraction...'))
            # For --all, use a large day range
            result = backfill_entities(days=365*10, batch_size=100)
        else:
            self.stdout.write(self.style.WARNING(f'Queuing events from last {days} days for extraction...'))
            result = backfill_entities(days=days, batch_size=100)

        if 'error' in result:
            self.stdout.write(self.style.ERROR(f'Error: {result["error"]}'))
            return

        events_queued = result['events_queued']
        self.stdout.write(self.style.SUCCESS(f'✓ Queued {events_queued} events for processing'))
        self.stdout.write(f'  Cutoff: {result["cutoff"]}\n')

        # Note: Celery tasks run asynchronously, so we can't show updated counts immediately
        self.stdout.write(self.style.WARNING(
            'Note: Entity extraction tasks are running asynchronously in Celery.\n'
            'Run this command again in a few minutes to see updated stats.\n'
        ))

        # Sync trending scores if requested
        if sync_trending:
            self.stdout.write(self.style.WARNING('Syncing trending scores from EntityMention records...'))
            sync_result = TrendingService.sync_trending_scores(days=days)
            self.stdout.write(self.style.SUCCESS(
                f'✓ Synced {sync_result["mentions_processed"]} mentions to Redis'
            ))
            self.stdout.write(f'  Cutoff: {sync_result["cutoff"]}\n')

            # Show top trending entities
            self.stdout.write(self.style.SUCCESS('Top 10 trending entities:'))
            trending = TrendingService.get_trending_entities(metric='mentions', limit=10)
            if trending:
                for i, entity_data in enumerate(trending, start=1):
                    self.stdout.write(
                        f'  {i}. {entity_data["canonical_name"]} ({entity_data["entity_type"]}): '
                        f'score={entity_data["score"]:.2f}, mentions={entity_data["mention_count"]}'
                    )
            else:
                self.stdout.write('  (No trending entities found)')

        self.stdout.write('\n' + self.style.SUCCESS('Done!'))
