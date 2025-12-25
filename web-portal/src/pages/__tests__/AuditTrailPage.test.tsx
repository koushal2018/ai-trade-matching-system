import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import AuditTrailPage from '../AuditTrailPage'

// Mock the audit service
vi.mock('../../services/auditService', () => ({
  auditService: {
    getAuditRecords: vi.fn().mockResolvedValue({
      records: [],
      total: 0,
      page: 0,
      pageSize: 25,
    }),
  },
}))

describe('AuditTrailPage', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuditTrailPage />
        </BrowserRouter>
      </QueryClientProvider>
    )
  }

  it('renders the audit trail page header', () => {
    renderComponent()
    expect(screen.getByText('Audit Trail')).toBeInTheDocument()
  })

  it('renders the export CSV button', () => {
    renderComponent()
    expect(screen.getByText('Export CSV')).toBeInTheDocument()
  })

  it('renders the table with correct columns', () => {
    renderComponent()
    expect(screen.getByText('Timestamp')).toBeInTheDocument()
    expect(screen.getByText('Session ID')).toBeInTheDocument()
    expect(screen.getByText('Action')).toBeInTheDocument()
    expect(screen.getByText('User')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()
    expect(screen.getByText('Details')).toBeInTheDocument()
  })

  it('shows empty state when no audit entries', async () => {
    renderComponent()
    // Wait for the query to complete
    await screen.findByText('No audit entries')
  })
})
