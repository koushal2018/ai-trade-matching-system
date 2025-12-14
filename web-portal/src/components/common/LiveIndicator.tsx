import React from 'react'
import { Box, Chip, Typography } from '@mui/material'
import { Circle as CircleIcon } from '@mui/icons-material'

interface LiveIndicatorProps {
  status: 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY' | 'OFFLINE'
  size?: 'small' | 'medium' | 'large'
  showLabel?: boolean
  animated?: boolean
}

const statusConfig = {
  HEALTHY: {
    color: '#1D8102',
    bgColor: 'rgba(29, 129, 2, 0.15)',
    label: 'Live',
    pulseColor: '#1D8102'
  },
  DEGRADED: {
    color: '#FF9900',
    bgColor: 'rgba(255, 153, 0, 0.15)',
    label: 'Degraded',
    pulseColor: '#FF9900'
  },
  UNHEALTHY: {
    color: '#D13212',
    bgColor: 'rgba(209, 50, 18, 0.15)',
    label: 'Issues',
    pulseColor: '#D13212'
  },
  OFFLINE: {
    color: '#687078',
    bgColor: 'rgba(104, 112, 120, 0.15)',
    label: 'Offline',
    pulseColor: '#687078'
  }
}

const sizeConfig = {
  small: { dot: 8, chip: 'small' as const },
  medium: { dot: 12, chip: 'medium' as const },
  large: { dot: 16, chip: 'medium' as const }
}

export default function LiveIndicator({ 
  status, 
  size = 'medium', 
  showLabel = true, 
  animated = true 
}: LiveIndicatorProps) {
  const config = statusConfig[status]
  const sizeConf = sizeConfig[size]

  if (showLabel) {
    return (
      <Chip
        size={sizeConf.chip}
        icon={
          <Box
            sx={{
              position: 'relative',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CircleIcon
              sx={{
                fontSize: sizeConf.dot,
                color: config.color,
                filter: animated ? `drop-shadow(0 0 4px ${config.color}60)` : 'none',
                animation: animated && status === 'HEALTHY' ? 'pulse 2s infinite' : 'none',
                '@keyframes pulse': {
                  '0%': {
                    opacity: 1,
                    transform: 'scale(1)',
                  },
                  '50%': {
                    opacity: 0.7,
                    transform: 'scale(1.1)',
                  },
                  '100%': {
                    opacity: 1,
                    transform: 'scale(1)',
                  },
                },
              }}
            />
            {animated && status === 'HEALTHY' && (
              <Box
                sx={{
                  position: 'absolute',
                  width: sizeConf.dot,
                  height: sizeConf.dot,
                  borderRadius: '50%',
                  backgroundColor: config.color,
                  opacity: 0.3,
                  animation: 'ripple 2s infinite',
                  '@keyframes ripple': {
                    '0%': {
                      transform: 'scale(1)',
                      opacity: 0.3,
                    },
                    '100%': {
                      transform: 'scale(2)',
                      opacity: 0,
                    },
                  },
                }}
              />
            )}
          </Box>
        }
        label={config.label}
        sx={{
          backgroundColor: config.bgColor,
          color: config.color,
          border: `1px solid ${config.color}40`,
          fontWeight: 600,
          fontSize: size === 'small' ? '0.7rem' : '0.75rem',
          '& .MuiChip-icon': {
            marginLeft: '4px',
          },
        }}
      />
    )
  }

  // Just the dot without label
  return (
    <Box
      sx={{
        position: 'relative',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <CircleIcon
        sx={{
          fontSize: sizeConf.dot,
          color: config.color,
          filter: animated ? `drop-shadow(0 0 4px ${config.color}60)` : 'none',
          animation: animated && status === 'HEALTHY' ? 'pulse 2s infinite' : 'none',
          '@keyframes pulse': {
            '0%': {
              opacity: 1,
              transform: 'scale(1)',
            },
            '50%': {
              opacity: 0.7,
              transform: 'scale(1.1)',
            },
            '100%': {
              opacity: 1,
              transform: 'scale(1)',
            },
          },
        }}
      />
      {animated && status === 'HEALTHY' && (
        <Box
          sx={{
            position: 'absolute',
            width: sizeConf.dot,
            height: sizeConf.dot,
            borderRadius: '50%',
            backgroundColor: config.color,
            opacity: 0.3,
            animation: 'ripple 2s infinite',
            '@keyframes ripple': {
              '0%': {
                transform: 'scale(1)',
                opacity: 0.3,
              },
              '100%': {
                transform: 'scale(2)',
                opacity: 0,
              },
            },
          }}
        />
      )}
    </Box>
  )
}

// Live timestamp component
export function LiveTimestamp() {
  const [timestamp, setTimestamp] = React.useState(new Date())

  React.useEffect(() => {
    const interval = setInterval(() => {
      setTimestamp(new Date())
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  const secondsAgo = Math.floor((Date.now() - timestamp.getTime()) / 1000)

  return (
    <Typography
      variant="caption"
      sx={{
        color: 'text.secondary',
        display: 'flex',
        alignItems: 'center',
        gap: 0.5,
        animation: 'fadeIn 0.3s ease-in-out',
        '@keyframes fadeIn': {
          '0%': { opacity: 0 },
          '100%': { opacity: 1 },
        },
      }}
    >
      <LiveIndicator status="HEALTHY" size="small" showLabel={false} />
      Last updated: {secondsAgo}s ago
    </Typography>
  )
}