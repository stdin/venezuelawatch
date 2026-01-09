const API_BASE = '/api'

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
  password_confirm: string
}

export interface LoginData {
  email: string
  password: string
}

export const api = {
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
    const response = await fetch('/_allauth/browser/v1/auth/signup', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
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
    const response = await fetch('/_allauth/browser/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
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
    const response = await fetch('/_allauth/browser/v1/auth/session', {
      method: 'DELETE',
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
}
