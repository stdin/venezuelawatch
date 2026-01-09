# Tasks package for data ingestion

# Import all tasks so they're registered with Celery autodiscovery
from data_pipeline.tasks.test_tasks import hello_world, add
from data_pipeline.tasks.gdelt_tasks import ingest_gdelt_events
from data_pipeline.tasks.reliefweb_tasks import ingest_reliefweb_updates
from data_pipeline.tasks.fred_tasks import ingest_fred_series, ingest_single_series
from data_pipeline.tasks.comtrade_tasks import ingest_comtrade_trade_data
from data_pipeline.tasks.worldbank_tasks import ingest_worldbank_indicators
from data_pipeline.tasks.intelligence_tasks import (
    analyze_event_intelligence,
    batch_analyze_events,
    update_sentiment_scores,
    update_risk_scores,
    update_entities,
    batch_recalculate_risk_scores,
)
from data_pipeline.tasks.sanctions_tasks import (
    refresh_sanctions_screening,
    screen_event_sanctions,
)

__all__ = [
    'hello_world',
    'add',
    'ingest_gdelt_events',
    'ingest_reliefweb_updates',
    'ingest_fred_series',
    'ingest_single_series',
    'ingest_comtrade_trade_data',
    'ingest_worldbank_indicators',
    'analyze_event_intelligence',
    'batch_analyze_events',
    'update_sentiment_scores',
    'update_risk_scores',
    'update_entities',
    'batch_recalculate_risk_scores',
    'refresh_sanctions_screening',
    'screen_event_sanctions',
]
