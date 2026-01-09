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
from data_pipeline.tasks.fred_tasks import ingest_fred_series
from data_pipeline.tasks.comtrade_tasks import ingest_comtrade_trade_data
from data_pipeline.tasks.worldbank_tasks import ingest_worldbank_indicators

logger = logging.getLogger(__name__)

router = Router()


# Request/Response schemas
class GDELTTriggerRequest(Schema):
    lookback_minutes: int = 15


class ReliefWebTriggerRequest(Schema):
    lookback_days: int = 1


class FREDTriggerRequest(Schema):
    lookback_days: int = 7


class ComtradeTriggerRequest(Schema):
    lookback_months: int = 3


class WorldBankTriggerRequest(Schema):
    lookback_years: int = 2


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


@router.post("/trigger/fred", response=TaskTriggerResponse)
def trigger_fred_ingestion(request: HttpRequest, payload: FREDTriggerRequest):
    """
    Trigger FRED economic series ingestion task.

    Called by GCP Cloud Scheduler daily at 10 AM UTC.

    Args:
        payload: Request body with lookback_days parameter

    Returns:
        TaskTriggerResponse with task ID and status
    """
    logger.info(f"Triggering FRED ingestion (lookback: {payload.lookback_days} days)")

    try:
        # Dispatch Celery task asynchronously
        result = ingest_fred_series.delay(lookback_days=payload.lookback_days)

        return TaskTriggerResponse(
            status="dispatched",
            task_id=result.id,
            task_name="fred",
            message=f"FRED ingestion task dispatched with {payload.lookback_days} day lookback"
        )

    except Exception as e:
        logger.error(f"Failed to trigger FRED ingestion: {e}", exc_info=True)
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=500
        )


@router.post("/trigger/comtrade", response=TaskTriggerResponse)
def trigger_comtrade_ingestion(request: HttpRequest, payload: ComtradeTriggerRequest):
    """
    Trigger UN Comtrade trade data ingestion task.

    Called by GCP Cloud Scheduler monthly on the 1st at 2 AM UTC.

    Args:
        payload: Request body with lookback_months parameter

    Returns:
        TaskTriggerResponse with task ID and status
    """
    logger.info(f"Triggering Comtrade ingestion (lookback: {payload.lookback_months} months)")

    try:
        # Dispatch Celery task asynchronously
        result = ingest_comtrade_trade_data.delay(lookback_months=payload.lookback_months)

        return TaskTriggerResponse(
            status="dispatched",
            task_id=result.id,
            task_name="comtrade",
            message=f"Comtrade ingestion task dispatched with {payload.lookback_months} month lookback"
        )

    except Exception as e:
        logger.error(f"Failed to trigger Comtrade ingestion: {e}", exc_info=True)
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=500
        )


@router.post("/trigger/worldbank", response=TaskTriggerResponse)
def trigger_worldbank_ingestion(request: HttpRequest, payload: WorldBankTriggerRequest):
    """
    Trigger World Bank development indicators ingestion task.

    Called by GCP Cloud Scheduler quarterly on the 1st at 3 AM UTC.

    Args:
        payload: Request body with lookback_years parameter

    Returns:
        TaskTriggerResponse with task ID and status
    """
    logger.info(f"Triggering World Bank ingestion (lookback: {payload.lookback_years} years)")

    try:
        # Dispatch Celery task asynchronously
        result = ingest_worldbank_indicators.delay(lookback_years=payload.lookback_years)

        return TaskTriggerResponse(
            status="dispatched",
            task_id=result.id,
            task_name="worldbank",
            message=f"World Bank ingestion task dispatched with {payload.lookback_years} year lookback"
        )

    except Exception as e:
        logger.error(f"Failed to trigger World Bank ingestion: {e}", exc_info=True)
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
