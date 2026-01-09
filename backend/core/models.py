import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone


class User(AbstractUser):
    """
    Custom user model with team-ready fields.

    Phase 2: Individual users (role='individual')
    Future: Add Team model with ForeignKey when team features needed
    """
    # Team-ready fields (nullable for backward compat when teams added)
    organization_name = models.CharField(max_length=200, blank=True, default='')
    role = models.CharField(
        max_length=50,
        default='individual',
        choices=[
            ('individual', 'Individual User'),
            ('team_member', 'Team Member'),
            ('team_admin', 'Team Admin'),
            ('org_admin', 'Organization Admin'),
        ]
    )

    # SaaS fields
    subscription_tier = models.CharField(
        max_length=50,
        default='free',
        choices=[
            ('free', 'Free'),
            ('pro', 'Professional'),
            ('enterprise', 'Enterprise'),
        ]
    )

    # User preferences
    timezone = models.CharField(max_length=50, default='UTC')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email or self.username


class Event(models.Model):
    """
    Time-series event data from multiple sources.
    Will be converted to TimescaleDB hypertable partitioned by timestamp.
    """
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Event metadata
    source = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Data source: GDELT, FRED, UN_COMTRADE, WORLD_BANK, RELIEFWEB, USITC, PORT_AUTHORITIES"
    )
    event_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Category: POLITICAL, ECONOMIC, TRADE, NATURAL_RESOURCE, TARIFF, DISASTER, etc."
    )

    # Time dimension (hypertable partition key)
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Event occurrence time (UTC)"
    )

    # Event content
    title = models.CharField(max_length=500)
    content = models.JSONField(
        help_text="Flexible event data structure varying by source"
    )

    # Analysis fields (populated by Phase 4-6)
    entities = ArrayField(
        models.CharField(max_length=200),
        blank=True,
        default=list,
        help_text="Extracted entities: people, companies, governments"
    )
    sentiment = models.FloatField(
        null=True,
        blank=True,
        help_text="Sentiment score from -1 (negative) to 1 (positive)"
    )
    risk_score = models.FloatField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Computed risk level (0-100)"
    )

    # Severity classification (SEV 1-5)
    severity = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        db_index=True,
        choices=[
            ('SEV1_CRITICAL', 'SEV1 - Critical'),
            ('SEV2_HIGH', 'SEV2 - High'),
            ('SEV3_MEDIUM', 'SEV3 - Medium'),
            ('SEV4_LOW', 'SEV4 - Low'),
            ('SEV5_MINIMAL', 'SEV5 - Minimal'),
        ],
        help_text="Event severity classification (SEV1=Critical to SEV5=Minimal)"
    )

    # LLM Intelligence fields (comprehensive analysis from Claude)
    summary = models.TextField(
        blank=True,
        null=True,
        help_text="LLM-generated concise summary (1-2 sentences)"
    )
    relationships = models.JSONField(
        blank=True,
        null=True,
        help_text="Entity relationships extracted by LLM (subject-predicate-object triples)"
    )
    themes = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        default=list,
        help_text="Thematic topics identified by LLM"
    )
    urgency = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        db_index=True,
        help_text="Urgency level: low, medium, high, immediate"
    )
    language = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Detected language code (ISO 639-1: en, es, ar, pt, etc.)"
    )
    llm_analysis = models.JSONField(
        blank=True,
        null=True,
        help_text="Complete LLM analysis results (for debugging and reference)"
    )

    # Record metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'events'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'source']),
            models.Index(fields=['-timestamp', 'event_type']),
            models.Index(fields=['-timestamp', 'risk_score']),
        ]

    def __str__(self):
        severity_str = f" [{self.severity}]" if self.severity else ""
        return f"{self.source} - {self.title[:50]}{severity_str}"


class SanctionsMatch(models.Model):
    """
    Records sanctions list matches for entities mentioned in events.
    Tracks sanctioned individuals and organizations with fuzzy match scores.
    """
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationship to event
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='sanctions_matches',
        help_text="Event containing the sanctioned entity"
    )

    # Matched entity details
    entity_name = models.CharField(
        max_length=200,
        help_text="Name matched from event's extracted entities"
    )
    entity_type = models.CharField(
        max_length=50,
        help_text="Type of entity: person, organization"
    )

    # Sanctions list information
    sanctions_list = models.CharField(
        max_length=100,
        help_text="Source sanctions list: OFAC-SDN, UN-1267, EU-SANCTIONS, etc."
    )
    match_score = models.FloatField(
        help_text="Fuzzy match confidence score (0.0-1.0)"
    )

    # Full sanctions data from API
    sanctions_data = models.JSONField(
        help_text="Complete API response with aliases, dates, programs, etc."
    )

    # Timestamps for data freshness tracking
    sanctions_checked_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this sanctions check was performed"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sanctions_matches'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event', '-match_score']),
            models.Index(fields=['-sanctions_checked_at']),
        ]

    def __str__(self):
        return f"{self.entity_name} ({self.sanctions_list}) - {self.match_score:.2f}"
