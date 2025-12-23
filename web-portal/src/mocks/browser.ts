import { setupWorker } from 'msw/browser'
import { handlers } from './handlers'

// Setup MSW service worker for browser
export const worker = setupWorker(...handlers)
