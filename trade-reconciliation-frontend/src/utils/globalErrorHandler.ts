import { ErrorHandler } from '../services/api/ErrorHandler';

/**
 * Sets up global error handlers for unhandled exceptions and promise rejections
 */
export const setupGlobalErrorHandlers = () => {
  // Handler for uncaught exceptions
  window.addEventListener('error', (event) => {
    const error = {
      status: 0,
      message: event.message || 'Uncaught error',
      details: {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error,
      },
    };
    
    ErrorHandler.logError(error);
    
    // Don't prevent the browser's default error handling
    return false;
  });
  
  // Handler for unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    const error = {
      status: 0,
      message: event.reason?.message || 'Unhandled promise rejection',
      details: event.reason,
    };
    
    ErrorHandler.logError(error);
    
    // Don't prevent the browser's default error handling
    return false;
  });
  
  console.log('Global error handlers have been set up');
};