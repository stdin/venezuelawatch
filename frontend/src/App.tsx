import { useState } from 'react'
import { useAuth } from './contexts/AuthContext'
import { LoginForm } from './components/LoginForm'
import { RegisterForm } from './components/RegisterForm'
import './App.css'

function App() {
  const { user, loading, logout } = useAuth()
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

  return (
    <div className="App">
      <h1>VenezuelaWatch</h1>
      <p>Welcome, {user.email}!</p>

      <div style={{ marginTop: '2rem', padding: '1rem', border: '1px solid #ccc', maxWidth: '400px', margin: '2rem auto' }}>
        <h2>User Profile</h2>
        <p><strong>Email:</strong> {user.email}</p>
        <p><strong>Role:</strong> {user.role}</p>
        <p><strong>Subscription:</strong> {user.subscription_tier}</p>
        <p><strong>Organization:</strong> {user.organization_name || 'None'}</p>
        <p><strong>Joined:</strong> {new Date(user.date_joined).toLocaleDateString()}</p>
      </div>

      <button onClick={logout} style={{ padding: '0.5rem 1rem', marginTop: '1rem' }}>
        Logout
      </button>
    </div>
  )
}

export default App
