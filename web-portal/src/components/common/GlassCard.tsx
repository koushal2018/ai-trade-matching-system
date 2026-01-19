import React, { forwardRef } from 'react'
import { Box, BoxProps } from '@mui/material'
import { glowColors } from '../../theme'

export interface GlassCardProps extends Omit<BoxProps, 'ref'> {
  /** Card variant style */
  variant?: 'default' | 'elevated' | 'inset' | 'subtle'
  /** Blur intensity */
  blur?: 'sm' | 'md' | 'lg' | 'xl'
  /** Gradient background style */
  gradient?: 'default' | 'primary' | 'success' | 'error' | 'warning' | 'info'
  /** Glow color for the card border and shadow */
  glowColor?: string
  /** Hover effect type */
  hoverEffect?: 'lift' | 'glow' | 'border' | 'all' | 'none'
  /** Enable entry animation */
  animateIn?: boolean
  /** Animation delay in seconds */
  animationDelay?: number
  /** Custom border radius */
  borderRadius?: number
  /** Children content */
  children?: React.ReactNode
}

const blurValues = {
  sm: 'blur(4px)',
  md: 'blur(10px)',
  lg: 'blur(20px)',
  xl: 'blur(40px)',
}

const gradients = {
  default: 'linear-gradient(135deg, rgba(28, 33, 39, 0.95) 0%, rgba(35, 42, 49, 0.95) 100%)',
  primary: 'linear-gradient(135deg, rgba(255, 153, 0, 0.08) 0%, rgba(28, 33, 39, 0.95) 50%, rgba(35, 42, 49, 0.95) 100%)',
  success: 'linear-gradient(135deg, rgba(29, 129, 2, 0.08) 0%, rgba(28, 33, 39, 0.95) 50%, rgba(35, 42, 49, 0.95) 100%)',
  error: 'linear-gradient(135deg, rgba(209, 50, 18, 0.08) 0%, rgba(28, 33, 39, 0.95) 50%, rgba(35, 42, 49, 0.95) 100%)',
  warning: 'linear-gradient(135deg, rgba(255, 153, 0, 0.08) 0%, rgba(28, 33, 39, 0.95) 50%, rgba(35, 42, 49, 0.95) 100%)',
  info: 'linear-gradient(135deg, rgba(9, 114, 211, 0.08) 0%, rgba(28, 33, 39, 0.95) 50%, rgba(35, 42, 49, 0.95) 100%)',
}

const variantStyles = {
  default: {
    boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
    border: '1px solid rgba(65, 77, 92, 0.3)',
  },
  elevated: {
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(65, 77, 92, 0.4)',
  },
  inset: {
    boxShadow: 'inset 0 2px 8px rgba(0, 0, 0, 0.2)',
    border: '1px solid rgba(65, 77, 92, 0.2)',
  },
  subtle: {
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
    border: '1px solid rgba(65, 77, 92, 0.15)',
  },
}

/**
 * GlassCard Component
 *
 * A reusable card with glassmorphism styling, hover effects, and entry animations.
 *
 * @example
 * <GlassCard variant="elevated" glowColor="#FF9900" animateIn>
 *   <Typography>Content</Typography>
 * </GlassCard>
 */
export const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  (
    {
      variant = 'default',
      blur = 'lg',
      gradient = 'default',
      glowColor,
      hoverEffect = 'all',
      animateIn = true,
      animationDelay = 0,
      borderRadius = 12,
      children,
      sx,
      ...rest
    },
    ref
  ) => {
    const baseColor = glowColor || glowColors.primary

    // Build hover styles based on effect type
    const getHoverStyles = () => {
      switch (hoverEffect) {
        case 'lift':
          return {
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
            },
          }
        case 'glow':
          return {
            '&:hover': {
              boxShadow: `0 4px 16px rgba(0, 0, 0, 0.2), 0 0 25px ${baseColor}30`,
              borderColor: `${baseColor}50`,
            },
          }
        case 'border':
          return {
            '&:hover': {
              borderColor: `${baseColor}60`,
            },
          }
        case 'all':
          return {
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: `0 8px 25px ${baseColor}20`,
              borderColor: `${baseColor}40`,
            },
            '&:active': {
              transform: 'translateY(-2px) scale(0.99)',
            },
          }
        case 'none':
        default:
          return {}
      }
    }

    // Entry animation keyframes
    const animationStyles = animateIn
      ? {
          animation: `slideInUp 0.6s ease-out ${animationDelay}s both`,
          '@keyframes slideInUp': {
            '0%': {
              opacity: 0,
              transform: 'translateY(30px)',
            },
            '100%': {
              opacity: 1,
              transform: 'translateY(0)',
            },
          },
        }
      : {}

    // Glow effect if glowColor is specified
    const glowStyles = glowColor
      ? {
          border: `1px solid ${glowColor}30`,
          boxShadow: `${variantStyles[variant].boxShadow}, 0 0 20px ${glowColor}15`,
        }
      : {}

    return (
      <Box
        ref={ref}
        sx={{
          // Base glass styles
          background: gradients[gradient],
          backdropFilter: blurValues[blur],
          WebkitBackdropFilter: blurValues[blur],
          borderRadius: `${borderRadius}px`,
          transition: 'all 0.15s ease-out',
          // Variant styles
          ...variantStyles[variant],
          // Glow override
          ...glowStyles,
          // Hover effects
          ...getHoverStyles(),
          // Entry animation
          ...animationStyles,
          // Custom sx prop overrides
          ...sx,
        }}
        {...rest}
      >
        {children}
      </Box>
    )
  }
)

GlassCard.displayName = 'GlassCard'

export default GlassCard
