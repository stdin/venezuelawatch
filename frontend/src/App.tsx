import { useState } from 'react'
import { useAuth } from './contexts/AuthContext'
import { LoginForm } from './components/LoginForm'
import { RegisterForm } from './components/RegisterForm'
import { Dashboard } from './pages/Dashboard'
import './App.css'

function App() {
  const { user, loading } = useAuth()
  const [showRegister, setShowRegister] = useState(false)

  if (loading) {
    return <div>Loading...</div>
  }

  if (!user) {
    return (
      <div className="App">
        <h1>VenezuelaWatch</h1>
        <p>Real-time intelligence platform for Venezuela events</p>

        {showRegister ? <RegisterForm /> : <LoginForm />}

        <p style={{ marginTop: '2rem' }}>
          <button onClick={() => setShowRegister(!showRegister)} style={{ background: 'none', border: 'none', color: 'blue', textDecoration: 'underline', cursor: 'pointer' }}>
            {showRegister ? 'Already have an account? Login' : "Don't have an account? Register"}
          </button>
        </p>
      </div>
    )
  }

  return <Dashboard />
}

export default App
