import { Component, ReactNode } from 'react'
import { Alert, Box, Button, Container, SpaceBetween } from '@cloudscape-design/components'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: React.ErrorInfo | null
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error to console for debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo)

    this.setState({
      error,
      errorInfo,
    })

    // In production, you might want to log to an error reporting service
    // e.g., Sentry, CloudWatch, etc.
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default fallback UI using CloudScape Alert
      return (
        <Container>
          <SpaceBetween size="l">
            <Alert
              type="error"
              header="Something went wrong"
              action={
                <Button onClick={this.handleReset} iconName="refresh">
                  Try again
                </Button>
              }
            >
              <SpaceBetween size="s">
                <Box variant="p">
                  An unexpected error occurred while rendering this component. Please try
                  refreshing the page or contact support if the problem persists.
                </Box>
                {this.state.error && (
                  <Box variant="code" fontSize="body-s">
                    {this.state.error.toString()}
                  </Box>
                )}
              </SpaceBetween>
            </Alert>
          </SpaceBetween>
        </Container>
      )
    }

    return this.props.children
  }
}
