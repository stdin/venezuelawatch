"""
Production settings for VenezuelaWatch.

This file extends the base settings.py with production-specific configuration.
Import this in production environments via:
    export DJANGO_SETTINGS_MODULE=config.settings_prod
"""
import os
from venezuelawatch.settings import *

# Security settings
DEBUG = False
SECRET_KEY = os.environ['SECRET_KEY']  # Must be set in production

# Allowed hosts - update with your production domain
ALLOWED_HOSTS = [
    'venezuelawatch.com',
    'www.venezuelawatch.com',
    'api.venezuelawatch.com',
    '.run.app',  # Cloud Run domains
]

# Database - expects DATABASE_URL environment variable
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,  # Require SSL for Cloud SQL
    )
}

# Celery configuration for production
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'default'

# Task execution settings
CELERY_TASK_ALWAYS_EAGER = False  # Execute tasks asynchronously
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_RESULT_EXPIRES = 3600  # Results expire after 1 hour
CELERY_TASK_RESULT_EXPIRES = 3600

# Worker settings
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Disable prefetching for long tasks
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # Restart worker after 1000 tasks

# Task routing (for future scaling)
CELERY_TASK_ROUTES = {
    'data_pipeline.tasks.gdelt.*': {'queue': 'realtime'},
    'data_pipeline.tasks.reliefweb.*': {'queue': 'realtime'},
    'data_pipeline.tasks.fred.*': {'queue': 'batch'},
    'data_pipeline.tasks.comtrade.*': {'queue': 'batch'},
    'data_pipeline.tasks.worldbank.*': {'queue': 'batch'},
}

# Static files - Google Cloud Storage
USE_GCS = True
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', 'venezuelawatch-static')
GS_DEFAULT_ACL = 'publicRead'
STATIC_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CORS configuration for production frontend
CORS_ALLOWED_ORIGINS = [
    'https://venezuelawatch.com',
    'https://www.venezuelawatch.com',
]
CORS_ALLOW_CREDENTIALS = True

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.sendgrid.net')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@venezuelawatch.com')

# Allauth settings for production
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
HEADLESS_FRONTEND_URLS = {
    "ACCOUNT_ACTIVATION_URL": "https://venezuelawatch.com/auth/verify/",
    "PASSWORD_RESET_URL": "https://venezuelawatch.com/auth/reset/",
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',  # JSON for Cloud Logging
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'data_pipeline': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# GCP Secret Manager - always enabled in production
SECRET_MANAGER_ENABLED = True
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')

# Cache configuration with Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'venezuelawatch',
        'TIMEOUT': 300,  # 5 minutes default
    }
}
