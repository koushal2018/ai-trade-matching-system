// Agent execution monitoring type definitions

export interface AgentExecution {
  id: string;
  name: string;
  type: AgentType;
  status: AgentExecutionStatus;
  startedAt: string;
  completedAt?: string;
  duration?: number; // milliseconds
  steps: ExecutionStep[];
  currentStep?: number;
  progress: ExecutionProgress;
  configuration: AgentConfiguration;
  results?: AgentExecutionResults;
  error?: AgentExecutionError;
  metadata: ExecutionMetadata;
}

export enum AgentType {
  TRADE_MATCHING = 'TRADE_MATCHING',
  DATA_EXTRACTION = 'DATA_EXTRACTION',
  RECONCILIATION = 'RECONCILIATION',
  VALIDATION = 'VALIDATION',
  REPORT_GENERATION = 'REPORT_GENERATION',
  CUSTOM = 'CUSTOM'
}

export enum AgentExecutionStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
  PAUSED = 'PAUSED',
  RETRYING = 'RETRYING'
}

export interface ExecutionStep {
  id: string;
  name: string;
  description: string;
  status: StepStatus;
  startedAt?: string;
  completedAt?: string;
  duration?: number;
  inputs?: Record<string, any>;
  outputs?: Record<string, any>;
  error?: StepError;
  logs: LogEntry[];
  subSteps?: ExecutionStep[];
  order: number;
}

export enum StepStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  SKIPPED = 'SKIPPED',
  RETRYING = 'RETRYING'
}

export interface StepError {
  code: string;
  message: string;
  details?: Record<string, any>;
  stack?: string;
  recoverable: boolean;
  retryCount?: number;
  maxRetries?: number;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  source: string;
  context?: Record<string, any>;
  stepId?: string;
}

export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
  FATAL = 'FATAL'
}

export interface ExecutionProgress {
  percentage: number;
  currentStepIndex: number;
  totalSteps: number;
  completedSteps: number;
  failedSteps: number;
  skippedSteps: number;
  estimatedTimeRemaining?: number; // milliseconds
  throughput?: ThroughputMetrics;
}

export interface ThroughputMetrics {
  itemsProcessed: number;
  totalItems: number;
  itemsPerSecond: number;
  averageItemProcessingTime: number;
}

export interface AgentConfiguration {
  id: string;
  name: string;
  version: string;
  parameters: Record<string, any>;
  environment: ExecutionEnvironment;
  resources: ResourceRequirements;
  scheduling: SchedulingConfig;
  notifications: NotificationConfig;
}

export interface ExecutionEnvironment {
  runtime: string;
  version: string;
  region?: string;
  instanceType?: string;
  containerImage?: string;
  environmentVariables?: Record<string, string>;
}

export interface ResourceRequirements {
  cpu: number; // cores
  memory: number; // MB
  storage: number; // GB
  timeout: number; // seconds
  maxRetries: number;
}

export interface SchedulingConfig {
  trigger: TriggerType;
  schedule?: string; // cron expression
  dependencies?: string[]; // agent execution IDs
  condition?: string; // JSON logic expression
  priority: Priority;
}

export enum TriggerType {
  MANUAL = 'MANUAL',
  SCHEDULED = 'SCHEDULED',
  EVENT = 'EVENT',
  DEPENDENCY = 'DEPENDENCY'
}

