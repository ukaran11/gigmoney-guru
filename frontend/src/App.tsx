import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useAuthStore } from './store/authStore'
import { useEffect, useState } from 'react'

// Pages
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Chat from './pages/Chat'
import Goals from './pages/Goals'
import Advances from './pages/Advances'
import Settings from './pages/Settings'

// Components
import Layout from './components/Layout'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { token } = useAuthStore()
  const [isReady, setIsReady] = useState(false)
  
  useEffect(() => {
    // Check localStorage directly on mount to handle hydration timing
    const storedToken = localStorage.getItem('token')
    if (storedToken && !token) {
      // Token exists in localStorage but not in store yet - wait for hydration
      const timeout = setTimeout(() => setIsReady(true), 100)
      return () => clearTimeout(timeout)
    }
    setIsReady(true)
  }, [token])
  
  if (!isReady) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }
  
  // Check both store token and localStorage token
  const hasToken = token || localStorage.getItem('token')
  return hasToken ? <>{children}</> : <Navigate to="/login" replace />
}

function App() {
  return (
    <Router>
      <Toaster 
        position="top-center"
        toastOptions={{
          duration: 3000,
          style: {
            background: '#333',
            color: '#fff',
            borderRadius: '8px',
          },
        }}
      />
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Protected routes */}
        <Route path="/" element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }>
          <Route index element={<Dashboard />} />
          <Route path="chat" element={<Chat />} />
          <Route path="goals" element={<Goals />} />
          <Route path="advances" element={<Advances />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        
        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  )
}

export default App
