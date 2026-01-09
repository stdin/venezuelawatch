"""
Base task classes for data ingestion.

Provides common functionality for all ingestion tasks including:
- Retry logic
- Error handling
- Success/failure hooks
- API credential retrieval
"""
from celery import Task
import logging

logger = logging.getLogger(__name__)


class BaseIngestionTask(Task):
    """
    Abstract base class for all data ingestion tasks.

    Provides common functionality:
    - Automatic retry on failure
    - Error logging
    - Success tracking
    - API credential management
    """

    # Retry configuration
    autoretry_for = (Exception,)
    max_retries = 3
    default_retry_delay = 60  # seconds

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Called when task fails after all retries.

        Args:
            exc: The exception raised
            task_id: Unique task ID
            args: Original task arguments
            kwargs: Original task keyword arguments
            einfo: Exception info object
        """
        logger.error(
            f"Task {self.name} [{task_id}] failed after {self.max_retries} retries",
            exc_info=exc,
            extra={
                'task_id': task_id,
                'task_name': self.name,
                'args': args,
                'kwargs': kwargs,
            }
        )

    def on_success(self, retval, task_id, args, kwargs):
        """
        Called when task succeeds.

        Args:
            retval: Task return value
            task_id: Unique task ID
            args: Original task arguments
            kwargs: Original task keyword arguments
        """
        logger.info(
            f"Task {self.name} [{task_id}] completed successfully",
            extra={
                'task_id': task_id,
                'task_name': self.name,
                'result': retval,
            }
        )

    def get_api_credential(self, key_name: str) -> str:
        """
        Retrieve API credential from Secret Manager or environment.

        Args:
            key_name: Name of the credential (e.g., 'fred-key', 'gdelt-key')

        Returns:
            The credential value

        Raises:
            ValueError: If credential not found
        """
        from data_pipeline.services.secrets import SecretManagerClient

        client = SecretManagerClient()
        secret_id = f'api-{key_name}'
        return client.get_secret(secret_id)
