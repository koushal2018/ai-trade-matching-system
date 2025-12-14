// Match review specific type definitions

import { Trade, TradeMatch, MatchStatus, FieldScoreBreakdown } from './trade.types';

export interface MatchReviewData {
  matches: TradeMatch[];
  summary: MatchingSummary;
  filters: AdvancedMatchFilter;
  pagination: MatchPagination;
}

export interface MatchingSummary {
  totalMatches: number;
  pendingReview: number;
  approved: number;
  rejected: number;
  averageScore: number;
  highConfidenceMatches: number;
  lowConfidenceMatches: number;
  lastRunTime?: string;
  processingTime?: number;
}

export interface AdvancedMatchFilter {
  status?: MatchStatus[];
  scoreRange?: {
    min: number;
    max: number;
  };
  dateRange?: {
    from: string;
    to: string;
  };
  counterparty?: string[];
  currency?: string[];
  amountRange?: {
    min: number;
    max: number;
  };
  reviewedBy?: string[];
  confidence?: ConfidenceLevel[];
  searchTerm?: string;
}

export enum ConfidenceLevel {
  HIGH = 'HIGH',     // Score >= 0.9
  MEDIUM = 'MEDIUM', // Score 0.7 - 0.89
  LOW = 'LOW'        // Score < 0.7
}

export interface MatchPagination {
  currentPage: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

export interface MatchDetail {
  match: TradeMatch;
  bankTradeDetails: TradeDetail;
  counterpartyTradeDetails: TradeDetail;
  similarityAnalysis: SimilarityAnalysis;
  fieldComparisons: DetailedFieldComparison[];
  auditTrail: MatchAuditEntry[];
  relatedMatches?: TradeMatch[];
}

export interface TradeDetail {
  trade: Trade;
  additionalFields?: Record<string, any>;
  sourceDocument?: DocumentReference;
  validationResults?: ValidationResult[];
}

export interface DocumentReference {
  id: string;
  filename: string;
  uploadedAt: string;
  size: number;
  type: string;
  url?: string;
}

export interface ValidationResult {
  field: string;
  isValid: boolean;
  message?: string;
  severity: 'ERROR' | 'WARNING' | 'INFO';
}

export interface SimilarityAnalysis {
  overallScore: number;
  fieldScores: FieldScoreBreakdown;
  algorithm: string;
  parameters: Record<string, any>;
  confidence: ConfidenceLevel;
  recommendations: string[];
}

export interface DetailedFieldComparison {
  fieldName: string;
  displayName: string;
  bankValue: any;
  counterpartyValue: any;
  score: number;
  isMatch: boolean;
  difference?: string | number;
  tolerance?: number;
  weight: number;
  explanation: string;
  impact: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface MatchAuditEntry {
  id: string;
  action: MatchAction;
  performedBy: string;
  performedAt: string;
  details: string;
  oldValue?: any;
  newValue?: any;
  comments?: string;
}

export enum MatchAction {
  CREATED = 'CREATED',
  REVIEWED = 'REVIEWED',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  COMMENTS_ADDED = 'COMMENTS_ADDED',
  ASSIGNED = 'ASSIGNED',
  UNASSIGNED = 'UNASSIGNED',
  SCORE_UPDATED = 'SCORE_UPDATED'
}

// Bulk operations
export interface BulkMatchOperation {
  type: BulkOperationType;
  matchIds: string[];
  parameters?: BulkOperationParameters;
}

export enum BulkOperationType {
  APPROVE = 'APPROVE',
  REJECT = 'REJECT',
  ASSIGN_REVIEWER = 'ASSIGN_REVIEWER',
  ADD_COMMENTS = 'ADD_COMMENTS',
  EXPORT = 'EXPORT'
}

export interface BulkOperationParameters {
  comments?: string;
  assignTo?: string;
  exportFormat?: 'CSV' | 'EXCEL' | 'PDF';
  reason?: string;
}

export interface BulkOperationResult {
  operationId: string;
  success: boolean;
  totalItems: number;
  processedItems: number;
  failedItems: number;
  results: BulkItemResult[];
  startedAt: string;
  completedAt?: string;
  errors?: string[];
}

export interface BulkItemResult {
  itemId: string;
  success: boolean;
  error?: string;
}

// Matching configuration
export interface MatchingConfig {
  algorithm: MatchingAlgorithm;
  thresholds: MatchingThresholds;
  fieldWeights: FieldWeights;
  tolerances: FieldTolerances;
  excludeFields?: string[];
  customRules?: MatchingRule[];
}

export enum MatchingAlgorithm {
  FUZZY = 'FUZZY',
  EXACT = 'EXACT',
  WEIGHTED = 'WEIGHTED',
  ML_BASED = 'ML_BASED'
}

export interface MatchingThresholds {
  autoApprove: number;    // Auto-approve above this score
  autoReject: number;     // Auto-reject below this score
  requireReview: number;  // Require manual review between auto-reject and auto-approve
}

export interface FieldWeights {
  amount: number;
  tradeDate: number;
  settleDate: number;
  counterparty: number;
  instrument: number;
  currency: number;
  [fieldName: string]: number;
}

export interface FieldTolerances {
  amount: number;         // Percentage tolerance
  tradeDate: number;      // Days tolerance
  settleDate: number;     // Days tolerance
  [fieldName: string]: number;
}

export interface MatchingRule {
  id: string;
  name: string;
  description: string;
  condition: string;      // JSON logic expression
  action: 'APPROVE' | 'REJECT' | 'FLAG' | 'ASSIGN';
  priority: number;
  enabled: boolean;
  parameters?: Record<string, any>;
}

// Statistics and metrics
export interface MatchingMetrics {
  period: {
    from: string;
    to: string;
  };
  totalTrades: number;
  matchedTrades: number;
  unmatchedTrades: number;
  matchRate: number;
  averageProcessingTime: number;
  scoreDistribution: ScoreDistribution;
  fieldAccuracy: FieldAccuracy;
  trendData: TrendDataPoint[];
}

export interface ScoreDistribution {
  high: number;    // >= 0.9
  medium: number;  // 0.7 - 0.89
  low: number;     // < 0.7
}

export interface FieldAccuracy {
  [fieldName: string]: {
    totalComparisons: number;
    matches: number;
    accuracy: number;
  };
}

export interface TrendDataPoint {
  date: string;
  matchRate: number;
  averageScore: number;
  totalMatches: number;
}

// Export interfaces
export interface MatchExportRequest {
  filters: AdvancedMatchFilter;
  format: 'CSV' | 'EXCEL' | 'PDF';
  includeFields: string[];
  includeAuditTrail?: boolean;
  includeComments?: boolean;
}

export interface MatchExportResult {
  requestId: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  downloadUrl?: string;
  filename?: string;
  size?: number;
  createdAt: string;
  expiresAt?: string;
  error?: string;
}
