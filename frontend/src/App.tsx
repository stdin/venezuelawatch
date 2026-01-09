import { useState } from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import { LoginForm } from './components/LoginForm'
import { RegisterForm } from './components/RegisterForm'
import { Dashboard } from './pages/Dashboard'
import { Entities } from './pages/Entities'
import './App.css'

function AuthenticatedApp() {
  const location = useLocation()

  return (
    <div className="app-container">
      {/* Navigation */}
      <nav className="app-nav">
        <div className="app-nav-brand">VenezuelaWatch</div>
        <div className="app-nav-links">
          <Link
            to="/"
            className={`app-nav-link ${location.pathname === '/' ? 'app-nav-link-active' : ''}`}
          >
            Dashboard
          </Link>
          <Link
            to="/entities"
            className={`app-nav-link ${location.pathname === '/entities' ? 'app-nav-link-active' : ''}`}
          >
            Entities
          </Link>
        </div>
      </nav>

      {/* Main content */}
      <div className="app-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/entities" element={<Entities />} />
        </Routes>
      </div>
    </div>
  )
}

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

  return (
    <BrowserRouter>
      <AuthenticatedApp />
    </BrowserRouter>
  )
}

export default App
