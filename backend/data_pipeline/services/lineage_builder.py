"""
Lineage builder service for temporal event chain analysis.

Builds chronological event sequences showing how events cascade over time,
with causal proximity heuristics and escalation detection.
"""
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from google.cloud import bigquery

logger = logging.getLogger(__name__)


class LineageBuilder:
    """
    Service to build temporal event lineages for entity relationships.

    Queries chronological event sequences, detects escalation patterns,
    and identifies causal chains through temporal proximity heuristics.
    """

    def __init__(self):
        """Initialize with BigQuery client."""
        self.bq_client = bigquery.Client()
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'venezuelawatch')
        self.dataset = 'venezuelawatch_data'

    def build_event_lineage(
        self,
        entity_a_id: str,
        entity_b_id: str,
        max_events: int = 20
    ) -> Dict[str, Any]:
        """
        Build temporal event lineage for two entities.

        Queries BigQuery for events where both entities appear, analyzes
        chronological sequence, detects escalation patterns, and identifies
        dominant themes.

        Args:
            entity_a_id: First entity UUID
            entity_b_id: Second entity UUID
            max_events: Maximum number of events to include

        Returns:
            Dictionary with:
                - events: List[EventNode] - Chronological event sequence
                - timeline_spans_days: int - Total time span
                - escalation_detected: bool - Risk scores trending up
                - dominant_themes: List[str] - Most frequent GKG themes
        """
        try:
            # Query BigQuery for events where both entities appear
            # Use parameterized query to prevent SQL injection
            query = f"""
            SELECT
                e.id,
                e.title,
                e.event_timestamp as published_at,
                e.risk_score,
                e.severity,
                e.metadata
            FROM `{self.project_id}.{self.dataset}.events` e
            WHERE
                (
                    JSON_EXTRACT_SCALAR(e.metadata, '$.linked_entities') LIKE @entity_a
                    OR JSON_EXTRACT_SCALAR(e.metadata, '$.linked_entities') LIKE @entity_b
                )
                AND e.event_timestamp IS NOT NULL
                AND e.risk_score IS NOT NULL
            ORDER BY e.event_timestamp ASC
            LIMIT @max_events
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("entity_a", "STRING", f"%{entity_a_id}%"),
                    bigquery.ScalarQueryParameter("entity_b", "STRING", f"%{entity_b_id}%"),
                    bigquery.ScalarQueryParameter("max_events", "INT64", max_events),
                ]
            )

            query_job = self.bq_client.query(query, job_config=job_config)
            results = query_job.result()

            # Build event nodes list
            events = []
            prev_timestamp = None
            all_themes = []

            for row in results:
                # Parse GKG themes from metadata
                metadata = row.metadata or {}
                gkg_data = metadata.get('gkg_data', {})
                v2_themes = gkg_data.get('V2Themes', '') if isinstance(gkg_data, dict) else ''

                # Parse themes (same logic as ThemeEnricher)
                event_themes = self._parse_themes(v2_themes)
                all_themes.extend(event_themes)

                # Calculate days since previous event
                days_since_prev = None
                if prev_timestamp and row.published_at:
                    time_diff = row.published_at - prev_timestamp
                    days_since_prev = time_diff.days

                # Build event node
                event_node = {
                    'id': row.id,
                    'title': row.title or 'Untitled Event',
                    'published_at': row.published_at.isoformat() if row.published_at else None,
                    'risk_score': float(row.risk_score) if row.risk_score else 0.0,
                    'severity': row.severity or 'UNKNOWN',
                    'themes': event_themes[:5],  # Limit to top 5 themes per event
                    'days_since_prev': days_since_prev
                }

                events.append(event_node)
                prev_timestamp = row.published_at

            # Calculate timeline span
            timeline_spans_days = 0
            if len(events) >= 2:
                first_date = datetime.fromisoformat(events[0]['published_at'].replace('Z', '+00:00'))
                last_date = datetime.fromisoformat(events[-1]['published_at'].replace('Z', '+00:00'))
                timeline_spans_days = (last_date - first_date).days

            # Detect escalation: Compare first vs last event risk scores
            escalation_detected = False
            if len(events) >= 2:
                first_risk = events[0]['risk_score']
                last_risk = events[-1]['risk_score']
                # Escalation if last risk is 20% higher than first
                escalation_detected = last_risk > first_risk * 1.2

            # Find dominant themes (most frequent)
            dominant_themes = self._get_dominant_themes(all_themes, top_n=5)

            logger.info(
                f"Built lineage with {len(events)} events, "
                f"span: {timeline_spans_days} days, "
                f"escalation: {escalation_detected}"
            )

            return {
                'events': events,
                'timeline_spans_days': timeline_spans_days,
                'escalation_detected': escalation_detected,
                'dominant_themes': dominant_themes
            }

        except Exception as e:
            logger.error(f"Failed to build event lineage: {e}", exc_info=True)
            # Return empty lineage on error
            return {
                'events': [],
                'timeline_spans_days': 0,
                'escalation_detected': False,
                'dominant_themes': []
            }

    def _parse_themes(self, v2_themes_string: str) -> List[str]:
        """
        Parse GKG V2Themes format.

        Format: "THEME1,offset1,offset2;THEME2,offset3,offset4"

        Args:
            v2_themes_string: Raw V2Themes string

        Returns:
            List of theme names
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

            return themes

        except Exception as e:
            logger.warning(f"Failed to parse themes: {e}")
            return []

    def _get_dominant_themes(self, all_themes: List[str], top_n: int = 5) -> List[str]:
        """
        Get most frequent themes from list.

        Args:
            all_themes: List of all theme mentions
            top_n: Number of top themes to return

        Returns:
            List of top N most frequent themes
        """
        if not all_themes:
            return []

        # Count theme frequencies
        theme_counts = {}
        for theme in all_themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1

        # Sort by frequency and return top N
        sorted_themes = sorted(
            theme_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [theme for theme, count in sorted_themes[:top_n]]
