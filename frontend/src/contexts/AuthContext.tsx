import React, { createContext, useContext, useState, useEffect } from 'react'
import type { User } from '../lib/api'
import { api } from '../lib/api'

interface AuthContextType {
  user: User | null
  loading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, passwordConfirm: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Check authentication status on mount
  useEffect(() => {
    initAuth()
  }, [])

  async function initAuth() {
    try {
      // Initialize CSRF token first
      await api.initCsrf()
      // Then check authentication status
      await checkAuth()
    } catch (err) {
      console.error('Failed to initialize auth:', err)
      setLoading(false)
    }
  }

  async function checkAuth() {
    try {
      const currentUser = await api.getCurrentUser()
      setUser(currentUser)
      setError(null)
    } catch (err) {
      // Not authenticated - this is fine
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  async function login(email: string, password: string) {
    setLoading(true)
    setError(null)
    try {
      await api.login({ email, password })
      await checkAuth()  // Fetch user details after login
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
      throw err
    } finally {
      setLoading(false)
    }
  }

  async function register(email: string, password: string, passwordConfirm: string) {
    setLoading(true)
    setError(null)
    try {
      // Validate passwords match on frontend
      if (password !== passwordConfirm) {
        throw new Error('Passwords do not match')
      }
      await api.register({ email, password })
      await checkAuth()  // Fetch user details after registration
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
      throw err
    } finally {
      setLoading(false)
    }
  }

  async function logout() {
    setLoading(true)
    setError(null)
    try {
      await api.logout()
      setUser(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Logout failed')
      throw err
    } finally {
      setLoading(false)
    }
  }

  async function refreshUser() {
    try {
      const currentUser = await api.getCurrentUser()
      setUser(currentUser)
      setError(null)
    } catch (err) {
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, error, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
