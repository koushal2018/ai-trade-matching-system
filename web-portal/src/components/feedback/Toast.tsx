import React, { useEffect, useState } from 'react'
import { Box, IconButton, Typography } from '@mui/material'
import {
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Close as CloseIcon,
} from '@mui/icons-material'
import { glowColors } from '../../theme'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface ToastProps {
  id: string
  message: string
  type: ToastType
  duration: number
  dismissible: boolean
  onDismiss: (id: string) => void
  title?: string
}

const typeConfig = {
  success: {
    icon: SuccessIcon,
    color: glowColors.success,
    bgColor: 'rgba(29, 129, 2, 0.1)',
    borderColor: 'rgba(29, 129, 2, 0.4)',
  },
  error: {
    icon: ErrorIcon,
    color: glowColors.error,
    bgColor: 'rgba(209, 50, 18, 0.1)',
    borderColor: 'rgba(209, 50, 18, 0.4)',
  },
  warning: {
    icon: WarningIcon,
    color: glowColors.warning,
    bgColor: 'rgba(255, 153, 0, 0.1)',
    borderColor: 'rgba(255, 153, 0, 0.4)',
  },
  info: {
    icon: InfoIcon,
    color: glowColors.info,
    bgColor: 'rgba(9, 114, 211, 0.1)',
    borderColor: 'rgba(9, 114, 211, 0.4)',
  },
}

export const Toast: React.FC<ToastProps> = ({
  id,
  message,
  type,
  duration,
  dismissible,
  onDismiss,
  title,
}) => {
  const [isExiting, setIsExiting] = useState(false)
  const [progress, setProgress] = useState(100)
  const config = typeConfig[type]
  const Icon = config.icon

  useEffect(() => {
    if (duration > 0) {
      const startTime = Date.now()
      const interval = setInterval(() => {
        const elapsed = Date.now() - startTime
        const remaining = Math.max(0, 100 - (elapsed / duration) * 100)
        setProgress(remaining)

        if (remaining <= 0) {
          clearInterval(interval)
          handleDismiss()
        }
      }, 50)

      return () => clearInterval(interval)
    }
  }, [duration])

  const handleDismiss = () => {
    setIsExiting(true)
    setTimeout(() => {
      onDismiss(id)
    }, 200)
  }

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'stretch',
        minWidth: '320px',
        maxWidth: '420px',
        background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.98) 0%, rgba(35, 42, 49, 0.98) 100%)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderRadius: '10px',
        border: `1px solid ${config.borderColor}`,
        boxShadow: `0 8px 32px rgba(0, 0, 0, 0.4), 0 0 20px ${config.color}15`,
        overflow: 'hidden',
        animation: isExiting
          ? 'slideOutRight 0.2s ease-in forwards'
          : 'slideInRight 0.3s ease-out',
        '@keyframes slideInRight': {
          '0%': {
            opacity: 0,
            transform: 'translateX(30px)',
          },
          '100%': {
            opacity: 1,
            transform: 'translateX(0)',
          },
        },
        '@keyframes slideOutRight': {
          '0%': {
            opacity: 1,
            transform: 'translateX(0)',
          },
          '100%': {
            opacity: 0,
            transform: 'translateX(30px)',
          },
        },
      }}
    >
      {/* Left colored border indicator */}
      <Box
        sx={{
          width: '4px',
          backgroundColor: config.color,
          flexShrink: 0,
        }}
      />

      {/* Content area */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          padding: '12px 16px',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5 }}>
          {/* Icon */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 28,
              height: 28,
              borderRadius: '6px',
              backgroundColor: config.bgColor,
              flexShrink: 0,
            }}
          >
            <Icon sx={{ fontSize: 18, color: config.color }} />
          </Box>

          {/* Message */}
          <Box sx={{ flex: 1, minWidth: 0 }}>
            {title && (
              <Typography
                variant="body2"
                sx={{
                  fontWeight: 600,
                  color: '#FFFFFF',
                  mb: 0.25,
                }}
              >
                {title}
              </Typography>
            )}
            <Typography
              variant="body2"
              sx={{
                color: title ? 'text.secondary' : '#FFFFFF',
                wordBreak: 'break-word',
              }}
            >
              {message}
            </Typography>
          </Box>

          {/* Close button */}
          {dismissible && (
            <IconButton
              size="small"
              onClick={handleDismiss}
              sx={{
                padding: '4px',
                color: 'text.secondary',
                '&:hover': {
                  color: '#FFFFFF',
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              <CloseIcon sx={{ fontSize: 16 }} />
            </IconButton>
          )}
        </Box>

        {/* Progress bar */}
        {duration > 0 && (
          <Box
            sx={{
              mt: 1.5,
              height: 2,
              backgroundColor: 'rgba(65, 77, 92, 0.3)',
              borderRadius: 1,
              overflow: 'hidden',
            }}
          >
            <Box
              sx={{
                height: '100%',
                width: `${progress}%`,
                backgroundColor: config.color,
                borderRadius: 1,
                transition: 'width 0.05s linear',
              }}
            />
          </Box>
        )}
      </Box>
    </Box>
  )
}

export default Toast
