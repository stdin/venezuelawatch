# Tasks package for data ingestion

# Import all tasks so they're registered with Celery autodiscovery
from data_pipeline.tasks.test_tasks import hello_world, add
from data_pipeline.tasks.gdelt_tasks import ingest_gdelt_events
from data_pipeline.tasks.reliefweb_tasks import ingest_reliefweb_updates
from data_pipeline.tasks.fred_tasks import ingest_fred_series, ingest_single_series

__all__ = [
    'hello_world',
    'add',
    'ingest_gdelt_events',
    'ingest_reliefweb_updates',
    'ingest_fred_series',
    'ingest_single_series',
]
