import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useNotifications } from './useNotifications'

const SESSION_TIMEOUT = 60 * 60 * 1000 // 1 hour in milliseconds
const WARNING_TIME = 5 * 60 * 1000 // 5 minutes before expiry

export const useSessionTimeout = () => {
  const { isAuthenticated, refreshSession, signOut } = useAuth()
  const { addNotification, dismissNotification } = useNotifications()
  const navigate = useNavigate()
  const [showWarning, setShowWarning] = useState(false)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  const warningTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const warningNotificationIdRef = useRef<string | null>(null)

  const clearTimers = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    if (warningTimeoutRef.current) {
      clearTimeout(warningTimeoutRef.current)
      warningTimeoutRef.current = null
    }
    if (warningNotificationIdRef.current) {
      dismissNotification(warningNotificationIdRef.current)
      warningNotificationIdRef.current = null
    }
  }

  const handleSessionExpiry = async () => {
    clearTimers()
    setShowWarning(false)
    
    try {
      await signOut()
      addNotification({
        type: 'warning',
        header: 'Session expired',
        content: 'Your session has expired. Please sign in again.',
        dismissible: true,
      })
      navigate('/login')
    } catch (error) {
      console.error('Error during session expiry:', error)
    }
  }

  const handleExtendSession = async () => {
    try {
      await refreshSession()
      clearTimers()
      setShowWarning(false)
      
      addNotification({
        type: 'success',
        header: 'Session extended',
        content: 'Your session has been extended.',
        dismissible: true,
      })
      
      // Restart the timers
      startTimers()
    } catch (error) {
      console.error('Error extending session:', error)
      addNotification({
        type: 'error',
        header: 'Failed to extend session',
        content: 'Unable to extend your session. Please sign in again.',
        dismissible: true,
      })
    }
  }

  const showWarningNotification = () => {
    setShowWarning(true)
    
    const notificationId = addNotification({
      type: 'warning',
      header: 'Your session will expire in 5 minutes',
      content: 'Click "Extend Session" to continue working.',
      dismissible: false,
      action: {
        text: 'Extend Session',
        onClick: handleExtendSession,
      },
    })
    
    warningNotificationIdRef.current = notificationId
  }

  const startTimers = () => {
    clearTimers()
    
    // Set warning timer (5 minutes before expiry)
    warningTimeoutRef.current = setTimeout(() => {
      showWarningNotification()
    }, SESSION_TIMEOUT - WARNING_TIME)
    
    // Set expiry timer
    timeoutRef.current = setTimeout(() => {
      handleSessionExpiry()
    }, SESSION_TIMEOUT)
  }

  const resetTimers = () => {
    if (isAuthenticated) {
      startTimers()
    }
  }

  useEffect(() => {
    if (isAuthenticated) {
      startTimers()
      
      // Reset timers on user activity
      const events = ['mousedown', 'keydown', 'scroll', 'touchstart']
      const handleActivity = () => {
        if (!showWarning) {
          resetTimers()
        }
      }
      
      events.forEach((event) => {
        window.addEventListener(event, handleActivity)
      })
      
      return () => {
        clearTimers()
        events.forEach((event) => {
          window.removeEventListener(event, handleActivity)
        })
      }
    } else {
      clearTimers()
    }
  }, [isAuthenticated, showWarning])

  return {
    showWarning,
    extendSession: handleExtendSession,
  }
}
