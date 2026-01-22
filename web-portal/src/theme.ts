import { createTheme } from '@mui/material/styles'

// AWS FSI Design Tokens
export const fsiColors = {
  // Primary Navy Blues (AWS FSI Brand)
  navy: {
    900: '#0a1628', // Deepest background
    800: '#0d1b2a', // Primary background
    700: '#1b263b', // Card background
    600: '#243b55', // Elevated surfaces
    500: '#2d4a6f', // Interactive elements
    400: '#3d5a80', // Borders, dividers
  },
  // AWS Orange Accent
  orange: {
    main: '#FF9900',
    light: '#FFB84D',
    dark: '#E6890A',
    glow: 'rgba(255, 153, 0, 0.3)',
  },
  // Status Colors
  status: {
    success: '#00D26A',
    successGlow: 'rgba(0, 210, 106, 0.3)',
    error: '#FF4757',
    errorGlow: 'rgba(255, 71, 87, 0.3)',
    warning: '#FFA502',
    warningGlow: 'rgba(255, 165, 2, 0.3)',
    info: '#3498db',
    infoGlow: 'rgba(52, 152, 219, 0.3)',
  },
  // Text Colors
  text: {
    primary: '#FFFFFF',
    secondary: '#A8B2C1',
    muted: '#6B7C93',
    disabled: '#4A5568',
  },
  // Accent Colors
  accent: {
    cyan: '#00D9FF',
    purple: '#A855F7',
    teal: '#14B8A6',
  },
}

// Glass effect tokens for FSI
export const glassTokens = {
  blur: {
    sm: 'blur(8px)',
    md: 'blur(16px)',
    lg: 'blur(24px)',
    xl: 'blur(40px)',
  },
  opacity: {
    light: 0.03,
    medium: 0.06,
    dark: 0.1,
    solid: 0.15,
  },
}

// Glow colors for status indicators
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

// Transition timing presets
export const transitions = {
  instant: '0.1s',
  fast: '0.15s',
  normal: '0.3s',
  slow: '0.5s',
  easeOut: 'ease-out',
  easeInOut: 'ease-in-out',
  smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
  bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
}

