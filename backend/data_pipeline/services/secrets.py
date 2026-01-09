"""
Secret Manager client for retrieving API credentials.

Provides secure access to API keys and credentials stored in GCP Secret Manager.
Falls back to environment variables when Secret Manager is disabled.
"""
import os
import logging
from typing import Dict
from django.conf import settings

logger = logging.getLogger(__name__)


class SecretManagerClient:
    """
    Client for retrieving secrets from GCP Secret Manager or environment variables.

    Features:
    - In-memory caching to reduce API calls
    - Graceful fallback to environment variables
    - Clear error messages for missing secrets
    """

    # Class-level cache for secrets
    _cache: Dict[str, str] = {}

    def __init__(self):
        """Initialize Secret Manager client."""
        self.project_id = getattr(settings, 'GCP_PROJECT_ID', None)
        self.enabled = getattr(settings, 'SECRET_MANAGER_ENABLED', False)

        if self.enabled and not self.project_id:
            logger.warning(
                "SECRET_MANAGER_ENABLED=True but GCP_PROJECT_ID not set. "
                "Falling back to environment variables."
            )
            self.enabled = False

        # Only import GCP library if enabled (avoid dependency if not using)
        if self.enabled:
            try:
                from google.cloud import secretmanager
                self.client = secretmanager.SecretManagerServiceClient()
            except ImportError:
                logger.error(
                    "google-cloud-secret-manager not installed. "
                    "Install with: pip install google-cloud-secret-manager"
                )
                self.enabled = False
                self.client = None
        else:
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

        Note:
            Secrets are cached in memory after first retrieval to reduce API calls.
            Cache key includes version for proper versioning support.
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

    def set_secret(self, secret_id: str, value: str) -> None:
        """
        Create or update a secret in GCP Secret Manager.

        Args:
            secret_id: Secret identifier
            value: Secret value to store

        Raises:
            RuntimeError: If Secret Manager not enabled or operation fails

        Note:
            This creates a new version of the secret if it already exists.
            For local development, set environment variables instead.
        """
        if not self.enabled or not self.client:
            raise RuntimeError(
                "Secret Manager not enabled. Cannot set secrets. "
                "For local development, set environment variables instead."
            )

        from google.cloud import secretmanager

        parent = f"projects/{self.project_id}"

        # Try to create the secret (will fail if it already exists)
        try:
            secret = self.client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {
                        "replication": {"automatic": {}},
                    },
                }
            )
            logger.info(f"Created new secret '{secret_id}'")
        except Exception as e:
            # Secret already exists, that's fine
            logger.debug(f"Secret '{secret_id}' already exists: {e}")

        # Add a new version with the value
        secret_name = f"{parent}/secrets/{secret_id}"
        try:
            version = self.client.add_secret_version(
                request={
                    "parent": secret_name,
                    "payload": {"data": value.encode('UTF-8')},
                }
            )
            logger.info(f"Added new version to secret '{secret_id}': {version.name}")

            # Clear cache for this secret
            self._clear_cache(secret_id)
        except Exception as e:
            logger.error(f"Failed to add version to secret '{secret_id}': {e}")
            raise

    def _clear_cache(self, secret_id: str = None):
        """
        Clear secret cache.

        Args:
            secret_id: If provided, clear only this secret. Otherwise clear all.
        """
        if secret_id:
            # Clear all versions of this secret
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{secret_id}:")]
            for key in keys_to_remove:
                del self._cache[key]
            logger.debug(f"Cleared cache for secret '{secret_id}'")
        else:
            self._cache.clear()
            logger.debug("Cleared entire secret cache")
