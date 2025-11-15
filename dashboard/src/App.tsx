import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './lib/store/auth'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Agents from './pages/Agents'
import Events from './pages/Events'
import Alerts from './pages/Alerts'
import Policies from './pages/Policies'
import Settings from './pages/Settings'

function App() {
  const { isAuthenticated } = useAuthStore()

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="agents" element={<Agents />} />
        <Route path="events" element={<Events />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="policies" element={<Policies />} />
        <Route path="settings" element={<Settings />} />
      </Route>

      {/* Catch all - redirect to dashboard if authenticated, login otherwise */}
      <Route
        path="*"
        element={
          <Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />
        }
      />
    </Routes>
  )
}

export default App
