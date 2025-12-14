// Admin settings and configuration type definitions

export interface SystemSettings {
  id: string;
  category: SettingsCategory;
  settings: SettingGroup[];
  lastUpdated: string;
  updatedBy: string;
  version: string;
}

export enum SettingsCategory {
  GENERAL = 'GENERAL',
  MATCHING = 'MATCHING',
  RECONCILIATION = 'RECONCILIATION',
  NOTIFICATIONS = 'NOTIFICATIONS',
  SECURITY = 'SECURITY',
  PERFORMANCE = 'PERFORMANCE',
  INTEGRATION = 'INTEGRATION',
  AUDIT = 'AUDIT'
}

export interface SettingGroup {
  id: string;
  name: string;
  description: string;
  icon?: string;
  settings: Setting[];
  permissions?: string[];
  order: number;
}

export interface Setting {
  key: string;
  name: string;
  description: string;
  type: SettingType;
  value: any;
  defaultValue: any;
  validation?: SettingValidation;
  options?: SettingOption[];
  dependencies?: SettingDependency[];
  sensitive?: boolean;
  requiresRestart?: boolean;
  category?: string;
  tags?: string[];
}

export enum SettingType {
  STRING = 'STRING',
  NUMBER = 'NUMBER',
  BOOLEAN = 'BOOLEAN',
  SELECT = 'SELECT',
  MULTI_SELECT = 'MULTI_SELECT',
  JSON = 'JSON',
  PASSWORD = 'PASSWORD',
  EMAIL = 'EMAIL',
  URL = 'URL',
  FILE_PATH = 'FILE_PATH',
  COLOR = 'COLOR',
  DATE = 'DATE',
  TIME = 'TIME'
}

export interface SettingValidation {
  required?: boolean;
  min?: number;
  max?: number;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  customValidator?: string;
  errorMessage?: string;
}

export interface SettingOption {
  label: string;
  value: any;
  description?: string;
  disabled?: boolean;
}

export interface SettingDependency {
  key: string;
  condition: DependencyCondition;
  value: any;
  action: DependencyAction;
}

export enum DependencyCondition {
  EQUALS = 'EQUALS',
  NOT_EQUALS = 'NOT_EQUALS',
  GREATER_THAN = 'GREATER_THAN',
  LESS_THAN = 'LESS_THAN',
  CONTAINS = 'CONTAINS'
}

export enum DependencyAction {
  SHOW = 'SHOW',
  HIDE = 'HIDE',
  ENABLE = 'ENABLE',
  DISABLE = 'DISABLE',
  REQUIRE = 'REQUIRE'
}

// User management types
export interface User {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  displayName: string;
  roles: Role[];
  permissions: Permission[];
  status: UserStatus;
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
  profile?: UserProfile;
  preferences?: UserPreferences;
}

export enum UserStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  SUSPENDED = 'SUSPENDED',
  PENDING = 'PENDING'
}

export interface UserProfile {
  avatar?: string;
  department?: string;
  title?: string;
  phone?: string;
  timezone?: string;
  language?: string;
  bio?: string;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  dateFormat: string;
  timeFormat: string;
  numberFormat: string;
  notifications: NotificationPreferences;
  dashboard: DashboardPreferences;
}

export interface NotificationPreferences {
  email: boolean;
  browser: boolean;
  slack: boolean;
  digest: DigestPreference;
  categories: NotificationCategory[];
}

export interface DigestPreference {
  frequency: 'IMMEDIATE' | 'HOURLY' | 'DAILY' | 'WEEKLY';
  time?: string; // HH:mm format
  timezone?: string;
}

export interface NotificationCategory {
  category: string;
  enabled: boolean;
  channels: string[];
}