// FSI Gradient presets
export const fsiGradients = {
  // Background gradients
  backgroundPrimary: `linear-gradient(180deg, ${fsiColors.navy[900]} 0%, ${fsiColors.navy[800]} 100%)`,
  backgroundCard: `linear-gradient(135deg, ${fsiColors.navy[700]} 0%, ${fsiColors.navy[800]} 100%)`,
  backgroundElevated: `linear-gradient(135deg, ${fsiColors.navy[600]} 0%, ${fsiColors.navy[700]} 100%)`,
  // Accent gradients
  orangeGradient: `linear-gradient(135deg, ${fsiColors.orange.main} 0%, ${fsiColors.orange.dark} 100%)`,
  orangeGlow: `linear-gradient(135deg, ${fsiColors.orange.light} 0%, ${fsiColors.orange.main} 100%)`,
  // Status gradients
  successGradient: `linear-gradient(135deg, ${fsiColors.status.success} 0%, #00B359 100%)`,
  errorGradient: `linear-gradient(135deg, ${fsiColors.status.error} 0%, #E6404F 100%)`,
  // Hero gradient
  heroGradient: `linear-gradient(135deg, ${fsiColors.navy[800]} 0%, ${fsiColors.navy[900]} 50%, ${fsiColors.navy[800]} 100%)`,
  // Mesh gradient for special sections
  meshGradient: `
    radial-gradient(at 40% 20%, rgba(255, 153, 0, 0.08) 0px, transparent 50%),
    radial-gradient(at 80% 0%, rgba(0, 217, 255, 0.05) 0px, transparent 50%),
    radial-gradient(at 0% 50%, rgba(168, 85, 247, 0.05) 0px, transparent 50%),
    ${fsiColors.navy[800]}
  `,
}

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: fsiColors.orange.main,
      light: fsiColors.orange.light,
      dark: fsiColors.orange.dark,
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: fsiColors.accent.cyan,
      contrastText: '#FFFFFF',
    },
    background: {
      default: fsiColors.navy[900],
      paper: fsiColors.navy[700],
    },
    text: {
      primary: fsiColors.text.primary,
      secondary: fsiColors.text.secondary,
      disabled: fsiColors.text.disabled,
    },
    success: {
      main: fsiColors.status.success,
      contrastText: '#FFFFFF',
    },
    warning: {
      main: fsiColors.status.warning,
      contrastText: '#FFFFFF',
    },
    error: {
      main: fsiColors.status.error,
      contrastText: '#FFFFFF',
    },
    info: {
      main: fsiColors.status.info,
      contrastText: '#FFFFFF',
    },
    divider: fsiColors.navy[400],
    grey: {
      50: '#F8FAFC',
      100: '#F1F5F9',
      200: '#E2E8F0',
      300: '#CBD5E1',
      400: '#94A3B8',
      500: '#64748B',
      600: '#475569',
      700: '#334155',
      800: '#1E293B',
      900: '#0F172A',
    },
  },
  typography: {
    fontFamily: '"Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      color: fsiColors.text.primary,
      letterSpacing: '-0.02em',
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 700,
      color: fsiColors.text.primary,
      letterSpacing: '-0.01em',
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 600,
      color: fsiColors.text.primary,
      letterSpacing: '-0.01em',
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.25rem',
      fontWeight: 600,
      color: fsiColors.text.primary,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.1rem',
      fontWeight: 600,
      color: fsiColors.text.primary,
      lineHeight: 1.5,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      color: fsiColors.text.primary,
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '0.95rem',
      fontWeight: 400,
      color: fsiColors.text.primary,
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      fontWeight: 400,
      color: fsiColors.text.secondary,
      lineHeight: 1.6,
    },
    caption: {
      fontSize: '0.75rem',
      fontWeight: 500,
      color: fsiColors.text.muted,
      letterSpacing: '0.02em',
    },
    overline: {
      fontSize: '0.7rem',
      fontWeight: 600,
      color: fsiColors.orange.main,
      letterSpacing: '0.1em',
      textTransform: 'uppercase',
    },
  },
  spacing: 8,
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          background: fsiGradients.meshGradient,
          minHeight: '100vh',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          background: fsiGradients.backgroundCard,
          border: `1px solid ${fsiColors.navy[400]}40`,
          borderRadius: '16px',
          boxShadow: '0 4px 24px rgba(0, 0, 0, 0.2)',
          backdropFilter: glassTokens.blur.md,
          WebkitBackdropFilter: glassTokens.blur.md,
          transition: `all ${transitions.normal} ${transitions.smooth}`,
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: `0 8px 32px rgba(0, 0, 0, 0.3), 0 0 0 1px ${fsiColors.orange.main}20`,
            borderColor: `${fsiColors.orange.main}40`,
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '10px',
          fontWeight: 600,
          textTransform: 'none',
          padding: '10px 20px',
          fontSize: '0.9rem',
          transition: `all ${transitions.fast} ${transitions.smooth}`,
          position: 'relative',
          overflow: 'hidden',
        },
        contained: {
          background: fsiGradients.orangeGradient,
          color: '#FFFFFF',
          boxShadow: `0 4px 14px ${fsiColors.orange.glow}`,
          '&:hover': {
            background: fsiGradients.orangeGlow,
            transform: 'translateY(-2px)',
            boxShadow: `0 6px 20px ${fsiColors.orange.glow}`,
          },
          '&:active': {
            transform: 'translateY(0)',
          },
        },
        outlined: {
          borderColor: `${fsiColors.orange.main}60`,
          color: fsiColors.orange.main,
          backdropFilter: glassTokens.blur.sm,
          '&:hover': {
            backgroundColor: `${fsiColors.orange.main}15`,
            borderColor: fsiColors.orange.main,
            transform: 'translateY(-1px)',
          },
        },
        text: {
          color: fsiColors.text.secondary,
          '&:hover': {
            backgroundColor: `${fsiColors.navy[500]}40`,
            color: fsiColors.text.primary,
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          fontWeight: 600,
          fontSize: '0.75rem',
          backdropFilter: glassTokens.blur.sm,
          transition: `all ${transitions.fast} ${transitions.smooth}`,
        },
        colorSuccess: {
          backgroundColor: `${fsiColors.status.success}20`,
          color: fsiColors.status.success,
          border: `1px solid ${fsiColors.status.success}40`,
        },
        colorWarning: {
          backgroundColor: `${fsiColors.status.warning}20`,
          color: fsiColors.status.warning,
          border: `1px solid ${fsiColors.status.warning}40`,
        },
        colorError: {
          backgroundColor: `${fsiColors.status.error}20`,
          color: fsiColors.status.error,
          border: `1px solid ${fsiColors.status.error}40`,
        },
        colorInfo: {
          backgroundColor: `${fsiColors.status.info}20`,
          color: fsiColors.status.info,
          border: `1px solid ${fsiColors.status.info}40`,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: `linear-gradient(180deg, ${fsiColors.navy[800]}F5 0%, ${fsiColors.navy[900]}F5 100%)`,
          backdropFilter: glassTokens.blur.lg,
          WebkitBackdropFilter: glassTokens.blur.lg,
          borderBottom: `1px solid ${fsiColors.navy[400]}30`,
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          background: `linear-gradient(180deg, ${fsiColors.navy[800]} 0%, ${fsiColors.navy[900]} 100%)`,
          backdropFilter: glassTokens.blur.lg,
          WebkitBackdropFilter: glassTokens.blur.lg,
          borderRight: `1px solid ${fsiColors.navy[400]}30`,
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: '10px',
          margin: '4px 12px',
          transition: `all ${transitions.fast} ${transitions.smooth}`,
          '&.Mui-selected': {
            backgroundColor: `${fsiColors.orange.main}15`,
            borderLeft: `3px solid ${fsiColors.orange.main}`,
            '&:hover': {
              backgroundColor: `${fsiColors.orange.main}20`,
            },
          },
          '&:hover': {
            backgroundColor: `${fsiColors.navy[500]}40`,
            transform: 'translateX(4px)',
          },
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          backgroundColor: `${fsiColors.navy[500]}40`,
          borderRadius: '6px',
          height: '8px',
        },
        bar: {
          borderRadius: '6px',
          background: fsiGradients.orangeGradient,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
        elevation1: {
          background: fsiGradients.backgroundCard,
          backdropFilter: glassTokens.blur.md,
          border: `1px solid ${fsiColors.navy[400]}30`,
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: fsiColors.navy[600],
          backdropFilter: glassTokens.blur.md,
          border: `1px solid ${fsiColors.navy[400]}50`,
          borderRadius: '8px',
          fontSize: '0.8rem',
          fontWeight: 500,
          padding: '8px 12px',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
        },
        arrow: {
          color: fsiColors.navy[600],
        },
      },
    },
    MuiPopover: {
      styleOverrides: {
        paper: {
          background: fsiGradients.backgroundElevated,
          backdropFilter: glassTokens.blur.lg,
          WebkitBackdropFilter: glassTokens.blur.lg,
          border: `1px solid ${fsiColors.navy[400]}40`,
          borderRadius: '14px',
          boxShadow: '0 12px 40px rgba(0, 0, 0, 0.4)',
        },
      },
    },
    MuiMenu: {
      styleOverrides: {
        paper: {
          background: fsiGradients.backgroundElevated,
          backdropFilter: glassTokens.blur.lg,
          WebkitBackdropFilter: glassTokens.blur.lg,
          border: `1px solid ${fsiColors.navy[400]}40`,
          borderRadius: '12px',
          boxShadow: '0 12px 40px rgba(0, 0, 0, 0.4)',
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          background: fsiGradients.backgroundCard,
          backdropFilter: glassTokens.blur.xl,
          WebkitBackdropFilter: glassTokens.blur.xl,
          border: `1px solid ${fsiColors.navy[400]}40`,
          borderRadius: '20px',
          boxShadow: '0 24px 64px rgba(0, 0, 0, 0.5)',
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          transition: `all ${transitions.fast} ${transitions.smooth}`,
          '&:hover': {
            backgroundColor: `${fsiColors.orange.main}08`,
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${fsiColors.navy[400]}30`,
          padding: '16px',
        },
        head: {
          backgroundColor: `${fsiColors.navy[600]}60`,
          fontWeight: 600,
          textTransform: 'uppercase',
          fontSize: '0.7rem',
          letterSpacing: '0.08em',
          color: fsiColors.text.muted,
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            backgroundColor: `${fsiColors.navy[800]}80`,
            backdropFilter: glassTokens.blur.sm,
            borderRadius: '10px',
            transition: `all ${transitions.fast} ${transitions.smooth}`,
            '& fieldset': {
              borderColor: `${fsiColors.navy[400]}40`,
              borderWidth: '1px',
            },
            '&:hover fieldset': {
              borderColor: `${fsiColors.orange.main}50`,
            },
            '&.Mui-focused fieldset': {
              borderColor: fsiColors.orange.main,
              borderWidth: '2px',
              boxShadow: `0 0 16px ${fsiColors.orange.glow}`,
            },
          },
          '& .MuiInputLabel-root': {
            color: fsiColors.text.muted,
            '&.Mui-focused': {
              color: fsiColors.orange.main,
            },
          },
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: `${fsiColors.navy[400]}40`,
          },
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: `${fsiColors.orange.main}50`,
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: fsiColors.orange.main,
          },
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          transition: `all ${transitions.fast} ${transitions.smooth}`,
          '&:hover': {
            backgroundColor: `${fsiColors.orange.main}15`,
            transform: 'scale(1.1)',
          },
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          backdropFilter: glassTokens.blur.md,
          borderRadius: '12px',
        },
        standardSuccess: {
          backgroundColor: `${fsiColors.status.success}15`,
          border: `1px solid ${fsiColors.status.success}40`,
          color: fsiColors.status.success,
        },
        standardError: {
          backgroundColor: `${fsiColors.status.error}15`,
          border: `1px solid ${fsiColors.status.error}40`,
          color: fsiColors.status.error,
        },
        standardWarning: {
          backgroundColor: `${fsiColors.status.warning}15`,
          border: `1px solid ${fsiColors.status.warning}40`,
          color: fsiColors.status.warning,
        },
        standardInfo: {
          backgroundColor: `${fsiColors.status.info}15`,
          border: `1px solid ${fsiColors.status.info}40`,
          color: fsiColors.status.info,
        },
      },
    },
    MuiAvatar: {
      styleOverrides: {
        root: {
          border: `2px solid ${fsiColors.navy[400]}50`,
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)',
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: `${fsiColors.navy[400]}40`,
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        root: {
          '& .MuiTabs-indicator': {
            backgroundColor: fsiColors.orange.main,
            height: '3px',
            borderRadius: '3px 3px 0 0',
          },
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          fontSize: '0.9rem',
          color: fsiColors.text.muted,
          transition: `all ${transitions.fast} ${transitions.smooth}`,
          '&.Mui-selected': {
            color: fsiColors.orange.main,
          },
          '&:hover': {
            color: fsiColors.text.primary,
            backgroundColor: `${fsiColors.navy[500]}30`,
          },
        },
      },
    },
    MuiSwitch: {
      styleOverrides: {
        root: {
          '& .MuiSwitch-switchBase.Mui-checked': {
            color: fsiColors.orange.main,
            '& + .MuiSwitch-track': {
              backgroundColor: fsiColors.orange.main,
            },
          },
        },
      },
    },
    MuiBadge: {
      styleOverrides: {
        badge: {
          background: fsiGradients.orangeGradient,
          boxShadow: `0 2px 8px ${fsiColors.orange.glow}`,
        },
      },
    },
  },
})
