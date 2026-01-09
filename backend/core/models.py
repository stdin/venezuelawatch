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
        return f"{self.source} - {self.title[:50]}"
