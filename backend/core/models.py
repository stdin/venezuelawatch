import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone


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
