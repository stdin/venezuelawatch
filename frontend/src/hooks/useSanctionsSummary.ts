import { useState, useEffect, useRef } from 'react'
import { api } from '../lib/api'
import type { SanctionsSummary } from '../lib/types'

interface UseSanctionsSummaryReturn {
  /** Sanctions summary or null if not yet loaded */
  summary: SanctionsSummary | null
  /** Loading state */
  loading: boolean
  /** Error state */
  error: Error | null
}

/**
 * React hook for fetching sanctions summary statistics
 *
 * @returns Object containing summary, loading state, and error
 *
 * @example
 * const { summary, loading, error } = useSanctionsSummary()
 *
 * if (loading) return <div>Loading...</div>
 * if (error) return <div>Error: {error.message}</div>
 * if (summary) {
 *   return (
 *     <div>
 *       <p>Total events with sanctions: {summary.total_events_with_sanctions}</p>
 *       <p>Unique entities: {summary.unique_sanctioned_entities}</p>
 *     </div>
 *   )
 * }
 */
export function useSanctionsSummary(): UseSanctionsSummaryReturn {
  const [summary, setSummary] = useState<SanctionsSummary | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<Error | null>(null)

  // Use ref to track abort controller for cleanup
  const abortControllerRef = useRef<AbortController | null>(null)

  useEffect(() => {
    const fetchSummary = async () => {
      // Abort any in-flight request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }

      // Create new abort controller for this request
      abortControllerRef.current = new AbortController()

      try {
        setLoading(true)
        setError(null)
        const data = await api.getSanctionsSummary()
        setSummary(data)
      } catch (err) {
        // Don't set error if request was aborted (component unmounted)
        if (err instanceof Error && err.name !== 'AbortError') {
          setError(err)
          console.error('Failed to fetch sanctions summary:', err)
        }
      } finally {
        setLoading(false)
      }
    }

    fetchSummary()

    // Cleanup: abort in-flight request on unmount
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, []) // Empty dependency array - fetch once on mount

  return {
    summary,
    loading,
    error,
  }
}
