"""
LLM client service using LiteLLM with Claude as primary provider.

Provides unified interface for:
- Enhanced sentiment analysis
- Event summarization
- Entity relationship extraction
- Explainable risk assessment
- Event classification
- Natural language Q&A
"""
import logging
import os
import json
import re
from typing import Dict, Any, Optional, List
from functools import lru_cache
import litellm
from litellm import completion, acompletion
from litellm.caching import Cache

from data_pipeline.services.secrets import SecretManagerClient

logger = logging.getLogger(__name__)

# Configure LiteLLM
litellm.set_verbose = False  # Disable verbose logging in production
litellm.drop_params = True   # Drop unsupported params instead of raising errors

# Enable Redis caching for cost optimization
try:
    litellm.cache = Cache(
        type="redis",
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        ttl=86400,  # 24 hour cache
    )
    logger.info("LiteLLM Redis caching enabled")
except Exception as e:
    logger.warning(f"Redis caching not available: {e}. Proceeding without cache.")


class LLMClient:
    """
    LLM client with Claude as primary provider and cost optimization.

    Features:
    - Automatic fallback to GPT-4 if Claude fails
    - Response caching (Redis)
    - Token usage tracking
    - Budget management
    - Rate limiting
    """

    _api_key: Optional[str] = None
    _initialized: bool = False

    # Model configurations (Claude 4.5 latest)
    PRIMARY_MODEL = "claude-sonnet-4-5-20250929"   # Best for complex reasoning
    FAST_MODEL = "claude-haiku-4-5-20251001"       # Fast, cost-effective
    PREMIUM_MODEL = "claude-opus-4-5-20251101"     # Most capable (use sparingly)

    # Budget limits
    MONTHLY_BUDGET_USD = 100.0

    @classmethod
    def initialize(cls):
        """
        Initialize LLM client with API keys from Secret Manager.

        Retrieves Anthropic API key and optional OpenAI fallback key.
        """
        if cls._initialized:
            return

        try:
            secret_client = SecretManagerClient()

            # Get Anthropic API key
            try:
                anthropic_key = secret_client.get_secret('anthropic-api-key')
                os.environ["ANTHROPIC_API_KEY"] = anthropic_key
                logger.info("Anthropic API key retrieved from Secret Manager")
            except ValueError:
                # Try environment variable
                anthropic_key = os.getenv("ANTHROPIC_API_KEY")
                if not anthropic_key:
                    logger.warning("No Anthropic API key found. LLM features will be limited.")

            # Get OpenAI API key for fallback (optional)
            try:
                openai_key = secret_client.get_secret('openai-api-key')
                os.environ["OPENAI_API_KEY"] = openai_key
                logger.info("OpenAI fallback API key retrieved")
            except ValueError:
                logger.info("No OpenAI fallback key configured (optional)")

            cls._initialized = True
            logger.info("LLM client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}", exc_info=True)
            cls._initialized = False

    @classmethod
    def _call_llm(
        cls,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Internal method to call LLM with automatic fallback.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (default: PRIMARY_MODEL)
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters for LiteLLM

        Returns:
            Dict with 'content', 'model', 'usage' keys
        """
        cls.initialize()

        if model is None:
            model = cls.PRIMARY_MODEL

        try:
            # Try primary model
            response = completion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            return {
                'content': response.choices[0].message.content,
                'model': response.model,
                'usage': {
                    'input_tokens': response.usage.prompt_tokens,
                    'output_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens,
                }
            }

        except Exception as e:
            logger.error(f"LLM call failed with {model}: {e}")

            # Try fallback if configured
            if os.getenv("OPENAI_API_KEY") and model != cls.FALLBACK_MODEL:
                logger.info(f"Attempting fallback to {cls.FALLBACK_MODEL}")
                try:
                    response = completion(
                        model=cls.FALLBACK_MODEL,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs
                    )

                    return {
                        'content': response.choices[0].message.content,
                        'model': response.model,
                        'usage': {
                            'input_tokens': response.usage.prompt_tokens,
                            'output_tokens': response.usage.completion_tokens,
                            'total_tokens': response.usage.total_tokens,
                        }
                    }
                except Exception as fallback_error:
                    logger.error(f"Fallback model also failed: {fallback_error}")
                    raise
            else:
                raise

    @classmethod
    def _call_llm_structured(
        cls,
        messages: List[Dict[str, str]],
        schema: Dict[str, Any],
        schema_name: str = "response",
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        strict: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call LLM with structured output using JSON schema.

        Uses native JSON schema support for Claude Sonnet 4.5 and Opus 4.5.
        Falls back to prompt-based approach for models without support (like Haiku).

        Args:
            messages: List of message dicts with 'role' and 'content'
            schema: JSON schema dict defining expected structure
            schema_name: Name for the schema
            model: Model to use (default: PRIMARY_MODEL)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            strict: Use strict schema validation (recommended for supported models)
            **kwargs: Additional parameters for LiteLLM

        Returns:
            Dict with 'content' (parsed dict), 'raw_content', 'model', 'usage' keys
        """
        cls.initialize()

        if model is None:
            model = cls.PRIMARY_MODEL

        # Determine if we should use native JSON schema or prompt-based approach
        # Claude Sonnet 4.5 and Opus 4.5 support native JSON schema
        supports_native_schema = model in [
            cls.PRIMARY_MODEL,    # claude-sonnet-4-5-20250929
            cls.PREMIUM_MODEL,    # claude-opus-4-5-20251101
        ]

        response_format = None
        if supports_native_schema:
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": strict,
                    "schema": schema
                }
            }
            logger.info(f"Using native JSON schema support for {model}")
        else:
            # Fallback: Add schema to prompt for models without native support (Haiku)
            logger.info(f"Model {model} using prompt-based JSON approach")
            messages = cls._add_schema_to_messages(messages, schema)

        try:
            response = completion(
                model=model,
                messages=messages,
                response_format=response_format,
                temperature=temperature,
                max_tokens=max_tokens,
                num_retries=2,  # Auto-retry on transient errors
                **kwargs
            )

            content_str = response.choices[0].message.content

            # Parse JSON - native schema should guarantee valid JSON
            try:
                content_dict = json.loads(content_str)
            except json.JSONDecodeError:
                # Robust parsing for prompt-based fallback
                logger.warning(f"JSON parse failed, using robust parser")
                content_dict = cls._parse_json_robust(content_str)

            return {
                'content': content_dict,
                'raw_content': content_str,
                'model': response.model,
                'usage': {
                    'input_tokens': response.usage.prompt_tokens,
                    'output_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens,
                }
            }

        except Exception as e:
            logger.error(f"Structured LLM call failed with {model}: {e}")

            # Try fallback if configured and not already using fallback
            if os.getenv("OPENAI_API_KEY") and "gpt" not in model.lower():
                logger.info("Attempting fallback to GPT-4")
                try:
                    return cls._call_llm_structured(
                        messages=messages,
                        schema=schema,
                        schema_name=schema_name,
                        model="gpt-4o",
                        temperature=temperature,
                        max_tokens=max_tokens,
                        strict=strict,
                        **kwargs
                    )
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")

            raise

    @classmethod
    def _parse_json_robust(cls, content: str) -> dict:
        """
        Robustly parse JSON from LLM response.

        Handles:
        - Markdown code fences (```json)
        - Leading/trailing whitespace
        - Text before/after JSON
        - Extracts first valid JSON object

        Args:
            content: Raw string response from LLM

        Returns:
            Parsed JSON dict

        Raises:
            ValueError: If no valid JSON found
        """
        import json
        import re

        content = content.strip()

        # Remove markdown code fences
        if content.startswith('```'):
            lines = content.split('\n')
            lines = lines[1:]  # Remove first line (```json or ```)
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]  # Remove last line (```)
            content = '\n'.join(lines).strip()

        # Try direct parse first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON object {...}
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Try to extract JSON array [...]
        array_match = re.search(r'\[.*\]', content, re.DOTALL)
        if array_match:
            try:
                return json.loads(array_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not extract valid JSON from response: {content[:200]}...")

    @classmethod
    def _add_schema_to_messages(
        cls,
        messages: List[Dict[str, str]],
        schema: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Add JSON schema to messages for models without native support.

        Adds schema specification to system message to guide prompt-based JSON generation.

        Args:
            messages: Original message list
            schema: JSON schema dict

        Returns:
            Updated message list with schema in system prompt
        """
        import json

        messages = messages.copy()
        schema_str = json.dumps(schema, indent=2)

        schema_instruction = f"""

IMPORTANT: You must respond with ONLY valid JSON matching this exact schema:

{schema_str}

Requirements:
- Respond with pure JSON only, no markdown code fences
- No text before or after the JSON
- All required fields must be present
- Follow the exact structure and types specified"""

        # Add to system message if exists, otherwise create one
        if messages and messages[0]['role'] == 'system':
            messages[0] = {
                'role': 'system',
                'content': messages[0]['content'] + schema_instruction
            }
        else:
            messages.insert(0, {
                'role': 'system',
                'content': f"You are a helpful AI assistant.{schema_instruction}"
            })

        return messages

    @classmethod
    def analyze_sentiment(cls, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Enhanced sentiment analysis with nuance and reasoning.

        Args:
            text: Text to analyze (title, description, or full content)
            context: Optional context (event type, source, timestamp)

        Returns:
            {
                'score': float (-1.0 to 1.0),
                'label': str ('positive', 'neutral', 'negative'),
                'confidence': float (0.0 to 1.0),
                'reasoning': str (explanation),
                'nuances': List[str] (detected nuances like sarcasm, skepticism)
            }
        """
        cls.initialize()

        system_prompt = """You are an expert sentiment analyzer specializing in political and economic news about Venezuela.

Your task is to analyze the sentiment of text and provide:
1. A sentiment score from -1.0 (very negative) to +1.0 (very positive)
2. A confidence level (0.0 to 1.0)
3. Brief reasoning for the score
4. Any detected nuances (sarcasm, skepticism, hope, fear, etc.)

Consider:
- Political context and implications
- Economic indicators and their impact
- Humanitarian concerns
- International relations
- Historical patterns

Respond in JSON format ONLY:
{
  "score": <float>,
  "label": "positive|neutral|negative",
  "confidence": <float>,
  "reasoning": "<brief explanation>",
  "nuances": ["<nuance1>", "<nuance2>"]
}"""

        context_str = ""
        if context:
            context_str = f"\nContext: Source={context.get('source')}, Type={context.get('event_type')}"

        user_prompt = f"""Analyze the sentiment of this text:{context_str}

Text: "{text}"

Provide your analysis in JSON format."""

        try:
            response = cls._call_llm(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=cls.PRIMARY_MODEL,
                temperature=0.2,
                max_tokens=300,
            )

            # Parse JSON response (strip markdown code fences if present)
            import json
            content = response['content'].strip()
            if content.startswith('```'):
                lines = content.split('\n')
                lines = lines[1:]  # Remove first line (```json or ```)
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]  # Remove last line (```)
                content = '\n'.join(lines).strip()

            result = json.loads(content)
            result['model_used'] = response['model']
            result['tokens_used'] = response['usage']['total_tokens']

            logger.info(f"LLM sentiment analysis: score={result['score']:.3f}, confidence={result['confidence']:.2f}")
            return result

        except Exception as e:
            logger.error(f"LLM sentiment analysis failed: {e}", exc_info=True)
            # Return neutral sentiment as fallback
            return {
                'score': 0.0,
                'label': 'neutral',
                'confidence': 0.0,
                'reasoning': f'Analysis failed: {str(e)}',
                'nuances': [],
                'model_used': 'error',
                'tokens_used': 0
            }

    @classmethod
    def summarize_event(cls, title: str, content: str, max_length: int = 200) -> Dict[str, Any]:
        """
        Generate concise summary of event content.

        Args:
            title: Event title
            content: Full event content (description, body, etc.)
            max_length: Maximum summary length in characters

        Returns:
            {
                'summary': str (concise summary),
                'key_points': List[str] (bullet points),
                'urgency': str ('low', 'medium', 'high', 'critical')
            }
        """
        cls.initialize()

        system_prompt = """You are an expert intelligence analyst specializing in Venezuela.

Generate a concise, informative summary that:
1. Captures the main point in 1-2 sentences
2. Extracts 2-3 key facts or implications
3. Assesses urgency level

Respond in JSON format ONLY:
{
  "summary": "<1-2 sentence summary>",
  "key_points": ["<point1>", "<point2>", "<point3>"],
  "urgency": "low|medium|high|critical"
}"""

        user_prompt = f"""Summarize this event:

Title: {title}

Content: {content[:2000]}

Provide a concise summary in JSON format."""

        try:
            response = cls._call_llm(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=cls.FAST_MODEL,  # Use Haiku for cost efficiency
                temperature=0.3,
                max_tokens=400,
            )

            import json
            content = response['content'].strip()
            if content.startswith('```'):
                lines = content.split('\n')
                lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                content = '\n'.join(lines).strip()

            result = json.loads(content)
            result['model_used'] = response['model']
            result['tokens_used'] = response['usage']['total_tokens']

            logger.info(f"Event summarized: {len(result['summary'])} chars, urgency={result['urgency']}")
            return result

        except Exception as e:
            logger.error(f"Event summarization failed: {e}", exc_info=True)
            return {
                'summary': title[:max_length],
                'key_points': [],
                'urgency': 'unknown',
                'model_used': 'error',
                'tokens_used': 0
            }

    @classmethod
    def extract_relationships(cls, text: str, entities: List[str]) -> Dict[str, Any]:
        """
        Extract relationships between entities mentioned in text.

        Args:
            text: Event text
            entities: List of entities already extracted

        Returns:
            {
                'relationships': [
                    {'subject': str, 'predicate': str, 'object': str, 'confidence': float}
                ],
                'themes': List[str] (overarching themes)
            }
        """
        cls.initialize()

        system_prompt = """You are an expert at extracting relationships between entities in political and economic news.

Given text and a list of entities, identify relationships between them.

Respond in JSON format ONLY:
{
  "relationships": [
    {"subject": "<entity1>", "predicate": "<relationship>", "object": "<entity2>", "confidence": <float>}
  ],
  "themes": ["<theme1>", "<theme2>"]
}"""

        entities_str = ", ".join(entities[:20])  # Limit to 20 entities
        user_prompt = f"""Extract relationships from this text:

Text: {text[:1500]}

Known entities: {entities_str}

Provide relationships in JSON format."""

        try:
            response = cls._call_llm(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=cls.PRIMARY_MODEL,
                temperature=0.2,
                max_tokens=600,
            )

            import json
            content = response['content'].strip()
            if content.startswith('```'):
                lines = content.split('\n')
                lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                content = '\n'.join(lines).strip()

            result = json.loads(content)
            result['model_used'] = response['model']
            result['tokens_used'] = response['usage']['total_tokens']

            logger.info(f"Extracted {len(result.get('relationships', []))} relationships")
            return result

        except Exception as e:
            logger.error(f"Relationship extraction failed: {e}", exc_info=True)
            return {
                'relationships': [],
                'themes': [],
                'model_used': 'error',
                'tokens_used': 0
            }

    @classmethod
    @lru_cache(maxsize=128)
    def get_usage_stats(cls) -> Dict[str, Any]:
        """
        Get token usage statistics (cached).

        Returns:
            {
                'total_tokens': int,
                'estimated_cost_usd': float,
                'calls_count': int
            }
        """
        # This would integrate with LiteLLM's tracking
        # For now, return placeholder
        return {
            'total_tokens': 0,
            'estimated_cost_usd': 0.0,
            'calls_count': 0
        }
