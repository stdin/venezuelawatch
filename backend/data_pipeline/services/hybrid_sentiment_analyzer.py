"""
Hybrid sentiment analyzer combining VADER and Claude LLM.

Strategy:
- Use VADER for quick baseline sentiment
- Use Claude for complex cases (political language, sarcasm, nuanced sentiment)
- Fall back gracefully if LLM unavailable
- Cache LLM results to minimize costs
"""
import logging
import os
from typing import Dict, Any, Optional
from django.core.cache import cache

from data_pipeline.services.sentiment_analyzer import SentimentAnalyzer
from data_pipeline.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class HybridSentimentAnalyzer:
    """
    Hybrid sentiment analyzer with intelligent routing between VADER and Claude.

    Decision Logic:
    1. Always get VADER baseline (fast, free)
    2. Check if event needs LLM analysis:
       - Political language detected
       - VADER confidence low
       - Contains negations/sarcasm indicators
       - User explicitly requests LLM
    3. If LLM needed and available, enhance with Claude
    4. Cache LLM results (24 hours) to avoid re-analysis
    """

    # Keywords that indicate complex sentiment requiring LLM
    COMPLEX_KEYWORDS = {
        # Political language
        'claims', 'alleges', 'denies', 'refutes', 'despite', 'however',
        'skepticism', 'criticism', 'controversy', 'disputed',
        # Sarcasm/irony indicators
        'so-called', 'supposedly', 'apparently', 'allegedly',
        # Emotional nuance
        'hope', 'fear', 'anxiety', 'tension', 'optimism', 'pessimism',
    }

    # Cache TTL for LLM results (24 hours)
    CACHE_TTL = 86400

    @classmethod
    def analyze_text(
        cls,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        force_llm: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze sentiment with hybrid approach.

        Args:
            text: Text to analyze
            context: Optional context (source, event_type, etc.)
            force_llm: Force LLM usage regardless of heuristics

        Returns:
            {
                'score': float (-1.0 to 1.0),
                'label': str ('positive', 'neutral', 'negative'),
                'confidence': float (0.0 to 1.0),
                'method': str ('vader', 'llm', 'hybrid'),
                'reasoning': str (explanation if LLM used),
                'nuances': List[str] (detected nuances if LLM used),
                'vader_score': float (original VADER score),
                'llm_score': float (LLM score if used)
            }
        """
        # Step 1: Get VADER baseline
        vader_score = SentimentAnalyzer.analyze_text(text)
        vader_detailed = SentimentAnalyzer.get_detailed_scores(text)

        # Step 2: Determine if LLM needed
        needs_llm = force_llm or cls._needs_llm_analysis(text, vader_detailed, context)

        if not needs_llm:
            # Use VADER only
            return {
                'score': vader_score,
                'label': SentimentAnalyzer.get_sentiment_label(vader_score),
                'confidence': cls._estimate_vader_confidence(vader_detailed),
                'method': 'vader',
                'reasoning': None,
                'nuances': [],
                'vader_score': vader_score,
                'llm_score': None,
            }

        # Step 3: Check if LLM available
        if not cls._is_llm_available():
            logger.info("LLM not available, falling back to VADER")
            return {
                'score': vader_score,
                'label': SentimentAnalyzer.get_sentiment_label(vader_score),
                'confidence': cls._estimate_vader_confidence(vader_detailed),
                'method': 'vader_fallback',
                'reasoning': 'LLM unavailable',
                'nuances': [],
                'vader_score': vader_score,
                'llm_score': None,
            }

        # Step 4: Check cache
        cache_key = f"sentiment_llm:{hash(text + str(context))}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("Using cached LLM sentiment result")
            cached_result['vader_score'] = vader_score
            return cached_result

        # Step 5: Use LLM for enhanced analysis
        try:
            llm_result = LLMClient.analyze_sentiment(text, context=context)

            # Blend VADER and LLM scores (weighted average)
            # LLM gets 70% weight, VADER gets 30% (LLM more reliable)
            blended_score = (0.7 * llm_result['score']) + (0.3 * vader_score)

            result = {
                'score': blended_score,
                'label': llm_result['label'],
                'confidence': llm_result['confidence'],
                'method': 'hybrid',
                'reasoning': llm_result['reasoning'],
                'nuances': llm_result.get('nuances', []),
                'vader_score': vader_score,
                'llm_score': llm_result['score'],
                'model_used': llm_result.get('model_used'),
                'tokens_used': llm_result.get('tokens_used'),
            }

            # Cache result
            cache.set(cache_key, result, cls.CACHE_TTL)

            logger.info(
                f"Hybrid sentiment: VADER={vader_score:.3f}, "
                f"LLM={llm_result['score']:.3f}, Blended={blended_score:.3f}"
            )

            return result

        except Exception as e:
            logger.error(f"LLM sentiment analysis failed: {e}, falling back to VADER")
            return {
                'score': vader_score,
                'label': SentimentAnalyzer.get_sentiment_label(vader_score),
                'confidence': cls._estimate_vader_confidence(vader_detailed),
                'method': 'vader_fallback',
                'reasoning': f'LLM failed: {str(e)}',
                'nuances': [],
                'vader_score': vader_score,
                'llm_score': None,
            }

    @classmethod
    def analyze_event(
        cls,
        event: 'Event',
        force_llm: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of an Event instance with hybrid approach.

        Args:
            event: Event model instance
            force_llm: Force LLM usage

        Returns:
            Sentiment analysis dict (same format as analyze_text)
        """
        # Prepare context
        context = {
            'source': event.source,
            'event_type': event.event_type,
        }

        # Collect text components
        text_parts = []
        if event.title:
            text_parts.append(event.title)

        content_dict = event.content if isinstance(event.content, dict) else {}
        for field in ['description', 'summary', 'text', 'body']:
            if field in content_dict and content_dict[field]:
                # Limit to first 1000 chars to avoid excessive API costs
                text_parts.append(str(content_dict[field])[:1000])

        combined_text = ' '.join(text_parts)

        return cls.analyze_text(combined_text, context=context, force_llm=force_llm)

    @classmethod
    def _needs_llm_analysis(
        cls,
        text: str,
        vader_detailed: Dict[str, float],
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Determine if text needs LLM analysis.

        Triggers:
        1. Political/GDELT sources (often have nuance)
        2. Contains complex keywords
        3. VADER neutral but has emotional words (ambiguous)
        4. Very high neu score with non-zero pos/neg (mixed sentiment)
        """
        text_lower = text.lower()

        # Trigger 1: Political sources
        if context and context.get('source') in {'GDELT'}:
            if context.get('event_type') in {'POLITICAL', 'CONFLICT'}:
                return True

        # Trigger 2: Complex keywords
        if any(keyword in text_lower for keyword in cls.COMPLEX_KEYWORDS):
            logger.info("Complex keywords detected, using LLM")
            return True

        # Trigger 3: Mixed sentiment (high neutral + some pos/neg)
        if vader_detailed['neu'] > 0.7 and (vader_detailed['pos'] > 0.1 or vader_detailed['neg'] > 0.1):
            logger.info("Mixed sentiment detected, using LLM")
            return True

        # Trigger 4: Very short text (< 50 chars) is ambiguous
        if len(text) < 50:
            return False  # Too short for LLM to add value

        return False

    @classmethod
    def _is_llm_available(cls) -> bool:
        """Check if LLM is configured and available."""
        return bool(os.getenv('ANTHROPIC_API_KEY'))

    @classmethod
    def _estimate_vader_confidence(cls, vader_detailed: Dict[str, float]) -> float:
        """
        Estimate VADER confidence based on score distribution.

        High confidence: Strong pos or neg, low neutral
        Low confidence: High neutral, mixed pos/neg
        """
        compound = vader_detailed.get('compound', 0.0)
        neu = vader_detailed.get('neu', 1.0)
        pos = vader_detailed.get('pos', 0.0)
        neg = vader_detailed.get('neg', 0.0)

        # Strong sentiment = high confidence
        if abs(compound) > 0.5:
            return 0.8

        # High neutral = low confidence
        if neu > 0.8:
            return 0.3

        # Mixed sentiment = low confidence
        if pos > 0.2 and neg > 0.2:
            return 0.4

        return 0.6
