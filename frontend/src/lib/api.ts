const API_BASE = '/api'

export interface HealthResponse {
  status: string
  service: string
}

export const api = {
  async healthCheck(): Promise<HealthResponse> {
    const response = await fetch(`${API_BASE}/health/health`)
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }
    return response.json()
  }
}
