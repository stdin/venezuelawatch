import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from '../lib/api'
import type { RiskEvent, EventFilterParams } from '../lib/types'

interface UseRiskEventsOptions {
  /** Poll interval in milliseconds for live updates */
  pollInterval?: number
}

interface UseRiskEventsReturn {
  /** Fetched events or null if not yet loaded */
  events: RiskEvent[] | null
  /** Loading state */
  loading: boolean
  /** Error state */
  error: Error | null
  /** Manually refetch events */
  refetch: () => void
}

/**
 * React hook for fetching and optionally polling risk intelligence events
 *
 * @param filters - Optional filters to apply to the event query
 * @param options - Optional configuration including poll interval
 * @returns Object containing events, loading state, error, and refetch function
 *
 * @example
 * // Fetch high-severity events
 * const { events, loading, error } = useRiskEvents({
 *   severity: 'SEV1_CRITICAL,SEV2_HIGH',
 *   days_back: 7
 * })
 *
 * @example
 * // Fetch with live polling every 30 seconds
 * const { events, loading, error } = useRiskEvents(
 *   { has_sanctions: true },
 *   { pollInterval: 30000 }
 * )
 */
export function useRiskEvents(
  filters?: EventFilterParams,
  options?: UseRiskEventsOptions
): UseRiskEventsReturn {
  const [events, setEvents] = useState<RiskEvent[] | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<Error | null>(null)

  // Use ref to track abort controller for cleanup
  const abortControllerRef = useRef<AbortController | null>(null)

  const fetchEvents = useCallback(async () => {
    // Abort any in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    // Create new abort controller for this request
    abortControllerRef.current = new AbortController()

    try {
      setLoading(true)
      setError(null)
      const data = await api.getRiskEvents(filters)
      setEvents(data)
    } catch (err) {
      // Don't set error if request was aborted (component unmounted)
      if (err instanceof Error && err.name !== 'AbortError') {
        setError(err)
        console.error('Failed to fetch risk events:', err)
      }
    } finally {
      setLoading(false)
    }
  }, [filters])

  // Fetch on mount and when filters change
  useEffect(() => {
    fetchEvents()

    // Set up polling if interval is provided
    let intervalId: number | undefined
    if (options?.pollInterval) {
      intervalId = window.setInterval(fetchEvents, options.pollInterval)
    }

    // Cleanup: abort in-flight requests and clear interval
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      if (intervalId) {
        clearInterval(intervalId)
      }
    }
  }, [fetchEvents, options?.pollInterval])

  return {
    events,
    loading,
    error,
    refetch: fetchEvents,
  }
}
