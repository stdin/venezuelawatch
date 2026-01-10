-- Canonical Events Table
-- Platform design schema with 30+ core fields + enhancement arrays for Phase 26+
-- Partitioned by DATE(event_timestamp) for efficient time-series queries

CREATE TABLE IF NOT EXISTS `canonical_events` (
  -- Identity
  id STRING NOT NULL,
  source STRING,  -- 'gdelt' | 'acled' | 'world_bank' | 'google_trends' | 'sec_edgar' | 'fred' | 'un_comtrade'
  source_event_id STRING,
  source_url STRING,
  source_name STRING,

  -- Temporal
  event_timestamp TIMESTAMP NOT NULL,  -- When event occurred
  ingested_at TIMESTAMP,  -- When we ingested it
  created_at TIMESTAMP NOT NULL,

  -- Classification (10-category taxonomy)
  category STRING,  -- POLITICAL | CONFLICT | ECONOMIC | TRADE | REGULATORY | INFRASTRUCTURE | HEALTHCARE | SOCIAL | ENVIRONMENTAL | ENERGY
  subcategory STRING,  -- Finer-grain classification (source-specific code)
  event_type STRING,  -- Source-specific event type

  -- Location
  country_code STRING,  -- 'VE'
  admin1 STRING,  -- State/province
  admin2 STRING,  -- City/district
  latitude FLOAT64,
  longitude FLOAT64,
  location STRING,  -- Legacy field

  -- Magnitude
  magnitude_raw FLOAT64,  -- Native value (deaths, %, Goldstein, etc.)
  magnitude_unit STRING,  -- 'fatalities' | 'percent_change' | 'goldstein' | 'usd' | 'interest_score' | 'mentions'
  magnitude_norm FLOAT64,  -- 0-1 normalized

  -- Sentiment/Direction
  direction STRING,  -- POSITIVE | NEGATIVE | NEUTRAL
  tone_raw FLOAT64,  -- Native tone score if available
  tone_norm FLOAT64,  -- 0-1 normalized (1 = most negative)

  -- Confidence
  num_sources INT64,  -- Number of sources reporting
  source_credibility FLOAT64,  -- 0-1 source tier weight
  confidence FLOAT64,  -- 0-1 composite confidence

  -- Actors
  actor1_name STRING,
  actor1_type STRING,  -- GOVERNMENT | MILITARY | REBEL | CIVILIAN | CORPORATE
  actor2_name STRING,
  actor2_type STRING,

  -- Commodities/Sectors
  commodities ARRAY<STRING>,  -- ['OIL', 'GOLD', etc.]
  sectors ARRAY<STRING>,  -- ['ENERGY', 'MINING', etc.]

  -- Legacy fields (backward compatibility)
  title STRING,
  content STRING,
  risk_score FLOAT64,
  severity STRING,  -- P1 | P2 | P3 | P4

  -- Enhancement arrays (Phase 26+)
  -- These remain empty in Phase 25, populated in Phase 26+ without schema migration
  themes ARRAY<STRING>,  -- GKG V2Themes (2300+ categories)
  quotations ARRAY<STRUCT<
    speaker STRING,
    text STRING,
    offset INT64
  >>,  -- Who-said-what tracking
  gcam_scores STRUCT<
    fear FLOAT64,
    anger FLOAT64,
    joy FLOAT64,
    sadness FLOAT64,
    surprise FLOAT64,
    disgust FLOAT64
  >,  -- GCAM emotional dimensions
  entity_relationships ARRAY<STRUCT<
    entity1_id STRING,
    entity2_id STRING,
    relationship_type STRING
  >>,  -- Actor network graphs
  related_events ARRAY<STRUCT<
    event_id STRING,
    relationship_type STRING,
    timestamp TIMESTAMP
  >>,  -- Narrative lineage tracking

  -- Metadata (source-specific payloads, extensible)
  metadata JSON
)
PARTITION BY DATE(event_timestamp)
OPTIONS(
  description="Canonical event model for Venezuela risk intelligence. Core 30+ fields from platform design + enhancement arrays for Phase 26+.",
  require_partition_filter=true
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_category ON `canonical_events`(category);
CREATE INDEX IF NOT EXISTS idx_severity ON `canonical_events`(severity);
CREATE INDEX IF NOT EXISTS idx_source ON `canonical_events`(source);
CREATE INDEX IF NOT EXISTS idx_direction ON `canonical_events`(direction);
