from google.cloud import aiplatform
from django.conf import settings
import pandas as pd
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class VertexAIForecaster:
    """Service for generating forecasts via Vertex AI endpoint."""

    def __init__(self):
        aiplatform.init(
            project=settings.VERTEX_AI_PROJECT_ID,
            location=settings.VERTEX_AI_LOCATION
        )
        self.endpoint = aiplatform.Endpoint(settings.VERTEX_AI_ENDPOINT_ID)

    def forecast(self, entity_id: int, horizon_days: int = 30) -> Dict:
        """
        Generate forecast for entity.

        Args:
            entity_id: Entity ID to forecast
            horizon_days: Forecast horizon (default 30)

        Returns:
            Dict with 'forecast' (list of points) and 'metadata'

        Raises:
            InsufficientDataError: Less than 14 days of history
            VertexAIError: Prediction request failed
        """
        from core.models import EntityMention

        # Check data sufficiency (14 days minimum per RESEARCH.md)
        history_count = EntityMention.objects.filter(
            entity_id=entity_id
        ).values('mentioned_at__date').distinct().count()

        if history_count < 14:
            raise InsufficientDataError(
                f"Need 14 days of history, found {history_count}"
            )

        # Prepare prediction instance
        instances = [{
            'entity_id': str(entity_id),
        }]

        try:
            # Get predictions from Vertex AI
            prediction = self.endpoint.predict(instances=instances)

            # Parse response into forecast format
            forecast_points = []
            for pred in prediction.predictions[0].get('value', []):
                forecast_points.append({
                    'ds': pred.get('time'),  # Timestamp
                    'yhat': pred.get('value'),  # Predicted risk score
                    'yhat_lower': pred.get('prediction_interval_lower_bound'),
                    'yhat_upper': pred.get('prediction_interval_upper_bound'),
                })

            return {
                'forecast': forecast_points[:horizon_days],
                'metadata': {
                    'entity_id': entity_id,
                    'horizon_days': horizon_days,
                    'model_version': self.endpoint.resource_name,
                }
            }

        except Exception as e:
            logger.error(f"Vertex AI prediction failed for entity {entity_id}: {e}")
            raise VertexAIError(f"Prediction failed: {str(e)}")


class InsufficientDataError(Exception):
    """Raised when entity lacks minimum history for forecasting."""
    pass


class VertexAIError(Exception):
    """Raised when Vertex AI prediction request fails."""
    pass
