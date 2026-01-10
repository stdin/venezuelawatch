-- BigQuery ETL query: PostgreSQL → BigQuery for Vertex AI Forecasting
-- Pulls entity risk data via EXTERNAL_QUERY (BigQuery Federated Query)
-- Aggregates daily and computes risk scores

-- NOTE: Replace PROJECT_ID and CONNECTION_ID before running
-- Usage: BigQuery Scheduled Query (daily 2 AM UTC)

CREATE OR REPLACE TABLE `intelligence.entity_risk_training_data` AS
WITH entity_mentions AS (
  SELECT
    entity_id,
    mentioned_at,
    event_id
  FROM EXTERNAL_QUERY(
    'projects/PROJECT_ID/locations/us-central1/connections/CONNECTION_ID',
    '''SELECT
         entity_id,
         mentioned_at,
         event_id
       FROM entity_mentions
       WHERE mentioned_at >= CURRENT_DATE - INTERVAL ''90 days'' '''
  )
),
events AS (
  SELECT
    id,
    risk_score
  FROM EXTERNAL_QUERY(
    'projects/PROJECT_ID/locations/us-central1/connections/CONNECTION_ID',
    '''SELECT
         id::text,
         risk_score
       FROM events
       WHERE risk_score IS NOT NULL'''
  )
)
SELECT
  CAST(em.entity_id AS STRING) as entity_id,
  TIMESTAMP(DATE(em.mentioned_at)) as mentioned_at,
  AVG(e.risk_score) as risk_score,
  -- Risk dimensions: Currently NULL (data not stored in PostgreSQL schema)
  -- Future: Extract from Event.llm_analysis JSON or add dedicated fields
  CAST(NULL AS FLOAT64) as sanctions_risk,
  CAST(NULL AS FLOAT64) as political_risk,
  CAST(NULL AS FLOAT64) as economic_risk,
  CAST(NULL AS FLOAT64) as supply_chain_risk
FROM entity_mentions em
JOIN events e ON CAST(e.id AS STRING) = CAST(em.event_id AS STRING)
WHERE e.risk_score IS NOT NULL
GROUP BY entity_id, DATE(em.mentioned_at)
ORDER BY entity_id, mentioned_at;
