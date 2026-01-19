import { useContext, useCallback } from 'react'
import { ToastContext, ToastType, ToastOptions } from '../components/feedback/ToastProvider'

export interface UseToastReturn {
  /** Show a toast notification */
  toast: (message: string, options?: Partial<ToastOptions>) => string
  /** Show a success toast */
  success: (message: string, options?: Omit<ToastOptions, 'type'>) => string
  /** Show an error toast */
  error: (message: string, options?: Omit<ToastOptions, 'type'>) => string
  /** Show a warning toast */
  warning: (message: string, options?: Omit<ToastOptions, 'type'>) => string
  /** Show an info toast */
  info: (message: string, options?: Omit<ToastOptions, 'type'>) => string
  /** Dismiss a specific toast by ID */
  dismiss: (id: string) => void
  /** Dismiss all toasts */
  dismissAll: () => void
}

/**
 * Hook to access toast notification functionality
 *
 * @example
 * const { success, error } = useToast()
 *
 * // Show success toast
 * success('File uploaded successfully!')
 *
 * // Show error with custom duration
 * error('Upload failed', { duration: 10000 })
 */
export function useToast(): UseToastReturn {
  const context = useContext(ToastContext)

  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }

  const { addToast, removeToast, removeAllToasts } = context

  const toast = useCallback(
    (message: string, options?: Partial<ToastOptions>) => {
      return addToast(message, {
        type: 'info',
        duration: 5000,
        dismissible: true,
        ...options,
      })
    },
    [addToast]
  )

  const success = useCallback(
    (message: string, options?: Omit<ToastOptions, 'type'>) => {
      return addToast(message, { ...options, type: 'success' })
    },
    [addToast]
  )

  const error = useCallback(
    (message: string, options?: Omit<ToastOptions, 'type'>) => {
      return addToast(message, { ...options, type: 'error', duration: options?.duration ?? 8000 })
    },
    [addToast]
  )

  const warning = useCallback(
    (message: string, options?: Omit<ToastOptions, 'type'>) => {
      return addToast(message, { ...options, type: 'warning' })
    },
    [addToast]
  )

  const info = useCallback(
    (message: string, options?: Omit<ToastOptions, 'type'>) => {
      return addToast(message, { ...options, type: 'info' })
    },
    [addToast]
  )

  const dismiss = useCallback(
    (id: string) => {
      removeToast(id)
    },
    [removeToast]
  )

  const dismissAll = useCallback(() => {
    removeAllToasts()
  }, [removeAllToasts])

  return {
    toast,
    success,
    error,
    warning,
    info,
    dismiss,
    dismissAll,
  }
}

export type { ToastType, ToastOptions }
export default useToast
