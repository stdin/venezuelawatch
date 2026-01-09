"""
Management command to test LLM integration with Claude.

Usage:
    python manage.py test_llm
    python manage.py test_llm --event-id=<uuid>
    python manage.py test_llm --sample
"""
import logging
from django.core.management.base import BaseCommand
from core.models import Event
from data_pipeline.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test LLM integration with Claude'

    def add_arguments(self, parser):
        parser.add_argument(
            '--event-id',
            type=str,
            help='Test with specific event ID'
        )
        parser.add_argument(
            '--sample',
            action='store_true',
            help='Use sample text instead of database events'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('LLM Integration Test (Claude via LiteLLM)'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

        # Check if API key is configured
        import os
        if not os.getenv('ANTHROPIC_API_KEY'):
            self.stdout.write(self.style.ERROR(
                'ANTHROPIC_API_KEY not set. Please configure in .env file.'
            ))
            self.stdout.write('Get your API key from: https://console.anthropic.com/')
            return

        if options['sample']:
            self._test_with_samples()
        elif options['event_id']:
            self._test_with_event(options['event_id'])
        else:
            self._test_with_samples()
            self._test_with_database_event()

    def _test_with_samples(self):
        """Test with sample texts."""
        self.stdout.write(self.style.SUCCESS('\n[Test 1] Enhanced Sentiment Analysis'))
        self.stdout.write('-' * 60)

        samples = [
            {
                'text': "Maduro's government claims economic recovery despite international skepticism",
                'context': {'source': 'GDELT', 'event_type': 'POLITICAL'}
            },
            {
                'text': "Venezuela faces severe humanitarian crisis as food shortages worsen",
                'context': {'source': 'RELIEFWEB', 'event_type': 'HUMANITARIAN'}
            },
            {
                'text': "Oil prices stabilize as Venezuela increases production capacity",
                'context': {'source': 'FRED', 'event_type': 'ECONOMIC'}
            }
        ]

        for i, sample in enumerate(samples, 1):
            self.stdout.write(f'\nSample {i}:')
            self.stdout.write(f'  Text: "{sample["text"]}"')
            self.stdout.write(f'  Context: {sample["context"]}')

            try:
                result = LLMClient.analyze_sentiment(
                    sample['text'],
                    context=sample['context']
                )

                self.stdout.write(self.style.SUCCESS('  ✓ Analysis complete:'))
                self.stdout.write(f'    Score: {result["score"]:.3f} ({result["label"]})')
                self.stdout.write(f'    Confidence: {result["confidence"]:.2f}')
                self.stdout.write(f'    Reasoning: {result["reasoning"]}')
                if result.get('nuances'):
                    self.stdout.write(f'    Nuances: {", ".join(result["nuances"])}')
                self.stdout.write(f'    Model: {result["model_used"]}')
                self.stdout.write(f'    Tokens: {result["tokens_used"]}')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Failed: {e}'))

        # Test summarization
        self.stdout.write(self.style.SUCCESS('\n\n[Test 2] Event Summarization'))
        self.stdout.write('-' * 60)

        long_content = """
        The Venezuelan government announced today that it has completed its defense plan
        amid escalating tensions with the United States. President Nicolas Maduro stated
        that the country is prepared to defend its sovereignty against any external threats.
        The announcement comes as the US has increased economic sanctions on Venezuela,
        targeting key sectors of the economy including oil and finance. International
        observers have expressed concern about the potential for military conflict,
        while humanitarian organizations warn that increased tensions could worsen
        the already dire humanitarian situation affecting millions of Venezuelans.
        """

        try:
            result = LLMClient.summarize_event(
                title="Venezuela Completes Defense Plan Amid US Tensions",
                content=long_content
            )

            self.stdout.write(self.style.SUCCESS('✓ Summarization complete:'))
            self.stdout.write(f'  Summary: {result["summary"]}')
            self.stdout.write(f'  Key Points:')
            for point in result['key_points']:
                self.stdout.write(f'    • {point}')
            self.stdout.write(f'  Urgency: {result["urgency"]}')
            self.stdout.write(f'  Model: {result["model_used"]}')
            self.stdout.write(f'  Tokens: {result["tokens_used"]}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed: {e}'))

        # Test relationship extraction
        self.stdout.write(self.style.SUCCESS('\n\n[Test 3] Relationship Extraction'))
        self.stdout.write('-' * 60)

        rel_text = "President Maduro met with Chinese President Xi Jinping to discuss PDVSA's oil exports to PetroChina"
        entities = ['Nicolás Maduro', 'Xi Jinping', 'PDVSA', 'PetroChina']

        try:
            result = LLMClient.extract_relationships(rel_text, entities)

            self.stdout.write(self.style.SUCCESS('✓ Relationship extraction complete:'))
            self.stdout.write(f'  Relationships found: {len(result.get("relationships", []))}')
            for rel in result.get('relationships', []):
                self.stdout.write(
                    f'    • {rel["subject"]} --[{rel["predicate"]}]--> {rel["object"]} '
                    f'(confidence: {rel["confidence"]:.2f})'
                )
            if result.get('themes'):
                self.stdout.write(f'  Themes: {", ".join(result["themes"])}')
            self.stdout.write(f'  Model: {result["model_used"]}')
            self.stdout.write(f'  Tokens: {result["tokens_used"]}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed: {e}'))

    def _test_with_database_event(self):
        """Test with a real event from database."""
        self.stdout.write(self.style.SUCCESS('\n\n[Test 4] Real Database Event'))
        self.stdout.write('-' * 60)

        try:
            event = Event.objects.order_by('-timestamp').first()
            if not event:
                self.stdout.write(self.style.WARNING('No events found in database'))
                return

            self._test_with_event(str(event.id))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to load event: {e}'))

    def _test_with_event(self, event_id: str):
        """Test with specific event."""
        try:
            event = Event.objects.get(id=event_id)

            self.stdout.write(f'\nEvent: {event.title[:80]}...')
            self.stdout.write(f'Source: {event.source}')
            self.stdout.write(f'Type: {event.event_type}')
            self.stdout.write(f'Timestamp: {event.timestamp}')

            # Test sentiment
            context = {
                'source': event.source,
                'event_type': event.event_type
            }

            result = LLMClient.analyze_sentiment(event.title, context=context)

            self.stdout.write(self.style.SUCCESS('\n✓ LLM Sentiment Analysis:'))
            self.stdout.write(f'  Score: {result["score"]:.3f} ({result["label"]})')
            self.stdout.write(f'  Confidence: {result["confidence"]:.2f}')
            self.stdout.write(f'  Reasoning: {result["reasoning"]}')
            if result.get('nuances'):
                self.stdout.write(f'  Nuances: {", ".join(result["nuances"])}')

            # Compare with VADER (if exists)
            if event.sentiment is not None:
                self.stdout.write(f'\nComparison with VADER:')
                self.stdout.write(f'  VADER score: {event.sentiment:.3f}')
                self.stdout.write(f'  Claude score: {result["score"]:.3f}')
                diff = abs(result["score"] - event.sentiment)
                self.stdout.write(f'  Difference: {diff:.3f}')

        except Event.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Event {event_id} not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Test failed: {e}'))
            import traceback
            traceback.print_exc()

        # Summary
        self.stdout.write(self.style.SUCCESS('\n\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('LLM Integration Test Complete'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
