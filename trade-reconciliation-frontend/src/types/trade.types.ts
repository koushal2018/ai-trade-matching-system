// Core trade-related type definitions
import React from 'react';

export interface Trade {
  id: string;
  tradeId: string;
  counterparty: string;
  tradeDate: string;
  settleDate: string;
  instrument: string;
  currency: string;
  amount: number;
  price?: number;
  quantity?: number;
  side: 'BUY' | 'SELL';
  status: TradeStatus;
  source: TradeSource;
  createdAt: string;
  updatedAt: string;
  metadata?: Record<string, any>;
}

export enum TradeStatus {
  PENDING = 'PENDING',
  CONFIRMED = 'CONFIRMED',
  SETTLED = 'SETTLED',
  CANCELLED = 'CANCELLED',
  FAILED = 'FAILED'
}

export enum TradeSource {
  BANK = 'BANK',
  COUNTERPARTY = 'COUNTERPARTY',
  EXTERNAL = 'EXTERNAL'
}

export interface TradeMatch {
  id: string;
  bankTrade: Trade;
  counterpartyTrade: Trade;
  matchScore: number;
  status: MatchStatus;
  fieldScores: FieldScoreBreakdown;
  reviewedBy?: string;
  reviewedAt?: string;
  comments?: string;
  createdAt: string;
  updatedAt: string;
}

export enum MatchStatus {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  UNDER_REVIEW = 'UNDER_REVIEW'
}

export interface FieldScoreBreakdown {
  overall: number;
  amount: number;
  date: number;
  counterparty: number;
  instrument: number;
  currency: number;
  [key: string]: number;
}

export interface ReconciliationResult {
  id: string;
  tradeId: string;
  bankTrade: Trade;
  counterpartyTrade: Trade;
  status: ReconciliationStatus;
  fieldComparisons: FieldComparison[];
  discrepancies: Discrepancy[];
  resolution?: ResolutionDetails;
  createdAt: string;
  updatedAt: string;
}

export enum ReconciliationStatus {
  MATCHED = 'MATCHED',
  MISMATCHED = 'MISMATCHED',
  PENDING = 'PENDING',
  RESOLVED = 'RESOLVED',
  REQUIRES_REVIEW = 'REQUIRES_REVIEW'
}

export interface FieldComparison {
  fieldName: string;
  bankValue: any;
  counterpartyValue: any;
  isMatch: boolean;
  tolerance?: number;
  difference?: number | string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
}

export interface Discrepancy {
  id: string;
  fieldName: string;
  expectedValue: any;
  actualValue: any;
  difference: number | string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  category: string;
  description: string;
  impact?: string;
  suggestion?: string;
}

export interface ResolutionDetails {
  resolvedBy: string;
  resolvedAt: string;
  resolutionType: 'APPROVED' | 'OVERRIDE' | 'EXCEPTION';
  comments: string;
  approvedBy?: string;
  supportingDocuments?: string[];
}

// Filter and search interfaces
export interface TradeFilter {
  dateRange?: {
    from: string;
    to: string;
  };
  status?: TradeStatus[];
  source?: TradeSource[];
  counterparty?: string[];
  currency?: string[];
  amountRange?: {
    min: number;
    max: number;
  };
  searchTerm?: string;
}

export interface TradeMatchFilter {
  status?: MatchStatus[];
  scoreThreshold?: {
    min: number;
    max: number;
  };
  dateRange?: {
    from: string;
    to: string;
  };
  reviewedBy?: string[];
  counterparty?: string[];
  searchTerm?: string;
}

// Bulk operation interfaces
export interface BulkMatchAction {
  type: 'APPROVE' | 'REJECT' | 'ASSIGN_REVIEWER';
  matchIds: string[];
  comments?: string;
  assignTo?: string;
}

export interface BulkActionResult {
  success: boolean;
  processedCount: number;
  failedCount: number;
  errors?: string[];
}

// Pagination and sorting
export interface PaginationParams {
  page: number;
  limit: number;
  total?: number;
}

export interface SortingParams {
  field: string;
  direction: 'ASC' | 'DESC';
}

export interface TableColumn<T = any> {
  key: keyof T;
  label: string;
  sortable?: boolean;
  filterable?: boolean;
  width?: string;
  render?: (value: any, row: T) => React.ReactNode;
}
