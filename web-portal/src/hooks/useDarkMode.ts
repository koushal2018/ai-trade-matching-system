import { useState, useEffect } from 'react'

/**
 * Hook to manage dark mode state
 * 
 * Features:
 * - Toggles 'awsui-dark-mode' CSS class on document.body
 * - Persists preference to localStorage
 * - Initializes from localStorage on mount
 * 
 * Requirements: 1.6, 13.1
 */
export function useDarkMode() {
  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    // Initialize from localStorage
    const stored = localStorage.getItem('darkMode')
    return stored === 'true'
  })

  useEffect(() => {
    // Apply dark mode class to document.body
    if (isDarkMode) {
      document.body.classList.add('awsui-dark-mode')
    } else {
      document.body.classList.remove('awsui-dark-mode')
    }

    // Persist to localStorage
    localStorage.setItem('darkMode', String(isDarkMode))
  }, [isDarkMode])

  const toggleDarkMode = () => {
    setIsDarkMode((prev) => !prev)
  }

  return {
    isDarkMode,
    toggleDarkMode,
  }
}
