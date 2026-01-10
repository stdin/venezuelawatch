"""
Narrative Generator service using Claude API for relationship explanations.

Generates causal narratives explaining how entities are connected through events.
Follows Phase 26 research on structured prompting for causal reasoning.
"""
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from google.cloud import bigquery
from anthropic import Anthropic

from core.models import Entity

logger = logging.getLogger(__name__)


class NarrativeGenerator:
    """
    Service to generate LLM-based narratives explaining entity relationships.

    Uses Claude API with structured prompting to create causal explanations
    of how entities are connected through events.
    """

    def __init__(self):
        """Initialize with Anthropic client and BigQuery client."""
        # Initialize Anthropic client
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set. Narrative generation will fail.")
        self.anthropic_client = Anthropic(api_key=api_key) if api_key else None

        # Initialize BigQuery client
        self.bq_client = bigquery.Client()
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'venezuelawatch')
        self.dataset = 'venezuelawatch_data'

    def get_connecting_events(
        self,
        entity_a_id: str,
        entity_b_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query BigQuery for events where both entities are mentioned.

        Args:
            entity_a_id: First entity UUID
            entity_b_id: Second entity UUID
            limit: Maximum number of events to return

        Returns:
            List of event dicts with: id, title, event_timestamp, risk_score, severity, themes
        """
        try:
            # Query events where both entities appear in metadata.linked_entities
            # Note: This assumes entity linking has been done during ingestion
            query = f"""
            SELECT
                e.id,
                e.title,
                e.event_timestamp,
                e.risk_score,
                e.severity,
                e.themes,
                e.category
            FROM `{self.project_id}.{self.dataset}.events` e
            WHERE
                (
                    JSON_EXTRACT_SCALAR(e.metadata, '$.linked_entities') LIKE @entity_a
                    OR JSON_EXTRACT_SCALAR(e.metadata, '$.linked_entities') LIKE @entity_b
                )
                AND e.event_timestamp IS NOT NULL
            ORDER BY e.event_timestamp DESC
            LIMIT @limit
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("entity_a", "STRING", f"%{entity_a_id}%"),
                    bigquery.ScalarQueryParameter("entity_b", "STRING", f"%{entity_b_id}%"),
                    bigquery.ScalarQueryParameter("limit", "INT64", limit),
                ]
            )

            query_job = self.bq_client.query(query, job_config=job_config)
            results = query_job.result()

            events = []
            for row in results:
                events.append({
                    'id': row.id,
                    'title': row.title or 'Untitled Event',
                    'published_at': row.event_timestamp.isoformat() if row.event_timestamp else None,
                    'risk_score': float(row.risk_score) if row.risk_score else 0.0,
                    'severity': row.severity or 'UNKNOWN',
                    'themes': row.themes if row.themes else [],
                    'category': row.category or 'UNKNOWN'
                })

            logger.info(f"Found {len(events)} connecting events for entities {entity_a_id} and {entity_b_id}")
            return events

        except Exception as e:
            logger.error(f"Failed to query connecting events: {e}", exc_info=True)
            return []

    def generate_relationship_narrative(
        self,
        entity_a: Entity,
        entity_b: Entity,
        connecting_events: List[Dict[str, Any]]
    ) -> str:
        """
        Generate LLM narrative explaining relationship between two entities.

        Follows Phase 26 research guidance:
        - Structured prompting with event sequences
        - Explicit causal reasoning instructions
        - Event metadata (risk scores, severity, themes)
        - Request for evidence citations

        Args:
            entity_a: First entity
            entity_b: Second entity
            connecting_events: List of events connecting them

        Returns:
            Generated narrative (2-3 sentences)
        """
        if not self.anthropic_client:
            return "Narrative generation unavailable: API key not configured."

        if not connecting_events:
            return f"No direct connection found between {entity_a.canonical_name} and {entity_b.canonical_name}."

        # Sort events chronologically
        sorted_events = sorted(
            connecting_events,
            key=lambda e: e.get('published_at', '') or ''
        )

        # Build event context string with metadata
        event_context_lines = []
        for event in sorted_events[:10]:  # Limit to 10 most relevant
            published = event.get('published_at', 'Unknown date')
            if published != 'Unknown date':
                try:
                    dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    published = dt.strftime('%Y-%m-%d')
                except:
                    pass

            title = event.get('title', 'Untitled')
            risk = event.get('risk_score', 0)
            severity = event.get('severity', 'UNKNOWN')
            themes = event.get('themes', [])
            themes_str = ', '.join(themes[:3]) if themes else 'None'

            event_context_lines.append(
                f"- {published}: {title} (Risk: {risk:.0f}, Severity: {severity}, Themes: {themes_str})"
            )

        event_context = '\n'.join(event_context_lines)

        # Structured prompt following Phase 26 research
        prompt = f"""You are an intelligence analyst explaining how two entities are connected through events.

Entity A: {entity_a.canonical_name} ({entity_a.entity_type})
Entity B: {entity_b.canonical_name} ({entity_b.entity_type})

Connecting Events (chronological):
{event_context}

Generate a concise causal narrative (2-3 sentences) explaining:
1. HOW these entities are connected (direct relationship or indirect through events)
2. WHY this relationship matters (risk implications)
3. WHAT happened in sequence (causal chain)

Focus on causality, not just co-occurrence. Be specific about evidence from events.
Respond with only the narrative text, no preamble."""

        try:
            # Call Claude API
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            narrative = message.content[0].text.strip()
            logger.info(f"Generated narrative for {entity_a.canonical_name} <-> {entity_b.canonical_name}")
            return narrative

        except Exception as e:
            logger.error(f"Failed to generate narrative: {e}", exc_info=True)
            return f"Unable to generate narrative: {str(e)}"
