/**
 * BaseApiService provides common functionality for API communication
 * including error handling, retry logic, and request/response processing.
 */
import { ErrorHandler, EnhancedError } from './ErrorHandler';

export interface ApiError {
  status: number;
  message: string;
  details?: any;
}

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
}

export interface RequestOptions {
  headers?: Record<string, string>;
  retryCount?: number;
  retryDelay?: number;
  timeout?: number;
}

export class BaseApiService {
  protected baseUrl: string;
  protected defaultOptions: RequestOptions;

  constructor(baseUrl: string, defaultOptions: RequestOptions = {}) {
    this.baseUrl = baseUrl;
    this.defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
      },
      retryCount: 3,
      retryDelay: 1000,
      timeout: 30000,
      ...defaultOptions,
    };
  }

  /**
   * Performs an API request with retry mechanism
   */
  protected async request<T>(
    endpoint: string,
    method: string,
    data?: any,
    options?: RequestOptions
  ): Promise<ApiResponse<T>> {
    const mergedOptions = { ...this.defaultOptions, ...options };
    const { retryCount, retryDelay } = mergedOptions;
    
    let lastError: Error | null = null;
    
    for (let attempt = 0; attempt <= retryCount!; attempt++) {
      try {
        const response = await this.performRequest<T>(endpoint, method, data, mergedOptions);
        return response;
      } catch (error) {
        lastError = error as Error;
        
        // Don't retry if it's a client error (4xx)
        if (error instanceof Error && 'status' in error && (error as any).status >= 400 && (error as any).status < 500) {
          break;
        }
        
        // Don't retry on the last attempt
        if (attempt === retryCount) {
          break;
        }
        
        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, retryDelay! * Math.pow(2, attempt)));
      }
    }
    
    return {
      error: {
        status: (lastError && 'status' in lastError) ? (lastError as any).status : 0,
        message: lastError?.message || 'Unknown error occurred',
        details: lastError,
      },
    };
  }

  /**
   * Performs the actual fetch request
   */
  private async performRequest<T>(
    endpoint: string,
    method: string,
    data?: any,
    options?: RequestOptions
  ): Promise<ApiResponse<T>> {
    const { headers, timeout } = options || {};
    
    const url = `${this.baseUrl}${endpoint}`;
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(url, {
        method,
        headers: headers as HeadersInit,
        body: data ? JSON.stringify(data) : undefined,
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error: ApiError = {
          status: response.status,
          message: errorData.message || response.statusText,
          details: errorData,
        };
        
        const customError = new Error(error.message) as Error & { status?: number };
        customError.status = error.status;
        throw customError;
      }
      
      const responseData = await response.json();
      
      return {
        data: responseData as T,
      };
    } catch (error) {
      clearTimeout(timeoutId);
      
      if ((error as Error).name === 'AbortError') {
        const customError = new Error('Request timeout') as Error & { status?: number };
        customError.status = 408;
        throw customError;
      }
      
      throw error;
    }
  }

  /**
   * Performs a GET request
   */
  protected async get<T>(endpoint: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, 'GET', undefined, options);
  }

  /**
   * Performs a POST request
   */
  protected async post<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, 'POST', data, options);
  }

  /**
   * Performs a PUT request
   */
  protected async put<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, 'PUT', data, options);
  }

  /**
   * Performs a DELETE request
   */
  protected async delete<T>(endpoint: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, 'DELETE', undefined, options);
  }

  /**
   * Handles API errors consistently
   */
  protected handleError(error: ApiError): never {
    // Enhance the error with additional metadata
    const enhancedError = ErrorHandler.enhanceError(error);
    
    // Log the error
    ErrorHandler.logError(error);
    
    // Throw the enhanced error
    throw enhancedError;
  }
}