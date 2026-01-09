"""
Named Entity Recognition (NER) service for extracting entities from event content.

Uses spaCy's pre-trained English model to identify:
- PERSON: People, political figures, activists
- ORG: Companies, organizations, government agencies
- GPE: Countries, cities, regions (geopolitical entities)
- NORP: Nationalities, religious/political groups
"""
import logging
from typing import List, Dict, Set, Optional
import spacy
from spacy.language import Language

logger = logging.getLogger(__name__)


class EntityExtractor:
    """
    spaCy-based named entity recognition for event text.

    Extracts and categorizes entities relevant to Venezuela intelligence:
    - Political figures and leaders
    - Organizations and government agencies
    - Countries and regions
    - Companies and economic actors
    """

    _nlp: Optional[Language] = None

    # Entity types to extract
    ENTITY_TYPES = {'PERSON', 'ORG', 'GPE', 'NORP'}

    # Venezuela-specific entities to always include
    VENEZUELA_ENTITIES = {
        'venezuela', 'caracas', 'maracaibo', 'valencia',
        'maduro', 'guaidó', 'guaido',
        'pdvsa', 'citgo',
        'bolivar', 'petro',  # Currency names
    }

    @classmethod
    def get_nlp(cls) -> Language:
        """
        Get or load spaCy English language model (singleton pattern).

        Returns:
            spaCy Language model for English
        """
        if cls._nlp is None:
            try:
                cls._nlp = spacy.load('en_core_web_sm')
                logger.info("spaCy English model loaded successfully")
            except OSError:
                logger.error(
                    "spaCy model 'en_core_web_sm' not found. "
                    "Run: python -m spacy download en_core_web_sm"
                )
                raise

        return cls._nlp

    @classmethod
    def extract_entities(cls, text: str, max_entities: int = 50) -> List[str]:
        """
        Extract named entities from text.

        Args:
            text: Text to analyze (title, description, or content)
            max_entities: Maximum number of entities to return

        Returns:
            List of entity strings (deduplicated and sorted by importance)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for entity extraction")
            return []

        nlp = cls.get_nlp()
        entities: Set[str] = set()

        try:
            # Process text with spaCy
            doc = nlp(text[:5000])  # Limit to 5000 chars for performance

            # Extract entities of relevant types
            for ent in doc.ents:
                if ent.label_ in cls.ENTITY_TYPES:
                    # Clean and normalize entity text
                    entity_text = cls._normalize_entity(ent.text)

                    if entity_text and len(entity_text) > 1:
                        entities.add(entity_text)

            # Always include Venezuela-specific entities if mentioned
            text_lower = text.lower()
            for venezuela_entity in cls.VENEZUELA_ENTITIES:
                if venezuela_entity in text_lower:
                    entities.add(venezuela_entity.title())

            # Sort entities by relevance (longer names first, then alphabetically)
            sorted_entities = sorted(
                entities,
                key=lambda e: (-len(e), e.lower())
            )

            # Limit to max_entities
            result = sorted_entities[:max_entities]

            logger.debug(f"Extracted {len(result)} entities from text: {result[:5]}...")
            return result

        except Exception as e:
            logger.error(f"Failed to extract entities from text: {e}", exc_info=True)
            return []

    @classmethod
    def extract_event_entities(cls, event: 'Event', max_entities: int = 50) -> List[str]:
        """
        Extract entities from an Event instance.

        Combines entities from title and content fields with deduplication.

        Args:
            event: Event model instance
            max_entities: Maximum number of entities to return

        Returns:
            List of unique entity strings
        """
        try:
            all_entities: Set[str] = set()

            # Extract from title
            if event.title:
                title_entities = cls.extract_entities(event.title, max_entities=20)
                all_entities.update(title_entities)

            # Extract from content fields
            content_dict = event.content if isinstance(event.content, dict) else {}

            for field in ['description', 'summary', 'text', 'body']:
                if field in content_dict and content_dict[field]:
                    field_text = str(content_dict[field])
                    field_entities = cls.extract_entities(field_text, max_entities=30)
                    all_entities.update(field_entities)

            # Sort and limit
            sorted_entities = sorted(
                all_entities,
                key=lambda e: (-len(e), e.lower())
            )

            result = sorted_entities[:max_entities]

            logger.info(f"Event {event.id} entities: extracted {len(result)} entities")

            return result

        except Exception as e:
            logger.error(f"Failed to extract entities for Event {event.id}: {e}", exc_info=True)
            return []

    @classmethod
    def _normalize_entity(cls, entity_text: str) -> str:
        """
        Normalize entity text for consistency.

        - Remove extra whitespace
        - Title case (proper nouns)
        - Remove special characters

        Args:
            entity_text: Raw entity text from NER

        Returns:
            Normalized entity string
        """
        # Remove extra whitespace
        normalized = ' '.join(entity_text.split())

        # Remove leading/trailing punctuation
        normalized = normalized.strip('.,;:!?()[]{}"\'-')

        # Title case
        normalized = normalized.title()

        return normalized

    @classmethod
    def categorize_entities(cls, entities: List[str]) -> Dict[str, List[str]]:
        """
        Categorize extracted entities by type.

        Args:
            entities: List of entity strings

        Returns:
            Dictionary with entity categories:
            {
                'people': [...],
                'organizations': [...],
                'locations': [...],
                'other': [...]
            }
        """
        if not entities:
            return {'people': [], 'organizations': [], 'locations': [], 'other': []}

        nlp = cls.get_nlp()
        categorized = {
            'people': [],
            'organizations': [],
            'locations': [],
            'other': []
        }

        try:
            # Process all entities together for efficiency
            combined_text = ' | '.join(entities)
            doc = nlp(combined_text)

            entity_map = {}
            for ent in doc.ents:
                entity_map[ent.text] = ent.label_

            # Categorize each entity
            for entity in entities:
                label = entity_map.get(entity)

                if label == 'PERSON':
                    categorized['people'].append(entity)
                elif label in {'ORG', 'NORP'}:
                    categorized['organizations'].append(entity)
                elif label == 'GPE':
                    categorized['locations'].append(entity)
                else:
                    categorized['other'].append(entity)

        except Exception as e:
            logger.error(f"Failed to categorize entities: {e}", exc_info=True)

        return categorized

    @classmethod
    def filter_relevant_entities(cls, entities: List[str]) -> List[str]:
        """
        Filter entities to only those relevant to Venezuela intelligence.

        Removes:
        - Generic terms (e.g., "Today", "Wednesday")
        - Common words misidentified as entities
        - Duplicate variations

        Args:
            entities: List of entity strings

        Returns:
            Filtered list of relevant entities
        """
        # Common words often misidentified as entities
        COMMON_WORDS = {
            'today', 'yesterday', 'tomorrow', 'monday', 'tuesday', 'wednesday',
            'thursday', 'friday', 'saturday', 'sunday', 'january', 'february',
            'march', 'april', 'may', 'june', 'july', 'august', 'september',
            'october', 'november', 'december', 'am', 'pm', 'etc', 'via',
        }

        filtered = []

        for entity in entities:
            entity_lower = entity.lower()

            # Skip common words
            if entity_lower in COMMON_WORDS:
                continue

            # Skip very short entities (likely abbreviations or noise)
            if len(entity) < 2:
                continue

            # Skip entities that are all numbers
            if entity.replace(',', '').replace('.', '').isdigit():
                continue

            filtered.append(entity)

        return filtered
