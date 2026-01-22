/**
 * AWS FSI Glassmorphism Design System
 *
 * Shared glass effect styles, variants, and utilities for
 * creating frosted glass UI components with AWS FSI branding.
 */

import { SxProps, Theme } from '@mui/material'
import { fsiColors, fsiGradients } from '../theme'

// Re-export glass tokens from theme
export const glassTokens = {
  // Blur levels
  blur: {
    none: 'blur(0)',
    sm: 'blur(8px)',
    md: 'blur(16px)',
    lg: 'blur(24px)',
    xl: 'blur(40px)',
  },

  // Opacity levels for glass backgrounds
  opacity: {
    light: 0.03,
    medium: 0.06,
    dark: 0.1,
    solid: 0.15,
  },

  // Border opacity
  borderOpacity: {
    subtle: 0.15,
    medium: 0.25,
    strong: 0.4,
  },

  // Shadow depths
  shadow: {
    sm: '0 2px 12px rgba(0, 0, 0, 0.15)',
    md: '0 4px 24px rgba(0, 0, 0, 0.2)',
    lg: '0 8px 40px rgba(0, 0, 0, 0.3)',
    xl: '0 16px 56px rgba(0, 0, 0, 0.4)',
  },
}

// FSI Status glow colors
export const glowColors = {
  primary: fsiColors.orange.main,
  success: fsiColors.status.success,
  error: fsiColors.status.error,
  warning: fsiColors.status.warning,
  info: fsiColors.status.info,
  purple: fsiColors.accent.purple,
  cyan: fsiColors.accent.cyan,
  neutral: fsiColors.text.muted,
}

// Glass background colors (with opacity) - FSI Navy theme
export const glassBackgrounds = {
  default: `${fsiColors.navy[700]}E6`,
  dark: `${fsiColors.navy[900]}F2`,
  light: `${fsiColors.navy[600]}B3`,
  elevated: `${fsiColors.navy[600]}D9`,
  inset: `${fsiColors.navy[800]}E6`,
}

// Gradient backgrounds - FSI themed
export const gradients = {
  default: fsiGradients.backgroundCard,
  primary: `linear-gradient(135deg, ${fsiColors.orange.main}15 0%, ${fsiColors.navy[700]} 40%, ${fsiColors.navy[800]} 100%)`,
  success: `linear-gradient(135deg, ${fsiColors.status.success}15 0%, ${fsiColors.navy[700]} 40%, ${fsiColors.navy[800]} 100%)`,
  error: `linear-gradient(135deg, ${fsiColors.status.error}15 0%, ${fsiColors.navy[700]} 40%, ${fsiColors.navy[800]} 100%)`,
  warning: `linear-gradient(135deg, ${fsiColors.status.warning}15 0%, ${fsiColors.navy[700]} 40%, ${fsiColors.navy[800]} 100%)`,
  info: `linear-gradient(135deg, ${fsiColors.status.info}15 0%, ${fsiColors.navy[700]} 40%, ${fsiColors.navy[800]} 100%)`,
  subtle: `linear-gradient(135deg, ${fsiColors.navy[600]}80 0%, ${fsiColors.navy[700]}CC 100%)`,
  mesh: fsiGradients.meshGradient,
  hero: fsiGradients.heroGradient,
}

// Glass border styles - FSI themed
export const glassBorders = {
  default: `1px solid ${fsiColors.navy[400]}40`,
  subtle: `1px solid ${fsiColors.navy[400]}25`,
  strong: `1px solid ${fsiColors.navy[400]}60`,
  glow: (color: string) => `1px solid ${color}50`,
}

// Base glass effect styles
export const glassBase: SxProps<Theme> = {
  backgroundColor: glassBackgrounds.default,
  backdropFilter: glassTokens.blur.md,
  WebkitBackdropFilter: glassTokens.blur.md,
  border: glassBorders.default,
  boxShadow: glassTokens.shadow.md,
}

