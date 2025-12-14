# Design Document: Agent Monitor

## Overview

The Agent Monitor is a comprehensive interface for users to interact with and monitor the Strands AI agents that power the trade reconciliation system. This feature enables users to trigger agent runs with custom parameters, view the agent's thinking process in real-time, monitor the status of ongoing runs, and review historical runs. The Agent Monitor serves as the central control panel for all AI agent operations within the trade reconciliation system.

## Architecture

The Agent Monitor will follow a component-based architecture within the React application, with clear separation of concerns:

1. **Presentation Layer**: React components that render the UI for the Agent Monitor
2. **State Management**: React context or Redux for managing application state
3. **Service Layer**: API services for communicating with the backend
4. **Utility Layer**: Helper functions for data formatting, validation, etc.

The Agent Monitor will integrate with the Strands agents located at `/Users/koushald/agentic-ai-reconcillation/strandsagents` through API calls to trigger runs, fetch status updates, and retrieve historical data.

## Components and Interfaces

### 1. AgentMonitorPage

The main container component that houses all Agent Monitor functionality and manages routing between different views.

```typescript
interface AgentMonitorPageProps {
  // Any props needed for the page
}

const AgentMonitorPage: React.FC<AgentMonitorPageProps> = (props) => {
  // Component implementation
};
```

### 2. AgentRunForm

A form component for configuring and triggering new agent runs.

```typescript
interface AgentRunFormProps {
  onSubmit: (config: AgentRunConfig) => Promise<void>;
  savedConfigurations?: SavedConfiguration[];
  onSaveConfiguration?: (config: SavedConfiguration) => Promise<void>;
}

const AgentRunForm: React.FC<AgentRunFormProps> = (props) => {
  // Component implementation
};
```

### 3. AgentThinkingProcess

A component for displaying the real-time thinking process of an agent.

```typescript
interface AgentThinkingProcessProps {
  runId: string;
  autoScroll?: boolean;
}

const AgentThinkingProcess: React.FC<AgentThinkingProcessProps> = (props) => {
  // Component implementation
};
```

### 4. AgentRunStatus

A component for displaying the status and progress of agent runs.

```typescript
interface AgentRunStatusProps {
  runs: AgentRun[];
  onCancelRun?: (runId: string) => Promise<void>;
}

const AgentRunStatus: React.FC<AgentRunStatusProps> = (props) => {
  // Component implementation
};
```

### 5. AgentRunHistory

A component for displaying and filtering historical agent runs.

```typescript
interface AgentRunHistoryProps {
  onSelectRun: (runId: string) => void;
  onCompareRuns?: (runIds: string[]) => void;
}

const AgentRunHistory: React.FC<AgentRunHistoryProps> = (props) => {
  // Component implementation
};
```

### 6. AgentSettings

A component for configuring agent settings and monitoring system health.

```typescript
interface AgentSettingsProps {
  onSaveSettings: (settings: AgentSettings) => Promise<void>;
}

const AgentSettings: React.FC<AgentSettingsProps> = (props) => {
  // Component implementation
};
```

## Data Models

### 1. AgentRunConfig

```typescript
interface AgentRunConfig {
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
```

### 2. SavedConfiguration

```typescript
interface SavedConfiguration {
  id: string;
  name: string;
  description?: string;
  config: AgentRunConfig;
  createdAt: string;
  updatedAt: string;
}
```

### 3. AgentRun

```typescript
interface AgentRun {
  id: string;
  agentType: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
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
}
```

### 4. AgentThinkingStep

```typescript
interface AgentThinkingStep {
  id: string;
  runId: string;
  timestamp: string;
  type: 'action' | 'decision' | 'observation' | 'error' | 'info';
  content: string;
  metadata?: {
    [key: string]: any; // Additional metadata specific to step type
  };
  parentId?: string; // For hierarchical thinking steps
}
```

### 5. AgentRunResults

```typescript
interface AgentRunResults {
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
```

### 6. AgentSettings

```typescript
interface AgentSettings {
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
```

## API Services

### 1. AgentService

```typescript
class AgentService {
  // Run management
  async triggerRun(config: AgentRunConfig): Promise<string> // Returns run ID
  async cancelRun(runId: string): Promise<boolean>
  async getRun(runId: string): Promise<AgentRun>
  async getActiveRuns(): Promise<AgentRun[]>
  async getRunHistory(filters?: RunHistoryFilters): Promise<AgentRun[]>
  
  // Thinking process
  async getThinkingProcess(runId: string): Promise<AgentThinkingStep[]>
  async subscribeToThinkingProcess(runId: string, callback: (step: AgentThinkingStep) => void): Promise<() => void> // Returns unsubscribe function
  
  // Configuration management
  async getSavedConfigurations(): Promise<SavedConfiguration[]>
  async saveConfiguration(config: SavedConfiguration): Promise<string> // Returns configuration ID
  async deleteConfiguration(configId: string): Promise<boolean>
  
  // Settings management
  async getSettings(): Promise<AgentSettings>
  async updateSettings(settings: AgentSettings): Promise<boolean>
  
  // System health
  async getSystemHealth(): Promise<SystemHealth>
}
```

## Error Handling

The Agent Monitor will implement a comprehensive error handling strategy:

1. **Form Validation**: Client-side validation for all form inputs with clear error messages
2. **API Error Handling**: Proper handling of API errors with user-friendly messages
3. **Retry Mechanism**: Automatic retry for transient errors with exponential backoff
4. **Error Boundaries**: React error boundaries to prevent the entire application from crashing
5. **Error Logging**: Logging of errors for debugging and monitoring purposes

Error messages will be displayed in a consistent manner using a toast notification system or inline error messages, depending on the context.

## Testing Strategy

The Agent Monitor will be tested using a combination of:

1. **Unit Tests**: Testing individual components and functions in isolation
2. **Integration Tests**: Testing the interaction between components
3. **End-to-End Tests**: Testing the entire feature from the user's perspective

Key test cases will include:

1. Form validation and submission
2. Real-time updates of agent thinking process
3. Status updates for running agents
4. Filtering and sorting of historical runs
5. Error handling and recovery
6. Performance under load (multiple concurrent runs)

## Implementation Considerations

1. **Real-time Updates**: WebSockets or Server-Sent Events will be used for real-time updates of agent thinking process and status
2. **Pagination**: Large datasets (like historical runs) will be paginated to improve performance
3. **Caching**: Frequently accessed data will be cached to reduce API calls
4. **Responsive Design**: The UI will be responsive to work well on different screen sizes
5. **Accessibility**: The UI will follow accessibility best practices (WCAG 2.1)
6. **Performance**: The UI will be optimized for performance, especially when displaying large amounts of data
7. **Security**: All API calls will be authenticated and authorized