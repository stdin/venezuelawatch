import type { RiskEvent, EventFilterParams, SanctionsSummary } from './types'

const API_BASE = '/api'

/**
 * Get CSRF token from cookies
 */
function getCsrfToken(): string | null {
  const name = 'csrftoken'
  const cookies = document.cookie.split(';')
  for (let cookie of cookies) {
    const [cookieName, cookieValue] = cookie.trim().split('=')
    if (cookieName === name) {
      return decodeURIComponent(cookieValue)
    }
  }
  return null
}

export interface HealthResponse {
  status: string
  service: string
}

export interface User {
  id: number
  email: string
  username: string
  first_name: string
  last_name: string
  organization_name: string
  role: 'individual' | 'team_member' | 'team_admin' | 'org_admin'
  subscription_tier: 'free' | 'pro' | 'enterprise'
  timezone: string
  date_joined: string
}

export interface AuthResponse {
  user: User
  access_token?: string  // Optional - we use httpOnly cookies
}

export interface RegisterData {
  email: string
  password: string
}

export interface LoginData {
  email: string
  password: string
}

export const api = {
  /**
   * Fetch CSRF token from Django
   * This endpoint doesn't exist yet, but we can use any GET endpoint to get the cookie
   */
  async initCsrf(): Promise<void> {
    // Just make a GET request to any Django endpoint to get the CSRF cookie
    await fetch(`${API_BASE}/health/health`, {
      credentials: 'include',
    })
  },

  async healthCheck(): Promise<HealthResponse> {
    const response = await fetch(`${API_BASE}/health/health`, {
      credentials: 'include',  // Include cookies
    })
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }
    return response.json()
  },

  // Authentication methods
  async register(data: RegisterData): Promise<AuthResponse> {
    const csrfToken = getCsrfToken()
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }
    if (csrfToken) {
      headers['X-CSRFToken'] = csrfToken
    }

    const response = await fetch('/_allauth/browser/v1/auth/signup', {
      method: 'POST',
      headers,
      credentials: 'include',  // Important: send/receive cookies
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Registration failed')
    }
    return response.json()
  },

  async login(data: LoginData): Promise<AuthResponse> {
    const csrfToken = getCsrfToken()
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }
    if (csrfToken) {
      headers['X-CSRFToken'] = csrfToken
    }

    const response = await fetch('/_allauth/browser/v1/auth/login', {
      method: 'POST',
      headers,
      credentials: 'include',
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Login failed')
    }
    return response.json()
  },

  async logout(): Promise<void> {
    const csrfToken = getCsrfToken()
    const headers: HeadersInit = {}
    if (csrfToken) {
      headers['X-CSRFToken'] = csrfToken
    }

    const response = await fetch('/_allauth/browser/v1/auth/session', {
      method: 'DELETE',
      headers,
      credentials: 'include',
    })
    if (!response.ok) {
      throw new Error('Logout failed')
    }
  },

  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${API_BASE}/user/me`, {
      credentials: 'include',
    })
    if (!response.ok) {
      throw new Error(`Failed to fetch user: ${response.status}`)
    }
    return response.json()
  },

  // Risk Intelligence methods
  async getRiskEvents(filters?: EventFilterParams): Promise<RiskEvent[]> {
    const params = new URLSearchParams()
    if (filters) {
      if (filters.severity) params.append('severity', filters.severity)
      if (filters.min_risk_score !== undefined) params.append('min_risk_score', filters.min_risk_score.toString())
      if (filters.max_risk_score !== undefined) params.append('max_risk_score', filters.max_risk_score.toString())
      if (filters.has_sanctions !== undefined) params.append('has_sanctions', filters.has_sanctions.toString())
      if (filters.event_type) params.append('event_type', filters.event_type)
      if (filters.source) params.append('source', filters.source)
      if (filters.days_back !== undefined) params.append('days_back', filters.days_back.toString())
      if (filters.limit !== undefined) params.append('limit', filters.limit.toString())
      if (filters.offset !== undefined) params.append('offset', filters.offset.toString())
    }

    const url = `${API_BASE}/risk/events${params.toString() ? `?${params.toString()}` : ''}`
    const response = await fetch(url, {
      credentials: 'include',
    })
    if (!response.ok) {
      throw new Error(`Failed to fetch risk events: ${response.status}`)
    }
    return response.json()
  },

  async getSanctionsSummary(): Promise<SanctionsSummary> {
    const response = await fetch(`${API_BASE}/risk/sanctions-summary`, {
      credentials: 'include',
    })
    if (!response.ok) {
      throw new Error(`Failed to fetch sanctions summary: ${response.status}`)
    }
    return response.json()
  },
}
