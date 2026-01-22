import React, { forwardRef } from 'react'
import { Box, BoxProps } from '@mui/material'
import { fsiColors, fsiGradients, glassTokens, glowColors } from '../../theme'

export interface GlassCardProps extends Omit<BoxProps, 'ref'> {
  /** Card variant style */
  variant?: 'default' | 'elevated' | 'inset' | 'subtle' | 'highlighted'
  /** Blur intensity */
  blur?: 'sm' | 'md' | 'lg' | 'xl'
  /** Gradient background style */
  gradient?: 'default' | 'primary' | 'success' | 'error' | 'warning' | 'info' | 'mesh'
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
  sm: glassTokens.blur.sm,
  md: glassTokens.blur.md,
  lg: glassTokens.blur.lg,
  xl: glassTokens.blur.xl,
}

const gradients = {
  default: fsiGradients.backgroundCard,
  primary: `linear-gradient(135deg, ${fsiColors.orange.main}10 0%, ${fsiColors.navy[700]} 30%, ${fsiColors.navy[800]} 100%)`,
  success: `linear-gradient(135deg, ${fsiColors.status.success}10 0%, ${fsiColors.navy[700]} 30%, ${fsiColors.navy[800]} 100%)`,
  error: `linear-gradient(135deg, ${fsiColors.status.error}10 0%, ${fsiColors.navy[700]} 30%, ${fsiColors.navy[800]} 100%)`,
  warning: `linear-gradient(135deg, ${fsiColors.status.warning}10 0%, ${fsiColors.navy[700]} 30%, ${fsiColors.navy[800]} 100%)`,
  info: `linear-gradient(135deg, ${fsiColors.status.info}10 0%, ${fsiColors.navy[700]} 30%, ${fsiColors.navy[800]} 100%)`,
  mesh: fsiGradients.meshGradient,
}

const variantStyles = {
  default: {
    boxShadow: '0 4px 24px rgba(0, 0, 0, 0.2)',
    border: `1px solid ${fsiColors.navy[400]}40`,
  },
  elevated: {
    boxShadow: '0 8px 40px rgba(0, 0, 0, 0.35)',
    border: `1px solid ${fsiColors.navy[400]}50`,
  },
  inset: {
    boxShadow: 'inset 0 2px 12px rgba(0, 0, 0, 0.25)',
    border: `1px solid ${fsiColors.navy[400]}30`,
  },
  subtle: {
    boxShadow: '0 2px 12px rgba(0, 0, 0, 0.15)',
    border: `1px solid ${fsiColors.navy[400]}25`,
  },
  highlighted: {
    boxShadow: `0 8px 40px rgba(0, 0, 0, 0.35), 0 0 30px ${fsiColors.orange.glow}`,
    border: `1px solid ${fsiColors.orange.main}40`,
  },
}

/**
 * GlassCard Component - AWS FSI Style
 *
 * A reusable card with modern glassmorphism styling optimized for AWS FSI branding.
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
      blur = 'md',
      gradient = 'default',
      glowColor,
      hoverEffect = 'all',
      animateIn = true,
      animationDelay = 0,
      borderRadius = 16,
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
              boxShadow: '0 12px 40px rgba(0, 0, 0, 0.35)',
            },
          }
        case 'glow':
          return {
            '&:hover': {
              boxShadow: `0 4px 24px rgba(0, 0, 0, 0.2), 0 0 40px ${baseColor}25`,
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
              transform: 'translateY(-3px)',
              boxShadow: `0 12px 40px rgba(0, 0, 0, 0.3), 0 0 30px ${baseColor}20`,
              borderColor: `${baseColor}50`,
            },
            '&:active': {
              transform: 'translateY(-1px) scale(0.995)',
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
          animation: `slideInUp 0.5s cubic-bezier(0.4, 0, 0.2, 1) ${animationDelay}s both`,
          '@keyframes slideInUp': {
            '0%': {
              opacity: 0,
              transform: 'translateY(24px)',
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
          border: `1px solid ${glowColor}40`,
          boxShadow: `${variantStyles[variant].boxShadow}, 0 0 30px ${glowColor}20`,
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
          transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
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
