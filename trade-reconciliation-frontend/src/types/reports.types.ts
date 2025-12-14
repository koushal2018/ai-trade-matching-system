// Reports and analytics type definitions

export interface ReportDefinition {
  id: string;
  name: string;
  description: string;
  type: ReportType;
  category: ReportCategory;
  template: ReportTemplate;
  schedule?: ReportSchedule;
  parameters: ReportParameter[];
  filters: ReportFilter[];
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  isPublic: boolean;
  tags: string[];
}

export enum ReportType {
  RECONCILIATION_SUMMARY = 'RECONCILIATION_SUMMARY',
  MATCH_ANALYSIS = 'MATCH_ANALYSIS',
  DISCREPANCY_ANALYSIS = 'DISCREPANCY_ANALYSIS',
  PERFORMANCE_METRICS = 'PERFORMANCE_METRICS',
  AUDIT_TRAIL = 'AUDIT_TRAIL',
  CUSTOM = 'CUSTOM'
}

export enum ReportCategory {
  OPERATIONAL = 'OPERATIONAL',
  COMPLIANCE = 'COMPLIANCE',
  ANALYTICS = 'ANALYTICS',
  MANAGEMENT = 'MANAGEMENT',
  TECHNICAL = 'TECHNICAL'
}

export interface ReportTemplate {
  id: string;
  name: string;
  layout: ReportLayout;
  sections: ReportSection[];
  styling: ReportStyling;
  format: ReportFormat;
}

export enum ReportLayout {
  SINGLE_PAGE = 'SINGLE_PAGE',
  MULTI_PAGE = 'MULTI_PAGE',
  DASHBOARD = 'DASHBOARD',
  TABBED = 'TABBED'
}

export interface ReportSection {
  id: string;
  name: string;
  type: SectionType;
  order: number;
  configuration: SectionConfiguration;
  dataSource: DataSourceConfig;
  visualization?: VisualizationConfig;
}

export enum SectionType {
  HEADER = 'HEADER',
  SUMMARY = 'SUMMARY',
  TABLE = 'TABLE',
  CHART = 'CHART',
  METRICS = 'METRICS',
  TEXT = 'TEXT',
  IMAGE = 'IMAGE',
  FOOTER = 'FOOTER'
}

export interface SectionConfiguration {
  title?: string;
  description?: string;
  showBorder?: boolean;
  backgroundColor?: string;
  height?: number;
  width?: number;
  padding?: number;
  margin?: number;
}

export interface DataSourceConfig {
  type: DataSourceType;
  endpoint?: string;
  query?: string;
  parameters?: Record<string, any>;
  aggregation?: AggregationConfig;
  sorting?: SortConfig[];
  filtering?: FilterConfig[];
}

export enum DataSourceType {
  API = 'API',
  DATABASE = 'DATABASE',
  STATIC = 'STATIC',
  CALCULATED = 'CALCULATED'
}

export interface AggregationConfig {
  groupBy: string[];
  aggregations: AggregationFunction[];
}

export interface AggregationFunction {
  field: string;
  function: 'SUM' | 'COUNT' | 'AVG' | 'MIN' | 'MAX' | 'DISTINCT';
  alias?: string;
}

export interface SortConfig {
  field: string;
  direction: 'ASC' | 'DESC';
}

export interface FilterConfig {
  field: string;
  operator: FilterOperator;
  value: any;
  condition?: 'AND' | 'OR';
}

export enum FilterOperator {
  EQUALS = 'EQUALS',
  NOT_EQUALS = 'NOT_EQUALS',
  GREATER_THAN = 'GREATER_THAN',
  LESS_THAN = 'LESS_THAN',
  CONTAINS = 'CONTAINS',
  IN = 'IN',
  BETWEEN = 'BETWEEN'
}

export interface VisualizationConfig {
  type: ChartType;
  options: ChartOptions;
  data: ChartDataConfig;
}

export enum ChartType {
  BAR = 'BAR',
  LINE = 'LINE',
  PIE = 'PIE',
  DOUGHNUT = 'DOUGHNUT',
  AREA = 'AREA',
  SCATTER = 'SCATTER',
  HEATMAP = 'HEATMAP',
  GAUGE = 'GAUGE',
  TABLE = 'TABLE'
}

export interface ChartOptions {
  title?: string;
  legend?: LegendConfig;
  axes?: AxesConfig;
  colors?: string[];
  responsive?: boolean;
  animation?: AnimationConfig;
}

