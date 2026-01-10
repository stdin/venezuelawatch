from ninja import Router
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from core.models import Entity
from .models import ForecastResult
from .services import VertexAIForecaster, InsufficientDataError, VertexAIError
from .schemas import ForecastResponse
import json

router = Router()


@router.post('/entities/{entity_id}/forecast', response=ForecastResponse)
def get_entity_forecast(request, entity_id: int, horizon_days: int = 30):
    """
    Get forecast for entity risk trajectory.

    Returns cached forecast if <24 hours old, otherwise generates new forecast.
    """
    entity = get_object_or_404(Entity, id=entity_id)

    # Check for recent cached forecast
    cached = ForecastResult.objects.filter(
        entity=entity,
        horizon_days=horizon_days,
        generated_at__gte=timezone.now() - timedelta(hours=24)
    ).first()

    if cached and not cached.is_stale(hours=24):
        return {
            'status': 'ready',
            'forecast': json.loads(cached.forecast_data) if isinstance(cached.forecast_data, str) else cached.forecast_data,
            'generated_at': cached.generated_at,
            'horizon_days': horizon_days,
        }

    # Generate new forecast
    try:
        forecaster = VertexAIForecaster()
        result = forecaster.forecast(entity_id, horizon_days)

        # Cache result
        ForecastResult.objects.create(
            entity=entity,
            forecast_data=result['forecast'],
            horizon_days=horizon_days,
            model_version=result['metadata']['model_version'],
        )

        return {
            'status': 'ready',
            'forecast': result['forecast'],
            'generated_at': timezone.now(),
            'horizon_days': horizon_days,
        }

    except InsufficientDataError as e:
        return {
            'status': 'insufficient_data',
            'horizon_days': horizon_days,
            'message': str(e),
        }

    except VertexAIError as e:
        return {
            'status': 'error',
            'horizon_days': horizon_days,
            'message': f"Forecast generation failed: {str(e)}",
        }
