"""
GDELT BigQuery Adapter - Reference Implementation

This adapter demonstrates the pattern for integrating external data sources.
It fetches Venezuela-related events from GDELT native BigQuery, enriches with
GKG metadata, and publishes to our time-series analytics pipeline.

**For developers adding new data sources:**
- Copy this file as a template (e.g., reliefweb_adapter.py)
- Follow the naming convention: {Source}Adapter class in {source}_adapter.py
- Implement fetch/transform/validate methods per DataSourceAdapter contract
- See inline comments marked "GDELT-specific" vs "General pattern"

**GDELT-specific design choices:**
- Queries gdelt-bq.gdeltv2.events_partitioned (Google's public dataset)
- Enriches with GKG data (themes, entities, tone) for richer intelligence
- Stores all 61 GDELT fields in metadata JSON for future analysis
- Uses GLOBALEVENTID for deduplication (other sources might use URL or composite keys)
- Maps QuadClass 1-4 to 'political' event type (other sources have different taxonomies)

**Dependencies:**
- GDELT native BigQuery access (no API key needed)
- GCP BigQuery client for queries
- GKG parser utilities for theme/entity extraction
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import pytz
from django.utils import timezone

from data_pipeline.adapters.base import DataSourceAdapter
from api.services.gdelt_bigquery_service import gdelt_bigquery_service
from api.services.gdelt_gkg_service import gdelt_gkg_service
from api.bigquery_models import Event as BigQueryEvent
from api.services.bigquery_service import bigquery_service
from api.services.gdelt_gkg_parsers import (
    parse_v2_themes,
    parse_v2_persons,
    parse_v2_organizations,
    parse_v2_locations,
    parse_v2_tone,
)

logger = logging.getLogger(__name__)


class GdeltAdapter(DataSourceAdapter):
    """
    GDELT BigQuery data source adapter.

    Fetches Venezuela-related events from GDELT's native BigQuery dataset,
    enriches with Global Knowledge Graph (GKG) data, and transforms to our
    standardized Event schema.

    This is the reference implementation for data source adapters. When building
    new adapters, use this as a template and follow the patterns established here.
    """

    # Class attributes define adapter metadata
    source_name = "GDELT"
    schedule_frequency = "*/15 * * * *"  # Every 15 minutes (matches GDELT update frequency)
    default_lookback_minutes = 15

    def fetch(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Fetch Venezuela events from GDELT BigQuery and enrich with GKG data.

        GDELT-specific: Queries gdelt-bq.gdeltv2.events_partitioned with Venezuela
        filters (ActionGeo_CountryCode='VE' or Actor1/2CountryCode='VE'). Other
        adapters might fetch from REST APIs, CSV files, or other data sources.

        GKG enrichment adds themes, entities (persons/organizations/locations), and
        sentiment analysis. This is optional but highly valuable for intelligence.
        Other data sources might not have equivalent metadata layers.

        Args:
            start_time: Start of time window (inclusive)
            end_time: End of time window (exclusive)
            limit: Maximum number of events to fetch (default: 1000)

        Returns:
            List of raw GDELT event dicts with optional 'gkg_parsed' field

        Raises:
            Exception: If BigQuery query fails
        """
        logger.info(
            f"Fetching GDELT events from {start_time} to {end_time} (limit: {limit})"
        )

        # Fetch Venezuela events from GDELT native BigQuery
        gdelt_events = gdelt_bigquery_service.get_venezuela_events(
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

        logger.info(f"Fetched {len(gdelt_events)} events from GDELT BigQuery")

        # GDELT-specific: Enrich with GKG data (themes, entities, sentiment)
        # Other adapters might skip enrichment or have different metadata sources
        events_with_gkg = 0
        events_without_gkg = 0
        total_themes = 0
        total_persons = 0
        total_orgs = 0

        for gdelt_event in gdelt_events:
            source_url = gdelt_event.get('SOURCEURL')
            if source_url:
                try:
                    # GDELT-specific: Parse DATEADDED (YYYYMMDDHHMMSS format)
                    # Other adapters might receive ISO 8601 or Unix timestamps
                    date_str = str(gdelt_event['DATEADDED'])
                    event_date = timezone.datetime.strptime(
                        date_str[:8], '%Y%m%d'
                    ).replace(tzinfo=pytz.UTC)

                    # Fetch GKG record by DocumentIdentifier (= SOURCEURL)
                    gkg_raw = gdelt_gkg_service.get_gkg_by_document_id(
                        document_id=source_url,
                        partition_date=event_date
                    )

                    if gkg_raw:
                        # Parse GKG fields into structured data
                        themes_list = parse_v2_themes(gkg_raw.get('V2Themes'))
                        persons_list = parse_v2_persons(gkg_raw.get('V2Persons'))
                        orgs_list = parse_v2_organizations(gkg_raw.get('V2Organizations'))
                        locations_list = parse_v2_locations(gkg_raw.get('V2Locations'))
                        tone_dict = parse_v2_tone(gkg_raw.get('V2Tone'))

                        # Build structured GKG dict
                        gdelt_event['gkg_parsed'] = {
                            'record_id': gkg_raw.get('GKGRECORDID'),
                            'source': gkg_raw.get('SourceCommonName'),
                            'themes': themes_list,
                            'persons': persons_list,
                            'organizations': orgs_list,
                            'locations': locations_list,
                            'tone': tone_dict,
                            'quotations': gkg_raw.get('Quotations', ''),
                            'gcam': gkg_raw.get('GCAM', '')
                        }

                        events_with_gkg += 1
                        total_themes += len(themes_list)
                        total_persons += len(persons_list)
                        total_orgs += len(orgs_list)

                        logger.debug(
                            f"Parsed GKG for {source_url[:50]}: "
                            f"{len(themes_list)} themes, {len(persons_list)} persons, "
                            f"{len(orgs_list)} orgs"
                        )
                    else:
                        events_without_gkg += 1

                except Exception as e:
                    logger.warning(f"Failed to parse GKG for {source_url[:50]}: {e}")
                    events_without_gkg += 1
            else:
                events_without_gkg += 1

        logger.info(
            f"GKG enrichment: {events_with_gkg} events with GKG data, "
            f"{events_without_gkg} without | "
            f"Parsed {total_themes} themes, {total_persons} persons, "
            f"{total_orgs} organizations"
        )

        return gdelt_events

    def transform(self, raw_events: List[Dict[str, Any]]) -> List[BigQueryEvent]:
        """
        Map GDELT schema to BigQuery Event schema.

        GDELT-specific: Stores all 61 native GDELT fields in metadata JSON for
        future analysis. This preserves the full richness of GDELT data even though
        our base Event schema only has a subset of fields.

        Other adapters would map their own schemas here. For example, ReliefWeb
        adapter might map 'headline' to title, 'body' to content, etc.

        Args:
            raw_events: List of raw GDELT event dicts from fetch()

        Returns:
            List of BigQueryEvent objects ready for validation and publishing

        Note:
            Failed transformations are logged but don't stop processing of other events.
        """
        bigquery_events = []

        for gdelt_event in raw_events:
            try:
                # GDELT-specific: Parse DATEADDED (YYYYMMDDHHMMSS format)
                # Other adapters might receive ISO 8601 or Unix timestamps
                date_str = str(gdelt_event['DATEADDED'])
                event_date = timezone.datetime.strptime(
                    date_str[:8], '%Y%m%d'
                ).replace(tzinfo=pytz.UTC)

                # Generate title from actors and event code
                # GDELT-specific: Actor names and event codes
                # Other adapters might have 'headline' or 'title' fields directly
                title = (
                    f"{gdelt_event.get('Actor1Name', 'Unknown')} - "
                    f"{gdelt_event.get('Actor2Name', 'Event')} "
                    f"({gdelt_event.get('EventCode', '')})"
                )

                # GDELT-specific: QuadClass categorizes as verbal/material cooperation/conflict
                # Values 1-4 all map to 'political' in our taxonomy
                # Other sources might use different event taxonomies (e.g., ACLED has 9 event types)
                quad_class = gdelt_event.get('QuadClass')
                event_type_map = {
                    1: 'political',  # Verbal Cooperation
                    2: 'political',  # Material Cooperation
                    3: 'political',  # Verbal Conflict
                    4: 'political'   # Material Conflict
                }
                event_type = event_type_map.get(quad_class, 'other')

                # Create BigQueryEvent with GDELT ID and fields
                # GDELT-specific: Use GLOBALEVENTID as unique identifier
                # Other adapters might use URL, composite keys, or source-specific IDs
                bq_event = BigQueryEvent(
                    id=str(gdelt_event['GLOBALEVENTID']),
                    source_url=gdelt_event.get('SOURCEURL', ''),
                    mentioned_at=event_date,
                    created_at=timezone.now(),
                    title=title[:500],  # Truncate if needed
                    content=f"GDELT Event: {gdelt_event.get('EventCode', '')} - Tone: {gdelt_event.get('AvgTone', 0)}",
                    source_name=self.source_name,
                    event_type=event_type,
                    location=gdelt_event.get('ActionGeo_FullName', 'Venezuela'),
                    risk_score=None,  # Computed by LLM downstream
                    severity=None,    # Computed by LLM downstream
                    metadata={
                        # GDELT-specific: Store all 61 fields in metadata
                        # This preserves full data fidelity for future analysis
                        # Other adapters should store their source-specific fields similarly
                        'goldstein_scale': gdelt_event.get('GoldsteinScale'),
                        'avg_tone': gdelt_event.get('AvgTone'),
                        'num_mentions': gdelt_event.get('NumMentions'),
                        'num_sources': gdelt_event.get('NumSources'),
                        'num_articles': gdelt_event.get('NumArticles'),
                        'quad_class': quad_class,
                        'actor1_code': gdelt_event.get('Actor1Code'),
                        'actor1_name': gdelt_event.get('Actor1Name'),
                        'actor2_code': gdelt_event.get('Actor2Code'),
                        'actor2_name': gdelt_event.get('Actor2Name'),
                        'event_code': gdelt_event.get('EventCode'),
                        'action_geo_lat': gdelt_event.get('ActionGeo_Lat'),
                        'action_geo_long': gdelt_event.get('ActionGeo_Long'),

                        # Religion & Ethnicity
                        'actor1_religion1_code': gdelt_event.get('Actor1Religion1Code'),
                        'actor1_religion2_code': gdelt_event.get('Actor1Religion2Code'),
                        'actor2_religion1_code': gdelt_event.get('Actor2Religion1Code'),
                        'actor2_religion2_code': gdelt_event.get('Actor2Religion2Code'),
                        'actor1_ethnic_code': gdelt_event.get('Actor1EthnicCode'),
                        'actor2_ethnic_code': gdelt_event.get('Actor2EthnicCode'),

                        # Enhanced Actor Classification
                        'actor1_known_group_code': gdelt_event.get('Actor1KnownGroupCode'),
                        'actor1_type2_code': gdelt_event.get('Actor1Type2Code'),
                        'actor2_known_group_code': gdelt_event.get('Actor2KnownGroupCode'),
                        'actor2_type3_code': gdelt_event.get('Actor2Type3Code'),

                        # Geographic Precision
                        'actor1_geo_adm1': gdelt_event.get('Actor1Geo_ADM1Code'),
                        'actor1_geo_adm2': gdelt_event.get('Actor1Geo_ADM2Code'),
                        'actor1_geo_feature_id': gdelt_event.get('Actor1Geo_FeatureID'),
                        'actor2_geo_adm1': gdelt_event.get('Actor2Geo_ADM1Code'),
                        'actor2_geo_adm2': gdelt_event.get('Actor2Geo_ADM2Code'),
                        'actor2_geo_feature_id': gdelt_event.get('Actor2Geo_FeatureID'),
                        'action_geo_adm1': gdelt_event.get('ActionGeo_ADM1Code'),
                        'action_geo_adm2': gdelt_event.get('ActionGeo_ADM2Code'),
                        'action_geo_feature_id': gdelt_event.get('ActionGeo_FeatureID'),

                        # GKG enrichment data (parsed into structured fields)
                        # GDELT-specific: GKG enrichment is optional but highly valuable
                        # Other sources might not have equivalent metadata layers
                        'gkg': gdelt_event.get('gkg_parsed') if 'gkg_parsed' in gdelt_event else None,
                    }
                )

                bigquery_events.append(bq_event)

            except Exception as e:
                logger.error(f"Failed to map GDELT event: {e}", exc_info=True)
                # Continue with other events - don't fail entire batch

        logger.info(f"Transformed {len(bigquery_events)} GDELT events to BigQuery schema")
        return bigquery_events

    def validate(self, event: BigQueryEvent) -> Tuple[bool, Optional[str]]:
        """
        Validate event completeness and check for duplicates.

        GDELT-specific: Uses GLOBALEVENTID for deduplication by querying BigQuery.
        Other adapters might use URL matching, composite keys, or source-specific IDs.

        Args:
            event: BigQueryEvent instance to validate

        Returns:
            Tuple of (is_valid, error_message):
            - (True, None) if valid and not duplicate
            - (False, "duplicate") if duplicate found
            - (False, "error description") for other validation failures

        Note:
            Duplicate detection queries BigQuery, so there's a small latency cost.
            This is acceptable for GDELT's 15-minute sync frequency. Higher-frequency
            adapters might want to use in-memory caching instead.
        """
        # Check required fields
        if not event.id:
            return (False, "Missing required field: id")
        if not event.source_url:
            return (False, "Missing required field: source_url")
        if not event.mentioned_at:
            return (False, "Missing required field: mentioned_at")
        if not event.title:
            return (False, "Missing required field: title")

        # GDELT-specific: Check for duplicates using GLOBALEVENTID
        # Other adapters might check by URL, hash, or composite keys
        try:
            existing_query = f"""
                SELECT COUNT(*) as count
                FROM `{bigquery_service.project_id}.{bigquery_service.dataset_id}.events`
                WHERE id = @event_id
            """
            from google.cloud import bigquery
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter('event_id', 'STRING', event.id)
                ]
            )
            results = bigquery_service.client.query(existing_query, job_config=job_config).result()
            row = list(results)[0]
            if row.count > 0:
                logger.debug(f"Skipping duplicate GDELT event: {event.id}")
                return (False, "duplicate")
        except Exception as e:
            logger.error(f"Failed to check for duplicate: {e}")
            # Continue with insert on duplicate check failure
            # Better to risk duplicate than lose data

        return (True, None)
