/**
 * API configuration
 */

// Base API URL - this should be environment-specific
export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3001/api';

// API endpoints
export const API_ENDPOINTS = {
  // Agent endpoints
  AGENT: {
    BASE: '/agents',
    RUNS: '/agents/runs',
    RUN_DETAIL: (runId: string) => `/agents/runs/${runId}`,
    THINKING_PROCESS: (runId: string) => `/agents/runs/${runId}/thinking`,
    CANCEL_RUN: (runId: string) => `/agents/runs/${runId}/cancel`,
    EXPORT_RUN: (runId: string, format: string) => `/agents/runs/${runId}/export?format=${format}`,
    SHARE_RUN: (runId: string) => `/agents/runs/${runId}/share`,
    ARCHIVE_RUN: (runId: string) => `/agents/runs/${runId}/archive`,
    UNARCHIVE_RUN: (runId: string) => `/agents/runs/${runId}/unarchive`,
    CONFIGURATIONS: '/agents/configurations',
    CONFIGURATION_DETAIL: (configId: string) => `/agents/configurations/${configId}`,
    SETTINGS: '/agents/settings',
    SYSTEM_HEALTH: '/agents/system-health',
  },
};

// WebSocket endpoints
export const WS_ENDPOINTS = {
  AGENT_THINKING: (runId: string) => `/ws/agents/runs/${runId}/thinking`,
  AGENT_STATUS: '/ws/agents/status',
};

// Request timeouts (in milliseconds)
export const REQUEST_TIMEOUTS = {
  DEFAULT: 30000, // 30 seconds
  LONG: 60000,    // 60 seconds
  SHORT: 10000,   // 10 seconds
};

// Retry configuration
export const RETRY_CONFIG = {
  MAX_RETRIES: 3,
  BASE_DELAY: 1000, // 1 second
};