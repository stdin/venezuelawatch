"""
Theme enricher service for GKG theme parsing and relationship categorization.

Parses GDELT GKG V2Themes format and enriches entity relationship edges
with thematic context for activity-based filtering.
"""
import logging
import os
from typing import List, Dict, Any, Optional

from google.cloud import bigquery

logger = logging.getLogger(__name__)


class ThemeEnricher:
    """
    Service to parse GKG themes and enrich entity relationships.

    Parses GDELT V2Themes format and categorizes relationships based on
    theme content (sanctions, trade, political, etc.).
    """

    def __init__(self):
        """Initialize with BigQuery client."""
        self.bq_client = bigquery.Client()
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'venezuelawatch')
        self.dataset = 'venezuelawatch_data'

    def parse_gkg_themes(self, v2_themes_string: str) -> List[str]:
        """
        Parse GDELT V2Themes format into list of theme names.

        Format: "THEME1,offset1,offset2;THEME2,offset3,offset4"
        Example: "WB_1234_SANCTIONS,0,10;ECON_TRADE,15,25"

        Args:
            v2_themes_string: Raw V2Themes string from GKG metadata

        Returns:
            List of unique theme names (empty list if None/empty)
        """
        if not v2_themes_string:
            return []

        try:
            theme_mentions = v2_themes_string.split(';')
            themes = []

            for mention in theme_mentions:
                if not mention.strip():
                    continue

                # Extract theme name (before first comma)
                parts = mention.split(',')
                if parts:
                    theme = parts[0].strip()
                    if theme:
                        themes.append(theme)

            # Return unique themes while preserving order
            seen = set()
            unique_themes = []
            for theme in themes:
                if theme not in seen:
                    seen.add(theme)
                    unique_themes.append(theme)

            return unique_themes

        except Exception as e:
            logger.warning(f"Failed to parse V2Themes '{v2_themes_string}': {e}")
            return []

    def categorize_relationship(self, theme_list: List[str]) -> str:
        """
        Map themes to relationship categories.

        Categories:
        - sanctions: SANCTION, EMBARGO themes
        - trade: TRADE, EXPORT themes
        - political: LEADER, GOV_ themes
        - adversarial: UNREST, PROTEST themes
        - energy: OIL, ENERGY themes
        - other: Default fallback

        Args:
            theme_list: List of GKG theme codes

        Returns:
            Primary category string
        """
        if not theme_list:
            return 'other'

        # Convert themes to uppercase for case-insensitive matching
        themes_upper = [theme.upper() for theme in theme_list]
        themes_str = ';'.join(themes_upper)

        # Priority order: more specific categories first
        if 'SANCTION' in themes_str or 'EMBARGO' in themes_str:
            return 'sanctions'
        elif 'TRADE' in themes_str or 'EXPORT' in themes_str:
            return 'trade'
        elif 'LEADER' in themes_str or 'GOV_' in themes_str:
            return 'political'
        elif 'UNREST' in themes_str or 'PROTEST' in themes_str:
            return 'adversarial'
        elif 'OIL' in themes_str or 'ENERGY' in themes_str:
            return 'energy'
        else:
            return 'other'

    def enrich_edge_with_themes(
        self,
        edge: Dict[str, Any],
        event_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Enrich edge with GKG themes from connecting events.

        Fetches events by IDs from BigQuery, extracts V2Themes from metadata,
        aggregates unique themes, and categorizes relationship.

        Args:
            edge: Edge dictionary with id, source, target, weight, data
            event_ids: List of event UUIDs connecting the entities

        Returns:
            Enriched edge with data.themes and data.category added
        """
        if not event_ids:
            # No events to enrich from
            edge['data']['themes'] = []
            edge['data']['category'] = 'other'
            return edge

        try:
            # Query BigQuery for event metadata
            # Use parameterized query to prevent SQL injection
            event_ids_str = ', '.join([f"'{eid}'" for eid in event_ids])

            query = f"""
            SELECT
                id,
                metadata
            FROM `{self.project_id}.{self.dataset}.events`
            WHERE id IN ({event_ids_str})
            LIMIT 100
            """

            query_job = self.bq_client.query(query)
            results = query_job.result()

            # Aggregate themes across all connecting events
            all_themes = []

            for row in results:
                metadata = row.metadata or {}
                gkg_data = metadata.get('gkg_data', {})

                # Handle both dict and potential string formats
                if isinstance(gkg_data, dict):
                    v2_themes = gkg_data.get('V2Themes', '')
                else:
                    # If gkg_data is a string (shouldn't be, but defensive)
                    v2_themes = ''

                # Parse themes
                event_themes = self.parse_gkg_themes(v2_themes)
                all_themes.extend(event_themes)

            # Deduplicate themes
            unique_themes = list(set(all_themes))

            # Categorize relationship
            category = self.categorize_relationship(unique_themes)

            # Add to edge data
            edge['data']['themes'] = unique_themes
            edge['data']['category'] = category

            logger.info(
                f"Enriched edge {edge['id']} with {len(unique_themes)} themes, category: {category}"
            )

            return edge

        except Exception as e:
            logger.error(f"Failed to enrich edge {edge.get('id')}: {e}", exc_info=True)

            # Return edge with empty themes on error (graceful degradation)
            edge['data']['themes'] = []
            edge['data']['category'] = 'other'
            return edge
