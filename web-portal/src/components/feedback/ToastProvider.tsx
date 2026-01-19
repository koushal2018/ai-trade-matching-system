import React, { createContext, useCallback, useState } from 'react'
import ToastContainer from './ToastContainer'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface ToastOptions {
  type: ToastType
  title?: string
  duration?: number
  dismissible?: boolean
}

interface Toast {
  id: string
  message: string
  type: ToastType
  title?: string
  duration: number
  dismissible: boolean
}

interface ToastContextValue {
  addToast: (message: string, options?: Partial<ToastOptions>) => string
  removeToast: (id: string) => void
  removeAllToasts: () => void
}

export const ToastContext = createContext<ToastContextValue | null>(null)

interface ToastProviderProps {
  children: React.ReactNode
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center'
  maxToasts?: number
}

/**
 * ToastProvider Component
 *
 * Provides toast notification context to the application.
 * Wrap your app with this provider to enable toast notifications.
 *
 * @example
 * <ToastProvider position="top-right" maxToasts={5}>
 *   <App />
 * </ToastProvider>
 */
export const ToastProvider: React.FC<ToastProviderProps> = ({
  children,
  position = 'top-right',
  maxToasts = 5,
}) => {
  const [toasts, setToasts] = useState<Toast[]>([])

  const generateId = () => `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

  const addToast = useCallback((message: string, options?: Partial<ToastOptions>): string => {
    const id = generateId()
    const newToast: Toast = {
      id,
      message,
      type: options?.type || 'info',
      title: options?.title,
      duration: options?.duration ?? 5000,
      dismissible: options?.dismissible ?? true,
    }

    setToasts((prev) => [...prev, newToast])
    return id
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  const removeAllToasts = useCallback(() => {
    setToasts([])
  }, [])

  return (
    <ToastContext.Provider value={{ addToast, removeToast, removeAllToasts }}>
      {children}
      <ToastContainer
        toasts={toasts}
        onDismiss={removeToast}
        position={position}
        maxToasts={maxToasts}
      />
    </ToastContext.Provider>
  )
}

export default ToastProvider
