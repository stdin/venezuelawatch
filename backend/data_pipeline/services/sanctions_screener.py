"""
Sanctions screening service for detecting sanctioned entities.

Screens extracted entities against OFAC and OpenSanctions databases
using fuzzy matching to handle name variations, transliterations, and aliases.

Uses free OFAC API by default, with optional OpenSanctions premium support.
"""
import logging
import requests
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.utils import timezone

from core.models import Event, SanctionsMatch
from data_pipeline.services.secrets import SecretManagerClient

logger = logging.getLogger(__name__)


class SanctionsScreener:
    """
    Screen entities against sanctions lists with fuzzy matching.

    Supports:
    - OFAC SDN (Specially Designated Nationals) list
    - OpenSanctions consolidated database (premium, optional)
    - Fuzzy name matching for aliases and transliterations
    - Threshold-based match confidence (0.6-0.7)
    """

    # Fuzzy match threshold (0.6 for initial match, 0.7 for recording)
    MATCH_THRESHOLD = 0.6
    RECORD_THRESHOLD = 0.7

    # API timeout
    API_TIMEOUT = 10  # seconds

    def __init__(self):
        """Initialize sanctions screener with API credentials."""
        self.secret_client = SecretManagerClient()
        self.opensanctions_api_key = settings.OPENSANCTIONS_API_KEY

        # If API key is empty, use free OFAC API
        self.use_opensanctions = bool(self.opensanctions_api_key)

        if self.use_opensanctions:
            logger.info("Using OpenSanctions API for sanctions screening")
        else:
            logger.info("Using free OFAC API for sanctions screening")

    @classmethod
    def screen_event_entities(cls, event: Event) -> float:
        """
        Screen all entities in event against sanctions lists.

        Args:
            event: Event object with llm_analysis containing entities

        Returns:
            sanctions_score: 0.0 if clean, 1.0 if sanctioned entity found

        Side effects:
            Creates SanctionsMatch records for matches above threshold
        """
        screener = cls()

        # Extract entities from LLM analysis
        if not event.llm_analysis or 'entities' not in event.llm_analysis:
            logger.debug(f"Event {event.id} has no entity data to screen")
            return 0.0

        entities = event.llm_analysis.get('entities', {})
        people = entities.get('people', [])
        organizations = entities.get('organizations', [])

        logger.info(
            f"Screening event {event.id}: {len(people)} people, "
            f"{len(organizations)} organizations"
        )

        max_match_score = 0.0

        # Screen people
        for person in people:
            if isinstance(person, dict):
                name = person.get('name', '')
            else:
                # Handle simple string format
                name = str(person)

            if not name:
                continue

            matches = screener._check_person(name)
            for match in matches:
                if match['score'] > max_match_score:
                    max_match_score = match['score']

                # Record matches above threshold
                if match['score'] >= cls.RECORD_THRESHOLD:
                    screener._create_sanctions_match(
                        event=event,
                        entity_name=name,
                        entity_type='person',
                        match_data=match
                    )

        # Screen organizations
        for org in organizations:
            if isinstance(org, dict):
                name = org.get('name', '')
            else:
                name = str(org)

            if not name:
                continue

            matches = screener._check_organization(name)
            for match in matches:
                if match['score'] > max_match_score:
                    max_match_score = match['score']

                if match['score'] >= cls.RECORD_THRESHOLD:
                    screener._create_sanctions_match(
                        event=event,
                        entity_name=name,
                        entity_type='organization',
                        match_data=match
                    )

        # Binary score: any match above threshold = sanctioned
        sanctions_score = 1.0 if max_match_score >= cls.RECORD_THRESHOLD else 0.0

        logger.info(
            f"Event {event.id} sanctions screening complete. "
            f"Max match score: {max_match_score:.3f}, "
            f"Sanctions score: {sanctions_score}"
        )

        return sanctions_score

    def _check_person(self, name: str) -> List[Dict]:
        """
        Fuzzy match person name against sanctions lists.

        Args:
            name: Person's name to check

        Returns:
            List of matches: [{'score': float, 'list': str, 'data': dict}]
        """
        if self.use_opensanctions:
            return self._check_opensanctions(name, schema='Person')
        else:
            return self._check_ofac(name, entity_type='individual')

    def _check_organization(self, name: str) -> List[Dict]:
        """
        Fuzzy match organization name against sanctions lists.

        Args:
            name: Organization name to check

        Returns:
            List of matches: [{'score': float, 'list': str, 'data': dict}]
        """
        if self.use_opensanctions:
            return self._check_opensanctions(name, schema='Organization')
        else:
            return self._check_ofac(name, entity_type='entity')

    def _check_opensanctions(self, name: str, schema: str) -> List[Dict]:
        """
        Check name against OpenSanctions API with fuzzy matching.

        Args:
            name: Name to check
            schema: Entity schema ('Person' or 'Organization')

        Returns:
            List of matches with scores
        """
        url = f"{settings.OPENSANCTIONS_BASE_URL}/match/default"
        params = {
            'schema': schema,
            'properties.name': name,
            'threshold': self.MATCH_THRESHOLD
        }
        headers = {
            'Authorization': f'Bearer {self.opensanctions_api_key}'
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=self.API_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            matches = []

            # Parse OpenSanctions response
            for result in data.get('results', []):
                match = {
                    'score': result.get('score', 0.0),
                    'list': result.get('dataset', 'OPENSANCTIONS'),
                    'data': result
                }
                matches.append(match)

            logger.debug(f"OpenSanctions: '{name}' -> {len(matches)} matches")
            return matches

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenSanctions API error for '{name}': {e}")
            return []

    def _check_ofac(self, name: str, entity_type: str) -> List[Dict]:
        """
        Check name against OFAC SDN list (free API).

        Uses OFAC Sanctions List Search API with fuzzy matching.

        Args:
            name: Name to check
            entity_type: 'individual' or 'entity'

        Returns:
            List of matches with scores
        """
        # OFAC Sanctions Search API endpoint
        url = 'https://sanctionssearch.ofac.treas.gov/api/PublicationPreview/SdnList'

        try:
            response = requests.get(url, timeout=self.API_TIMEOUT)
            response.raise_for_status()

            data = response.json()
            matches = []

            # Search through SDN entries
            sdn_entries = data.get('sdnEntries', [])

            for entry in sdn_entries:
                entry_type = entry.get('sdnType', '').lower()
                entry_name = entry.get('name', '')

                # Filter by entity type
                type_match = (
                    (entity_type == 'individual' and entry_type == 'individual') or
                    (entity_type == 'entity' and entry_type != 'individual')
                )

                if not type_match:
                    continue

                # Calculate fuzzy match score
                score = self._calculate_name_similarity(name, entry_name)

                if score >= self.MATCH_THRESHOLD:
                    match = {
                        'score': score,
                        'list': 'OFAC-SDN',
                        'data': {
                            'name': entry_name,
                            'uid': entry.get('uid'),
                            'type': entry.get('sdnType'),
                            'programs': entry.get('programs', []),
                            'remarks': entry.get('remarks', '')
                        }
                    }
                    matches.append(match)

            logger.debug(f"OFAC: '{name}' ({entity_type}) -> {len(matches)} matches")
            return matches

        except requests.exceptions.RequestException as e:
            logger.error(f"OFAC API error for '{name}': {e}")
            return []

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate fuzzy similarity between two names.

        Uses simple normalized Levenshtein distance for name matching.
        Handles case-insensitive comparison and whitespace normalization.

        Args:
            name1: First name
            name2: Second name

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Normalize names
        n1 = name1.lower().strip()
        n2 = name2.lower().strip()

        # Exact match
        if n1 == n2:
            return 1.0

        # Check if one name contains the other (partial match)
        if n1 in n2 or n2 in n1:
            return 0.8

        # Calculate Levenshtein distance
        distance = self._levenshtein_distance(n1, n2)
        max_len = max(len(n1), len(n2))

        if max_len == 0:
            return 0.0

        # Normalize to 0-1 score
        similarity = 1.0 - (distance / max_len)

        return similarity

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein distance between two strings.

        Classic dynamic programming algorithm for edit distance.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Edit distance (number of operations)
        """
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)

        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Cost of insertions, deletions, or substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _create_sanctions_match(
        self,
        event: Event,
        entity_name: str,
        entity_type: str,
        match_data: Dict
    ) -> SanctionsMatch:
        """
        Create SanctionsMatch record for a detected match.

        Args:
            event: Event containing the entity
            entity_name: Name of the matched entity
            entity_type: 'person' or 'organization'
            match_data: Match data with score, list, and full data

        Returns:
            Created SanctionsMatch instance
        """
        sanctions_match = SanctionsMatch.objects.create(
            event=event,
            entity_name=entity_name,
            entity_type=entity_type,
            sanctions_list=match_data['list'],
            match_score=match_data['score'],
            sanctions_data=match_data['data'],
        )

        logger.info(
            f"Created SanctionsMatch: {entity_name} ({entity_type}) "
            f"matched {match_data['list']} with score {match_data['score']:.3f}"
        )

        return sanctions_match
