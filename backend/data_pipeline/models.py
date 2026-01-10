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
