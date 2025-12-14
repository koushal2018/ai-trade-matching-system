import React, { createContext, useContext, useState, useCallback } from 'react';
import Toast, { ToastType } from '../components/common/Toast';
import { ErrorCategory, ErrorSeverity } from '../services/api/ErrorHandler';

export interface ToastContextType {
  showToast: (type: ToastType, message: string, duration?: number) => void;
  showSuccess: (message: string, duration?: number) => void;
  showError: (message: string, duration?: number) => void;
  showWarning: (message: string, duration?: number) => void;
  showInfo: (message: string, duration?: number) => void;
  showApiError: (error: any, fallbackMessage?: string) => void;
  clearToasts: () => void;
}

export const ToastContext = createContext<ToastContextType | undefined>(undefined);

interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

// Default durations for different toast types
const DEFAULT_DURATIONS = {
  success: 3000,
  error: 8000,
  warning: 5000,
  info: 4000,
};

// Maximum number of toasts to show at once
const MAX_TOASTS = 3;

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((type: ToastType, message: string, duration?: number) => {
    const id = Math.random().toString(36).substring(2, 9);
    const defaultDuration = DEFAULT_DURATIONS[type] || 5000;
    
    setToasts((prevToasts) => {
      // If we already have MAX_TOASTS, remove the oldest one
      const updatedToasts = prevToasts.length >= MAX_TOASTS 
        ? prevToasts.slice(1) 
        : prevToasts;
        
      return [...updatedToasts, { 
        id, 
        type, 
        message, 
        duration: duration || defaultDuration 
      }];
    });
  }, []);

  const showSuccess = useCallback((message: string, duration?: number) => {
    showToast('success', message, duration);
  }, [showToast]);

  const showError = useCallback((message: string, duration?: number) => {
    showToast('error', message, duration);
  }, [showToast]);

  const showWarning = useCallback((message: string, duration?: number) => {
    showToast('warning', message, duration);
  }, [showToast]);

  const showInfo = useCallback((message: string, duration?: number) => {
    showToast('info', message, duration);
  }, [showToast]);

  // Special handler for API errors that uses the ErrorHandler service
  const showApiError = useCallback((error: any, fallbackMessage?: string) => {
    let message = fallbackMessage || 'An unexpected error occurred';
    let type: ToastType = 'error';
    
    // If it's an API error with userMessage, use that
    if (error && error.userMessage) {
      message = error.userMessage;
    }
    
    // Determine toast type based on error severity if available
    if (error && error.severity) {
      switch (error.severity) {
        case ErrorSeverity.INFO:
          type = 'info';
          break;
        case ErrorSeverity.WARNING:
          type = 'warning';
          break;
        case ErrorSeverity.ERROR:
        case ErrorSeverity.CRITICAL:
          type = 'error';
          break;
        default:
          type = 'error';
      }
    }
    
    showToast(type, message);
  }, [showToast]);

  const clearToasts = useCallback(() => {
    setToasts([]);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prevToasts) => prevToasts.filter((toast) => toast.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ 
      showToast, 
      showSuccess, 
      showError, 
      showWarning, 
      showInfo, 
      showApiError,
      clearToasts 
    }}>
      {children}
      <div className="fixed bottom-0 right-0 p-4 space-y-4 z-50">
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            type={toast.type}
            message={toast.message}
            duration={toast.duration}
            onClose={() => removeToast(toast.id)}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = (): ToastContextType => {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};