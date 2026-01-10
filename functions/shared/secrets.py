"""
GCP Secret Manager integration for Cloud Functions.

Retrieves API keys from Secret Manager with fallback to environment variables.
No Django dependencies.
"""
import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class SecretManagerClient:
    """Client for retrieving secrets from GCP Secret Manager or environment variables."""

    # Class-level cache for secrets
    _cache: Dict[str, str] = {}

    def __init__(self):
        """Initialize Secret Manager client."""
        self.project_id = os.environ.get('GCP_PROJECT_ID')

        if not self.project_id:
            logger.warning("GCP_PROJECT_ID not set, will use environment variables only")
            self.enabled = False
            self.client = None
        else:
            try:
                from google.cloud import secretmanager
                self.client = secretmanager.SecretManagerServiceClient()
                self.enabled = True
                logger.info("Secret Manager client initialized")
            except ImportError:
                logger.error("google-cloud-secret-manager not installed")
                self.enabled = False
                self.client = None

    def get_secret(self, secret_id: str, version: str = 'latest') -> str:
        """
        Retrieve a secret from Secret Manager or environment variables.

        Args:
            secret_id: Secret identifier (e.g., 'api-fred-key')
            version: Secret version (default: 'latest')

        Returns:
            The secret value as a string

        Raises:
            ValueError: If secret not found in Secret Manager or environment
        """
        cache_key = f"{secret_id}:{version}"

        # Check cache first
        if cache_key in self._cache:
            logger.debug(f"Retrieved secret '{secret_id}' from cache")
            return self._cache[cache_key]

        # Try Secret Manager if enabled
        if self.enabled and self.client:
            try:
                secret_value = self._get_from_secret_manager(secret_id, version)
                self._cache[cache_key] = secret_value
                logger.info(f"Retrieved secret '{secret_id}' from Secret Manager")
                return secret_value
            except Exception as e:
                logger.warning(
                    f"Failed to retrieve '{secret_id}' from Secret Manager: {e}. "
                    f"Falling back to environment variable."
                )

        # Fall back to environment variable
        # Convert secret_id to env var format: api-fred-key -> API_FRED_KEY
        env_var_name = secret_id.upper().replace('-', '_')
        secret_value = os.environ.get(env_var_name)

        if secret_value is None:
            raise ValueError(
                f"Secret '{secret_id}' not found in Secret Manager or environment. "
                f"Set environment variable {env_var_name} or add to Secret Manager."
            )

        self._cache[cache_key] = secret_value
        logger.info(f"Retrieved secret '{secret_id}' from environment variable {env_var_name}")
        return secret_value

    def _get_from_secret_manager(self, secret_id: str, version: str) -> str:
        """
        Retrieve secret from GCP Secret Manager.

        Args:
            secret_id: Secret identifier
            version: Secret version

        Returns:
            Secret value as string

        Raises:
            Exception: If secret not found or API call fails
        """
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"

        try:
            response = self.client.access_secret_version(request={"name": name})
            return response.payload.data.decode('UTF-8')
        except Exception as e:
            logger.error(f"Error accessing secret '{secret_id}' from Secret Manager: {e}")
            raise
