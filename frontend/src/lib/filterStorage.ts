import type { EventFilterParams } from './types'

const STORAGE_KEY = 'dashboard-filters'

/**
 * Default filter values
 */
const DEFAULT_FILTERS: EventFilterParams = {
  days_back: 30,
  min_risk_score: 0,
  max_risk_score: 100,
}

/**
 * Save filters to localStorage and update URL query parameters
 */
export function saveFiltersToStorage(filters: EventFilterParams): void {
  try {
    // Save to localStorage
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filters))

    // Update URL query params
    const params = new URLSearchParams()

    if (filters.severity) params.set('severity', filters.severity)
    if (filters.min_risk_score !== undefined) params.set('min_risk_score', filters.min_risk_score.toString())
    if (filters.max_risk_score !== undefined) params.set('max_risk_score', filters.max_risk_score.toString())
    if (filters.has_sanctions) params.set('has_sanctions', 'true')
    if (filters.event_type) params.set('event_type', filters.event_type)
    if (filters.source) params.set('source', filters.source)
    if (filters.days_back !== undefined) params.set('days_back', filters.days_back.toString())
    if (filters.limit !== undefined) params.set('limit', filters.limit.toString())
    if (filters.offset !== undefined) params.set('offset', filters.offset.toString())

    // Update URL without page reload
    const newUrl = params.toString() ? `?${params.toString()}` : window.location.pathname
    window.history.replaceState({}, '', newUrl)
  } catch (error) {
    console.error('Failed to save filters to storage:', error)
  }
}

/**
 * Load filters from URL query params, localStorage, or defaults
 * Priority: URL > localStorage > defaults
 */
export function loadFiltersFromStorage(): EventFilterParams {
  try {
    // First, try to load from URL query params
    const urlParams = new URLSearchParams(window.location.search)

    if (urlParams.toString()) {
      const filters: EventFilterParams = { ...DEFAULT_FILTERS }

      if (urlParams.has('severity')) filters.severity = urlParams.get('severity') || undefined
      if (urlParams.has('min_risk_score')) filters.min_risk_score = parseInt(urlParams.get('min_risk_score') || '0', 10)
      if (urlParams.has('max_risk_score')) filters.max_risk_score = parseInt(urlParams.get('max_risk_score') || '100', 10)
      if (urlParams.has('has_sanctions')) filters.has_sanctions = urlParams.get('has_sanctions') === 'true'
      if (urlParams.has('event_type')) filters.event_type = urlParams.get('event_type') || undefined
      if (urlParams.has('source')) filters.source = urlParams.get('source') || undefined
      if (urlParams.has('days_back')) filters.days_back = parseInt(urlParams.get('days_back') || '30', 10)
      if (urlParams.has('limit')) filters.limit = parseInt(urlParams.get('limit') || '100', 10)
      if (urlParams.has('offset')) filters.offset = parseInt(urlParams.get('offset') || '0', 10)

      return filters
    }

    // If no URL params, try localStorage
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored) as EventFilterParams
      return { ...DEFAULT_FILTERS, ...parsed }
    }

    // Fall back to defaults
    return DEFAULT_FILTERS
  } catch (error) {
    console.error('Failed to load filters from storage:', error)
    return DEFAULT_FILTERS
  }
}

/**
 * Clear filters from both localStorage and URL
 */
export function clearFiltersFromStorage(): void {
  try {
    // Remove from localStorage
    localStorage.removeItem(STORAGE_KEY)

    // Clear URL query params
    window.history.replaceState({}, '', window.location.pathname)
  } catch (error) {
    console.error('Failed to clear filters from storage:', error)
  }
}