// Glass card variants - FSI themed
export const glassVariants = {
  default: {
    background: gradients.default,
    backdropFilter: glassTokens.blur.md,
    WebkitBackdropFilter: glassTokens.blur.md,
    border: glassBorders.default,
    boxShadow: glassTokens.shadow.md,
  } as SxProps<Theme>,

  elevated: {
    background: fsiGradients.backgroundElevated,
    backdropFilter: glassTokens.blur.lg,
    WebkitBackdropFilter: glassTokens.blur.lg,
    border: glassBorders.strong,
    boxShadow: glassTokens.shadow.lg,
  } as SxProps<Theme>,

  inset: {
    background: glassBackgrounds.inset,
    backdropFilter: glassTokens.blur.sm,
    WebkitBackdropFilter: glassTokens.blur.sm,
    border: glassBorders.subtle,
    boxShadow: 'inset 0 2px 12px rgba(0, 0, 0, 0.25)',
  } as SxProps<Theme>,

  subtle: {
    background: gradients.subtle,
    backdropFilter: glassTokens.blur.sm,
    WebkitBackdropFilter: glassTokens.blur.sm,
    border: glassBorders.subtle,
    boxShadow: glassTokens.shadow.sm,
  } as SxProps<Theme>,

  highlighted: {
    background: gradients.primary,
    backdropFilter: glassTokens.blur.lg,
    WebkitBackdropFilter: glassTokens.blur.lg,
    border: `1px solid ${fsiColors.orange.main}50`,
    boxShadow: `${glassTokens.shadow.lg}, 0 0 40px ${fsiColors.orange.glow}`,
  } as SxProps<Theme>,
}

// Create a glow variant with a specific color
export const createGlowVariant = (color: string): SxProps<Theme> => ({
  background: gradients.default,
  backdropFilter: glassTokens.blur.md,
  WebkitBackdropFilter: glassTokens.blur.md,
  border: `1px solid ${color}40`,
  boxShadow: `${glassTokens.shadow.md}, 0 0 30px ${color}20`,
  '&:hover': {
    border: `1px solid ${color}60`,
    boxShadow: `${glassTokens.shadow.lg}, 0 0 40px ${color}30`,
  },
})

// Gradient overlays for cards - FSI themed
export const gradientOverlays = {
  primary: {
    position: 'relative',
    '&::before': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      height: '3px',
      background: `linear-gradient(90deg, ${glowColors.primary} 0%, transparent 100%)`,
      borderRadius: '16px 16px 0 0',
    },
  } as SxProps<Theme>,

  success: {
    position: 'relative',
    '&::before': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      height: '3px',
      background: `linear-gradient(90deg, ${glowColors.success} 0%, transparent 100%)`,
      borderRadius: '16px 16px 0 0',
    },
  } as SxProps<Theme>,

  error: {
    position: 'relative',
    '&::before': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      height: '3px',
      background: `linear-gradient(90deg, ${glowColors.error} 0%, transparent 100%)`,
      borderRadius: '16px 16px 0 0',
    },
  } as SxProps<Theme>,

  cyan: {
    position: 'relative',
    '&::before': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      height: '3px',
      background: `linear-gradient(90deg, ${glowColors.cyan} 0%, transparent 100%)`,
      borderRadius: '16px 16px 0 0',
    },
  } as SxProps<Theme>,
}

// Status-specific card backgrounds - FSI themed
export const statusBackgrounds = {
  success: {
    background: `linear-gradient(135deg, ${fsiColors.status.success}12 0%, ${fsiColors.navy[700]} 50%)`,
    borderLeft: `4px solid ${glowColors.success}`,
  },
  error: {
    background: `linear-gradient(135deg, ${fsiColors.status.error}12 0%, ${fsiColors.navy[700]} 50%)`,
    borderLeft: `4px solid ${glowColors.error}`,
  },
  warning: {
    background: `linear-gradient(135deg, ${fsiColors.status.warning}12 0%, ${fsiColors.navy[700]} 50%)`,
    borderLeft: `4px solid ${glowColors.warning}`,
  },
  info: {
    background: `linear-gradient(135deg, ${fsiColors.status.info}12 0%, ${fsiColors.navy[700]} 50%)`,
    borderLeft: `4px solid ${glowColors.info}`,
  },
}

