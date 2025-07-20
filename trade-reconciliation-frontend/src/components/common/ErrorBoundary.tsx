import React, { Component, ErrorInfo, ReactNode } from 'react';
import { useToast } from '../../context/ToastContext';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

// This context allows functional components to trigger error boundary resets
const ErrorBoundaryContext = React.createContext<{ reset: () => void }>({
  reset: () => {},
});

export const useErrorBoundary = () => React.useContext(ErrorBoundaryContext);

// We need to use a class component for ErrorBoundary as React's error boundary functionality
// is only available in class components
class ErrorBoundaryClass extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // You can log the error to an error reporting service
    console.error('Error caught by ErrorBoundary:', error, errorInfo);
    
    // Call the onError prop if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  reset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // You can render any custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-full flex items-center justify-center p-6 bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6 border border-red-100">
            <div className="flex items-center justify-center mb-4">
              <div className="bg-red-100 rounded-full p-3">
                <svg className="h-8 w-8 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
            </div>
            <h2 className="text-center text-xl font-semibold text-gray-900 mb-2">Something went wrong</h2>
            <p className="text-center text-gray-600 mb-6">
              We've encountered an unexpected error. Please try refreshing the page or contact support if the problem persists.
            </p>
            <div className="flex justify-center">
              <button
                onClick={this.reset}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Try Again
              </button>
            </div>
            {this.state.error && (
              <div className="mt-4 p-3 bg-gray-50 rounded text-xs text-gray-500 overflow-auto max-h-32">
                <p className="font-semibold">Error details:</p>
                <p className="font-mono">{this.state.error.toString()}</p>
              </div>
            )}
          </div>
        </div>
      );
    }

    return (
      <ErrorBoundaryContext.Provider value={{ reset: this.reset }}>
        {this.props.children}
      </ErrorBoundaryContext.Provider>
    );
  }
}

// This wrapper component allows us to use the toast context within the error boundary
const ErrorBoundary: React.FC<ErrorBoundaryProps> = (props) => {
  // We can't use hooks directly in class components, so we use this functional wrapper
  const toast = useToast();
  
  const handleError = (error: Error, errorInfo: ErrorInfo) => {
    // Show a toast notification when an error occurs
    toast.showToast('error', 'An unexpected error occurred. Some functionality may be affected.');
    
    // Call the original onError if provided
    if (props.onError) {
      props.onError(error, errorInfo);
    }
  };
  
  return <ErrorBoundaryClass {...props} onError={handleError} />;
};

export default ErrorBoundary;