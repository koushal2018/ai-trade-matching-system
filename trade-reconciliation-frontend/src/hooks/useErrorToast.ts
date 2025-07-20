import { useCallback } from 'react';
import { useToast } from '../context/ToastContext';
import { ErrorHandler, EnhancedError } from '../services/api/ErrorHandler';
import { ApiError } from '../services/api/BaseApiService';

/**
 * A custom hook that combines error handling with toast notifications
 */
export const useErrorToast = () => {
  const toast = useToast();
  
  /**
   * Handles an API error and shows an appropriate toast notification
   */
  const handleApiError = useCallback((error: any, fallbackMessage?: string) => {
    // If it's already an enhanced error, use it directly
    if (error && error.category && error.severity && error.userMessage) {
      toast.showApiError(error);
      return error;
    }
    
    // If it's a basic API error, enhance it
    if (error && (error.status || error.message)) {
      const enhancedError = ErrorHandler.enhanceError(error as ApiError);
      toast.showApiError(enhancedError);
      return enhancedError;
    }
    
    // For other types of errors, create a generic error
    const genericError = {
      status: 500,
      message: error?.message || fallbackMessage || 'An unexpected error occurred',
    };
    
    const enhancedError = ErrorHandler.enhanceError(genericError);
    toast.showApiError(enhancedError);
    return enhancedError;
  }, [toast]);
  
  /**
   * Wraps an async function with error handling and toast notifications
   */
  const withErrorToast = useCallback(<T>(
    asyncFn: () => Promise<T>,
    options?: {
      successMessage?: string;
      errorMessage?: string;
      showSuccessToast?: boolean;
    }
  ) => {
    const { successMessage, errorMessage, showSuccessToast = false } = options || {};
    
    return async (): Promise<T | null> => {
      try {
        const result = await asyncFn();
        
        if (showSuccessToast && successMessage) {
          toast.showSuccess(successMessage);
        }
        
        return result;
      } catch (error) {
        handleApiError(error, errorMessage);
        return null;
      }
    };
  }, [toast, handleApiError]);
  
  return {
    handleApiError,
    withErrorToast,
  };
};