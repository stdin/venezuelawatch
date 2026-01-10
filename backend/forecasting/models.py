from django.db import models
from django.utils import timezone


class ForecastResult(models.Model):
    """Cached forecast results from Vertex AI."""

    entity = models.ForeignKey(
        'core.Entity',
        on_delete=models.CASCADE,
        related_name='forecasts'
    )
    forecast_data = models.JSONField(
        help_text="Forecast points with ds, yhat, yhat_lower, yhat_upper"
    )
    dimensional_forecasts = models.JSONField(
        null=True,
        blank=True,
        help_text="Dimensional breakdowns (sanctions, political, economic)"
    )
    horizon_days = models.IntegerField(default=30)
    generated_at = models.DateTimeField(default=timezone.now)
    model_version = models.CharField(
        max_length=255,
        blank=True,
        help_text="Vertex AI model resource name"
    )

    class Meta:
        db_table = 'forecasting_forecastresult'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['entity', '-generated_at']),
        ]

    def is_stale(self, hours=24):
        """Check if forecast is older than threshold."""
        return timezone.now() - self.generated_at > timezone.timedelta(hours=hours)

    def __str__(self):
        return f"Forecast for {self.entity} ({self.generated_at})"
