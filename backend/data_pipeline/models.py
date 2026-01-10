import uuid
from django.db import models


class MentionSpike(models.Model):
    """
    Stores detected mention spikes from GDELT eventmentions_partitioned table.

    A spike indicates unusual media attention to an event, calculated using
    rolling 7-day baseline (average and standard deviation).
    """

    # Link to BigQuery event (no ForeignKey - polyglot architecture)
    event_id = models.CharField(
        max_length=50,
        db_index=True,
        help_text="GLOBALEVENTID from BigQuery events"
    )

    # Spike timing
    spike_date = models.DateField(
        db_index=True,
        help_text="Date when spike occurred"
    )

    # Mention metrics
    mention_count = models.IntegerField(
        help_text="Actual mention count on spike date"
    )

    # Baseline statistics (7-day rolling window excluding current day)
    baseline_avg = models.FloatField(
        help_text="7-day rolling average of mentions"
    )
    baseline_stddev = models.FloatField(
        help_text="7-day rolling standard deviation of mentions"
    )

    # Spike metrics
    z_score = models.FloatField(
        db_index=True,
        help_text="Statistical significance: (count - avg) / stddev"
    )

    CONFIDENCE_CHOICES = [
        ('MEDIUM', 'Medium (z >= 2.0)'),
        ('HIGH', 'High (z >= 3.0)'),
        ('CRITICAL', 'Critical (z >= 4.0)'),
    ]

    confidence_level = models.CharField(
        max_length=10,
        choices=CONFIDENCE_CHOICES,
        help_text="Spike confidence level"
    )

    # Metadata
    detected_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When spike was detected and recorded"
    )

    class Meta:
        # Prevent duplicate spike records for same event on same date
        unique_together = [['event_id', 'spike_date']]

        # Composite indexes for common query patterns
        indexes = [
            # "Show me recent critical spikes" (descending z-score)
            models.Index(fields=['spike_date', '-z_score'], name='spike_date_zscore_idx'),

            # "Show me spikes by confidence level over time"
            models.Index(fields=['confidence_level', 'spike_date'], name='confidence_date_idx'),
        ]

        verbose_name = "Mention Spike"
        verbose_name_plural = "Mention Spikes"

    def __str__(self):
        return f"Spike for event {self.event_id} on {self.spike_date} (z={self.z_score:.2f})"


class CanonicalEntity(models.Model):
    """
    Canonical entity registry for cross-dataset entity linking.

    Stores the primary/canonical representation of entities (persons,
    organizations, governments, locations) mentioned across multiple data sources.
    """

    # Entity identification
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for canonical entity"
    )

    primary_name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Primary/canonical name for this entity"
    )

    ENTITY_TYPE_CHOICES = [
        ('person', 'Person'),
        ('organization', 'Organization'),
        ('government', 'Government'),
        ('location', 'Location'),
    ]

    entity_type = models.CharField(
        max_length=20,
        choices=ENTITY_TYPE_CHOICES,
        help_text="Type of entity"
    )

    # Geographic context
    country_code = models.CharField(
        max_length=2,
        null=True,
        blank=True,
        help_text="ISO 3166-1 alpha-2 country code for geographic filtering"
    )

    # Flexible additional data
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Flexible storage for additional entity data"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this canonical entity was created"
    )

    last_verified = models.DateTimeField(
        auto_now=True,
        help_text="Last time this entity record was updated/verified"
    )

    class Meta:
        indexes = [
            # Geographic filtering: "Show me all organizations in VE"
            models.Index(fields=['entity_type', 'country_code'], name='entity_type_country_idx'),

            # Name search
            models.Index(fields=['primary_name'], name='primary_name_idx'),
        ]

        verbose_name = "Canonical Entity"
        verbose_name_plural = "Canonical Entities"

    def __str__(self):
        return f"{self.primary_name} ({self.entity_type})"


class EntityAlias(models.Model):
    """
    Tracks name variations and aliases for canonical entities.

    Links different name representations from various data sources to their
    canonical entity, with confidence scores and resolution method tracking.
    """

    # Link to canonical entity
    canonical_entity = models.ForeignKey(
        CanonicalEntity,
        on_delete=models.CASCADE,
        related_name='aliases',
        help_text="The canonical entity this alias refers to"
    )

    # Alias details
    alias = models.CharField(
        max_length=255,
        db_index=True,
        help_text="The actual name variant/alias"
    )

    SOURCE_CHOICES = [
        ('gdelt', 'GDELT'),
        ('google_trends', 'Google Trends'),
        ('sec_edgar', 'SEC EDGAR'),
        ('world_bank', 'World Bank'),
    ]

    source = models.CharField(
        max_length=50,
        choices=SOURCE_CHOICES,
        help_text="Data source where this alias was found"
    )

    # Resolution metadata
    confidence = models.FloatField(
        db_index=True,
        help_text="Splink match_probability (0.0-1.0) or 1.0 for exact matches"
    )

    RESOLUTION_METHOD_CHOICES = [
        ('exact', 'Exact Match'),
        ('splink', 'Splink Probabilistic'),
        ('llm', 'LLM Disambiguation'),
    ]

    resolution_method = models.CharField(
        max_length=10,
        choices=RESOLUTION_METHOD_CHOICES,
        help_text="Method used to resolve this alias to canonical entity"
    )

    # Timestamps
    first_seen = models.DateTimeField(
        auto_now_add=True,
        help_text="When this alias was first encountered"
    )

    last_seen = models.DateTimeField(
        auto_now=True,
        help_text="Most recent encounter of this alias"
    )

    class Meta:
        # Each alias can appear only once per source
        unique_together = [['alias', 'source']]

        indexes = [
            # Alias lookups: "Find canonical entity for name 'PDVSA' from Google Trends"
            models.Index(fields=['alias'], name='alias_idx'),

            # Source-specific queries: "Show me all aliases from SEC EDGAR for this entity"
            models.Index(fields=['canonical_entity', 'source'], name='canonical_source_idx'),

            # Confidence filtering: "Show me high-confidence matches only"
            models.Index(fields=['confidence'], name='confidence_idx'),
        ]

        verbose_name = "Entity Alias"
        verbose_name_plural = "Entity Aliases"

    def __str__(self):
        return f"{self.alias} → {self.canonical_entity.primary_name} ({self.resolution_method})"
