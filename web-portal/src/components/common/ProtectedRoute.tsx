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

  // DEVELOPMENT MODE: Bypass authentication
  // TODO: Remove this before production deployment
  const isDevelopment = import.meta.env.DEV
  if (isDevelopment) {
    return <>{children}</>
  }

  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
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
