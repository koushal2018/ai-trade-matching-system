/**
 * Glassmorphism Design System
 *
 * Shared glass effect styles, variants, and utilities for
 * creating frosted glass UI components.
 */

import { SxProps, Theme } from '@mui/material'

// Glass effect configuration tokens
export const glassTokens = {
  // Blur levels
  blur: {
    none: 'blur(0)',
    sm: 'blur(4px)',
    md: 'blur(10px)',
    lg: 'blur(20px)',
    xl: 'blur(40px)',
  },

  // Opacity levels for glass backgrounds
  opacity: {
    light: 0.05,
    medium: 0.1,
    dark: 0.15,
    solid: 0.25,
  },

  // Border opacity
  borderOpacity: {
    subtle: 0.1,
    medium: 0.2,
    strong: 0.3,
  },

  // Shadow depths
  shadow: {
    sm: '0 2px 8px rgba(0, 0, 0, 0.15)',
    md: '0 4px 16px rgba(0, 0, 0, 0.2)',
    lg: '0 8px 32px rgba(0, 0, 0, 0.25)',
    xl: '0 16px 48px rgba(0, 0, 0, 0.3)',
  },
}

// Status glow colors
export const glowColors = {
  primary: '#FF9900',
  success: '#1D8102',
  error: '#D13212',
  warning: '#FF9900',
  info: '#0972D3',
  purple: '#9C27B0',
  neutral: '#9BA7B4',
}

// Glass background colors (with opacity)
export const glassBackgrounds = {
  default: 'rgba(28, 33, 39, 0.8)',
  dark: 'rgba(15, 20, 25, 0.9)',
  light: 'rgba(35, 42, 49, 0.7)',
  elevated: 'rgba(40, 48, 56, 0.85)',
  inset: 'rgba(20, 25, 30, 0.9)',
}

// Gradient backgrounds
export const gradients = {
  default: 'linear-gradient(135deg, rgba(28, 33, 39, 0.95) 0%, rgba(35, 42, 49, 0.95) 100%)',
  primary: 'linear-gradient(135deg, rgba(255, 153, 0, 0.1) 0%, rgba(28, 33, 39, 0.95) 100%)',
  success: 'linear-gradient(135deg, rgba(29, 129, 2, 0.1) 0%, rgba(28, 33, 39, 0.95) 100%)',
  error: 'linear-gradient(135deg, rgba(209, 50, 18, 0.1) 0%, rgba(28, 33, 39, 0.95) 100%)',
  warning: 'linear-gradient(135deg, rgba(255, 153, 0, 0.1) 0%, rgba(28, 33, 39, 0.95) 100%)',
  info: 'linear-gradient(135deg, rgba(9, 114, 211, 0.1) 0%, rgba(28, 33, 39, 0.95) 100%)',
  subtle: 'linear-gradient(135deg, rgba(35, 42, 49, 0.6) 0%, rgba(28, 33, 39, 0.8) 100%)',
}

// Glass border styles
export const glassBorders = {
  default: '1px solid rgba(65, 77, 92, 0.3)',
  subtle: '1px solid rgba(65, 77, 92, 0.15)',
  strong: '1px solid rgba(65, 77, 92, 0.5)',
  glow: (color: string) => `1px solid ${color}40`,
}

// Base glass effect styles
export const glassBase: SxProps<Theme> = {
  backgroundColor: glassBackgrounds.default,
  backdropFilter: glassTokens.blur.lg,
  WebkitBackdropFilter: glassTokens.blur.lg, // Safari support
  border: glassBorders.default,
  boxShadow: glassTokens.shadow.md,
}

// Glass card variants
export const glassVariants = {
  default: {
    background: gradients.default,
    backdropFilter: glassTokens.blur.lg,
    WebkitBackdropFilter: glassTokens.blur.lg,
    border: glassBorders.default,
    boxShadow: glassTokens.shadow.md,
  } as SxProps<Theme>,

  elevated: {
    background: gradients.default,
    backdropFilter: glassTokens.blur.xl,
    WebkitBackdropFilter: glassTokens.blur.xl,
    border: glassBorders.strong,
    boxShadow: glassTokens.shadow.lg,
  } as SxProps<Theme>,

  inset: {
    background: 'rgba(20, 25, 30, 0.5)',
    backdropFilter: glassTokens.blur.md,
    WebkitBackdropFilter: glassTokens.blur.md,
    border: glassBorders.subtle,
    boxShadow: 'inset 0 2px 8px rgba(0, 0, 0, 0.2)',
  } as SxProps<Theme>,

  subtle: {
    background: gradients.subtle,
    backdropFilter: glassTokens.blur.md,
    WebkitBackdropFilter: glassTokens.blur.md,
    border: glassBorders.subtle,
    boxShadow: glassTokens.shadow.sm,
  } as SxProps<Theme>,
}