export interface LegendConfig {
  show: boolean;
  position: 'top' | 'bottom' | 'left' | 'right';
  align: 'start' | 'center' | 'end';
}

export interface AxesConfig {
  x?: AxisConfig;
  y?: AxisConfig;
}

export interface AxisConfig {
  label?: string;
  min?: number;
  max?: number;
  format?: string;
  showGridLines?: boolean;
}

export interface AnimationConfig {
  enabled: boolean;
  duration: number;
  easing: string;
}

export interface ChartDataConfig {
  xAxis: string;
  yAxis: string[];
  series?: SeriesConfig[];
}

export interface SeriesConfig {
  name: string;
  field: string;
  type?: ChartType;
  color?: string;
}

export interface ReportStyling {
  theme: 'light' | 'dark' | 'custom';
  primaryColor?: string;
  secondaryColor?: string;
  fontFamily?: string;
  fontSize?: number;
  headerStyle?: StyleConfig;
  bodyStyle?: StyleConfig;
}

export interface StyleConfig {
  backgroundColor?: string;
  textColor?: string;
  borderColor?: string;
  borderWidth?: number;
  borderRadius?: number;
}

export enum ReportFormat {
  PDF = 'PDF',
  EXCEL = 'EXCEL',
  CSV = 'CSV',
  HTML = 'HTML',
  JSON = 'JSON'
}

export interface ReportSchedule {
  id: string;
  frequency: ScheduleFrequency;
  cronExpression?: string;
  timezone: string;
  startDate: string;
  endDate?: string;
  enabled: boolean;
  recipients: ReportRecipient[];
  deliveryMethod: DeliveryMethod;
}

export enum ScheduleFrequency {
  ONCE = 'ONCE',
  DAILY = 'DAILY',
  WEEKLY = 'WEEKLY',
  MONTHLY = 'MONTHLY',
  QUARTERLY = 'QUARTERLY',
  YEARLY = 'YEARLY',
  CUSTOM = 'CUSTOM'
}

export interface ReportRecipient {
  type: RecipientType;
  address: string;
  name?: string;
}

export enum RecipientType {
  EMAIL = 'EMAIL',
  SLACK = 'SLACK',
  WEBHOOK = 'WEBHOOK'
}

export enum DeliveryMethod {
  EMAIL_ATTACHMENT = 'EMAIL_ATTACHMENT',
  EMAIL_LINK = 'EMAIL_LINK',
  SLACK_MESSAGE = 'SLACK_MESSAGE',
  WEBHOOK_POST = 'WEBHOOK_POST',
  FILE_SYSTEM = 'FILE_SYSTEM'
}

export interface ReportParameter {
  name: string;
  type: ParameterType;
  description: string;
  required: boolean;
  defaultValue?: any;
  options?: ParameterOption[];
  validation?: ParameterValidation;
}

export enum ParameterType {
  STRING = 'STRING',
  NUMBER = 'NUMBER',
  DATE = 'DATE',
  DATE_RANGE = 'DATE_RANGE',
  BOOLEAN = 'BOOLEAN',
  SELECT = 'SELECT',
  MULTI_SELECT = 'MULTI_SELECT'
}

export interface ParameterOption {
  label: string;
  value: any;
}

export interface ParameterValidation {
  min?: number;
  max?: number;
  pattern?: string;
  required?: boolean;
}

export interface ReportFilter {
  field: string;
  operator: FilterOperator;
  value: any;
  description?: string;
  userConfigurable: boolean;
}

// Report execution types
export interface ReportExecution {
  id: string;
  reportId: string;
  status: ExecutionStatus;
  startedAt: string;
  completedAt?: string;
  duration?: number;
  parameters: Record<string, any>;
  results?: ReportResults;
  error?: ExecutionError;
  triggeredBy: string;
  executionType: ExecutionType;
}

export enum ExecutionStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED'
}

export enum ExecutionType {
  MANUAL = 'MANUAL',
  SCHEDULED = 'SCHEDULED',
  API = 'API'
}

export interface ReportResults {
  data: any[];
  summary: ResultSummary;
  files: GeneratedFile[];
  metadata: ResultsMetadata;
}

export interface ResultSummary {
  totalRecords: number;
  processingTime: number;
  dataFreshness: string;
  warnings?: string[];
  notes?: string[];
}

export interface GeneratedFile {
  id: string;
  filename: string;
  format: ReportFormat;
  size: number;
  url?: string;
  expiresAt?: string;
}

export interface ResultsMetadata {
  generatedAt: string;
  version: string;
  filters: Record<string, any>;
  aggregations: Record<string, any>;
}

