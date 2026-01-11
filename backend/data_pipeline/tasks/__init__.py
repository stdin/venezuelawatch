# Tasks package for data ingestion

# NOTE: Celery removed in Phase 18, replaced by Cloud Functions
# These imports kept for backward compatibility with deprecated API endpoints
# from data_pipeline.tasks.test_tasks import hello_world, add  # REMOVED: Celery dependency
# from data_pipeline.tasks.gdelt_sync_task import sync_gdelt_events  # REMOVED: Celery dependency
# from data_pipeline.tasks.reliefweb_tasks import ingest_reliefweb_updates  # REMOVED: Celery dependency
# from data_pipeline.tasks.fred_tasks import ingest_fred_series, ingest_single_series  # REMOVED: Celery dependency
# from data_pipeline.tasks.comtrade_tasks import ingest_comtrade_trade_data  # REMOVED: Celery dependency
# from data_pipeline.tasks.worldbank_tasks import ingest_worldbank_indicators  # REMOVED: Celery dependency
# from data_pipeline.tasks.intelligence_tasks import (  # REMOVED: Celery dependency
#     analyze_event_intelligence,
#     batch_analyze_events,
#     update_sentiment_scores,
#     update_risk_scores,
#     update_entities,
#     batch_recalculate_risk_scores,
#     batch_classify_severity,
# )
# from data_pipeline.tasks.sanctions_tasks import (  # REMOVED: Celery dependency
#     refresh_sanctions_screening,
#     screen_event_sanctions,
# )

# All tasks deprecated - Cloud Functions replaced Celery in Phase 18
__all__ = []
