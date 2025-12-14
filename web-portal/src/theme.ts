import { createTheme } from '@mui/material/styles'

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
          backgroundColor: '#1C2127',
          border: '1px solid #414D5C',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
          backdropFilter: 'blur(10px)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '4px',
          fontWeight: 600,
          textTransform: 'none',
          padding: '8px 16px',
          transition: 'all 0.15s ease-in-out',
        },
        contained: {
          backgroundColor: '#FF9900',
          color: '#FFFFFF',
          '&:hover': {
            backgroundColor: '#E6890A',
            transform: 'translateY(-1px)',
            boxShadow: '0 4px 12px rgba(255, 153, 0, 0.3)',
          },
        },
        outlined: {
          borderColor: '#FF9900',
          color: '#FF9900',
          '&:hover': {
            backgroundColor: 'rgba(255, 153, 0, 0.08)',
            borderColor: '#E6890A',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '4px',
          fontWeight: 600,
        },
        colorSuccess: {
          backgroundColor: '#1D8102',
          color: '#FFFFFF',
        },
        colorWarning: {
          backgroundColor: '#FF9900',
          color: '#FFFFFF',
        },
        colorError: {
          backgroundColor: '#D13212',
          color: '#FFFFFF',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#232F3E', // AWS Dark Blue
          color: '#FFFFFF',
          backdropFilter: 'blur(10px)',
          borderBottom: '1px solid #414D5C',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#232F3E', // AWS Dark Blue
          borderRight: '1px solid #414D5C',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          margin: '4px 8px',
          '&.Mui-selected': {
            backgroundColor: 'rgba(255, 153, 0, 0.12)',
            borderLeft: '3px solid #FF9900',
            '&:hover': {
              backgroundColor: 'rgba(255, 153, 0, 0.16)',
            },
          },
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.08)',
          },
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          backgroundColor: '#414D5C',
          borderRadius: '4px',
          height: '6px',
        },
        bar: {
          borderRadius: '4px',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
})