export enum Priority {
  LOW = 'LOW',
  NORMAL = 'NORMAL',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

export interface NotificationConfig {
  onSuccess?: NotificationChannel[];
  onFailure?: NotificationChannel[];
  onStart?: NotificationChannel[];
  channels: NotificationChannelConfig[];
}

export interface NotificationChannel {
  type: ChannelType;
  target: string;
  template?: string;
}

export enum ChannelType {
  EMAIL = 'EMAIL',
  SLACK = 'SLACK',
  WEBHOOK = 'WEBHOOK',
  SMS = 'SMS'
}

export interface NotificationChannelConfig {
  id: string;
  type: ChannelType;
  name: string;
  configuration: Record<string, any>;
  enabled: boolean;
}

export interface AgentExecutionResults {
  summary: AgentResultSummary;
  outputs: Record<string, any>;
  artifacts: ExecutionArtifact[];
  metrics: ExecutionMetrics;
}

export interface AgentResultSummary {
  success: boolean;
  itemsProcessed: number;
  itemsSuccessful: number;
  itemsFailed: number;
  executionTime: number;
  key_insights?: string[];
  recommendations?: string[];
}

export interface ExecutionArtifact {
  id: string;
  name: string;
  type: ArtifactType;
  size: number;
  url?: string;
  metadata?: Record<string, any>;
  createdAt: string;
}

export enum ArtifactType {
  REPORT = 'REPORT',
  DATA_FILE = 'DATA_FILE',
  LOG_FILE = 'LOG_FILE',
  SCREENSHOT = 'SCREENSHOT',
  CHART = 'CHART',
  OTHER = 'OTHER'
}

export interface ExecutionMetrics {
  performanceMetrics: AgentPerformanceMetrics;
  resourceUtilization: ResourceUtilization;
  qualityMetrics: QualityMetrics;
}

export interface AgentPerformanceMetrics {
  totalExecutionTime: number;
  averageStepTime: number;
  fastestStep: StepMetric;
  slowestStep: StepMetric;
  throughput: number;
}

export interface StepMetric {
  stepName: string;
  duration: number;
  timestamp: string;
}

export interface ResourceUtilization {
  peakCpuUsage: number; // percentage
  averageCpuUsage: number;
  peakMemoryUsage: number; // MB
  averageMemoryUsage: number;
  diskIoRead: number; // MB
  diskIoWrite: number; // MB
  networkIn: number; // MB
  networkOut: number; // MB
}

export interface QualityMetrics {
  accuracy?: number; // percentage
  precision?: number; // percentage
  recall?: number; // percentage
  f1Score?: number;
  errorRate: number; // percentage
  dataQualityScore?: number;
}

export interface AgentExecutionError {
  code: string;
  message: string;
  details: Record<string, any>;
  stack?: string;
  timestamp: string;
  recoverable: boolean;
  retryAttempts: number;
  lastRetryAt?: string;
}

export interface ExecutionMetadata {
  createdBy: string;
  environment: string;
  version: string;
  tags: string[];
  correlationId?: string;
  parentExecutionId?: string;
  childExecutionIds?: string[];
  sourceFiles?: string[];
  gitCommit?: string;
}

// Historical and analytics types
export interface ExecutionHistory {
  executions: AgentExecution[];
  summary: HistorySummary;
  pagination: HistoryPagination;
  filters: ExecutionHistoryFilter;
}

export interface HistorySummary {
  totalExecutions: number;
  successfulExecutions: number;
  failedExecutions: number;
  averageExecutionTime: number;
  successRate: number;
  totalItemsProcessed: number;
  trends: ExecutionTrend[];
}

export interface ExecutionTrend {
  date: string;
  executions: number;
  successRate: number;
  averageTime: number;
  itemsProcessed: number;
}

export interface HistoryPagination {
  currentPage: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

export interface ExecutionHistoryFilter {
  agentTypes?: AgentType[];
  status?: AgentExecutionStatus[];
  dateRange?: {
    from: string;
    to: string;
  };
  createdBy?: string[];
  environment?: string[];
  tags?: string[];
  duration?: {
    min: number;
    max: number;
  };
  searchTerm?: string;
}

// Real-time monitoring types
export interface ExecutionMonitor {
  executionId: string;
  isLive: boolean;
  updates: ExecutionUpdate[];
  subscription: MonitorSubscription;
}

export interface ExecutionUpdate {
  id: string;
  timestamp: string;
  type: UpdateType;
  data: Record<string, any>;
  executionId: string;
  stepId?: string;
}

export enum UpdateType {
  STATUS_CHANGE = 'STATUS_CHANGE',
  PROGRESS_UPDATE = 'PROGRESS_UPDATE',
  STEP_STARTED = 'STEP_STARTED',
  STEP_COMPLETED = 'STEP_COMPLETED',
  STEP_FAILED = 'STEP_FAILED',
  LOG_ENTRY = 'LOG_ENTRY',
  METRICS_UPDATE = 'METRICS_UPDATE',
  ERROR_OCCURRED = 'ERROR_OCCURRED'
}

export interface MonitorSubscription {
  id: string;
  executionId: string;
  events: UpdateType[];
  websocketUrl: string;
  connected: boolean;
  lastHeartbeat?: string;
}

// Control and management types
export interface ExecutionControl {
  executionId: string;
  availableActions: ControlAction[];
}

export enum ControlAction {
  START = 'START',
  PAUSE = 'PAUSE',
  RESUME = 'RESUME',
  CANCEL = 'CANCEL',
  RETRY = 'RETRY',
  SKIP_STEP = 'SKIP_STEP',
  RESTART = 'RESTART'
}

export interface ControlRequest {
  executionId: string;
  action: ControlAction;
  parameters?: Record<string, any>;
  reason?: string;
  requestedBy: string;
}

export interface ControlResponse {
  success: boolean;
  message: string;
  newStatus?: AgentExecutionStatus;
  error?: string;
}

// Queue and scheduling types
export interface ExecutionQueue {
  pending: QueuedExecution[];
  running: AgentExecution[];
  summary: QueueSummary;
}

export interface QueuedExecution {
  id: string;
  agentType: AgentType;
  configuration: AgentConfiguration;
  queuedAt: string;
  estimatedStartTime?: string;
  priority: Priority;
  position: number;
  dependencies?: string[];
}

export interface QueueSummary {
  totalPending: number;
  totalRunning: number;
  averageWaitTime: number;
  estimatedQueueClearTime?: number;
  highPriorityCount: number;
  resourceUtilization: number; // percentage
}

// Template and configuration types
export interface AgentTemplate {
  id: string;
  name: string;
  description: string;
  type: AgentType;
  version: string;
  configuration: TemplateConfiguration;
  parameters: AgentParameterDefinition[];
  tags: string[];
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  isPublic: boolean;
  usageCount: number;
}

export interface TemplateConfiguration {
  runtime: ExecutionEnvironment;
  resources: ResourceRequirements;
  steps: StepTemplate[];
  defaultParameters: Record<string, any>;
}

export interface StepTemplate {
  name: string;
  description: string;
  type: string;
  configuration: Record<string, any>;
  order: number;
  optional: boolean;
  retryable: boolean;
}

export interface AgentParameterDefinition {
  name: string;
  type: AgentParameterType;
  description: string;
  required: boolean;
  defaultValue?: any;
  validation?: AgentValidationRule[];
  options?: AgentParameterOption[];
}

export enum AgentParameterType {
  STRING = 'STRING',
  NUMBER = 'NUMBER',
  BOOLEAN = 'BOOLEAN',
  DATE = 'DATE',
  SELECT = 'SELECT',
  MULTI_SELECT = 'MULTI_SELECT',
  FILE = 'FILE',
  JSON = 'JSON'
}

export interface AgentParameterOption {
  label: string;
  value: any;
  description?: string;
}

export interface AgentValidationRule {
  type: string;
  parameters: Record<string, any>;
  message: string;
}
