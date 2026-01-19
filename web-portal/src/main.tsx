import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material'
import '@cloudscape-design/global-styles/index.css'
import '@cloudscape-design/global-styles/dark-mode-utils.css'
import App from './App'
import { AuthProvider } from './contexts/AuthContext'

// Create dark theme for MUI components
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#FF9900',
    },
    secondary: {
      main: '#146EB4',
    },
    background: {
      default: '#0f1114',
      paper: '#1c2127',
    },
    text: {
      primary: '#FFFFFF',
      secondary: '#9BA7B4',
    },
  },
  typography: {
    fontFamily: '"Amazon Ember", "Helvetica Neue", Helvetica, Arial, sans-serif',
  },
})

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10000,
      gcTime: 300000, // formerly cacheTime
      retry: 2,
    },
  },
})

// Enable MSW in development mode (disabled when VITE_DISABLE_MSW=true)
async function enableMocking() {
  console.log('[DEBUG] VITE_DISABLE_MSW:', import.meta.env.VITE_DISABLE_MSW)
  console.log('[DEBUG] DEV mode:', import.meta.env.DEV)
  
  if (import.meta.env.DEV && import.meta.env.VITE_DISABLE_MSW !== 'true') {
    console.log('[DEBUG] Starting MSW...')
    const { worker } = await import('./mocks/browser')
    return worker.start({
      onUnhandledRequest: 'warn',
    })
  }
  console.log('[DEBUG] MSW disabled - using real API')
  return Promise.resolve()
}

enableMocking().then(() => {
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <ThemeProvider theme={darkTheme}>
        <CssBaseline />
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <AuthProvider>
              <App />
            </AuthProvider>
          </BrowserRouter>
          <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
      </ThemeProvider>
    </React.StrictMode>,
  )
})
