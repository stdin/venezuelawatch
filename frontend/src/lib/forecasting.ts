/**
 * Forecasting API client for entity risk predictions
 */

const API_BASE = '/api'

export interface ForecastPoint {
  ds: string  // ISO timestamp
  yhat: number  // Predicted value
  yhat_lower: number  // Lower confidence bound
  yhat_upper: number  // Upper confidence bound
}

export interface ForecastResponse {
  status: 'ready' | 'insufficient_data' | 'error'
  forecast?: ForecastPoint[]
  generated_at?: string
  horizon_days: number
  message?: string
}

export async function fetchEntityForecast(
  entityId: string,
  horizonDays: number = 30
): Promise<ForecastResponse> {
  const response = await fetch(
    `${API_BASE}/forecasting/entities/${entityId}/forecast`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ horizon_days: horizonDays }),
    }
  )

  if (!response.ok) {
    throw new Error(`Failed to fetch forecast: ${response.status}`)
  }

  return response.json()
}
