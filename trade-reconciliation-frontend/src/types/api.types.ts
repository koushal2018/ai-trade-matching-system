// API and HTTP request/response type definitions

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: ApiError;
  metadata?: ResponseMetadata;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
  field?: string;
  timestamp: string;
  traceId?: string;
}

export interface ResponseMetadata {
  timestamp: string;
  version: string;
  requestId: string;
  processingTime: number;
  rateLimit?: RateLimitInfo;
}

export interface RateLimitInfo {
  limit: number;
  remaining: number;
  resetTime: string;
}

// Pagination types
export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationInfo;
  total: number;
}

export interface PaginationInfo {
  page: number;
  pageSize: number;
  totalPages: number;
  totalItems: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

export interface PaginationRequest {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'ASC' | 'DESC';
}

// HTTP method types
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface RequestConfig {
  method: HttpMethod;
  url: string;
  headers?: Record<string, string>;
  params?: Record<string, any>;
  data?: any;
  timeout?: number;
  retries?: number;
  auth?: AuthConfig;
}

export interface AuthConfig {
  type: 'Bearer' | 'Basic' | 'ApiKey';
  token?: string;
  username?: string;
  password?: string;
  apiKey?: string;
}

// Upload types
export interface FileUploadRequest {
  file: File;
  filename?: string;
  metadata?: Record<string, any>;
  onProgress?: (progress: number) => void;
}

export interface FileUploadResponse {
  fileId: string;
  filename: string;
  size: number;
  contentType: string;
  url?: string;
  metadata?: Record<string, any>;
}

export interface MultipartUploadRequest {
  files: FileUploadRequest[];
  metadata?: Record<string, any>;
}

// Batch operation types
export interface BatchRequest<T> {
  operations: BatchOperation<T>[];
  metadata?: Record<string, any>;
}

export interface BatchOperation<T> {
  id: string;
  method: HttpMethod;
  resource: string;
  data?: T;
}

export interface BatchResponse<T> {
  results: BatchOperationResult<T>[];
  summary: BatchSummary;
}

export interface BatchOperationResult<T> {
  id: string;
  success: boolean;
  data?: T;
  error?: ApiError;
}

export interface BatchSummary {
  total: number;
  successful: number;
  failed: number;
  processingTime: number;
}

// WebSocket types
export interface WebSocketMessage {
  id: string;
  type: string;
  timestamp: string;
  data: any;
  channel?: string;
}

export interface WebSocketSubscription {
  id: string;
  channel: string;
  events: string[];
  filters?: Record<string, any>;
}

export interface WebSocketConfig {
  url: string;
  protocols?: string[];
  heartbeatInterval?: number;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  auth?: AuthConfig;
}

// Search and filter types
export interface SearchRequest {
  query?: string;
  filters?: Record<string, any>;
  sort?: SortCriteria[];
  pagination?: PaginationRequest;
  facets?: string[];
}

export interface SortCriteria {
  field: string;
  order: 'ASC' | 'DESC';
}

export interface SearchResponse<T> {
  items: T[];
  total: number;
  facets?: SearchFacet[];
  suggestions?: string[];
  pagination: PaginationInfo;
  searchTime: number;
}

export interface SearchFacet {
  field: string;
  values: FacetValue[];
}

export interface FacetValue {
  value: string;
  count: number;
  selected?: boolean;
}

// Cache types
export interface CacheConfig {
  ttl?: number; // Time to live in seconds
  maxAge?: number;
  staleWhileRevalidate?: boolean;
  cacheKey?: string;
}

// Error handling types
export enum HttpStatusCode {
  OK = 200,
  CREATED = 201,
  ACCEPTED = 202,
  NO_CONTENT = 204,
  BAD_REQUEST = 400,
  UNAUTHORIZED = 401,
  FORBIDDEN = 403,
  NOT_FOUND = 404,
  METHOD_NOT_ALLOWED = 405,
  CONFLICT = 409,
  UNPROCESSABLE_ENTITY = 422,
  TOO_MANY_REQUESTS = 429,
  INTERNAL_SERVER_ERROR = 500,
  BAD_GATEWAY = 502,
  SERVICE_UNAVAILABLE = 503,
  GATEWAY_TIMEOUT = 504
}

export interface NetworkError {
  name: 'NetworkError';
  message: string;
  status?: number;
  code?: string;
  isTimeout: boolean;
  isOffline: boolean;
}

export interface ValidationError {
  name: 'ValidationError';
  message: string;
  field: string;
  code: string;
  value?: any;
}

// Request interceptor types
export interface RequestInterceptor {
  onRequest?: (config: RequestConfig) => RequestConfig | Promise<RequestConfig>;
  onRequestError?: (error: any) => Promise<any>;
}

export interface ResponseInterceptor {
  onResponse?: (response: any) => any | Promise<any>;
  onResponseError?: (error: any) => Promise<any>;
}

// Health check types
export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy' | 'degraded';
  timestamp: string;
  version: string;
  uptime: number;
  checks: HealthCheck[];
}

export interface HealthCheck {
  name: string;
  status: 'pass' | 'fail' | 'warn';
  time: string;
  output?: string;
}

// Logging types
export interface ApiLog {
  id: string;
  method: HttpMethod;
  url: string;
  status: number;
  duration: number;
  timestamp: string;
  userId?: string;
  userAgent?: string;
  ipAddress?: string;
  requestId: string;
  error?: ApiError;
}

export interface LogFilter {
  methods?: HttpMethod[];
  statusCodes?: number[];
  dateRange?: {
    from: string;
    to: string;
  };
  userId?: string;
  minDuration?: number;
  maxDuration?: number;
}

// Rate limiting types
export interface RateLimitConfig {
  windowMs: number;
  maxRequests: number;
  skipSuccessfulRequests?: boolean;
  skipFailedRequests?: boolean;
  keyGenerator?: (request: any) => string;
}

export interface RateLimitStatus {
  limit: number;
  current: number;
  remaining: number;
  resetTime: Date;
  isBlocked: boolean;
}
