// Reconciliation detail specific type definitions

import { Trade, FieldComparison, Discrepancy, ResolutionDetails, ReconciliationStatus } from './trade.types';

export interface ReconciliationDetail {
  id: string;
  tradeId: string;
  bankTrade: Trade;
  counterpartyTrade: Trade;
  status: ReconciliationStatus;
  summary: ReconciliationSummary;
  fieldComparisons: ReconciliationFieldComparison[];
  discrepancies: EnhancedDiscrepancy[];
  resolution?: ResolutionDetails;
  auditTrail: ReconciliationAuditEntry[];
  attachments?: ReconciliationAttachment[];
  createdAt: string;
  updatedAt: string;
  reviewedBy?: string;
  reviewedAt?: string;
}

export interface ReconciliationSummary {
  totalFields: number;
  matchedFields: number;
  mismatchedFields: number;
  criticalDiscrepancies: number;
  warningDiscrepancies: number;
  infoDiscrepancies: number;
  overallScore: number;
  riskLevel: RiskLevel;
  recommendedAction: RecommendedAction;
}

export enum RiskLevel {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

export enum RecommendedAction {
  AUTO_APPROVE = 'AUTO_APPROVE',
  MANUAL_REVIEW = 'MANUAL_REVIEW',
  REJECT = 'REJECT',
  ESCALATE = 'ESCALATE'
}

export interface ReconciliationFieldComparison extends FieldComparison {
  fieldType: FieldType;
  displayName: string;
  category: FieldCategory;
  weight: number;
  toleranceConfig?: ToleranceConfig;
  validationRules?: ValidationRule[];
  historicalData?: HistoricalFieldData;
  explanation?: string;
  suggestedResolution?: string;
}

export enum FieldType {
  NUMERIC = 'NUMERIC',
  DATE = 'DATE',
  STRING = 'STRING',
  CURRENCY = 'CURRENCY',
  ENUM = 'ENUM',
  BOOLEAN = 'BOOLEAN'
}

export enum FieldCategory {
  FINANCIAL = 'FINANCIAL',
  IDENTIFICATION = 'IDENTIFICATION',
  TEMPORAL = 'TEMPORAL',
  COUNTERPARTY = 'COUNTERPARTY',
  INSTRUMENT = 'INSTRUMENT',
  METADATA = 'METADATA'
}

export interface ToleranceConfig {
  type: ToleranceType;
  value: number;
  unit?: string;
  description: string;
}

export enum ToleranceType {
  ABSOLUTE = 'ABSOLUTE',
  PERCENTAGE = 'PERCENTAGE',
  DAYS = 'DAYS',
  EXACT = 'EXACT'
}

export interface ValidationRule {
  id: string;
  name: string;
  type: ValidationType;
  parameters: Record<string, any>;
  errorMessage: string;
  severity: 'ERROR' | 'WARNING' | 'INFO';
}

export enum ValidationType {
  REQUIRED = 'REQUIRED',
  FORMAT = 'FORMAT',
  RANGE = 'RANGE',
  CUSTOM = 'CUSTOM',
  BUSINESS_RULE = 'BUSINESS_RULE'
}

export interface HistoricalFieldData {
  averageAccuracy: number;
  commonDiscrepancies: string[];
  lastUpdated: string;
  sampleSize: number;
}

export interface EnhancedDiscrepancy extends Discrepancy {
  analysisDetails: DiscrepancyAnalysis;
  resolutionOptions: ResolutionOption[];
  similarCases?: SimilarCase[];
  businessImpact: BusinessImpact;
  escalationRequired: boolean;
}

export interface DiscrepancyAnalysis {
  rootCause?: string;
  likelihood: number; // 0-1 confidence in the analysis
  patterns: string[];
  relatedFields?: string[];
  systematicIssue: boolean;
}

export interface ResolutionOption {
  id: string;
  type: ResolutionType;
  description: string;
  action: string;
  impact: string;
  confidence: number;
  requiredApproval?: ApprovalLevel;
  estimatedTime?: number; // minutes
}

export enum ResolutionType {
  ACCEPT_BANK = 'ACCEPT_BANK',
  ACCEPT_COUNTERPARTY = 'ACCEPT_COUNTERPARTY',
  MANUAL_OVERRIDE = 'MANUAL_OVERRIDE',
  REQUEST_CLARIFICATION = 'REQUEST_CLARIFICATION',
  ESCALATE = 'ESCALATE',
  DEFER = 'DEFER'
}

export enum ApprovalLevel {
  NONE = 'NONE',
  SUPERVISOR = 'SUPERVISOR',
  MANAGER = 'MANAGER',
  SENIOR_MANAGER = 'SENIOR_MANAGER'
}

export interface SimilarCase {
  id: string;
  similarity: number;
  resolution: ResolutionType;
  outcome: string;
  date: string;
}

export interface BusinessImpact {
  financialImpact?: number;
  operationalRisk: RiskLevel;
  complianceRisk: RiskLevel;
  reputationalRisk: RiskLevel;
  description: string;
}

export interface ReconciliationAuditEntry {
  id: string;
  action: ReconciliationAction;
  performedBy: string;
  performedAt: string;
  details: string;
  fieldName?: string;
  oldValue?: any;
  newValue?: any;
  comments?: string;
  attachments?: string[];
  ipAddress?: string;
  userAgent?: string;
}

export enum ReconciliationAction {
  CREATED = 'CREATED',
  FIELD_REVIEWED = 'FIELD_REVIEWED',
  DISCREPANCY_IDENTIFIED = 'DISCREPANCY_IDENTIFIED',
  RESOLUTION_APPLIED = 'RESOLUTION_APPLIED',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  ESCALATED = 'ESCALATED',
  COMMENTS_ADDED = 'COMMENTS_ADDED',
  ATTACHMENT_ADDED = 'ATTACHMENT_ADDED',
  STATUS_CHANGED = 'STATUS_CHANGED',
  TOLERANCE_APPLIED = 'TOLERANCE_APPLIED'
}

export interface ReconciliationAttachment {
  id: string;
  filename: string;
  size: number;
  type: string;
  uploadedBy: string;
  uploadedAt: string;
  description?: string;
  category: AttachmentCategory;
  url?: string;
}

export enum AttachmentCategory {
  SUPPORTING_DOCUMENT = 'SUPPORTING_DOCUMENT',
  APPROVAL_DOCUMENT = 'APPROVAL_DOCUMENT',
  EVIDENCE = 'EVIDENCE',
  COMMUNICATION = 'COMMUNICATION',
  OTHER = 'OTHER'
}

// Workflow and process interfaces
export interface ReconciliationWorkflow {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
  triggers: WorkflowTrigger[];
  enabled: boolean;
  priority: number;
}

export interface WorkflowStep {
  id: string;
  name: string;
  description: string;
  type: StepType;
  condition?: string; // JSON logic expression
  action: StepAction;
  parameters: Record<string, any>;
  timeout?: number; // minutes
  order: number;
}

export enum StepType {
  VALIDATION = 'VALIDATION',
  APPROVAL = 'APPROVAL',
  NOTIFICATION = 'NOTIFICATION',
  ASSIGNMENT = 'ASSIGNMENT',
  ESCALATION = 'ESCALATION',
  CUSTOM = 'CUSTOM'
}

export interface StepAction {
  type: ActionType;
  parameters: Record<string, any>;
  onSuccess?: string; // Next step ID
  onFailure?: string; // Next step ID
}

export enum ActionType {
  SEND_EMAIL = 'SEND_EMAIL',
  ASSIGN_USER = 'ASSIGN_USER',
  UPDATE_STATUS = 'UPDATE_STATUS',
  CREATE_TASK = 'CREATE_TASK',
  LOG_AUDIT = 'LOG_AUDIT',
  CALL_API = 'CALL_API'
}

export interface WorkflowTrigger {
  event: TriggerEvent;
  condition?: string; // JSON logic expression
  enabled: boolean;
}

export enum TriggerEvent {
  RECONCILIATION_CREATED = 'RECONCILIATION_CREATED',
  DISCREPANCY_FOUND = 'DISCREPANCY_FOUND',
  STATUS_CHANGED = 'STATUS_CHANGED',
  APPROVAL_REQUIRED = 'APPROVAL_REQUIRED',
  TIMEOUT_EXCEEDED = 'TIMEOUT_EXCEEDED'
}

// Filtering and search
export interface ReconciliationFilter {
  status?: ReconciliationStatus[];
  riskLevel?: RiskLevel[];
  dateRange?: {
    from: string;
    to: string;
  };
  assignedTo?: string[];
  counterparty?: string[];
  currency?: string[];
  amountRange?: {
    min: number;
    max: number;
  };
  discrepancyTypes?: string[];
  fieldCategories?: FieldCategory[];
  hasUnresolvedDiscrepancies?: boolean;
  requiresApproval?: boolean;
  searchTerm?: string;
}

export interface ReconciliationSort {
  field: ReconciliationSortField;
  direction: 'ASC' | 'DESC';
}

export enum ReconciliationSortField {
  CREATED_AT = 'CREATED_AT',
  UPDATED_AT = 'UPDATED_AT',
  TRADE_DATE = 'TRADE_DATE',
  AMOUNT = 'AMOUNT',
  RISK_LEVEL = 'RISK_LEVEL',
  SCORE = 'SCORE',
  DISCREPANCY_COUNT = 'DISCREPANCY_COUNT'
}

// Analytics and reporting
export interface ReconciliationMetrics {
  period: {
    from: string;
    to: string;
  };
  summary: ReconciliationMetricsSummary;
  fieldAnalysis: FieldAnalysisMetrics;
  trendData: ReconciliationTrendData[];
  topDiscrepancies: TopDiscrepancy[];
  performance: ReconciliationPerformanceMetrics;
}

export interface ReconciliationMetricsSummary {
  totalReconciliations: number;
  matched: number;
  mismatched: number;
  resolved: number;
  pending: number;
  averageResolutionTime: number; // hours
  automationRate: number; // percentage
  accuracyRate: number; // percentage
}

export interface FieldAnalysisMetrics {
  [fieldName: string]: {
    totalComparisons: number;
    matches: number;
    mismatches: number;
    accuracy: number;
    averageResolutionTime: number;
    commonDiscrepancies: string[];
  };
}

export interface ReconciliationTrendData {
  date: string;
  totalReconciliations: number;
  matchRate: number;
  averageResolutionTime: number;
  automationRate: number;
  criticalDiscrepancies: number;
}

export interface TopDiscrepancy {
  fieldName: string;
  category: FieldCategory;
  frequency: number;
  averageImpact: number;
  commonCauses: string[];
  suggestedFixes: string[];
}

export interface ReconciliationPerformanceMetrics {
  averageProcessingTime: number; // milliseconds
  peakProcessingTime: number;
  throughput: number; // reconciliations per hour
  errorRate: number; // percentage
  systemLoad: number; // percentage
}
