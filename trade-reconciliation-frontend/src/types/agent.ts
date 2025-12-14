/**
 * Type definitions for the Agent Monitor feature
 */

// Agent run configuration
export interface AgentRunConfig {
  agentType: string;
  parameters: {
    matchingThreshold?: number;
    numericTolerance?: number;
    reportBucket?: string;
    [key: string]: any; // Additional parameters specific to agent type
  };
  inputData?: {
    tradeIds?: string[];
    documentIds?: string[];
    dateRange?: {
      startDate: string;
      endDate: string;
    };
    [key: string]: any; // Additional input data specific to agent type
  };
}

// Saved configuration
export interface SavedConfiguration {
  id: string;
  name: string;
  description?: string;
  config: AgentRunConfig;
  createdAt: string;
  updatedAt: string;
}

// Agent run status
export type AgentRunStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';

// Agent run
export interface AgentRun {
  id: string;
  agentType: string;
  status: AgentRunStatus;
  progress: number; // 0-100
  startTime?: string;
  endTime?: string;
  config: AgentRunConfig;
  error?: string;
  results?: AgentRunResults;
  metrics?: {
    duration: number;
    resourceUsage: {
      cpu: number;
      memory: number;
    };
    [key: string]: any; // Additional metrics specific to agent type
  };
  archived?: boolean; // Whether the run has been archived
  archivedAt?: string; // When the run was archived
  archivedBy?: string; // Who archived the run
}

// Agent thinking step type
export type AgentThinkingStepType = 'action' | 'decision' | 'observation' | 'error' | 'info';

// Agent thinking step
export interface AgentThinkingStep {
  id: string;
  runId: string;
  timestamp: string;
  type: AgentThinkingStepType;
  content: string;
  metadata?: {
    [key: string]: any; // Additional metadata specific to step type
  };
  parentId?: string; // For hierarchical thinking steps
  children?: AgentThinkingStep[]; // Child steps for hierarchical display
}

// Agent run results
export interface AgentRunResults {
  summary: string;
  outputData: {
    [key: string]: any; // Output data specific to agent type
  };
  generatedReports?: {
    id: string;
    name: string;
    url: string;
    type: string;
  }[];
  actionItems?: {
    id: string;
    description: string;
    type: string;
    status: 'pending' | 'completed' | 'ignored';
  }[];
}

// Agent settings
export interface AgentSettings {
  globalSettings: {
    maxConcurrentRuns: number;
    defaultMatchingThreshold: number;
    defaultNumericTolerance: number;
    defaultReportBucket: string;
  };
  agentSpecificSettings: {
    [agentType: string]: {
      [key: string]: any; // Settings specific to agent type
    };
  };
}

// System health
export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  metrics: {
    cpu: number; // Percentage (0-100)
    memory: number; // Percentage (0-100)
    disk: number; // Percentage (0-100)
    uptime: number; // Seconds
  };
  agents: {
    [agentType: string]: {
      status: 'healthy' | 'degraded' | 'unhealthy';
      lastRun?: string;
      message?: string;
    };
  };
}

// Run history filters
export interface RunHistoryFilters {
  agentType?: string;
  status?: AgentRunStatus;
  startDate?: string;
  endDate?: string;
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortDirection?: 'asc' | 'desc';
  showArchived?: boolean;
}