"""
Comprehensive one-shot LLM intelligence analysis with hybrid GDELT scoring.

Uses Claude to analyze events in any language, extracting:
- Sentiment (score, label, reasoning, nuances)
- Summary (concise summary, key points)
- Entities (people, orgs, locations with roles)
- Relationships (entity relationships graph)
- Risk assessment (hybrid score combining GDELT quantitative + LLM qualitative)
- Themes and topics
- Urgency level
- Language detection

All in a single LLM API call for efficiency.
"""
import logging
import json
from typing import Dict, Any, Optional, List
from django.core.cache import cache
from django.conf import settings

from data_pipeline.services.llm_client import LLMClient
from data_pipeline.services.gdelt_quantitative_scorer import GdeltQuantitativeScorer

logger = logging.getLogger(__name__)


class LLMIntelligence:
    """
    Comprehensive intelligence analysis using hybrid GDELT + LLM scoring.

    Performs complete event analysis in one API call:
    - Multilingual support (Spanish, English, Arabic, Portuguese, etc.)
    - Sentiment analysis with cultural context
    - Entity extraction and relationship mapping
    - Hybrid risk scoring (GDELT quantitative + LLM qualitative)
    - Event summarization and key insights
    """

    # Cache TTL (24 hours)
    CACHE_TTL = 86400

    # GDELT scorer (class-level, reuse across calls)
    _gdelt_scorer = None

    @classmethod
    def get_gdelt_scorer(cls):
        """Get or create GDELT scorer with configured weights."""
        if cls._gdelt_scorer is None:
            weights = settings.HYBRID_SCORING.get('gdelt_weights')
            cls._gdelt_scorer = GdeltQuantitativeScorer(weights=weights)
        return cls._gdelt_scorer

    @classmethod
    def analyze_event_comprehensive(
        cls,
        title: str,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        model: str = "fast"  # "fast" (Haiku), "standard" (Sonnet), "premium" (Opus)
    ) -> Dict[str, Any]:
        """
        Perform comprehensive intelligence analysis with hybrid scoring.

        Now computes hybrid risk score combining GDELT quantitative signals
        with LLM qualitative analysis using configurable weights.

        Args:
            title: Event title
            content: Event content (description, body, etc.)
            context: Optional context (must include 'metadata' for GDELT scoring)
            model: Model tier to use ("fast", "standard", "premium")

        Returns:
            Intelligence analysis dict with hybrid risk score
        """
        # Check cache first
        cache_key = f"llm_intelligence:{hash(title + content + str(context) + model)}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("Using cached LLM intelligence result")
            return cached_result

        # Step 1: Compute GDELT quantitative score
        gdelt_score = None
        if context and 'metadata' in context:
            try:
                scorer = cls.get_gdelt_scorer()
                gdelt_score = scorer.score_event(context['metadata'])
                logger.info(f"GDELT quantitative score: {gdelt_score:.2f}")
            except Exception as e:
                logger.warning(f"GDELT scoring failed, proceeding with LLM-only: {e}")
                gdelt_score = None

        # Select model based on tier
        model_name = {
            "fast": LLMClient.FAST_MODEL,
            "standard": LLMClient.PRIMARY_MODEL,
            "premium": LLMClient.PREMIUM_MODEL
        }.get(model, LLMClient.PRIMARY_MODEL)

        # Define JSON schema for structured response
        schema = cls._get_intelligence_schema()

        # Build comprehensive analysis prompt (includes GDELT score)
        system_prompt = cls._build_system_prompt()
        user_prompt = cls._build_analysis_prompt(
            title, content, context, gdelt_score=gdelt_score
        )

        try:
            import time
            start_time = time.time()

            # Use structured output method with JSON schema
            response = LLMClient._call_llm_structured(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                schema=schema,
                schema_name="intelligence_analysis",
                model=model_name,
                temperature=0.3,
                max_tokens=2048,
                strict=True
            )

            processing_time = int((time.time() - start_time) * 1000)

            # Response is already parsed as dict from structured output
            result = response['content']

            # Step 2: Extract LLM qualitative risk score
            llm_risk_score = result['risk']['score'] * 100  # Convert 0-1 to 0-100

            # Step 3: Compute hybrid score using weighted average
            if gdelt_score is not None:
                weights = settings.HYBRID_SCORING['weights']
                hybrid_score = (
                    weights['gdelt'] * gdelt_score +
                    weights['llm'] * llm_risk_score
                )
                logger.info(
                    f"Hybrid score: {hybrid_score:.2f} "
                    f"(GDELT={gdelt_score:.2f} × {weights['gdelt']}, "
                    f"LLM={llm_risk_score:.2f} × {weights['llm']})"
                )
            else:
                # Fallback to LLM-only if GDELT scoring failed
                hybrid_score = llm_risk_score
                logger.warning("Using LLM-only score (GDELT unavailable)")

            # Step 4: Derive severity from hybrid score
            severity = cls._derive_severity(hybrid_score)

            # Update result with hybrid scoring
            result['risk']['score'] = hybrid_score / 100  # Store as 0-1 for consistency
            result['risk']['hybrid_score'] = hybrid_score  # Also store 0-100 version
            result['risk']['gdelt_score'] = gdelt_score
            result['risk']['llm_score'] = llm_risk_score
            result['risk']['severity'] = severity

            # Add metadata
            result['metadata'] = {
                'model_used': response['model'],
                'tokens_used': response['usage']['total_tokens'],
                'processing_time_ms': processing_time,
                'used_native_schema': model_name in [LLMClient.PRIMARY_MODEL, LLMClient.PREMIUM_MODEL],
                'scoring_method': 'hybrid' if gdelt_score is not None else 'llm_only'
            }

            # Cache result
            cache.set(cache_key, result, cls.CACHE_TTL)

            logger.info(
                f"Intelligence analysis complete: "
                f"hybrid_score={hybrid_score:.2f}, "
                f"severity={severity}, "
                f"sentiment={result['sentiment']['score']:.2f}, "
                f"entities={len(result['entities']['people']) + len(result['entities']['organizations'])}, "
                f"tokens={response['usage']['total_tokens']}, "
                f"time={processing_time}ms"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            return cls._get_fallback_result(title, content, f"JSON parse error: {str(e)}")

        except Exception as e:
            logger.error(f"LLM intelligence analysis failed: {e}", exc_info=True)
            return cls._get_fallback_result(title, content, str(e))

    @classmethod
    def _get_intelligence_schema(cls) -> Dict[str, Any]:
        """
        Get JSON schema for intelligence analysis response.

        Defines the complete structure for LLM structured output with strict validation.

        Returns:
            JSON schema dict with all required fields and types
        """
        return {
            "type": "object",
            "properties": {
                "sentiment": {
                    "type": "object",
                    "properties": {
                        "score": {
                            "type": "number",
                            "minimum": -1.0,
                            "maximum": 1.0,
                            "description": "Sentiment score from -1.0 (very negative) to +1.0 (very positive)"
                        },
                        "label": {
                            "type": "string",
                            "enum": ["positive", "neutral", "negative"],
                            "description": "Categorical sentiment label"
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Confidence level in the sentiment assessment"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Brief explanation for the sentiment score (1-2 sentences)"
                        },
                        "nuances": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Detected nuances like sarcasm, skepticism, hope, fear"
                        }
                    },
                    "required": ["score", "label", "confidence", "reasoning", "nuances"],
                    "additionalProperties": False
                },
                "summary": {
                    "type": "object",
                    "properties": {
                        "short": {
                            "type": "string",
                            "description": "1-2 sentence summary capturing the essence"
                        },
                        "key_points": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 3,
                            "maxItems": 5,
                            "description": "3-5 bullet points highlighting crucial information"
                        },
                        "full": {
                            "type": "string",
                            "description": "2-3 paragraph detailed summary (if content is substantial)"
                        }
                    },
                    "required": ["short", "key_points"],
                    "additionalProperties": False
                },
                "entities": {
                    "type": "object",
                    "properties": {
                        "people": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "role": {"type": "string"},
                                    "relevance": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                                },
                                "required": ["name", "role", "relevance"],
                                "additionalProperties": False
                            }
                        },
                        "organizations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "relevance": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                                },
                                "required": ["name", "type", "relevance"],
                                "additionalProperties": False
                            }
                        },
                        "locations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "relevance": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                                },
                                "required": ["name", "type", "relevance"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["people", "organizations", "locations"],
                    "additionalProperties": False
                },
                "relationships": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "subject": {"type": "string"},
                            "predicate": {"type": "string"},
                            "object": {"type": "string"},
                            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                        },
                        "required": ["subject", "predicate", "object", "confidence"],
                        "additionalProperties": False
                    }
                },
                "risk": {
                    "type": "object",
                    "properties": {
                        "score": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Risk score from 0.0 (no risk) to 1.0 (critical risk)"
                        },
                        "level": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "description": "Categorical risk level"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "2-3 sentences explaining the risk assessment"
                        },
                        "factors": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific risk factors identified"
                        },
                        "mitigation": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Suggested actions or areas to monitor"
                        }
                    },
                    "required": ["score", "level", "reasoning", "factors"],
                    "additionalProperties": False
                },
                "themes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Overarching themes (e.g., political_instability, humanitarian_crisis)"
                },
                "urgency": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "immediate"],
                    "description": "Time sensitivity and potential impact assessment"
                },
                "language": {
                    "type": "string",
                    "pattern": "^[a-z]{2}$",
                    "description": "ISO 639-1 language code (en, es, pt, ar, ru, zh, etc.)"
                }
            },
            "required": [
                "sentiment",
                "summary",
                "entities",
                "relationships",
                "risk",
                "themes",
                "urgency",
                "language"
            ],
            "additionalProperties": False
        }

    @classmethod
    def _build_system_prompt(cls) -> str:
        """Build comprehensive system prompt for intelligence analysis."""
        return """You are an expert intelligence analyst specializing in Venezuela and Latin America.

Your task is to perform comprehensive analysis of news events, reports, and intelligence data in ANY language (English, Spanish, Portuguese, Arabic, Russian, Chinese, etc.).

You must analyze and provide:

1. **Sentiment Analysis**
   - Score from -1.0 (very negative) to +1.0 (very positive)
   - Label: positive, neutral, negative
   - Confidence level (0.0 to 1.0)
   - Brief reasoning (1-2 sentences)
   - Nuances detected (sarcasm, skepticism, hope, fear, etc.)

2. **Summary**
   - Short: 1-2 sentence summary capturing the essence
   - Key points: 3-5 bullet points highlighting crucial information
   - Full: 2-3 paragraph detailed summary (if content is substantial)

3. **Entity Extraction**
   - People: Name, role/title, relevance score (0.0-1.0)
   - Organizations: Name, type, relevance score
   - Locations: Name, type (city/region/country), relevance score
   - Extract Venezuela-specific entities (Maduro, PDVSA, Caracas, etc.)

4. **Relationships**
   - Subject-predicate-object triples showing how entities relate
   - Confidence score for each relationship

5. **Risk Assessment**
   - Score from 0.0 (no risk) to 1.0 (critical risk)
   - Level: low, medium, high, critical
   - Reasoning (2-3 sentences explaining the assessment)
   - Factors: List of specific risk factors identified
   - Mitigation: Suggested actions or areas to monitor

6. **Themes and Topics**
   - Overarching themes (e.g., "political_instability", "humanitarian_crisis", "economic_sanctions")

7. **Urgency Level**
   - low, medium, high, immediate
   - Based on time sensitivity and potential impact

8. **Language Detection**
   - ISO 639-1 language code (en, es, pt, ar, ru, zh, etc.)

**Context Awareness:**
- Understand Venezuelan political context (Maduro government, opposition, sanctions)
- Recognize humanitarian crisis indicators (food shortages, migration, healthcare collapse)
- Identify economic factors (oil prices, inflation, trade, sanctions)
- Assess geopolitical relationships (US, Russia, China, Cuba, Colombia)

**Output Format:**
Respond ONLY with valid JSON matching this exact structure:

```json
{
  "sentiment": {
    "score": <float>,
    "label": "positive|neutral|negative",
    "confidence": <float>,
    "reasoning": "<explanation>",
    "nuances": ["<nuance1>", "<nuance2>"]
  },
  "summary": {
    "short": "<1-2 sentences>",
    "key_points": ["<point1>", "<point2>", "<point3>"],
    "full": "<2-3 paragraphs>"
  },
  "entities": {
    "people": [
      {"name": "<name>", "role": "<role>", "relevance": <float>}
    ],
    "organizations": [
      {"name": "<name>", "type": "<type>", "relevance": <float>}
    ],
    "locations": [
      {"name": "<name>", "type": "<city|region|country>", "relevance": <float>}
    ]
  },
  "relationships": [
    {"subject": "<entity1>", "predicate": "<relationship>", "object": "<entity2>", "confidence": <float>}
  ],
  "risk": {
    "score": <float>,
    "level": "low|medium|high|critical",
    "reasoning": "<explanation>",
    "factors": ["<factor1>", "<factor2>"],
    "mitigation": ["<action1>", "<action2>"]
  },
  "themes": ["<theme1>", "<theme2>"],
  "urgency": "low|medium|high|immediate",
  "language": "<iso-code>"
}
```

**Important:**
- Analyze in the original language, but respond in English JSON
- Be culturally aware and context-sensitive
- Provide objective analysis without political bias
- Extract Venezuelan-specific entities and relationships
- Consider historical context and patterns"""

    @classmethod
    def _derive_severity(cls, hybrid_score: float) -> str:
        """
        Derive SEV1-5 severity level from hybrid risk score.

        Args:
            hybrid_score: Hybrid score (0-100)

        Returns:
            Severity level: SEV1, SEV2, SEV3, SEV4, or SEV5
        """
        thresholds = settings.HYBRID_SCORING['severity_thresholds']

        if hybrid_score >= thresholds['SEV5']:
            return 'SEV5'  # Critical
        elif hybrid_score >= thresholds['SEV4']:
            return 'SEV4'  # High
        elif hybrid_score >= thresholds['SEV3']:
            return 'SEV3'  # Medium
        elif hybrid_score >= thresholds['SEV2']:
            return 'SEV2'  # Low
        else:
            return 'SEV1'  # Minimal

    @classmethod
    def _build_analysis_prompt(
        cls,
        title: str,
        content: str,
        context: Optional[Dict[str, Any]],
        gdelt_score: Optional[float] = None
    ) -> str:
        """
        Build user prompt for analysis (now includes GDELT score).

        Args:
            title: Event title
            content: Event content
            context: Optional context
            gdelt_score: Optional GDELT quantitative score (0-100)

        Returns:
            Analysis prompt with GDELT context
        """
        context_str = ""
        if context:
            context_parts = []
            if 'source' in context:
                context_parts.append(f"Source: {context['source']}")
            if 'event_type' in context:
                context_parts.append(f"Event Type: {context['event_type']}")
            if 'timestamp' in context:
                context_parts.append(f"Date: {context['timestamp']}")

            if context_parts:
                context_str = f"\n\nContext:\n" + "\n".join(f"- {part}" for part in context_parts)

        # Add GDELT quantitative score to prompt
        gdelt_str = ""
        if gdelt_score is not None:
            gdelt_str = f"""

**GDELT Quantitative Signals:**
The GDELT database has computed a quantitative risk score for this event based on:
- Goldstein scale (cooperation/conflict indicator)
- Tone/sentiment analysis
- Presence of CRISIS/PROTEST/CONFLICT themes
- Theme intensity

GDELT Risk Score: {gdelt_score:.1f}/100

You should consider this quantitative assessment alongside your qualitative analysis.
You may agree, disagree, or refine it based on the full context and nuances in the text."""

        # Limit content to 5000 chars to avoid excessive token usage
        content_truncated = content[:5000] if len(content) > 5000 else content

        return f"""Analyze this event and provide comprehensive intelligence:

**Title:** {title}

**Content:** {content_truncated}{context_str}{gdelt_str}

Provide your analysis in the exact JSON format specified in the system prompt."""

    @classmethod
    def _get_fallback_result(
        cls,
        title: str,
        content: str,
        error_message: str
    ) -> Dict[str, Any]:
        """Return fallback result when LLM fails."""
        return {
            'sentiment': {
                'score': 0.0,
                'label': 'neutral',
                'confidence': 0.0,
                'reasoning': f'Analysis failed: {error_message}',
                'nuances': []
            },
            'summary': {
                'short': title[:200],
                'key_points': [],
                'full': content[:500]
            },
            'entities': {
                'people': [],
                'organizations': [],
                'locations': []
            },
            'relationships': [],
            'risk': {
                'score': 0.5,
                'level': 'unknown',
                'reasoning': f'Analysis failed: {error_message}',
                'factors': [],
                'mitigation': []
            },
            'themes': [],
            'urgency': 'unknown',
            'language': 'unknown',
            'metadata': {
                'model_used': 'fallback',
                'tokens_used': 0,
                'processing_time_ms': 0
            }
        }

    @classmethod
    def analyze_event_model(
        cls,
        event: 'Event',
        model: str = "fast"
    ) -> Dict[str, Any]:
        """
        Analyze an Event model instance.

        Args:
            event: Event instance
            model: Model tier ("fast", "standard", "premium")

        Returns:
            Complete intelligence analysis dict
        """
        # Extract text content
        title = event.title or ""

        content_parts = []
        if isinstance(event.content, dict):
            for field in ['description', 'summary', 'body', 'text']:
                if field in event.content and event.content[field]:
                    content_parts.append(str(event.content[field]))

        content = ' '.join(content_parts) if content_parts else title

        # Build context (include metadata for GDELT scoring)
        context = {
            'source': event.source,
            'event_type': event.event_type,
            'timestamp': str(event.timestamp),
        }

        # Add metadata if available (for GDELT scoring)
        if hasattr(event, 'metadata') and event.metadata:
            context['metadata'] = event.metadata

        return cls.analyze_event_comprehensive(
            title=title,
            content=content,
            context=context,
            model=model
        )