// Create a glow variant with a specific color
export const createGlowVariant = (color: string): SxProps<Theme> => ({
  background: gradients.default,
  backdropFilter: glassTokens.blur.lg,
  WebkitBackdropFilter: glassTokens.blur.lg,
  border: `1px solid ${color}30`,
  boxShadow: `${glassTokens.shadow.md}, 0 0 20px ${color}15`,
  '&:hover': {
    border: `1px solid ${color}50`,
    boxShadow: `${glassTokens.shadow.lg}, 0 0 30px ${color}25`,
  },
})

// Gradient overlays for cards
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
      borderRadius: '8px 8px 0 0',
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
      borderRadius: '8px 8px 0 0',
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
      borderRadius: '8px 8px 0 0',
    },
  } as SxProps<Theme>,
}

// Status-specific card backgrounds
export const statusBackgrounds = {
  success: {
    background: 'linear-gradient(135deg, rgba(29, 129, 2, 0.08) 0%, rgba(28, 33, 39, 0.95) 50%)',
    borderLeft: `3px solid ${glowColors.success}`,
  },
  error: {
    background: 'linear-gradient(135deg, rgba(209, 50, 18, 0.08) 0%, rgba(28, 33, 39, 0.95) 50%)',
    borderLeft: `3px solid ${glowColors.error}`,
  },
  warning: {
    background: 'linear-gradient(135deg, rgba(255, 153, 0, 0.08) 0%, rgba(28, 33, 39, 0.95) 50%)',
    borderLeft: `3px solid ${glowColors.warning}`,
  },
  info: {
    background: 'linear-gradient(135deg, rgba(9, 114, 211, 0.08) 0%, rgba(28, 33, 39, 0.95) 50%)',
    borderLeft: `3px solid ${glowColors.info}`,
  },
}

// Hover effect utilities
export const glassHoverEffects = {
  lift: {
    transition: 'all 0.15s ease-out',
    '&:hover': {
      transform: 'translateY(-4px)',
      boxShadow: glassTokens.shadow.lg,
    },
  },

  glow: (color: string = glowColors.primary) => ({
    transition: 'all 0.15s ease-out',
    '&:hover': {
      boxShadow: `${glassTokens.shadow.md}, 0 0 25px ${color}30`,
      borderColor: `${color}50`,
    },
  }),

  border: (color: string = glowColors.primary) => ({
    transition: 'border-color 0.15s ease-out',
    '&:hover': {
      borderColor: `${color}60`,
    },
  }),

  all: (color: string = glowColors.primary) => ({
    transition: 'all 0.15s ease-out',
    '&:hover': {
      transform: 'translateY(-4px)',
      boxShadow: `0 8px 25px ${color}20`,
      borderColor: `${color}40`,
    },
    '&:active': {
      transform: 'translateY(-2px) scale(0.99)',
    },
  }),
}

// Complete glass card style builder
export const createGlassCardStyle = (options: {
  variant?: 'default' | 'elevated' | 'inset' | 'subtle'
  gradient?: 'default' | 'primary' | 'success' | 'error' | 'warning' | 'info'
  glowColor?: string
  hoverEffect?: 'lift' | 'glow' | 'border' | 'all' | 'none'
  borderRadius?: number
} = {}): SxProps<Theme> => {
  const {
    variant = 'default',
    gradient = 'default',
    glowColor,
    hoverEffect = 'all',
    borderRadius = 12,
  } = options

  const baseStyle = {
    ...glassVariants[variant],
    background: gradients[gradient] || gradients.default,
    borderRadius: `${borderRadius}px`,
  }

  // Add glow if specified
  const glowStyle = glowColor ? {
    border: `1px solid ${glowColor}30`,
    boxShadow: `${glassTokens.shadow.md}, 0 0 20px ${glowColor}15`,
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

// Input field glass styles
export const glassInputStyles: SxProps<Theme> = {
  '& .MuiOutlinedInput-root': {
    backgroundColor: 'rgba(20, 25, 30, 0.5)',
    backdropFilter: glassTokens.blur.sm,
    borderRadius: '8px',
    '& fieldset': {
      borderColor: 'rgba(65, 77, 92, 0.3)',
    },
    '&:hover fieldset': {
      borderColor: 'rgba(255, 153, 0, 0.3)',
    },
    '&.Mui-focused fieldset': {
      borderColor: glowColors.primary,
      boxShadow: `0 0 10px ${glowColors.primary}30`,
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
