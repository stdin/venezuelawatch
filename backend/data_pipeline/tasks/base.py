"""
Base task class for Celery ingestion tasks.

Provides common functionality for data pipeline tasks.
"""
from celery import Task


class BaseIngestionTask(Task):
    """
    Base class for data ingestion Celery tasks.

    Provides common configuration and error handling for all ingestion tasks.
    """

    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Error handler called when task fails.

        Override to add custom failure handling (notifications, etc.)
        """
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """
        Success handler called when task completes.

        Override to add custom success handling (metrics, etc.)
        """
        super().on_success(retval, task_id, args, kwargs)
