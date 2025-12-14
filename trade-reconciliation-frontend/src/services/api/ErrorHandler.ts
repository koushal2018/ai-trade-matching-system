/**
 * ErrorHandler provides utilities for handling API errors
 * and displaying them to the user.
 */

import { ApiError } from './BaseApiService';

// Define error categories
export enum ErrorCategory {
  NETWORK = 'network',
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
  VALIDATION = 'validation',
  SERVER = 'server',
  UNKNOWN = 'unknown',
}

// Define error severity
export enum ErrorSeverity {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical',
}

// Enhanced error with additional metadata
export interface EnhancedError extends ApiError {
  category: ErrorCategory;
  severity: ErrorSeverity;
  userMessage: string;
  timestamp: number;
  id: string;
}

export class ErrorHandler {
  /**
   * Categorizes an API error
   */
  public static categorizeError(error: ApiError): ErrorCategory {
    const { status } = error;
    
    if (!status || status === 0) {
      return ErrorCategory.NETWORK;
    }
    
    if (status === 401) {
      return ErrorCategory.AUTHENTICATION;
    }
    
    if (status === 403) {
      return ErrorCategory.AUTHORIZATION;
    }
    
    if (status === 400 || status === 422) {
      return ErrorCategory.VALIDATION;
    }
    
    if (status >= 500) {
      return ErrorCategory.SERVER;
    }
    
    return ErrorCategory.UNKNOWN;
  }

  /**
   * Determines the severity of an error
   */
  public static determineSeverity(error: ApiError): ErrorSeverity {
    const { status } = error;
    const category = this.categorizeError(error);
    
    if (category === ErrorCategory.NETWORK) {
      return ErrorSeverity.WARNING;
    }
    
    if (category === ErrorCategory.AUTHENTICATION || category === ErrorCategory.AUTHORIZATION) {
      return ErrorSeverity.WARNING;
    }
    
    if (category === ErrorCategory.VALIDATION) {
      return ErrorSeverity.INFO;
    }
    
    if (category === ErrorCategory.SERVER) {
      return ErrorSeverity.ERROR;
    }
    
    if (status >= 500) {
      return ErrorSeverity.CRITICAL;
    }
    
    return ErrorSeverity.ERROR;
  }

  /**
   * Creates a user-friendly error message
   */
  public static createUserMessage(error: ApiError): string {
    const { status, message } = error;
    const category = this.categorizeError(error);
    
    switch (category) {
      case ErrorCategory.NETWORK:
        return 'Unable to connect to the server. Please check your internet connection and try again.';
      
      case ErrorCategory.AUTHENTICATION:
        return 'Your session has expired. Please log in again.';
      
      case ErrorCategory.AUTHORIZATION:
        return 'You do not have permission to perform this action.';
      
      case ErrorCategory.VALIDATION:
        return message || 'Please check your input and try again.';
      
      case ErrorCategory.SERVER:
        return 'The server encountered an error. Please try again later.';
      
      default:
        return message || 'An unexpected error occurred. Please try again.';
    }
  }

  /**
   * Enhances an API error with additional metadata
   */
  public static enhanceError(error: ApiError): EnhancedError {
    const category = this.categorizeError(error);
    const severity = this.determineSeverity(error);
    const userMessage = this.createUserMessage(error);
    
    return {
      ...error,
      category,
      severity,
      userMessage,
      timestamp: Date.now(),
      id: Math.random().toString(36).substring(2, 15),
    };
  }

  /**
   * Logs an error for debugging and monitoring
   */
  public static logError(error: ApiError): void {
    const enhancedError = this.enhanceError(error);
    
    console.error('API Error:', enhancedError);
    
    // Here you could add integration with error tracking services
    // like Sentry, LogRocket, etc.
  }
}