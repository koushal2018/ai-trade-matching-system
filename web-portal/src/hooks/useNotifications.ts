import { useState, useCallback, useEffect, useRef, createElement } from 'react'
import { Button } from '@cloudscape-design/components'
import type { FlashbarProps } from '@cloudscape-design/components'

export interface NotificationAction {
  text: string
  onClick: () => void
}

export interface NotificationItem {
  type: FlashbarProps.Type
  header: string
  content?: string
  dismissible?: boolean
  action?: NotificationAction
}

let notificationIdCounter = 0

export const useNotifications = () => {
  const [notifications, setNotifications] = useState<FlashbarProps.MessageDefinition[]>([])
  const timeoutsRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map())

  // Generate unique ID for notifications
  const generateId = useCallback(() => {
    return `notification-${++notificationIdCounter}-${Date.now()}`
  }, [])

  // Add a notification
  const addNotification = useCallback(
    (notification: NotificationItem) => {
      const id = generateId()
      
      // Prepare the notification for CloudScape Flashbar
      const flashbarNotification: FlashbarProps.MessageDefinition = {
        type: notification.type,
        header: notification.header,
        content: notification.content,
        dismissible: notification.dismissible ?? true,
        dismissLabel: 'Dismiss',
        id,
        onDismiss: () => dismissNotification(id),
        // Correct CloudScape API: use action property with Button component
        action: notification.action
          ? createElement(Button, { onClick: notification.action.onClick }, notification.action.text)
          : undefined,
      }

      setNotifications((prev) => [...prev, flashbarNotification])

      // Auto-dismiss success notifications after 5 seconds
      if (notification.type === 'success' && notification.dismissible !== false) {
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
