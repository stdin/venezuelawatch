import { useEffect, useState } from 'react'
import { api } from './lib/api'
import './App.css'

function App() {
  const [apiStatus, setApiStatus] = useState<string>('checking...')

  useEffect(() => {
    api.healthCheck()
      .then(data => setApiStatus(data.status))
      .catch(() => setApiStatus('error'))
  }, [])

  return (
    <div className="App">
      <h1>VenezuelaWatch</h1>
      <p>Real-time intelligence platform for Venezuela events</p>
      <p>API Status: {apiStatus}</p>
    </div>
  )
}

export default App
