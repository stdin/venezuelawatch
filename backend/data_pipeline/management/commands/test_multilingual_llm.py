"""
Management command to test multilingual LLM intelligence analysis.

Tests comprehensive analysis with Claude in multiple languages:
- Spanish (primary for Venezuela)
- Portuguese (Brazilian reports)
- English (international news)
- Arabic (Middle East perspective)

Usage:
    python manage.py test_multilingual_llm
"""
import logging
from django.core.management.base import BaseCommand
from data_pipeline.services.llm_intelligence import LLMIntelligence

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test multilingual LLM intelligence analysis'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('Multilingual LLM Intelligence Test'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        # Check if API key is configured
        import os
        if not os.getenv('ANTHROPIC_API_KEY'):
            self.stdout.write(self.style.ERROR(
                'ANTHROPIC_API_KEY not set. Please configure in .env file.'
            ))
            self.stdout.write('Get your API key from: https://console.anthropic.com/')
            return

        # Test samples in different languages
        samples = [
            {
                'language': 'Spanish',
                'title': 'Maduro anuncia nuevas medidas económicas ante crisis',
                'content': '''
                El presidente Nicolás Maduro anunció hoy un paquete de medidas económicas
                para enfrentar la crisis que afecta a Venezuela. Las medidas incluyen
                controles de precios más estrictos y la creación de una nueva moneda digital.
                Los expertos económicos expresan escepticismo sobre la efectividad de estas
                políticas, señalando que medidas similares en el pasado no lograron
                estabilizar la economía. La oposición criticó duramente el anuncio,
                argumentando que el gobierno evita abordar las causas estructurales
                de la crisis económica del país.
                ''',
                'context': {'source': 'SPANISH_NEWS', 'event_type': 'POLITICAL'}
            },
            {
                'language': 'Portuguese',
                'title': 'Brasil recebe milhares de refugiados venezuelanos',
                'content': '''
                O Brasil registrou a chegada de mais de 10 mil refugiados venezuelanos
                na última semana, segundo dados da Polícia Federal. A maioria entra
                pelo estado de Roraima, fugindo da crise humanitária que assola a
                Venezuela. As autoridades brasileiras estão trabalhando com organizações
                internacionais para fornecer abrigo e assistência básica aos refugiados.
                A situação coloca pressão adicional sobre os recursos do estado de
                Roraima, que já enfrenta desafios econômicos próprios.
                ''',
                'context': {'source': 'BRAZILIAN_NEWS', 'event_type': 'HUMANITARIAN'}
            },
            {
                'language': 'English',
                'title': 'US imposes new sanctions on Venezuelan oil sector',
                'content': '''
                The United States Treasury Department announced today comprehensive
                sanctions targeting Venezuela's state oil company PDVSA and its
                subsidiaries. The sanctions aim to pressure the Maduro government
                to restore democratic governance. However, humanitarian organizations
                warn that the sanctions could worsen the already dire humanitarian
                situation in Venezuela. The European Union expressed concerns about
                the potential humanitarian impact while supporting democratic transition.
                ''',
                'context': {'source': 'REUTERS', 'event_type': 'ECONOMIC'}
            },
            {
                'language': 'Arabic',
                'title': 'فنزويلا تعزز علاقاتها مع دول الشرق الأوسط',
                'content': '''
                أعلنت الحكومة الفنزويلية عن خطط لتعزيز العلاقات الاقتصادية والدبلوماسية
                مع دول الشرق الأوسط، في محاولة لتنويع شركائها التجاريين في ظل العقوبات
                الغربية. وقد أجرى الرئيس مادورو محادثات مع مسؤولين من عدة دول
                لمناقشة التعاون في قطاع النفط والطاقة. ويرى محللون أن هذا التوجه
                يهدف إلى تقليل اعتماد فنزويلا على الأسواق الغربية والبحث عن بدائل
                اقتصادية في آسيا والشرق الأوسط.
                ''',
                'context': {'source': 'AL_JAZEERA', 'event_type': 'DIPLOMATIC'}
            },
        ]

        for i, sample in enumerate(samples, 1):
            self.stdout.write(self.style.SUCCESS(f'\n[Test {i}] {sample["language"]} Analysis'))
            self.stdout.write('-' * 70)
            self.stdout.write(f'\nTitle: {sample["title"]}')
            self.stdout.write(f'Context: {sample["context"]}')
            self.stdout.write(f'\nContent preview: {sample["content"][:150]}...\n')

            try:
                # Perform comprehensive LLM analysis
                result = LLMIntelligence.analyze_event_comprehensive(
                    title=sample['title'],
                    content=sample['content'],
                    context=sample['context'],
                    model='fast'  # Use Haiku for testing
                )

                # Display results
                self.stdout.write(self.style.SUCCESS('\n✓ Analysis complete:'))

                # Language detection
                self.stdout.write(f'\n  Detected Language: {result["language"]}')

                # Sentiment
                sentiment = result['sentiment']
                self.stdout.write(f'\n  Sentiment:')
                self.stdout.write(f'    Score: {sentiment["score"]:.3f} ({sentiment["label"]})')
                self.stdout.write(f'    Confidence: {sentiment["confidence"]:.2f}')
                self.stdout.write(f'    Reasoning: {sentiment["reasoning"]}')
                if sentiment.get('nuances'):
                    self.stdout.write(f'    Nuances: {", ".join(sentiment["nuances"])}')

                # Summary
                summary = result['summary']
                self.stdout.write(f'\n  Summary:')
                self.stdout.write(f'    Short: {summary["short"]}')
                if summary.get('key_points'):
                    self.stdout.write(f'    Key Points:')
                    for point in summary['key_points']:
                        self.stdout.write(f'      • {point}')

                # Entities
                entities = result['entities']
                total_entities = (
                    len(entities.get('people', [])) +
                    len(entities.get('organizations', [])) +
                    len(entities.get('locations', []))
                )
                self.stdout.write(f'\n  Entities: {total_entities} total')
                if entities.get('people'):
                    self.stdout.write(f'    People: {len(entities["people"])}')
                    for person in entities['people'][:3]:
                        self.stdout.write(f'      • {person["name"]} ({person["role"]})')
                if entities.get('organizations'):
                    self.stdout.write(f'    Organizations: {len(entities["organizations"])}')
                    for org in entities['organizations'][:3]:
                        self.stdout.write(f'      • {org["name"]} ({org["type"]})')

                # Risk
                risk = result['risk']
                self.stdout.write(f'\n  Risk Assessment:')
                self.stdout.write(f'    Score: {risk["score"]:.3f} ({risk["level"]})')
                self.stdout.write(f'    Reasoning: {risk["reasoning"]}')
                if risk.get('factors'):
                    self.stdout.write(f'    Factors: {", ".join(risk["factors"][:3])}')

                # Themes and urgency
                self.stdout.write(f'\n  Themes: {", ".join(result["themes"][:5])}')
                self.stdout.write(f'  Urgency: {result["urgency"]}')

                # Metadata
                metadata = result['metadata']
                self.stdout.write(f'\n  Model: {metadata["model_used"]}')
                self.stdout.write(f'  Tokens: {metadata["tokens_used"]}')
                self.stdout.write(f'  Time: {metadata["processing_time_ms"]}ms')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'\n✗ Analysis failed: {e}'))
                import traceback
                traceback.print_exc()

        # Summary
        self.stdout.write(self.style.SUCCESS('\n\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('Multilingual Analysis Test Complete'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write('\nTested languages:')
        self.stdout.write('  ✓ Spanish (Español) - Primary language for Venezuela')
        self.stdout.write('  ✓ Portuguese (Português) - Brazilian perspective')
        self.stdout.write('  ✓ English - International news')
        self.stdout.write('  ✓ Arabic (العربية) - Middle East perspective')
        self.stdout.write('\nAll languages should be analyzed with equal accuracy.')
        self.stdout.write('Claude 4.5 Haiku provides multilingual support out of the box.\n')
