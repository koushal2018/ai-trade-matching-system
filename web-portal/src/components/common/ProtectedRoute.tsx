import { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Box, Spinner } from '@cloudscape-design/components'
import { useAuth } from '../../contexts/AuthContext'

interface ProtectedRouteProps {
  children: ReactNode
}

export const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  // DEMO MODE: Bypass authentication for demonstration
  // TODO: Remove this before production deployment
  const isDevelopment = import.meta.env.DEV
  const isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true'
  const isMSWEnabled = import.meta.env.VITE_ENABLE_MSW === 'true'
  if (isDevelopment || isDemoMode || isMSWEnabled) {
    return <>{children}</>
  }

  if (isLoading) {
    return (
      <Box textAlign="center" padding={{ vertical: 'xxxl' }}>
        <Spinner size="large" />
      </Box>
    )
  }

  if (!isAuthenticated) {
    // Redirect to login page, but save the location they were trying to access
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  return <>{children}</>
}
