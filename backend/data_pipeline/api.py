"""
Data pipeline API endpoints for task triggering and monitoring.

Provides HTTP endpoints for Cloud Scheduler to trigger Celery tasks.
"""
import logging
from typing import Optional, Dict, Any
from ninja import Router, Schema
from django.http import HttpRequest, JsonResponse

from data_pipeline.tasks.gdelt_tasks import ingest_gdelt_events
from data_pipeline.tasks.reliefweb_tasks import ingest_reliefweb_updates

logger = logging.getLogger(__name__)

router = Router()


# Request/Response schemas
class GDELTTriggerRequest(Schema):
    lookback_minutes: int = 15


class ReliefWebTriggerRequest(Schema):
    lookback_days: int = 1


class TaskTriggerResponse(Schema):
    status: str
    task_id: str
    task_name: str
    message: Optional[str] = None


@router.post("/trigger/gdelt", response=TaskTriggerResponse)
def trigger_gdelt_ingestion(request: HttpRequest, payload: GDELTTriggerRequest):
    """
    Trigger GDELT ingestion task.

    Called by GCP Cloud Scheduler every 15 minutes.

    Args:
        payload: Request body with lookback_minutes parameter

    Returns:
        TaskTriggerResponse with task ID and status
    """
    logger.info(f"Triggering GDELT ingestion (lookback: {payload.lookback_minutes} minutes)")

    try:
        # Dispatch Celery task asynchronously
        result = ingest_gdelt_events.delay(lookback_minutes=payload.lookback_minutes)

        return TaskTriggerResponse(
            status="dispatched",
            task_id=result.id,
            task_name="gdelt",
            message=f"GDELT ingestion task dispatched with {payload.lookback_minutes} minute lookback"
        )

    except Exception as e:
        logger.error(f"Failed to trigger GDELT ingestion: {e}", exc_info=True)
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=500
        )


@router.post("/trigger/reliefweb", response=TaskTriggerResponse)
def trigger_reliefweb_ingestion(request: HttpRequest, payload: ReliefWebTriggerRequest):
    """
    Trigger ReliefWeb ingestion task.

    Called by GCP Cloud Scheduler daily at 9 AM UTC.

    Args:
        payload: Request body with lookback_days parameter

    Returns:
        TaskTriggerResponse with task ID and status
    """
    logger.info(f"Triggering ReliefWeb ingestion (lookback: {payload.lookback_days} days)")

    try:
        # Dispatch Celery task asynchronously
        result = ingest_reliefweb_updates.delay(lookback_days=payload.lookback_days)

        return TaskTriggerResponse(
            status="dispatched",
            task_id=result.id,
            task_name="reliefweb",
            message=f"ReliefWeb ingestion task dispatched with {payload.lookback_days} day lookback"
        )

    except Exception as e:
        logger.error(f"Failed to trigger ReliefWeb ingestion: {e}", exc_info=True)
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=500
        )


@router.get("/health")
def health_check(request: HttpRequest):
    """
    Health check endpoint for Cloud Scheduler.

    Returns:
        Simple health status
    """
    return {"status": "healthy", "service": "data_pipeline"}
