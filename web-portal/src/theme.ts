import { createTheme } from '@mui/material/styles'

// Glass effect tokens
export const glassTokens = {
  blur: {
    sm: 'blur(4px)',
    md: 'blur(10px)',
    lg: 'blur(20px)',
    xl: 'blur(40px)',
  },
  opacity: {
    light: 0.05,
    medium: 0.1,
    dark: 0.15,
    solid: 0.25,
  },
}

// Glow colors for status indicators
export const glowColors = {
  primary: '#FF9900',
  success: '#1D8102',
  error: '#D13212',
  warning: '#FF9900',
  info: '#0972D3',
  purple: '#9C27B0',
  neutral: '#9BA7B4',
}

// Transition timing presets
export const transitions = {
  instant: '0.1s',
  fast: '0.15s',
  normal: '0.3s',
  slow: '0.6s',
  easeOut: 'ease-out',
  easeInOut: 'ease-in-out',
  bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
}

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#FF9900', // AWS Orange
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#146EB4', // AWS Light Blue
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#0F1419', // AWS Gray 900
      paper: '#1C2127', // AWS Gray 800
    },
    text: {
      primary: '#FFFFFF', // Pure white for primary text
      secondary: '#9BA7B4', // AWS Gray 400
      disabled: '#687078', // AWS Gray 500
    },
    success: {
      main: '#1D8102', // AWS Success Green
      contrastText: '#FFFFFF',
    },
    warning: {
      main: '#FF9900', // AWS Orange
      contrastText: '#FFFFFF',
    },
    error: {
      main: '#D13212', // AWS Error Red
      contrastText: '#FFFFFF',
    },
    info: {
      main: '#0972D3', // AWS Info Blue
      contrastText: '#FFFFFF',
    },
    divider: '#414D5C', // AWS Gray 600
    // Extended AWS Grayscale Palette
    grey: {
      50: '#E9F0F7',
      100: '#D5E0EC',
      200: '#C1CDD9',
      300: '#AEBAC7',
      400: '#9BA7B4',
      500: '#687078',
      600: '#414D5C',
      700: '#232A31',
      800: '#1C2127',
      900: '#0F1419',
    },
  },
  typography: {
    fontFamily: '"Amazon Ember", "Helvetica Neue", Helvetica, Arial, sans-serif',
    h1: {
      fontSize: '28px',
      fontWeight: 700,
      color: '#FFFFFF',
    },
    h2: {
      fontSize: '24px',
      fontWeight: 600,
      color: '#FFFFFF',
    },
    h3: {
      fontSize: '20px',
      fontWeight: 600,
      color: '#FFFFFF',
    },
    h4: {
      fontSize: '18px',
      fontWeight: 600,
      color: '#FFFFFF',
    },
    h5: {
      fontSize: '16px',
      fontWeight: 600,
      color: '#FFFFFF',
    },
    h6: {
      fontSize: '14px',
      fontWeight: 600,
      color: '#FFFFFF',
    },
    body1: {
      fontSize: '14px',
      fontWeight: 400,
      color: '#FFFFFF',
    },
    body2: {
      fontSize: '12px',
      fontWeight: 400,
      color: '#9BA7B4',
    },
    caption: {
      fontSize: '11px',
      fontWeight: 400,
      color: '#687078',
    },
  },
  spacing: 8, // 8px base unit
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.95) 0%, rgba(35, 42, 49, 0.95) 100%)',
          border: '1px solid rgba(65, 77, 92, 0.3)',
          borderRadius: '12px',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          transition: 'all 0.15s ease-out',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0 8px 25px rgba(255, 153, 0, 0.15)',
            borderColor: 'rgba(255, 153, 0, 0.3)',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          fontWeight: 600,
          textTransform: 'none',
          padding: '8px 16px',
          transition: 'all 0.15s ease-out',
          position: 'relative',
          overflow: 'hidden',
        },
        contained: {
          background: 'linear-gradient(135deg, #FF9900 0%, #E6890A 100%)',
          color: '#FFFFFF',
          boxShadow: '0 2px 8px rgba(255, 153, 0, 0.3)',
          '&:hover': {
            background: 'linear-gradient(135deg, #FFB84D 0%, #FF9900 100%)',
            transform: 'translateY(-1px) scale(1.02)',
            boxShadow: '0 4px 16px rgba(255, 153, 0, 0.4)',
          },
          '&:active': {
            transform: 'translateY(0) scale(0.98)',
          },
        },
        outlined: {
          borderColor: 'rgba(255, 153, 0, 0.5)',
          color: '#FF9900',
          backdropFilter: 'blur(4px)',
          '&:hover': {
            backgroundColor: 'rgba(255, 153, 0, 0.1)',
            borderColor: '#FF9900',
            transform: 'translateY(-1px)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '6px',
          fontWeight: 600,
          backdropFilter: 'blur(4px)',
          transition: 'all 0.15s ease-out',
        },
        colorSuccess: {
          backgroundColor: 'rgba(29, 129, 2, 0.15)',
          color: '#1D8102',
          border: '1px solid rgba(29, 129, 2, 0.3)',
        },
        colorWarning: {
          backgroundColor: 'rgba(255, 153, 0, 0.15)',
          color: '#FF9900',
          border: '1px solid rgba(255, 153, 0, 0.3)',
        },
        colorError: {
          backgroundColor: 'rgba(209, 50, 18, 0.15)',
          color: '#D13212',
          border: '1px solid rgba(209, 50, 18, 0.3)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: 'linear-gradient(180deg, rgba(35, 47, 62, 0.95) 0%, rgba(28, 33, 39, 0.95) 100%)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(65, 77, 92, 0.3)',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          background: 'linear-gradient(180deg, rgba(35, 47, 62, 0.98) 0%, rgba(28, 33, 39, 0.98) 100%)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderRight: '1px solid rgba(65, 77, 92, 0.3)',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          margin: '4px 8px',
          transition: 'all 0.15s ease-out',
          '&.Mui-selected': {
            backgroundColor: 'rgba(255, 153, 0, 0.12)',
            borderLeft: '3px solid #FF9900',
            '&:hover': {
              backgroundColor: 'rgba(255, 153, 0, 0.16)',
            },
          },
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.08)',
            transform: 'translateX(4px)',
          },
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          backgroundColor: 'rgba(65, 77, 92, 0.3)',
          borderRadius: '4px',
          height: '6px',
        },
        bar: {
          borderRadius: '4px',
          background: 'linear-gradient(90deg, #FF9900 0%, #FFB84D 100%)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
        elevation1: {
          background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.95) 0%, rgba(35, 42, 49, 0.95) 100%)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(65, 77, 92, 0.3)',
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: 'rgba(28, 33, 39, 0.95)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(65, 77, 92, 0.3)',
          borderRadius: '6px',
          fontSize: '12px',
          fontWeight: 500,
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.3)',
        },
        arrow: {
          color: 'rgba(28, 33, 39, 0.95)',
        },
      },
    },
    MuiPopover: {
      styleOverrides: {
        paper: {
          background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.98) 0%, rgba(35, 42, 49, 0.98) 100%)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(65, 77, 92, 0.3)',
          borderRadius: '12px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
        },
      },
    },
    MuiMenu: {
      styleOverrides: {
        paper: {
          background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.98) 0%, rgba(35, 42, 49, 0.98) 100%)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(65, 77, 92, 0.3)',
          borderRadius: '8px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.98) 0%, rgba(35, 42, 49, 0.98) 100%)',
          backdropFilter: 'blur(30px)',
          WebkitBackdropFilter: 'blur(30px)',
          border: '1px solid rgba(65, 77, 92, 0.3)',
          borderRadius: '16px',
          boxShadow: '0 16px 48px rgba(0, 0, 0, 0.5)',
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          transition: 'all 0.15s ease-out',
          '&:hover': {
            backgroundColor: 'rgba(255, 153, 0, 0.05)',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid rgba(65, 77, 92, 0.2)',
        },
        head: {
          backgroundColor: 'rgba(35, 42, 49, 0.5)',
          fontWeight: 600,
          textTransform: 'uppercase',
          fontSize: '11px',
          letterSpacing: '0.5px',
          color: '#9BA7B4',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            backgroundColor: 'rgba(20, 25, 30, 0.5)',
            backdropFilter: 'blur(4px)',
            borderRadius: '8px',
            transition: 'all 0.15s ease-out',
            '& fieldset': {
              borderColor: 'rgba(65, 77, 92, 0.3)',
            },
            '&:hover fieldset': {
              borderColor: 'rgba(255, 153, 0, 0.3)',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#FF9900',
              boxShadow: '0 0 10px rgba(255, 153, 0, 0.2)',
            },
          },
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: 'rgba(65, 77, 92, 0.3)',
          },
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: 'rgba(255, 153, 0, 0.3)',
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: '#FF9900',
          },
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          transition: 'all 0.15s ease-out',
          '&:hover': {
            backgroundColor: 'rgba(255, 153, 0, 0.1)',
            transform: 'scale(1.1)',
          },
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          backdropFilter: 'blur(10px)',
          borderRadius: '8px',
        },
        standardSuccess: {
          backgroundColor: 'rgba(29, 129, 2, 0.15)',
          border: '1px solid rgba(29, 129, 2, 0.3)',
        },
        standardError: {
          backgroundColor: 'rgba(209, 50, 18, 0.15)',
          border: '1px solid rgba(209, 50, 18, 0.3)',
        },
        standardWarning: {
          backgroundColor: 'rgba(255, 153, 0, 0.15)',
          border: '1px solid rgba(255, 153, 0, 0.3)',
        },
        standardInfo: {
          backgroundColor: 'rgba(9, 114, 211, 0.15)',
          border: '1px solid rgba(9, 114, 211, 0.3)',
        },
      },
    },
    MuiAvatar: {
      styleOverrides: {
        root: {
          border: '2px solid rgba(65, 77, 92, 0.3)',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
        },
      },
    },
  },
})