// Hover effect utilities - FSI themed
export const glassHoverEffects = {
  lift: {
    transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
    '&:hover': {
      transform: 'translateY(-4px)',
      boxShadow: glassTokens.shadow.lg,
    },
  },

  glow: (color: string = glowColors.primary) => ({
    transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
    '&:hover': {
      boxShadow: `${glassTokens.shadow.md}, 0 0 40px ${color}25`,
      borderColor: `${color}60`,
    },
  }),

  border: (color: string = glowColors.primary) => ({
    transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
    '&:hover': {
      borderColor: `${color}70`,
    },
  }),

  all: (color: string = glowColors.primary) => ({
    transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
    '&:hover': {
      transform: 'translateY(-3px)',
      boxShadow: `0 12px 40px rgba(0, 0, 0, 0.3), 0 0 30px ${color}20`,
      borderColor: `${color}50`,
    },
    '&:active': {
      transform: 'translateY(-1px) scale(0.995)',
    },
  }),
}

// Complete glass card style builder - FSI themed
export const createGlassCardStyle = (options: {
  variant?: 'default' | 'elevated' | 'inset' | 'subtle' | 'highlighted'
  gradient?: 'default' | 'primary' | 'success' | 'error' | 'warning' | 'info' | 'mesh'
  glowColor?: string
  hoverEffect?: 'lift' | 'glow' | 'border' | 'all' | 'none'
  borderRadius?: number
} = {}): SxProps<Theme> => {
  const {
    variant = 'default',
    gradient = 'default',
    glowColor,
    hoverEffect = 'all',
    borderRadius = 16,
  } = options

  const baseStyle = {
    ...glassVariants[variant],
    background: gradients[gradient] || gradients.default,
    borderRadius: `${borderRadius}px`,
  }

  // Add glow if specified
  const glowStyle = glowColor ? {
    border: `1px solid ${glowColor}40`,
    boxShadow: `${glassTokens.shadow.md}, 0 0 30px ${glowColor}20`,
  } : {}

  // Add hover effect
  let hoverStyle = {}
  if (hoverEffect !== 'none') {
    if (hoverEffect === 'lift') {
      hoverStyle = glassHoverEffects.lift
    } else if (hoverEffect === 'glow') {
      hoverStyle = glassHoverEffects.glow(glowColor || glowColors.primary)
    } else if (hoverEffect === 'border') {
      hoverStyle = glassHoverEffects.border(glowColor || glowColors.primary)
    } else {
      hoverStyle = glassHoverEffects.all(glowColor || glowColors.primary)
    }
  }

  return {
    ...baseStyle,
    ...glowStyle,
    ...hoverStyle,
  }
}

// Input field glass styles - FSI themed
export const glassInputStyles: SxProps<Theme> = {
  '& .MuiOutlinedInput-root': {
    backgroundColor: `${fsiColors.navy[800]}80`,
    backdropFilter: glassTokens.blur.sm,
    borderRadius: '10px',
    '& fieldset': {
      borderColor: `${fsiColors.navy[400]}40`,
    },
    '&:hover fieldset': {
      borderColor: `${fsiColors.orange.main}50`,
    },
    '&.Mui-focused fieldset': {
      borderColor: fsiColors.orange.main,
      boxShadow: `0 0 16px ${fsiColors.orange.glow}`,
    },
  },
}

// Export a combined styles object for convenience
export default {
  glassTokens,
  glowColors,
  glassBackgrounds,
  gradients,
  glassBorders,
  glassBase,
  glassVariants,
  createGlowVariant,
  gradientOverlays,
  statusBackgrounds,
  glassHoverEffects,
  createGlassCardStyle,
  glassInputStyles,
}
