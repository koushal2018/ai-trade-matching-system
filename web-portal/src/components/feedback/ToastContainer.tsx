import React from 'react'
import { Box } from '@mui/material'
import Toast, { ToastProps } from './Toast'

export interface ToastContainerProps {
  toasts: Array<Omit<ToastProps, 'onDismiss'>>
  onDismiss: (id: string) => void
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center'
  maxToasts?: number
}

const positionStyles = {
  'top-right': {
    top: 16,
    right: 16,
    alignItems: 'flex-end',
  },
  'top-left': {
    top: 16,
    left: 16,
    alignItems: 'flex-start',
  },
  'bottom-right': {
    bottom: 16,
    right: 16,
    alignItems: 'flex-end',
  },
  'bottom-left': {
    bottom: 16,
    left: 16,
    alignItems: 'flex-start',
  },
  'top-center': {
    top: 16,
    left: '50%',
    transform: 'translateX(-50%)',
    alignItems: 'center',
  },
  'bottom-center': {
    bottom: 16,
    left: '50%',
    transform: 'translateX(-50%)',
    alignItems: 'center',
  },
}

/**
 * ToastContainer Component
 *
 * Renders a stack of toast notifications at a specified position.
 * Limits the number of visible toasts and removes oldest when max is exceeded.
 */
export const ToastContainer: React.FC<ToastContainerProps> = ({
  toasts,
  onDismiss,
  position = 'top-right',
  maxToasts = 5,
}) => {
  // Limit visible toasts
  const visibleToasts = toasts.slice(-maxToasts)

  if (visibleToasts.length === 0) {
    return null
  }

  const posStyle = positionStyles[position]
  const isTop = position.includes('top')

  return (
    <Box
      sx={{
        position: 'fixed',
        zIndex: 9999,
        display: 'flex',
        flexDirection: isTop ? 'column' : 'column-reverse',
        gap: 1.5,
        pointerEvents: 'none',
        ...posStyle,
      }}
    >
      {visibleToasts.map((toast) => (
        <Box
          key={toast.id}
          sx={{
            pointerEvents: 'auto',
          }}
        >
          <Toast {...toast} onDismiss={onDismiss} />
        </Box>
      ))}
    </Box>
  )
}

export default ToastContainer