export interface DashboardPreferences {
  defaultView: string;
  autoRefresh: boolean;
  refreshInterval: number;
  widgets: string[];
  layout: any;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: Permission[];
  isSystem: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface Permission {
  id: string;
  name: string;
  description: string;
  resource: string;
  action: string;
  conditions?: PermissionCondition[];
}

export interface PermissionCondition {
  field: string;
  operator: string;
  value: any;
}

// Audit and logging types
export interface AuditLog {
  id: string;
  timestamp: string;
  userId: string;
  username: string;
  action: AuditAction;
  resource: string;
  resourceId?: string;
  details: AuditDetails;
  ipAddress: string;
  userAgent: string;
  sessionId?: string;
  outcome: AuditOutcome;
}

export enum AuditAction {
  CREATE = 'CREATE',
  READ = 'READ',
  UPDATE = 'UPDATE',
  DELETE = 'DELETE',
  LOGIN = 'LOGIN',
  LOGOUT = 'LOGOUT',
  EXPORT = 'EXPORT',
  IMPORT = 'IMPORT',
  APPROVE = 'APPROVE',
  REJECT = 'REJECT'
}

export interface AuditDetails {
  description: string;
  oldValues?: Record<string, any>;
  newValues?: Record<string, any>;
  metadata?: Record<string, any>;
}

export enum AuditOutcome {
  SUCCESS = 'SUCCESS',
  FAILURE = 'FAILURE',
  PARTIAL = 'PARTIAL'
}

export interface AuditFilter {
  dateRange?: {
    from: string;
    to: string;
  };
  users?: string[];
  actions?: AuditAction[];
  resources?: string[];
  outcomes?: AuditOutcome[];
  searchTerm?: string;
}

// System monitoring types
export interface SystemHealth {
  timestamp: string;
  overall: HealthStatus;
  components: ComponentHealth[];
  metrics: SystemMetrics;
  alerts: HealthAlert[];
}

export enum HealthStatus {
  HEALTHY = 'HEALTHY',
  WARNING = 'WARNING',
  CRITICAL = 'CRITICAL',
  UNKNOWN = 'UNKNOWN'
}

export interface ComponentHealth {
  name: string;
  status: HealthStatus;
  description: string;
  metrics?: Record<string, number>;
  lastChecked: string;
  uptime?: number;
}

export interface SystemMetrics {
  cpu: MetricValue;
  memory: MetricValue;
  disk: MetricValue;
  network: NetworkMetrics;
  database: DatabaseMetrics;
  performance: PerformanceMetrics;
}

export interface MetricValue {
  current: number;
  average: number;
  peak: number;
  unit: string;
  threshold?: MetricThreshold;
}

export interface MetricThreshold {
  warning: number;
  critical: number;
}

export interface NetworkMetrics {
  inbound: MetricValue;
  outbound: MetricValue;
  latency: MetricValue;
  errors: number;
}

export interface DatabaseMetrics {
  connections: MetricValue;
  queries: MetricValue;
  size: MetricValue;
  responseTime: MetricValue;
}

export interface PerformanceMetrics {
  requestsPerSecond: MetricValue;
  averageResponseTime: MetricValue;
  errorRate: MetricValue;
  uptime: number;
}

export interface HealthAlert {
  id: string;
  level: AlertLevel;
  component: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
  acknowledgedBy?: string;
}

export enum AlertLevel {
  INFO = 'INFO',
  WARNING = 'WARNING',
  ERROR = 'ERROR',
  CRITICAL = 'CRITICAL'
}

// Configuration management types
export interface Configuration {
  id: string;
  name: string;
  description: string;
  environment: Environment;
  version: string;
  configuration: ConfigurationData;
  schema: ConfigurationSchema;
  status: ConfigurationStatus;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  deployedAt?: string;
}

export enum Environment {
  DEVELOPMENT = 'DEVELOPMENT',
  TESTING = 'TESTING',
  STAGING = 'STAGING',
  PRODUCTION = 'PRODUCTION'
}

export interface ConfigurationData {
  [key: string]: any;
}

export interface ConfigurationSchema {
  type: 'object';
  properties: Record<string, SchemaProperty>;
  required?: string[];
}

export interface SchemaProperty {
  type: string;
  description?: string;
  default?: any;
  enum?: any[];
  minimum?: number;
  maximum?: number;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  properties?: Record<string, SchemaProperty>;
}

export enum ConfigurationStatus {
  DRAFT = 'DRAFT',
  ACTIVE = 'ACTIVE',
  ARCHIVED = 'ARCHIVED',
  PENDING_DEPLOYMENT = 'PENDING_DEPLOYMENT'
}

// Data management types
export interface DataRetentionPolicy {
  id: string;
  name: string;
  description: string;
  dataType: DataType;
  retentionPeriod: number; // days
  archiveEnabled: boolean;
  archivePeriod?: number; // days
  compressionEnabled: boolean;
  encryptionRequired: boolean;
  conditions?: RetentionCondition[];
  schedule: RetentionSchedule;
  createdAt: string;
  updatedAt: string;
}

export enum DataType {
  TRADES = 'TRADES',
  MATCHES = 'MATCHES',
  RECONCILIATIONS = 'RECONCILIATIONS',
  AUDIT_LOGS = 'AUDIT_LOGS',
  SYSTEM_LOGS = 'SYSTEM_LOGS',
  REPORTS = 'REPORTS',
  UPLOADS = 'UPLOADS'
}

export interface RetentionCondition {
  field: string;
  operator: string;
  value: any;
}

export interface RetentionSchedule {
  frequency: 'DAILY' | 'WEEKLY' | 'MONTHLY';
  time: string; // HH:mm format
  timezone: string;
  enabled: boolean;
}

export interface BackupConfiguration {
  id: string;
  name: string;
  description: string;
  dataTypes: DataType[];
  schedule: BackupSchedule;
  retention: BackupRetention;
  destination: BackupDestination;
  encryption: BackupEncryption;
  compression: boolean;
  enabled: boolean;
  lastBackup?: string;
  nextBackup?: string;
  status: BackupStatus;
}

export interface BackupSchedule {
  frequency: 'HOURLY' | 'DAILY' | 'WEEKLY' | 'MONTHLY';
  interval: number;
  time?: string; // HH:mm format
  dayOfWeek?: number; // 0-6
  dayOfMonth?: number; // 1-31
  timezone: string;
}

export interface BackupRetention {
  keepHourly: number;
  keepDaily: number;
  keepWeekly: number;
  keepMonthly: number;
  keepYearly: number;
}

export interface BackupDestination {
  type: 'LOCAL' | 'S3' | 'AZURE' | 'GCP';
  configuration: Record<string, any>;
  testConnection?: boolean;
}

export interface BackupEncryption {
  enabled: boolean;
  algorithm?: string;
  keyId?: string;
  keyRotation?: boolean;
}

export enum BackupStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  RUNNING = 'RUNNING',
  FAILED = 'FAILED',
  PAUSED = 'PAUSED'
}

