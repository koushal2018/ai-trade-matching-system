import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { Amplify } from 'aws-amplify'
import {
  signIn,
  signOut,
  getCurrentUser,
  fetchAuthSession,
  AuthUser,
} from 'aws-amplify/auth'

// Configure Amplify
Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID,
      userPoolClientId: import.meta.env.VITE_COGNITO_CLIENT_ID,
      loginWith: {
        email: true,
      },
    },
  },
})

interface AuthContextType {
  user: AuthUser | null
  isAuthenticated: boolean
  isLoading: boolean
  signIn: (username: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  refreshSession: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Check authentication status on mount
  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const currentUser = await getCurrentUser()
      setUser(currentUser)
    } catch (error) {
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSignIn = async (username: string, password: string) => {
    try {
      await signIn({ username, password })
      await checkAuthStatus()
    } catch (error) {
      console.error('Sign in error:', error)
      throw error
    }
  }

  const handleSignOut = async () => {
    try {
      await signOut()
      setUser(null)
      // Clear sensitive data from localStorage
      localStorage.removeItem('sessionId')
      localStorage.removeItem('traceId')
    } catch (error) {
      console.error('Sign out error:', error)
      throw error
    }
  }

  const refreshSession = async () => {
    try {
      await fetchAuthSession({ forceRefresh: true })
    } catch (error) {
      console.error('Session refresh error:', error)
      throw error
    }
  }

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    signIn: handleSignIn,
    signOut: handleSignOut,
    refreshSession,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
