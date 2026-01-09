"""
World Bank development indicators ingestion tasks.

Fetches Venezuela development indicators (GDP, inflation, poverty, etc.)
for annual/quarterly reporting.
"""
import logging
from typing import Dict, Any, Optional
from celery import shared_task
from django.db import transaction
from django.utils import timezone

from data_pipeline.tasks.base import BaseIngestionTask
from data_pipeline.services.worldbank_client import WorldBankClient
from data_pipeline.services.event_mapper import map_worldbank_to_event
from data_pipeline.config.worldbank_config import (
    VENEZUELA_INDICATORS,
    get_indicator_config,
)
from core.models import Event

logger = logging.getLogger(__name__)


@shared_task(base=BaseIngestionTask, bind=True)
def ingest_worldbank_indicators(
    self,
    lookback_years: int = 2,
    indicator_ids: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Ingest Venezuela development indicators from World Bank.

    Fetches latest available data for tracked indicators (GDP, inflation,
    poverty, unemployment, etc.) and creates Events.

    Args:
        lookback_years: Number of years to look back (default: 2)
        indicator_ids: Optional list of specific indicator IDs to fetch.
                      If None, fetches all indicators in VENEZUELA_INDICATORS.

    Returns:
        {
            'indicators_processed': int,
            'observations_created': int,
            'observations_skipped': int,
            'indicators_failed': int,
        }
    """
    logger.info(f"Starting World Bank ingestion (lookback_years={lookback_years})")

    # Initialize client
    client = WorldBankClient()

    # Determine which indicators to fetch
    if indicator_ids:
        indicators_to_fetch = {
            id: VENEZUELA_INDICATORS[id]
            for id in indicator_ids
            if id in VENEZUELA_INDICATORS
        }
    else:
        indicators_to_fetch = VENEZUELA_INDICATORS

    logger.info(f"Fetching {len(indicators_to_fetch)} indicators")

    # Track metrics
    indicators_processed = 0
    observations_created = 0
    observations_skipped = 0
    indicators_failed = 0

    # Calculate year range
    current_year = timezone.now().year
    start_year = current_year - lookback_years
    end_year = current_year

    # Process each indicator
    for indicator_id, indicator_config in indicators_to_fetch.items():
        logger.info(f"Processing indicator: {indicator_config['name']} ({indicator_id})")

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
                logger.warning(f"No data available for {indicator_id} in the specified period")
                indicators_failed += 1
                continue

            logger.info(f"Found {len(data_points)} observations for {indicator_id}")

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
                    logger.debug(f"Skipping duplicate observation: {indicator_id} {year}")
                    observations_skipped += 1
                    continue

                # Map to Event
                try:
                    indicator_data = {
                        'indicator_id': indicator_id,
                        'year': year,
                        'value': value,
                    }
                    event = map_worldbank_to_event(indicator_data, indicator_config)

                    # Save to database
                    with transaction.atomic():
                        event.save()
                        observations_created += 1
                        logger.debug(f"Created indicator event: {event.title}")

                except Exception as e:
                    logger.error(f"Failed to create event for {indicator_id} {year}: {e}", exc_info=True)
                    observations_skipped += 1

            indicators_processed += 1

        except Exception as e:
            logger.error(f"Failed to process indicator {indicator_id}: {e}", exc_info=True)
            indicators_failed += 1
            continue

    result = {
        'indicators_processed': indicators_processed,
        'observations_created': observations_created,
        'observations_skipped': observations_skipped,
        'indicators_failed': indicators_failed,
    }

    logger.info(
        f"World Bank ingestion complete: {indicators_processed} indicators processed, "
        f"{observations_created} observations created, {observations_skipped} skipped, "
        f"{indicators_failed} failed"
    )

    return result
