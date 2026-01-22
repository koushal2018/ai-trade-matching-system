import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Box } from '@mui/material'
import Dashboard from './pages/Dashboard'
import HITLPanel from './pages/HITLPanel'
import AuditTrailPage from './pages/AuditTrailPage'
import TradeMatchingPage from './pages/TradeMatchingPage'
import RealTimeMonitor from './pages/RealTimeMonitor'
import MatchingQueuePage from './pages/MatchingQueuePage'
import ExceptionsPage from './pages/ExceptionsPage'
import { LoginPage } from './pages/LoginPage'
import { useSessionTimeout } from './hooks/useSessionTimeout'
import { ErrorBoundary } from './components/common/ErrorBoundary'
import { ProtectedRoute } from './components/common/ProtectedRoute'
import Layout from './components/Layout'
import { fsiColors, fsiGradients } from './theme'

function App() {
  const location = useLocation()

  // Session timeout management
  useSessionTimeout()

  // Don't show layout on login page - use custom styled login
  if (location.pathname === '/login') {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          bgcolor: fsiColors.navy[900],
          backgroundImage: fsiGradients.meshGradient,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Routes>
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </Box>
    )
  }

  return (
    <Layout>
      <ErrorBoundary>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <ErrorBoundary>
                  <Dashboard />
                </ErrorBoundary>
              </ProtectedRoute>
            }
          />
          <Route
            path="/upload"
            element={
              <ProtectedRoute>
                <ErrorBoundary>
                  <TradeMatchingPage />
                </ErrorBoundary>
              </ProtectedRoute>
            }
          />
          <Route
            path="/hitl"
            element={
              <ProtectedRoute>
                <ErrorBoundary>
                  <HITLPanel />
                </ErrorBoundary>
              </ProtectedRoute>
            }
          />
          <Route
            path="/audit"
            element={
              <ProtectedRoute>
                <ErrorBoundary>
                  <AuditTrailPage />
                </ErrorBoundary>
              </ProtectedRoute>
            }
          />
          <Route
            path="/monitor"
            element={
              <ProtectedRoute>
                <ErrorBoundary>
                  <RealTimeMonitor />
                </ErrorBoundary>
              </ProtectedRoute>
            }
          />
          <Route
            path="/queue"
            element={
              <ProtectedRoute>
                <ErrorBoundary>
                  <MatchingQueuePage />
                </ErrorBoundary>
              </ProtectedRoute>
            }
          />
          <Route
            path="/exceptions"
            element={
              <ProtectedRoute>
                <ErrorBoundary>
                  <ExceptionsPage />
                </ErrorBoundary>
              </ProtectedRoute>
            }
          />
        </Routes>
      </ErrorBoundary>
    </Layout>
  )
}

export default App
