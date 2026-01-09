# Tasks package for data ingestion

# Import all tasks so they're registered with Celery autodiscovery
from data_pipeline.tasks.test_tasks import hello_world, add

__all__ = ['hello_world', 'add']
