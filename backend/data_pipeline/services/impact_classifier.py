"""
Impact classifier service for event severity assessment.

Implements NCISS-style weighted multi-criteria severity scoring to classify events
into SEV1 (Critical) to SEV5 (Minimal) levels based on scope, duration,
reversibility, and economic impact.

Severity classification is independent of risk score:
- Severity = Impact assessment (how bad is it?)
- Risk = Probability × Impact (how likely × how bad?)
"""
import logging
from typing import Dict
from core.models import Event
from data_pipeline.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class ImpactClassifier:
    """
    Event severity classification using NCISS-style weighted scoring.

    Classifies events into SEV1 (Critical) to SEV5 (Minimal) based on
    multi-criteria assessment: scope, duration, reversibility, economic impact.

    Uses LLM for context-aware assessment (not keyword matching) to handle
    nuanced situations where identical terms have different severity levels
    (e.g., "economic crisis" could be SEV2-4 depending on actual impact).
    """

    # Criteria weights (MUST sum to 1.0 to prevent score inflation)
    WEIGHTS = {
        'scope': 0.35,              # Geographic/population reach
        'duration': 0.25,           # Time to resolve/impact
        'reversibility': 0.20,      # Can it be undone
        'economic_impact': 0.20,    # Financial cost/disruption
    }

    # Severity thresholds (0.0-1.0 score → SEV level)
    SEVERITY_THRESHOLDS = [
        (0.80, 'SEV1_CRITICAL'),
        (0.60, 'SEV2_HIGH'),
        (0.40, 'SEV3_MEDIUM'),
        (0.20, 'SEV4_LOW'),
        (0.00, 'SEV5_MINIMAL'),
    ]

    @classmethod
    def classify_severity(cls, event: Event) -> str:
        """
        Classify event severity using LLM-extracted criteria.

        Args:
            event: Event instance with title and content

        Returns:
            Severity level: 'SEV1_CRITICAL', 'SEV2_HIGH', 'SEV3_MEDIUM', 'SEV4_LOW', 'SEV5_MINIMAL'
        """
        # Extract criteria using LLM
        criteria = cls._extract_severity_criteria(event)

        # Calculate weighted severity score
        severity_score = sum(
            criteria.get(criterion, 0.5) * weight
            for criterion, weight in cls.WEIGHTS.items()
        )

        # Map to SEV level
        return cls._score_to_severity(severity_score)

    @classmethod
    def _extract_severity_criteria(cls, event: Event) -> Dict[str, float]:
        """
        Use LLM to assess severity criteria for event.

        Returns:
            {
                'scope': float (0.0=local, 0.5=national, 1.0=international),
                'duration': float (0.0=hours, 0.5=weeks, 1.0=months/permanent),
                'reversibility': float (0.0=easily reversed, 1.0=irreversible),
                'economic_impact': float (0.0=minimal, 0.5=moderate, 1.0=major disruption)
            }
        """
        llm = LLMClient()

        # Extract content description from Event.content JSONField
        description = ''
        if isinstance(event.content, dict):
            description = event.content.get('description', '')
            if not description:
                # Try other common keys
                description = event.content.get('summary', '')
            if not description:
                description = event.content.get('text', '')

        system_prompt = """You are an expert severity analyst for Venezuela intelligence.

Analyze events and rate each severity criterion on a 0.0-1.0 scale based on objective impact measures.

Respond with ONLY valid JSON (no markdown, no code fences):
{"scope": X.X, "duration": X.X, "reversibility": X.X, "economic_impact": X.X}"""

        user_prompt = f"""Analyze this Venezuela event and rate each severity criterion on a 0.0-1.0 scale:

Event: {event.title}
Description: {description}

Criteria:
1. **Scope** (geographic/population reach):
   - 0.0 = Local (city/region)
   - 0.5 = National (Venezuela-wide)
   - 1.0 = International (affects other countries/global markets)

2. **Duration** (time to resolve or impact persists):
   - 0.0 = Hours to days
   - 0.5 = Weeks to months
   - 1.0 = Months to years or permanent

3. **Reversibility** (can damage/changes be undone):
   - 0.0 = Easily reversed (policy can change back)
   - 0.5 = Difficult to reverse (structural changes needed)
   - 1.0 = Irreversible (deaths, destroyed infrastructure, permanent shifts)

4. **Economic Impact** (financial cost/disruption):
   - 0.0 = Minimal (<$1M or negligible disruption)
   - 0.5 = Moderate ($1M-$100M or sector disruption)
   - 1.0 = Major (>$100M or economy-wide disruption)

Return ONLY valid JSON (no markdown):
{{"scope": X.X, "duration": X.X, "reversibility": X.X, "economic_impact": X.X}}"""

        try:
            # Define JSON schema for structured output
            schema = {
                "type": "object",
                "properties": {
                    "scope": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "duration": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "reversibility": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "economic_impact": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0
                    }
                },
                "required": ["scope", "duration", "reversibility", "economic_impact"],
                "additionalProperties": False
            }

            response = llm._call_llm_structured(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                schema=schema,
                schema_name="severity_criteria",
                model=llm.FAST_MODEL,  # Use Haiku for cost efficiency
                temperature=0.2,
                max_tokens=200,
            )

            criteria = response['content']
            logger.info(
                f"LLM severity criteria for Event {event.id}: "
                f"scope={criteria['scope']:.2f}, duration={criteria['duration']:.2f}, "
                f"reversibility={criteria['reversibility']:.2f}, economic_impact={criteria['economic_impact']:.2f}"
            )
            return criteria

        except Exception as e:
            logger.warning(f"LLM severity extraction failed for Event {event.id}: {e}")
            # Fallback to medium severity (0.5) for all criteria
            return {criterion: 0.5 for criterion in cls.WEIGHTS.keys()}

    @staticmethod
    def _score_to_severity(score: float) -> str:
        """Map 0.0-1.0 score to SEV1-5 level."""
        for threshold, level in ImpactClassifier.SEVERITY_THRESHOLDS:
            if score >= threshold:
                return level
        return 'SEV5_MINIMAL'
