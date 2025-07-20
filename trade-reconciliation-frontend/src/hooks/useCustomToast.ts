import { useContext } from 'react';
import { ToastContext } from '../context/ToastContext';
import { ToastType } from '../components/common/Toast';

/**
 * Custom hook that provides toast functionality with a fallback
 * to console.log if the toast context is not available
 */
export const useCustomToast = () => {
  // Always call useContext (React Hook) unconditionally
  const toastContext = useContext(ToastContext);
  const hasToastContext = toastContext !== undefined;
  
  // Create toast functions that work with or without the context
  const showToast = (type: ToastType, message: string, duration?: number) => {
    if (hasToastContext && toastContext) {
      toastContext.showToast(type, message, duration);
    } else {
      console.log(`Toast (${type}): ${message}`);
    }
  };
  
  const showSuccess = (message: string, duration?: number) => {
    if (hasToastContext && toastContext) {
      toastContext.showSuccess(message, duration);
    } else {
      console.log(`Toast (success): ${message}`);
    }
  };
  
  const showError = (message: string, duration?: number) => {
    if (hasToastContext && toastContext) {
      toastContext.showError(message, duration);
    } else {
      console.error(`Toast (error): ${message}`);
    }
  };
  
  const showWarning = (message: string, duration?: number) => {
    if (hasToastContext && toastContext) {
      toastContext.showWarning(message, duration);
    } else {
      console.warn(`Toast (warning): ${message}`);
    }
  };
  
  const showInfo = (message: string, duration?: number) => {
    if (hasToastContext && toastContext) {
      toastContext.showInfo(message, duration);
    } else {
      console.info(`Toast (info): ${message}`);
    }
  };
  
  const showApiError = (error: any, fallbackMessage?: string) => {
    if (hasToastContext && toastContext) {
      toastContext.showApiError(error, fallbackMessage);
    } else {
      console.error(`API Error:`, error, fallbackMessage);
    }
  };

  return { 
    showToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showApiError
  };
};