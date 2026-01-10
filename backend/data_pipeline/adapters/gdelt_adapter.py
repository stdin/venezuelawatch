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
from data_pipeline.services.category_classifier import CategoryClassifier
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
        Transform GDELT events to canonical Event schema with normalizer logic.

        Implements canonical normalizer from platform design (section 5.2):
        - Category classification using CAMEO codes
        - Magnitude normalization (GoldsteinScale → 0-1)
        - Tone normalization (AvgTone → 0-1, inverted)
        - Direction classification (POSITIVE/NEGATIVE/NEUTRAL)
        - Confidence scoring based on num_sources
        - Actor extraction from GDELT fields
        - GKG enrichment preserved for Phase 26+

        Args:
            raw_events: List of raw GDELT event dicts from fetch()

        Returns:
            List of BigQueryEvent objects with canonical fields populated

        Note:
            Failed transformations are logged but don't stop processing of other events.
        """
        bigquery_events = []

        for gdelt_event in raw_events:
            try:
                # Parse DATEADDED (YYYYMMDDHHMMSS format)
                date_str = str(gdelt_event['DATEADDED'])
                event_date = timezone.datetime.strptime(
                    date_str[:8], '%Y%m%d'
                ).replace(tzinfo=pytz.UTC)

                # Classify category using CAMEO EventCode
                event_code = gdelt_event.get('EventCode', '')
                category, subcategory = CategoryClassifier.classify('gdelt', {'EventCode': event_code})

                # Normalize magnitude: GoldsteinScale (-10 to +10) → 0-1
                goldstein = gdelt_event.get('GoldsteinScale', 0) or 0
                magnitude_norm = (goldstein + 10) / 20  # → 0-1

                # Determine direction based on GoldsteinScale
                if goldstein < -2:
                    direction = "NEGATIVE"
                elif goldstein > 2:
                    direction = "POSITIVE"
                else:
                    direction = "NEUTRAL"

                # Normalize tone: AvgTone (inverted so negative tone → higher risk)
                avg_tone = gdelt_event.get('AvgTone', 0) or 0
                tone_norm = min(max((avg_tone * -1 + 10) / 20, 0), 1)

                # Confidence scoring
                num_sources = gdelt_event.get('NumSources', 1) or 1
                source_credibility = 0.7  # GDELT baseline
                confidence = min(num_sources / 10, 1.0) * source_credibility

                # Extract actors
                actor1_name = gdelt_event.get('Actor1Name')
                actor2_name = gdelt_event.get('Actor2Name')

                # Classify actor types (simplified for Phase 25, LLM enhancement in Phase 26+)
                actor1_type = self._classify_actor_type(gdelt_event.get('Actor1Code'))
                actor2_type = self._classify_actor_type(gdelt_event.get('Actor2Code'))

                # Extract commodities/sectors from GKG themes if available
                commodities = []
                sectors = []
                if 'gkg_parsed' in gdelt_event and gdelt_event['gkg_parsed']:
                    themes = gdelt_event['gkg_parsed'].get('themes', [])
                    commodities, sectors = self._extract_commodities_sectors(themes)

                # Generate title from actors and event code
                title = (
                    f"{actor1_name or 'Unknown'} - "
                    f"{actor2_name or 'Event'} "
                    f"({event_code})"
                )

                # Create canonical BigQueryEvent
                bq_event = BigQueryEvent(
                    # Identity
                    id=str(gdelt_event['GLOBALEVENTID']),
                    source='gdelt',
                    source_event_id=str(gdelt_event['GLOBALEVENTID']),
                    source_url=gdelt_event.get('SOURCEURL', ''),
                    source_name=self.source_name,

                    # Temporal
                    event_timestamp=event_date,
                    ingested_at=timezone.now(),
                    created_at=timezone.now(),

                    # Classification
                    category=category,
                    subcategory=subcategory,
                    event_type=event_code,

                    # Location
                    country_code='VE',
                    admin1=gdelt_event.get('ActionGeo_ADM1Code'),
                    admin2=gdelt_event.get('ActionGeo_ADM2Code'),
                    latitude=gdelt_event.get('ActionGeo_Lat'),
                    longitude=gdelt_event.get('ActionGeo_Long'),
                    location=gdelt_event.get('ActionGeo_FullName', 'Venezuela'),

                    # Magnitude
                    magnitude_raw=goldstein,
                    magnitude_unit='goldstein',
                    magnitude_norm=magnitude_norm,

                    # Direction/Tone
                    direction=direction,
                    tone_raw=avg_tone,
                    tone_norm=tone_norm,

                    # Confidence
                    num_sources=num_sources,
                    source_credibility=source_credibility,
                    confidence=confidence,

                    # Actors
                    actor1_name=actor1_name,
                    actor1_type=actor1_type,
                    actor2_name=actor2_name,
                    actor2_type=actor2_type,

                    # Commodities/Sectors
                    commodities=commodities,
                    sectors=sectors,

                    # Legacy fields
                    title=title[:500],
                    content=f"GDELT Event: {event_code} - Tone: {avg_tone}",
                    risk_score=None,  # Computed in Phase 25-02 (scoring)
                    severity=None,    # Computed in Phase 25-02 (severity)

                    # Enhancement arrays (Phase 26+)
                    # For now, preserve GKG themes in metadata, migrate to themes array in Phase 26
                    themes=[],  # Will populate from GKG in Phase 26
                    quotations=[],  # Will populate from GKG quotations in Phase 26
                    gcam_scores=None,  # Will populate from GKG GCAM in Phase 26
                    entity_relationships=[],  # Phase 26+
                    related_events=[],  # Phase 27+

                    # Metadata (preserve all GDELT fields + GKG data)
                    metadata={
                        # GDELT core fields
                        'goldstein_scale': goldstein,
                        'avg_tone': avg_tone,
                        'num_mentions': gdelt_event.get('NumMentions'),
                        'num_sources': num_sources,
                        'num_articles': gdelt_event.get('NumArticles'),
                        'quad_class': gdelt_event.get('QuadClass'),
                        'actor1_code': gdelt_event.get('Actor1Code'),
                        'actor2_code': gdelt_event.get('Actor2Code'),
                        'event_code': event_code,

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

                        # GKG data (Phase 26 will migrate to canonical enhancement arrays)
                        'gkg_data': gdelt_event.get('gkg_parsed'),
                    }
                )

                bigquery_events.append(bq_event)

            except Exception as e:
                logger.error(f"Failed to transform GDELT event: {e}", exc_info=True)
                # Continue with other events - don't fail entire batch

        logger.info(f"Transformed {len(bigquery_events)} GDELT events to canonical schema")
        return bigquery_events

    def _classify_actor_type(self, actor_code: Optional[str]) -> Optional[str]:
        """
        Classify actor type from GDELT actor code.

        Simplified heuristic for Phase 25. Phase 26+ will use LLM for better classification.
        """
        if not actor_code:
            return None

        code = actor_code.upper()

        # Government codes
        if 'GOV' in code or 'MIL' in code or 'LEG' in code or 'JUD' in code:
            return 'GOVERNMENT'

        # Military codes
        if 'MIL' in code or 'ARM' in code:
            return 'MILITARY'

        # Rebel/opposition codes
        if 'REB' in code or 'OPP' in code or 'INS' in code:
            return 'REBEL'

        # Corporate codes
        if 'BUS' in code or 'COP' in code:
            return 'CORPORATE'

        # Default to civilian
        return 'CIVILIAN'

    def _extract_commodities_sectors(self, themes: List[str]) -> Tuple[List[str], List[str]]:
        """
        Extract commodities and sectors from GKG themes.

        Simple keyword matching for Phase 25. Phase 26+ will use theme taxonomy mapping.
        """
        commodities = []
        sectors = []

        theme_text = ' '.join(themes).upper()

        # Commodity keywords
        if 'OIL' in theme_text or 'PETROLEUM' in theme_text:
            commodities.append('OIL')
            sectors.append('ENERGY')
        if 'GOLD' in theme_text:
            commodities.append('GOLD')
            sectors.append('MINING')
        if 'GAS' in theme_text:
            commodities.append('GAS')
            sectors.append('ENERGY')

        return (list(set(commodities)), list(set(sectors)))

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
