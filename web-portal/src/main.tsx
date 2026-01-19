import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider, CssBaseline } from '@mui/material'
import '@cloudscape-design/global-styles/index.css'
import '@cloudscape-design/global-styles/dark-mode-utils.css'
import App from './App'
import { AuthProvider } from './contexts/AuthContext'
import { ToastProvider } from './components/feedback/ToastProvider'
import { theme } from './theme'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10000,
      gcTime: 300000, // formerly cacheTime
      retry: 2,
    },
  },
})

// Enable MSW for mocking API (enabled when VITE_ENABLE_MSW=true or in DEV mode)
async function enableMocking() {
  console.log('[DEBUG] VITE_ENABLE_MSW:', import.meta.env.VITE_ENABLE_MSW)
  console.log('[DEBUG] VITE_DISABLE_MSW:', import.meta.env.VITE_DISABLE_MSW)
  console.log('[DEBUG] DEV mode:', import.meta.env.DEV)

  // Enable MSW if explicitly enabled OR in dev mode (unless explicitly disabled)
  const shouldEnableMSW =
    import.meta.env.VITE_ENABLE_MSW === 'true' ||
    (import.meta.env.DEV && import.meta.env.VITE_DISABLE_MSW !== 'true')

  if (shouldEnableMSW) {
    console.log('[DEBUG] Starting MSW...')
    const { worker } = await import('./mocks/browser')
    return worker.start({
      onUnhandledRequest: 'bypass',
    })
  }
  console.log('[DEBUG] MSW disabled - using real API')
  return Promise.resolve()
}

enableMocking().then(() => {
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <AuthProvider>
              <ToastProvider position="top-right" maxToasts={5}>
                <App />
              </ToastProvider>
            </AuthProvider>
          </BrowserRouter>
          <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
      </ThemeProvider>
    </React.StrictMode>,
  )
})
