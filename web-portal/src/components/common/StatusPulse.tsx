import React from 'react'
import { Box, Chip, Typography } from '@mui/material'
import { glowColors } from '../../theme'

export type StatusType = 'healthy' | 'degraded' | 'unhealthy' | 'offline' | 'processing' | 'pending'

export interface StatusPulseProps {
  /** Status type */
  status: StatusType
  /** Size of the indicator */
  size?: 'small' | 'medium' | 'large'
  /** Show label text */
  showLabel?: boolean
  /** Custom label override */
  label?: string
  /** Enable pulse animation */
  animated?: boolean
  /** Variant display style */
  variant?: 'dot' | 'chip' | 'badge'
}

const statusConfig: Record<StatusType, {
  color: string
  label: string
  bgColor: string
  shouldPulse: boolean
}> = {
  healthy: {
    color: glowColors.success,
    label: 'Healthy',
    bgColor: 'rgba(29, 129, 2, 0.15)',
    shouldPulse: true,
  },
  degraded: {
    color: glowColors.warning,
    label: 'Degraded',
    bgColor: 'rgba(255, 153, 0, 0.15)',
    shouldPulse: true,
  },
  unhealthy: {
    color: glowColors.error,
    label: 'Unhealthy',
    bgColor: 'rgba(209, 50, 18, 0.15)',
    shouldPulse: false,
  },
  offline: {
    color: glowColors.neutral,
    label: 'Offline',
    bgColor: 'rgba(155, 167, 180, 0.15)',
    shouldPulse: false,
  },
  processing: {
    color: glowColors.info,
    label: 'Processing',
    bgColor: 'rgba(9, 114, 211, 0.15)',
    shouldPulse: true,
  },
  pending: {
    color: glowColors.neutral,
    label: 'Pending',
    bgColor: 'rgba(155, 167, 180, 0.15)',
    shouldPulse: false,
  },
}

const sizeConfig = {
  small: { dot: 8, ring: 16, chip: 'small' as const, fontSize: '0.7rem' },
  medium: { dot: 10, ring: 20, chip: 'medium' as const, fontSize: '0.75rem' },
  large: { dot: 14, ring: 28, chip: 'medium' as const, fontSize: '0.875rem' },
}

/**
 * StatusPulse Component
 *
 * Enhanced status indicator with pulse and ripple animations.
 * Replaces LiveIndicator with more versatile options.
 *
 * @example
 * <StatusPulse status="healthy" variant="chip" />
 * <StatusPulse status="processing" variant="dot" animated />
 */
export const StatusPulse: React.FC<StatusPulseProps> = ({
  status,
  size = 'medium',
  showLabel = true,
  label,
  animated = true,
  variant = 'chip',
}) => {
  const config = statusConfig[status]
  const sizeConf = sizeConfig[size]
  const displayLabel = label || config.label
  const shouldAnimate = animated && config.shouldPulse

  // Render just the dot
  const renderDot = () => (
    <Box
      sx={{
        position: 'relative',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: sizeConf.ring,
        height: sizeConf.ring,
      }}
    >
      {/* Core dot */}
      <Box
        sx={{
          width: sizeConf.dot,
          height: sizeConf.dot,
          borderRadius: '50%',
          backgroundColor: config.color,
          boxShadow: `0 0 ${sizeConf.dot / 2}px ${config.color}`,
          zIndex: 2,
          animation: shouldAnimate ? 'pulse 2s ease-in-out infinite' : 'none',
          '@keyframes pulse': {
            '0%': {
              opacity: 1,
              transform: 'scale(1)',
            },
            '50%': {
              opacity: 0.8,
              transform: 'scale(1.15)',
            },
            '100%': {
              opacity: 1,
              transform: 'scale(1)',
            },
          },
        }}
      />

      {/* Ripple ring */}
      {shouldAnimate && (
        <Box
          sx={{
            position: 'absolute',
            width: sizeConf.dot,
            height: sizeConf.dot,
            borderRadius: '50%',
            border: `1px solid ${config.color}`,
            animation: 'ripple 2s ease-out infinite',
            '@keyframes ripple': {
              '0%': {
                transform: 'scale(1)',
                opacity: 0.6,
              },
              '100%': {
                transform: 'scale(2.5)',
                opacity: 0,
              },
            },
          }}
        />
      )}
    </Box>
  )

  // Render variants
  switch (variant) {
    case 'dot':
      if (!showLabel) {
        return renderDot()
      }
      return (
        <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 1 }}>
          {renderDot()}
          <Typography
            variant="body2"
            sx={{
              color: config.color,
              fontWeight: 500,
              fontSize: sizeConf.fontSize,
            }}
          >
            {displayLabel}
          </Typography>
        </Box>
      )

    case 'badge':
      return (
        <Box
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 0.75,
            padding: '4px 10px',
            borderRadius: '12px',
            backgroundColor: config.bgColor,
            border: `1px solid ${config.color}30`,
            backdropFilter: 'blur(4px)',
          }}
        >
          {renderDot()}
          {showLabel && (
            <Typography
              variant="body2"
              sx={{
                color: config.color,
                fontWeight: 600,
                fontSize: sizeConf.fontSize,
              }}
            >
              {displayLabel}
            </Typography>
          )}
        </Box>
      )

    case 'chip':
    default:
      return (
        <Chip
          size={sizeConf.chip}
          icon={
            <Box sx={{ display: 'flex', ml: 0.5 }}>
              {renderDot()}
            </Box>
          }
          label={showLabel ? displayLabel : undefined}
          sx={{
            backgroundColor: config.bgColor,
            color: config.color,
            border: `1px solid ${config.color}40`,
            fontWeight: 600,
            fontSize: sizeConf.fontSize,
            backdropFilter: 'blur(4px)',
            '& .MuiChip-icon': {
              marginLeft: '6px',
              marginRight: showLabel ? '-4px' : '6px',
            },
            '& .MuiChip-label': {
              paddingRight: showLabel ? '12px' : '0',
              paddingLeft: showLabel ? '4px' : '0',
            },
          }}
        />
      )
  }
}

/**
 * Map legacy status strings to StatusPulse status types
 */
export const mapLegacyStatus = (status: string): StatusType => {
  const statusMap: Record<string, StatusType> = {
    'HEALTHY': 'healthy',
    'DEGRADED': 'degraded',
    'UNHEALTHY': 'unhealthy',
    'OFFLINE': 'offline',
    'PROCESSING': 'processing',
    'PENDING': 'pending',
    'RUNNING': 'processing',
    'COMPLETED': 'healthy',
    'FAILED': 'unhealthy',
    'IDLE': 'pending',
  }
  return statusMap[status.toUpperCase()] || 'pending'
}

export default StatusPulse
