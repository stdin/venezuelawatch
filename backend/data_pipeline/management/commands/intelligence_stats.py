"""
Management command to display risk intelligence statistics.

Provides overview of:
- Risk score coverage and distribution
- Severity classification distribution
- Sanctions match statistics
- Data quality metrics
"""
from django.core.management.base import BaseCommand
from core.models import Event, SanctionsMatch
from django.db.models import Avg, Max, Min, StdDev, Count, Q


class Command(BaseCommand):
    help = 'Display risk intelligence statistics'

    def handle(self, *args, **options):
        total_events = Event.objects.count()

        if total_events == 0:
            self.stdout.write(self.style.WARNING('No events in database'))
            return

        events_with_risk = Event.objects.filter(risk_score__isnull=False).count()
        events_with_severity = Event.objects.filter(severity__isnull=False).count()
        events_with_sanctions = Event.objects.filter(sanctions_matches__isnull=False).distinct().count()

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Risk Intelligence Statistics'))
        self.stdout.write('=' * 60 + '\n')

        # Overall coverage
        self.stdout.write(self.style.HTTP_INFO('Overall Coverage'))
        self.stdout.write(f'Total events: {total_events:,}')
        self.stdout.write(
            f'Events with risk scores: {events_with_risk:,} '
            f'({events_with_risk/total_events*100:.1f}%)'
        )
        self.stdout.write(
            f'Events with severity: {events_with_severity:,} '
            f'({events_with_severity/total_events*100:.1f}%)'
        )
        self.stdout.write(
            f'Events with sanctions matches: {events_with_sanctions:,} '
            f'({events_with_sanctions/total_events*100:.1f}%)'
        )

        # Severity distribution
        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(self.style.HTTP_INFO('Severity Distribution'))
        self.stdout.write('-' * 60)

        severity_levels = [
            'SEV1_CRITICAL',
            'SEV2_HIGH',
            'SEV3_MEDIUM',
            'SEV4_LOW',
            'SEV5_MINIMAL'
        ]

        for severity in severity_levels:
            count = Event.objects.filter(severity=severity).count()
            if events_with_severity > 0:
                pct = count / events_with_severity * 100
                self.stdout.write(f'{severity:15} {count:6,} events ({pct:5.1f}%)')
            else:
                self.stdout.write(f'{severity:15} {count:6,} events')

        # Risk score distribution
        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(self.style.HTTP_INFO('Risk Score Distribution'))
        self.stdout.write('-' * 60)

        risk_stats = Event.objects.filter(risk_score__isnull=False).aggregate(
            avg=Avg('risk_score'),
            max=Max('risk_score'),
            min=Min('risk_score'),
            stddev=StdDev('risk_score')
        )

        if risk_stats['avg']:
            self.stdout.write(f'Average:        {risk_stats["avg"]:.2f}')
            self.stdout.write(f'Min:            {risk_stats["min"]:.2f}')
            self.stdout.write(f'Max:            {risk_stats["max"]:.2f}')
            self.stdout.write(f'Std Deviation:  {risk_stats["stddev"]:.2f}')

            # Risk score ranges
            critical = Event.objects.filter(risk_score__gte=75).count()
            high = Event.objects.filter(risk_score__gte=50, risk_score__lt=75).count()
            medium = Event.objects.filter(risk_score__gte=25, risk_score__lt=50).count()
            low = Event.objects.filter(risk_score__lt=25).count()

            self.stdout.write('\nRisk Score Ranges:')
            self.stdout.write(f'  Critical (75-100): {critical:6,} events')
            self.stdout.write(f'  High (50-74):      {high:6,} events')
            self.stdout.write(f'  Medium (25-49):    {medium:6,} events')
            self.stdout.write(f'  Low (0-24):        {low:6,} events')
        else:
            self.stdout.write('No risk score data available')

        # Sanctions statistics
        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(self.style.HTTP_INFO('Sanctions Statistics'))
        self.stdout.write('-' * 60)

        total_matches = SanctionsMatch.objects.count()
        unique_entities = SanctionsMatch.objects.values('entity_name').distinct().count()

        self.stdout.write(f'Total sanctions matches: {total_matches:,}')
        self.stdout.write(f'Unique sanctioned entities: {unique_entities:,}')

        # By entity type
        self.stdout.write('\nBy Entity Type:')
        entity_types = SanctionsMatch.objects.values('entity_type').annotate(
            count=Count('id')
        ).order_by('-count')

        for item in entity_types:
            self.stdout.write(f'  {item["entity_type"]:20} {item["count"]:6,} matches')

        # By sanctions list
        self.stdout.write('\nBy Sanctions List:')
        sanctions_lists = SanctionsMatch.objects.values('sanctions_list').annotate(
            count=Count('id')
        ).order_by('-count')

        for item in sanctions_lists:
            self.stdout.write(f'  {item["sanctions_list"]:20} {item["count"]:6,} matches')

        # By source
        self.stdout.write('\n' + '-' * 60)
        self.stdout.write(self.style.HTTP_INFO('Events by Source'))
        self.stdout.write('-' * 60)

        sources = Event.objects.values('source').annotate(
            count=Count('id'),
            with_risk=Count('id', filter=Q(risk_score__isnull=False)),
            with_severity=Count('id', filter=Q(severity__isnull=False))
        ).order_by('-count')

        for item in sources:
            risk_pct = item['with_risk'] / item['count'] * 100 if item['count'] > 0 else 0
            sev_pct = item['with_severity'] / item['count'] * 100 if item['count'] > 0 else 0
            self.stdout.write(
                f'{item["source"]:15} {item["count"]:6,} events '
                f'({risk_pct:.0f}% risk, {sev_pct:.0f}% severity)'
            )

        self.stdout.write('\n' + '=' * 60 + '\n')
