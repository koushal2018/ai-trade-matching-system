/**
 * Validation utilities for forms
 */

export type ValidationResult = {
  isValid: boolean;
  message?: string;
};

export const validateRequired = (value: any): ValidationResult => {
  if (value === undefined || value === null || value === '') {
    return {
      isValid: false,
      message: 'This field is required',
    };
  }
  return { isValid: true };
};

export const validateNumber = (value: any, min?: number, max?: number): ValidationResult => {
  if (value === undefined || value === null || value === '') {
    return { isValid: true }; // Empty is valid, use validateRequired if the field is required
  }
  
  const numberValue = Number(value);
  
  if (isNaN(numberValue)) {
    return {
      isValid: false,
      message: 'Please enter a valid number',
    };
  }
  
  if (min !== undefined && numberValue < min) {
    return {
      isValid: false,
      message: `Please enter a number greater than or equal to ${min}`,
    };
  }
  
  if (max !== undefined && numberValue > max) {
    return {
      isValid: false,
      message: `Please enter a number less than or equal to ${max}`,
    };
  }
  
  return { isValid: true };
};

export const validateEmail = (value: string): ValidationResult => {
  if (value === undefined || value === null || value === '') {
    return { isValid: true }; // Empty is valid, use validateRequired if the field is required
  }
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  
  if (!emailRegex.test(value)) {
    return {
      isValid: false,
      message: 'Please enter a valid email address',
    };
  }
  
  return { isValid: true };
};

export const validateUrl = (value: string): ValidationResult => {
  if (value === undefined || value === null || value === '') {
    return { isValid: true }; // Empty is valid, use validateRequired if the field is required
  }
  
  try {
    new URL(value);
    return { isValid: true };
  } catch (error) {
    return {
      isValid: false,
      message: 'Please enter a valid URL',
    };
  }
};

export const validateLength = (value: string, min?: number, max?: number): ValidationResult => {
  if (value === undefined || value === null || value === '') {
    return { isValid: true }; // Empty is valid, use validateRequired if the field is required
  }
  
  if (min !== undefined && value.length < min) {
    return {
      isValid: false,
      message: `Please enter at least ${min} characters`,
    };
  }
  
  if (max !== undefined && value.length > max) {
    return {
      isValid: false,
      message: `Please enter no more than ${max} characters`,
    };
  }
  
  return { isValid: true };
};

export const validatePattern = (value: string, pattern: RegExp, message: string): ValidationResult => {
  if (value === undefined || value === null || value === '') {
    return { isValid: true }; // Empty is valid, use validateRequired if the field is required
  }
  
  if (!pattern.test(value)) {
    return {
      isValid: false,
      message,
    };
  }
  
  return { isValid: true };
};

export const validateDateRange = (startDate: string, endDate: string): ValidationResult => {
  if (!startDate || !endDate) {
    return { isValid: true }; // Empty is valid, use validateRequired if the field is required
  }
  
  const start = new Date(startDate);
  const end = new Date(endDate);
  
  if (isNaN(start.getTime()) || isNaN(end.getTime())) {
    return {
      isValid: false,
      message: 'Please enter valid dates',
    };
  }
  
  if (start > end) {
    return {
      isValid: false,
      message: 'Start date must be before end date',
    };
  }
  
  return { isValid: true };
};