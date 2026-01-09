/**
 * TypeScript interfaces for Risk Intelligence API
 *
 * These types match the backend Risk Intelligence API schema
 * defined in backend/docs/risk-intelligence-api.md
 */

/**
 * Sanctions match found in an event
 */
export interface SanctionsMatch {
  /** Name of the sanctioned entity */
  entity_name: string
  /** Type of entity */
  entity_type: 'person' | 'organization' | 'vessel' | 'other'
  /** Sanctions list the entity appears on (e.g., OFAC-SDN, UN-1267) */
  sanctions_list: string
  /** Confidence score of the match (0-1) */
  match_score: number
}

/**
 * Entities extracted from event content
 */
export interface EventEntities {
  /** People mentioned in the event */
  people: string[]
  /** Organizations mentioned in the event */
  organizations: string[]
  /** Locations mentioned in the event */
  locations: string[]
}

/**
 * Risk intelligence event with multi-dimensional risk analysis
 */
export interface RiskEvent {
  /** Unique event identifier */
  id: string
  /** Data source (e.g., GDELT, UN, Reuters) */
  source: string
  /** Event type (e.g., POLITICAL, ECONOMIC, TRADE) */
  event_type: string
  /** Event timestamp in ISO 8601 format */
  timestamp: string
  /** Event title */
  title: string
  /** LLM-generated summary */
  summary: string
  /** Flexible JSON content specific to event type */
  content: Record<string, any>
  /** Composite risk score (0-100) */
  risk_score: number
  /** NCISS-style severity classification */
  severity: 'SEV1_CRITICAL' | 'SEV2_HIGH' | 'SEV3_MEDIUM' | 'SEV4_LOW' | 'SEV5_MINIMAL'
  /** Sentiment score (-1 to 1, negative = higher risk) */
  sentiment: number
  /** Urgency level */
  urgency: 'immediate' | 'high' | 'medium' | 'low'
  /** Thematic tags for the event */
  themes: string[]
  /** Entities extracted from the event */
  entities: EventEntities
  /** Sanctions matches found in the event */
  sanctions_matches: SanctionsMatch[]
}

/**
 * Query parameters for filtering risk events
 */
export interface EventFilterParams {
  /** Comma-separated severity levels (e.g., "SEV1_CRITICAL,SEV2_HIGH") */
  severity?: string
  /** Minimum risk score (0-100) */
  min_risk_score?: number
  /** Maximum risk score (0-100) */
  max_risk_score?: number
  /** Filter to events with sanctions matches */
  has_sanctions?: boolean
  /** Filter by event type */
  event_type?: string
  /** Filter by data source */
  source?: string
  /** Lookback period in days (default: 30) */
  days_back?: number
  /** Page size (default: 100, max: 1000) */
  limit?: number
  /** Pagination offset (default: 0) */
  offset?: number
}

/**
 * Aggregate statistics on sanctions matches
 */
export interface SanctionsSummary {
  /** Total number of events with sanctions matches */
  total_events_with_sanctions: number
  /** Number of unique sanctioned entities found */
  unique_sanctioned_entities: number
  /** Breakdown by entity type (e.g., {person: 5, organization: 3}) */
  by_entity_type: Record<string, number>
  /** Breakdown by sanctions list (e.g., {"OFAC-SDN": 6, "UN-1267": 2}) */
  by_sanctions_list: Record<string, number>
}

/**
 * Entity extracted from events
 */
export interface Entity {
  id: string
  canonical_name: string
  entity_type: 'PERSON' | 'ORGANIZATION' | 'GOVERNMENT' | 'LOCATION'
  mention_count: number
  first_seen: string
  last_seen: string
  trending_score?: number
  trending_rank?: number
}

/**
 * Extended entity profile with sanctions and risk data
 */
export interface EntityProfile extends Entity {
  aliases: string[]
  metadata?: Record<string, any>
  sanctions_status: boolean
  risk_score?: number
  recent_events: Array<{
    id: string
    title: string
    source: string
    event_type: string
    risk_score?: number
    severity?: string
    timestamp: string
  }>
}

/**
 * Entity mention in an event
 */
export interface EntityMention {
  id: string
  raw_name: string
  match_score: number
  relevance?: number
  mentioned_at: string
  event_summary: {
    id: string
    title: string
    source: string
    event_type: string
    risk_score?: number
    severity?: string
    timestamp: string
  }
}

/**
 * Timeline of entity mentions
 */
export interface EntityTimeline {
  entity_id: string
  canonical_name: string
  total_mentions: number
  mentions: EntityMention[]
  time_range: {
    start: string
    end: string
  }
}

/**
 * Metric types for entity trending
 */
export type EntityMetric = 'mentions' | 'risk' | 'sanctions'

/**
 * Chat message with support for tool results
 */
export interface ChatMessage {
  /** Message role - user or assistant */
  role: 'user' | 'assistant'
  /** Message text content */
  content: string
  /** Tool results for assistant messages (optional) */
  toolResults?: Array<{
    toolName: string
    toolCallId: string
    result: any
  }>
}

/**
 * Tool call in assistant message
 */
export interface ToolCall {
  /** Tool identifier */
  id: string
  /** Tool name */
  name: string
  /** Tool input parameters as JSON */
  input: Record<string, any>
}

/**
 * Tool execution result
 */
export interface ToolResult {
  /** Tool call ID this result corresponds to */
  tool_use_id: string
  /** Result content as JSON */
  content: any
  /** Whether the tool call resulted in an error */
  is_error?: boolean
}