// Integration management types
export interface Integration {
  id: string;
  name: string;
  description: string;
  type: IntegrationType;
  provider: IntegrationProvider;
  configuration: IntegrationConfiguration;
  credentials: IntegrationCredentials;
  status: IntegrationStatus;
  healthCheck: IntegrationHealthCheck;
  metadata: IntegrationMetadata;
  createdAt: string;
  updatedAt: string;
}

export enum IntegrationType {
  API = 'API',
  DATABASE = 'DATABASE',
  FILE_SYSTEM = 'FILE_SYSTEM',
  MESSAGE_QUEUE = 'MESSAGE_QUEUE',
  EMAIL = 'EMAIL',
  WEBHOOK = 'WEBHOOK'
}

export enum IntegrationProvider {
  CUSTOM = 'CUSTOM',
  AWS = 'AWS',
  AZURE = 'AZURE',
  GCP = 'GCP',
  SALESFORCE = 'SALESFORCE',
  SLACK = 'SLACK',
  MICROSOFT = 'MICROSOFT'
}

export interface IntegrationConfiguration {
  endpoint?: string;
  version?: string;
  timeout?: number;
  retries?: number;
  rateLimiting?: RateLimitConfiguration;
  dataMapping?: DataMappingConfiguration;
  customSettings?: Record<string, any>;
}

export interface RateLimitConfiguration {
  requestsPerSecond: number;
  burstSize: number;
  backoffStrategy: 'LINEAR' | 'EXPONENTIAL';
}

export interface DataMappingConfiguration {
  inputMapping: Record<string, string>;
  outputMapping: Record<string, string>;
  transformations?: TransformationRule[];
}

export interface TransformationRule {
  field: string;
  type: 'FORMAT' | 'CALCULATE' | 'LOOKUP' | 'CONDITIONAL';
  configuration: Record<string, any>;
}

export interface IntegrationCredentials {
  type: 'API_KEY' | 'OAUTH' | 'BASIC' | 'CERTIFICATE';
  encrypted: boolean;
  expiresAt?: string;
  rotationEnabled?: boolean;
  rotationInterval?: number; // days
}

export enum IntegrationStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  ERROR = 'ERROR',
  TESTING = 'TESTING',
  CONFIGURING = 'CONFIGURING'
}

export interface IntegrationHealthCheck {
  lastChecked: string;
  status: HealthStatus;
  responseTime: number;
  errorCount: number;
  successRate: number;
  uptime: number;
}

export interface IntegrationMetadata {
  version: string;
  tags: string[];
  documentation?: string;
  supportContact?: string;
  maintenanceWindow?: string;
}

// License and compliance types
export interface LicenseInfo {
  type: LicenseType;
  edition: string;
  maxUsers: number;
  currentUsers: number;
  features: string[];
  expirationDate?: string;
  support: SupportLevel;
  compliance: ComplianceInfo;
}

export enum LicenseType {
  TRIAL = 'TRIAL',
  STANDARD = 'STANDARD',
  PROFESSIONAL = 'PROFESSIONAL',
  ENTERPRISE = 'ENTERPRISE'
}

export enum SupportLevel {
  COMMUNITY = 'COMMUNITY',
  BUSINESS = 'BUSINESS',
  ENTERPRISE = 'ENTERPRISE',
  PREMIUM = 'PREMIUM'
}

export interface ComplianceInfo {
  certifications: string[];
  dataResidency: string[];
  auditFrequency: string;
  lastAudit?: string;
  nextAudit?: string;
}
