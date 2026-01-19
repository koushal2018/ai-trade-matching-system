import { useState, useCallback } from 'react'

interface UseCopyToClipboardReturn {
  /** Whether the text was copied successfully */
  copied: boolean
  /** Error message if copy failed */
  error: string | null
  /** Function to copy text to clipboard */
  copy: (text: string) => Promise<boolean>
  /** Reset the copied state */
  reset: () => void
}

/**
 * Hook for copying text to clipboard with status tracking
 *
 * @param resetDelay - Time in ms before resetting copied state (default: 2000)
 *
 * @example
 * const { copied, copy } = useCopyToClipboard()
 *
 * <button onClick={() => copy('Hello World')}>
 *   {copied ? 'Copied!' : 'Copy'}
 * </button>
 */
export function useCopyToClipboard(resetDelay: number = 2000): UseCopyToClipboardReturn {
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const copy = useCallback(
    async (text: string): Promise<boolean> => {
      if (!navigator?.clipboard) {
        setError('Clipboard API not available')
        return false
      }

      try {
        await navigator.clipboard.writeText(text)
        setCopied(true)
        setError(null)

        // Reset after delay
        if (resetDelay > 0) {
          setTimeout(() => {
            setCopied(false)
          }, resetDelay)
        }

        return true
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to copy'
        setError(errorMessage)
        setCopied(false)
        return false
      }
    },
    [resetDelay]
  )

  const reset = useCallback(() => {
    setCopied(false)
    setError(null)
  }, [])

  return { copied, error, copy, reset }
}

export default useCopyToClipboard
