-- BigQuery Schema for VenezuelaWatch Time-Series Data
-- Run with: bq query --use_legacy_sql=false < backend/config/bigquery_schema.sql
-- Prerequisites: Dataset must exist (bq mk --dataset --location=US venezuelawatch-staging:venezuelawatch_analytics)

-- 1. Events Table - Event time-series from Phase 1/3/4
CREATE TABLE IF NOT EXISTS `venezuelawatch-staging.venezuelawatch_analytics.events` (
    id STRING NOT NULL,
    title STRING,
    content STRING,
    source_url STRING NOT NULL,
    source_name STRING,
    event_type STRING,
    location STRING,
    risk_score FLOAT64,
    severity STRING,
    mentioned_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL,
    metadata JSON
)
PARTITION BY DATE(mentioned_at)
CLUSTER BY event_type, source_name
OPTIONS(
    description="Event time-series data from GDELT, ReliefWeb, and other sources"
);

-- 2. Entity Mentions Table - EntityMention time-series from Phase 6
CREATE TABLE IF NOT EXISTS `venezuelawatch-staging.venezuelawatch_analytics.entity_mentions` (
    id STRING NOT NULL,
    entity_id STRING NOT NULL,
    event_id STRING NOT NULL,
    mentioned_at TIMESTAMP NOT NULL,
    context STRING
)
PARTITION BY DATE(mentioned_at)
CLUSTER BY entity_id
OPTIONS(
    description="Entity mention records linking entities to events"
);

-- 3. FRED Indicators Table - FRED economic data from Phase 3
CREATE TABLE IF NOT EXISTS `venezuelawatch-staging.venezuelawatch_analytics.fred_indicators` (
    series_id STRING NOT NULL,
    date DATE NOT NULL,
    value FLOAT64,
    series_name STRING,
    units STRING
)
PARTITION BY date
CLUSTER BY series_id
OPTIONS(
    description="FRED economic indicators for Venezuela (oil prices, inflation, etc.)"
);

-- 4. UN Comtrade Table - UN Comtrade trade data from Phase 3
CREATE TABLE IF NOT EXISTS `venezuelawatch-staging.venezuelawatch_analytics.un_comtrade` (
    period DATE NOT NULL,
    reporter_code STRING NOT NULL,
    commodity_code STRING NOT NULL,
    trade_flow STRING NOT NULL,
    value_usd FLOAT64
)
PARTITION BY period
CLUSTER BY commodity_code
OPTIONS(
    description="UN Comtrade trade flow data (oil, food, medicine, machinery)"
);

-- 5. World Bank Table - World Bank indicators from Phase 3
CREATE TABLE IF NOT EXISTS `venezuelawatch-staging.venezuelawatch_analytics.world_bank` (
    indicator_id STRING NOT NULL,
    date DATE NOT NULL,
    value FLOAT64,
    country_code STRING
)
PARTITION BY date
CLUSTER BY indicator_id
OPTIONS(
    description="World Bank development indicators for Venezuela"
);
