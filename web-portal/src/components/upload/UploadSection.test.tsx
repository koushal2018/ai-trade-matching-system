import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { UploadSection } from './UploadSection'

describe('UploadSection', () => {
  it('renders the container with header', () => {
    const mockBankUpload = vi.fn()
    const mockCounterpartyUpload = vi.fn()

    render(
      <UploadSection
        onBankUploadComplete={mockBankUpload}
        onCounterpartyUploadComplete={mockCounterpartyUpload}
      />
    )

    expect(screen.getByText('Upload Trade Confirmations')).toBeInTheDocument()
    expect(screen.getByText('Upload trade confirmation PDFs from both bank and counterparty sides')).toBeInTheDocument()
  })

  it('renders both FileUploadCard components', () => {
    const mockBankUpload = vi.fn()
    const mockCounterpartyUpload = vi.fn()

    render(
      <UploadSection
        onBankUploadComplete={mockBankUpload}
        onCounterpartyUploadComplete={mockCounterpartyUpload}
      />
    )

    expect(screen.getByText('Bank Confirmation')).toBeInTheDocument()
    expect(screen.getByText('Counterparty Confirmation')).toBeInTheDocument()
  })

  it('passes disabled prop to both FileUploadCard components', () => {
    const mockBankUpload = vi.fn()
    const mockCounterpartyUpload = vi.fn()

    const { container } = render(
      <UploadSection
        onBankUploadComplete={mockBankUpload}
        onCounterpartyUploadComplete={mockCounterpartyUpload}
        disabled={true}
      />
    )

    // Both file upload inputs should be present
    const fileInputs = container.querySelectorAll('input[type="file"]')
    expect(fileInputs).toHaveLength(2)
  })

  it('displays constraint text for both upload areas', () => {
    const mockBankUpload = vi.fn()
    const mockCounterpartyUpload = vi.fn()

    render(
      <UploadSection
        onBankUploadComplete={mockBankUpload}
        onCounterpartyUploadComplete={mockCounterpartyUpload}
      />
    )

    // Check that constraint text appears (should appear twice, once for each upload card)
    const constraintTexts = screen.getAllByText('Accepted file types: PDF. Maximum file size: 10 MB.')
    expect(constraintTexts).toHaveLength(2)
  })
})
