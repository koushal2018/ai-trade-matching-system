import { useState, useCallback, useEffect, useRef } from 'react'
import type { FlashbarProps } from '@cloudscape-design/components'

export interface NotificationItem extends FlashbarProps.MessageDefinition {
  id?: string
}

let notificationIdCounter = 0

export const useNotifications = () => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([])
  const timeoutsRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map())

  // Generate unique ID for notifications
  const generateId = useCallback(() => {
    return `notification-${++notificationIdCounter}-${Date.now()}`
  }, [])

  // Add a notification
  const addNotification = useCallback(
    (notification: Omit<NotificationItem, 'id'>) => {
      const id = generateId()
      const newNotification: NotificationItem = {
        ...notification,
        id,
        dismissible: notification.dismissible ?? true,
      }

      setNotifications((prev) => [...prev, newNotification])

      // Auto-dismiss success notifications after 5 seconds
      if (notification.type === 'success') {
        const timeout = setTimeout(() => {
          dismissNotification(id)
        }, 5000)
        timeoutsRef.current.set(id, timeout)
      }

      return id
    },
    [generateId]
  )

  // Dismiss a specific notification
  const dismissNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((notification) => notification.id !== id))

    // Clear timeout if exists
    const timeout = timeoutsRef.current.get(id)
    if (timeout) {
      clearTimeout(timeout)
      timeoutsRef.current.delete(id)
    }
  }, [])

  // Clear all notifications
  const clearAllNotifications = useCallback(() => {
    setNotifications([])

    // Clear all timeouts
    timeoutsRef.current.forEach((timeout) => clearTimeout(timeout))
    timeoutsRef.current.clear()
  }, [])

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      timeoutsRef.current.forEach((timeout) => clearTimeout(timeout))
      timeoutsRef.current.clear()
    }
  }, [])

  return {
    notifications,
    addNotification,
    dismissNotification,
    clearAllNotifications,
  }
}