export interface ExecutionError {
  code: string;
  message: string;
  details: string;
  step?: string;
  retryable: boolean;
}

// Analytics and metrics types
export interface ReportMetrics {
  reportId: string;
  period: MetricsPeriod;
  executionCount: number;
  averageExecutionTime: number;
  successRate: number;
  popularityScore: number;
  userCount: number;
  lastExecuted?: string;
  trends: MetricsTrend[];
}

export interface MetricsPeriod {
  from: string;
  to: string;
  granularity: 'HOUR' | 'DAY' | 'WEEK' | 'MONTH';
}

export interface MetricsTrend {
  timestamp: string;
  executions: number;
  averageTime: number;
  success: number;
  failure: number;
}

// Dashboard types
export interface Dashboard {
  id: string;
  name: string;
  description: string;
  layout: DashboardLayout;
  widgets: DashboardWidget[];
  filters: DashboardFilter[];
  refreshInterval?: number;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  isPublic: boolean;
  tags: string[];
}

export interface DashboardLayout {
  type: 'GRID' | 'FLEXIBLE';
  columns: number;
  rowHeight: number;
  margin: number;
  padding: number;
}

export interface DashboardWidget {
  id: string;
  type: WidgetType;
  title: string;
  position: WidgetPosition;
  configuration: WidgetConfiguration;
  dataSource: DataSourceConfig;
  refreshInterval?: number;
}

export enum WidgetType {
  METRIC = 'METRIC',
  CHART = 'CHART',
  TABLE = 'TABLE',
  TEXT = 'TEXT',
  GAUGE = 'GAUGE',
  PROGRESS = 'PROGRESS',
  LIST = 'LIST'
}

export interface WidgetPosition {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface WidgetConfiguration {
  visualization?: VisualizationConfig;
  formatting?: FormattingConfig;
  interactions?: InteractionConfig;
}

export interface FormattingConfig {
  numberFormat?: string;
  dateFormat?: string;
  currencySymbol?: string;
  precision?: number;
}

export interface InteractionConfig {
  clickAction?: ClickAction;
  hoverAction?: HoverAction;
  drillDown?: DrillDownConfig;
}

export interface ClickAction {
  type: 'NAVIGATE' | 'FILTER' | 'MODAL' | 'NONE';
  target?: string;
  parameters?: Record<string, any>;
}

export interface HoverAction {
  showTooltip: boolean;
  tooltipFields?: string[];
}

export interface DrillDownConfig {
  enabled: boolean;
  levels: DrillDownLevel[];
}

export interface DrillDownLevel {
  field: string;
  label: string;
  filters?: FilterConfig[];
}

export interface DashboardFilter {
  id: string;
  name: string;
  type: FilterType;
  field: string;
  defaultValue?: any;
  options?: FilterOption[];
  appliesTo?: string[]; // Widget IDs
}

export enum FilterType {
  TEXT = 'TEXT',
  DATE = 'DATE',
  DATE_RANGE = 'DATE_RANGE',
  NUMBER = 'NUMBER',
  SELECT = 'SELECT',
  MULTI_SELECT = 'MULTI_SELECT',
  BOOLEAN = 'BOOLEAN'
}

export interface FilterOption {
  label: string;
  value: any;
  count?: number;
}

// Export and sharing types
export interface ExportRequest {
  type: ExportType;
  format: ReportFormat;
  filters?: Record<string, any>;
  options?: ExportOptions;
}

export enum ExportType {
  REPORT = 'REPORT',
  DASHBOARD = 'DASHBOARD',
  WIDGET = 'WIDGET',
  DATA = 'DATA'
}

export interface ExportOptions {
  includeFilters?: boolean;
  includeMetadata?: boolean;
  template?: string;
  compression?: boolean;
  password?: string;
}

export interface ShareRequest {
  resourceId: string;
  resourceType: 'REPORT' | 'DASHBOARD';
  recipients: string[];
  permissions: SharePermission[];
  message?: string;
  expiresAt?: string;
}

export enum SharePermission {
  VIEW = 'VIEW',
  EDIT = 'EDIT',
  SHARE = 'SHARE',
  DELETE = 'DELETE'
}

export interface ShareResponse {
  shareId: string;
  shareUrl?: string;
  expiresAt?: string;
  recipients: ShareRecipient[];
}

export interface ShareRecipient {
  email: string;
  permissions: SharePermission[];
  status: 'PENDING' | 'ACCEPTED' | 'REJECTED';
  invitedAt: string;
  acceptedAt?: string;
}
