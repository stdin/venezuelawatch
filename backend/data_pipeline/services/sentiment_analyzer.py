"""
Sentiment analysis service for event content.

Uses VADER (Valence Aware Dictionary and sEntiment Reasoner) for social media
and news text sentiment analysis. Returns sentiment scores from -1 (negative)
to +1 (positive).
"""
import logging
from typing import Optional, Dict, Any
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    VADER-based sentiment analyzer for event text.

    VADER is well-suited for news articles and social media text as it:
    - Handles capitalization, punctuation, and intensifiers
    - Understands negations and contractions
    - Works well on short to medium length texts
    """

    _analyzer: Optional[SentimentIntensityAnalyzer] = None

    @classmethod
    def get_analyzer(cls) -> SentimentIntensityAnalyzer:
        """
        Get or initialize the VADER sentiment analyzer (singleton pattern).

        Returns:
            SentimentIntensityAnalyzer instance
        """
        if cls._analyzer is None:
            cls._analyzer = SentimentIntensityAnalyzer()
            logger.info("VADER sentiment analyzer initialized")
        return cls._analyzer

    @classmethod
    def analyze_text(cls, text: str) -> float:
        """
        Analyze sentiment of text and return compound score.

        Args:
            text: Text to analyze (title, description, or content)

        Returns:
            Sentiment score from -1.0 (most negative) to +1.0 (most positive)
            - Positive sentiment: score >= 0.05
            - Neutral sentiment: -0.05 < score < 0.05
            - Negative sentiment: score <= -0.05
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for sentiment analysis")
            return 0.0

        analyzer = cls.get_analyzer()

        try:
            # Get polarity scores
            scores = analyzer.polarity_scores(text)

            # Return compound score (normalized weighted composite)
            compound_score = scores['compound']

            logger.debug(f"Sentiment analysis: '{text[:50]}...' -> {compound_score:.3f}")
            return compound_score

        except Exception as e:
            logger.error(f"Failed to analyze sentiment for text: {e}", exc_info=True)
            return 0.0

    @classmethod
    def analyze_event(cls, event: 'Event') -> float:
        """
        Analyze sentiment of an Event instance.

        Combines title and relevant content fields with weighted importance:
        - Title: 60% weight (most indicative of sentiment)
        - Description/summary: 30% weight
        - Full content: 10% weight (if available)

        Args:
            event: Event model instance

        Returns:
            Weighted sentiment score from -1.0 to +1.0
        """
        try:
            # Collect text components with weights
            components = []

            # Title (highest weight)
            if event.title:
                title_sentiment = cls.analyze_text(event.title)
                components.append((title_sentiment, 0.6))

            # Description or summary from content
            content_dict = event.content if isinstance(event.content, dict) else {}
            description = content_dict.get('description') or content_dict.get('summary')

            if description:
                desc_sentiment = cls.analyze_text(description)
                components.append((desc_sentiment, 0.3))

            # Full content text (if available and different from description)
            full_text = content_dict.get('text') or content_dict.get('body')
            if full_text and full_text != description:
                # Limit to first 500 characters to avoid overwhelming the analyzer
                full_text = full_text[:500]
                text_sentiment = cls.analyze_text(full_text)
                components.append((text_sentiment, 0.1))

            # Calculate weighted average
            if not components:
                logger.warning(f"No text content found for Event {event.id}")
                return 0.0

            # Normalize weights to sum to 1.0
            total_weight = sum(weight for _, weight in components)
            weighted_sentiment = sum(
                sentiment * (weight / total_weight)
                for sentiment, weight in components
            )

            logger.info(
                f"Event {event.id} sentiment: {weighted_sentiment:.3f} "
                f"(based on {len(components)} components)"
            )

            return round(weighted_sentiment, 4)

        except Exception as e:
            logger.error(f"Failed to analyze sentiment for Event {event.id}: {e}", exc_info=True)
            return 0.0

    @classmethod
    def get_sentiment_label(cls, score: float) -> str:
        """
        Convert sentiment score to human-readable label.

        Args:
            score: Sentiment score from -1.0 to +1.0

        Returns:
            Sentiment label: 'positive', 'neutral', or 'negative'
        """
        if score >= 0.05:
            return 'positive'
        elif score <= -0.05:
            return 'negative'
        else:
            return 'neutral'

    @classmethod
    def get_detailed_scores(cls, text: str) -> Dict[str, float]:
        """
        Get detailed sentiment breakdown for text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with keys:
            - neg: Negative sentiment proportion (0.0 to 1.0)
            - neu: Neutral sentiment proportion (0.0 to 1.0)
            - pos: Positive sentiment proportion (0.0 to 1.0)
            - compound: Overall sentiment score (-1.0 to +1.0)
        """
        if not text or not text.strip():
            return {'neg': 0.0, 'neu': 1.0, 'pos': 0.0, 'compound': 0.0}

        analyzer = cls.get_analyzer()

        try:
            scores = analyzer.polarity_scores(text)
            return scores
        except Exception as e:
            logger.error(f"Failed to get detailed sentiment scores: {e}", exc_info=True)
            return {'neg': 0.0, 'neu': 1.0, 'pos': 0.0, 'compound': 0.0}
