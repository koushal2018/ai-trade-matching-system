# Trade Reconciliation Frontend - Component Architecture

## Overview
This document outlines the component architecture for the trade reconciliation frontend, including component hierarchy, shared libraries, state management, and routing structure.

## Architecture Principles
- **Modular Design**: Features organized in self-contained modules
- **Reusable Components**: Shared UI components across features
- **Separation of Concerns**: Clear separation between UI, business logic, and data
- **TypeScript First**: Full type safety throughout the application
- **Performance Optimized**: Code splitting and lazy loading

## Directory Structure

```
src/
├── components/
│   ├── shared/              # Shared/reusable components
│   │   ├── ui/              # Basic UI components
│   │   ├── layout/          # Layout components
│   │   ├── data/            # Data display components
│   │   └── forms/           # Form components
│   ├── features/            # Feature-specific components
│   │   ├── match-review/    # Match Review feature
│   │   ├── reconciliation/  # Reconciliation Detail feature
│   │   ├── reports/         # Reports feature
│   │   ├── admin/           # Admin Settings feature
│   │   └── agents/          # Agent Execution Monitor
│   └── pages/               # Top-level page components
├── hooks/                   # Custom React hooks
├── services/                # API and external services
├── store/                   # State management
├── types/                   # TypeScript type definitions
├── utils/                   # Utility functions
└── constants/               # Application constants
```

## Shared Components Library

### Core UI Components (`src/components/shared/ui/`)

#### Button Components
```typescript
// Button.tsx - Primary button component
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'danger' | 'ghost';
  size: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  icon?: ReactNode;
  children: ReactNode;
  onClick?: () => void;
}

// ButtonGroup.tsx - Button group container
// LoadingButton.tsx - Button with loading state
// DropdownButton.tsx - Button with dropdown menu
```

#### Form Components
```typescript
// Input.tsx - Text input with validation
interface InputProps {
  label?: string;
  error?: string;
  required?: boolean;
  disabled?: boolean;
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
}

// Select.tsx - Dropdown select
// MultiSelect.tsx - Multi-selection dropdown
// DatePicker.tsx - Date selection component
// DateRangePicker.tsx - Date range selection
// NumberInput.tsx - Numeric input with validation
// TextArea.tsx - Multi-line text input
// Checkbox.tsx - Checkbox input
// Radio.tsx - Radio button input
// Switch.tsx - Toggle switch
```

#### Display Components
```typescript
// Badge.tsx - Status badges
interface BadgeProps {
  variant: 'success' | 'warning' | 'error' | 'info' | 'neutral';
  size: 'sm' | 'md' | 'lg';
  children: ReactNode;
}

// StatusIndicator.tsx - Status with icon and color
// ProgressBar.tsx - Progress indication
// Skeleton.tsx - Loading placeholder
// Spinner.tsx - Loading spinner
// Tooltip.tsx - Hover tooltip
// Avatar.tsx - User avatar
```

### Layout Components (`src/components/shared/layout/`)

#### Layout Structure
```typescript
// MainLayout.tsx - Main application layout
interface MainLayoutProps {
  children: ReactNode;
  sidebar?: ReactNode;
  header?: ReactNode;
}

// PageLayout.tsx - Individual page layout
interface PageLayoutProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  breadcrumb?: BreadcrumbItem[];
  children: ReactNode;
}

// Card.tsx - Content card container
// Panel.tsx - Collapsible panel
// Tabs.tsx - Tab navigation
// Sidebar.tsx - Navigation sidebar
// Header.tsx - Page header
// Breadcrumb.tsx - Navigation breadcrumb
```

### Data Components (`src/components/shared/data/`)

#### Table Components
```typescript
// DataTable.tsx - Main data table component
interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  loading?: boolean;
  pagination?: PaginationConfig;
  sorting?: SortingConfig;
  filtering?: FilteringConfig;
  selection?: SelectionConfig;
  onRowClick?: (row: T) => void;
}

// Column.tsx - Table column definition
// TableHeader.tsx - Table header with sorting
// TableBody.tsx - Table body with virtualization
// TableFooter.tsx - Table footer with pagination
// TableFilters.tsx - Table filtering interface
// BulkActions.tsx - Bulk action toolbar
```

#### Chart Components
```typescript
// Chart.tsx - Base chart component
interface ChartProps {
  type: 'bar' | 'line' | 'pie' | 'doughnut';
  data: ChartData;
  options?: ChartOptions;
  loading?: boolean;
}

// BarChart.tsx - Bar chart
// LineChart.tsx - Line chart
// PieChart.tsx - Pie chart
// MetricCard.tsx - Metric display card
```

### Modal and Dialog Components (`src/components/shared/ui/`)

```typescript
// Modal.tsx - Base modal component
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  children: ReactNode;
}

// ConfirmDialog.tsx - Confirmation dialog
// FormModal.tsx - Modal with form
// DetailModal.tsx - Detail view modal
// AlertDialog.tsx - Alert/warning dialog
```

## Feature Components Architecture

### Match Review Feature (`src/components/features/match-review/`)

```typescript
// Structure
match-review/
├── MatchReview.tsx          # Main feature page
├── components/
│   ├── MatchTable.tsx       # Match listing table
│   ├── MatchFilters.tsx     # Filtering interface
│   ├── MatchDetail.tsx      # Match detail modal
│   ├── BulkActions.tsx      # Bulk operation toolbar
│   ├── MatchCard.tsx        # Individual match card
│   └── ScoreBreakdown.tsx   # Similarity score details
├── hooks/
│   ├── useMatches.tsx       # Match data management
│   ├── useMatchFilters.tsx  # Filter state management
│   └── useMatchActions.tsx  # Match actions (approve/reject)
└── types/
    └── match.types.ts       # Match-specific types
```

#### Key Components
```typescript
// MatchReview.tsx - Main page component
export const MatchReview: React.FC = () => {
  const { matches, loading, refetch } = useMatches();
  const { filters, setFilters } = useMatchFilters();
  const { approveMatch, rejectMatch } = useMatchActions();

  return (
    <PageLayout title="Match Review" actions={<RunMatchingButton />}>
      <MatchFilters filters={filters} onChange={setFilters} />
      <MatchTable
        data={matches}
        loading={loading}
        onApprove={approveMatch}
        onReject={rejectMatch}
      />
    </PageLayout>
  );
};

// MatchTable.tsx - Match data table
interface MatchTableProps {
  data: TradeMatch[];
  loading: boolean;
  onApprove: (matchId: string) => void;
  onReject: (matchId: string) => void;
}
```

### Reconciliation Detail Feature (`src/components/features/reconciliation/`)

```typescript
// Structure
reconciliation/
├── ReconciliationDetail.tsx    # Main feature page
├── components/
│   ├── ReconciliationSummary.tsx    # Summary dashboard
│   ├── FieldComparison.tsx          # Field-by-field comparison
│   ├── DiscrepancyAnalysis.tsx      # Discrepancy breakdown
│   ├── AuditTrail.tsx               # Historical timeline
│   ├── ResolutionWorkflow.tsx       # Resolution actions
│   └── FieldDifferenceCard.tsx      # Individual field diff
├── hooks/
│   ├── useReconciliation.tsx        # Reconciliation data
│   ├── useFieldComparison.tsx       # Field comparison logic
│   └── useResolution.tsx            # Resolution actions
└── types/
    └── reconciliation.types.ts      # Reconciliation types
```

### Reports Feature (`src/components/features/reports/`)

```typescript
// Structure
reports/
├── Reports.tsx               # Main feature page
├── components/
│   ├── ReportDashboard.tsx   # Reports overview
│   ├── ReportBuilder.tsx     # Custom report builder
│   ├── ReportViewer.tsx      # Report display
│   ├── ReportFilters.tsx     # Report filtering
│   ├── ExportOptions.tsx     # Export functionality
│   └── ScheduleConfig.tsx    # Scheduled reports
├── hooks/
│   ├── useReports.tsx        # Report data management
│   ├── useReportBuilder.tsx  # Report building logic
│   └── useReportExport.tsx   # Export functionality
└── types/
    └── report.types.ts       # Report-specific types
```

### Admin Settings Feature (`src/components/features/admin/`)

```typescript
// Structure
admin/
├── AdminSettings.tsx        # Main feature page
├── components/
│   ├── UserManagement.tsx   # User management tab
│   ├── SystemSettings.tsx   # System configuration
│   ├── MatchingRules.tsx    # Matching rules config
│   ├── DataSources.tsx      # Data source management
│   ├── Notifications.tsx    # Notification settings
│   └── SystemMonitor.tsx    # System health monitoring
├── hooks/
│   ├── useUsers.tsx         # User management
│   ├── useSystemConfig.tsx  # System configuration
│   └── useMatchingRules.tsx # Matching rules
└── types/
    └── admin.types.ts       # Admin-specific types
```

### Agent Execution Monitor (`src/components/features/agents/`)

```typescript
// Structure
agents/
├── AgentMonitor.tsx          # Main monitoring page
├── components/
│   ├── ExecutionDashboard.tsx    # Live execution dashboard
│   ├── ExecutionHistory.tsx      # Historical executions
│   ├── ExecutionDetail.tsx       # Detailed execution view
│   ├── ExecutionControls.tsx     # Start/stop controls
│   ├── StepTimeline.tsx          # Step-by-step timeline
│   ├── LogViewer.tsx             # Real-time log display
│   └── PerformanceCharts.tsx     # Performance analytics
├── hooks/
│   ├── useAgentExecution.tsx     # Execution state management
│   ├── useWebSocket.tsx          # Real-time communication
│   └── useExecutionHistory.tsx   # Historical data
└── types/
    └── agent.types.ts            # Agent execution types
```

## State Management Architecture

### Store Structure (`src/store/`)

```typescript
// Structure
store/
├── index.ts                 # Store configuration
├── slices/
│   ├── authSlice.ts         # Authentication state
│   ├── uiSlice.ts           # UI state (modals, loading)
│   ├── matchSlice.ts        # Match review state
│   ├── reconciliationSlice.ts # Reconciliation state
│   ├── reportSlice.ts       # Reports state
│   ├── adminSlice.ts        # Admin settings state
│   └── agentSlice.ts        # Agent execution state
└── middleware/
    ├── apiMiddleware.ts     # API call middleware
    └── websocketMiddleware.ts # WebSocket middleware
```

### React Query Integration

```typescript
// hooks/api/
├── useMatches.ts           # Match data queries
├── useReconciliation.ts    # Reconciliation queries
├── useReports.ts           # Report queries
├── useUsers.ts             # User management queries
└── useAgentExecution.ts    # Agent execution queries

// Query client configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 3,
      refetchOnWindowFocus: false,
    },
  },
});
```

### WebSocket Integration

```typescript
// services/websocket.ts
export class WebSocketService {
  private socket: WebSocket | null = null;
  private subscribers: Map<string, Set<Function>> = new Map();

  connect(url: string): void;
  disconnect(): void;
  subscribe(event: string, callback: Function): () => void;
  send(event: string, data: any): void;
}

// hooks/useWebSocket.ts
export const useWebSocket = (url: string) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  
  return { isConnected, lastMessage, sendMessage };
};
```

## Routing Architecture

### Route Structure (`src/App.tsx`)

```typescript
// Main routing configuration
const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { path: '/', element: <Dashboard /> },
      { path: '/dashboard', element: <Dashboard /> },
      { path: '/upload', element: <DocumentUpload /> },
      { path: '/trades', element: <Trades /> },
      {
        path: '/matches',
        element: <MatchReview />,
        children: [
          { path: ':matchId', element: <MatchDetail /> }
        ]
      },
      {
        path: '/reconciliation',
        element: <ReconciliationDetail />,
        children: [
          { path: ':reconciliationId', element: <ReconciliationView /> }
        ]
      },
      {
        path: '/reports',
        element: <Reports />,
        children: [
          { path: 'builder', element: <ReportBuilder /> },
          { path: ':reportId', element: <ReportViewer /> }
        ]
      },
      {
        path: '/admin',
        element: <AdminSettings />,
        children: [
          { path: 'users', element: <UserManagement /> },
          { path: 'system', element: <SystemSettings /> },
          { path: 'matching', element: <MatchingRules /> }
        ]
      },
      {
        path: '/agents',
        element: <AgentMonitor />,
        children: [
          { path: 'monitor/:executionId', element: <ExecutionMonitor /> },
          { path: 'history', element: <ExecutionHistory /> },
          { path: 'history/:executionId', element: <ExecutionDetail /> }
        ]
      }
    ]
  }
]);
```

### Route Guards and Protection

```typescript
// components/auth/ProtectedRoute.tsx
interface ProtectedRouteProps {
  children: ReactNode;
  requiredPermission?: string;
  fallback?: ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredPermission,
  fallback = <Navigate to="/login" />
}) => {
  const { user, hasPermission } = useAuth();
  
  if (!user) return fallback;
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return <div>Access Denied</div>;
  }
  
  return <>{children}</>;
};
```

## Performance Optimization

### Code Splitting

```typescript
// Lazy loading of feature components
const MatchReview = lazy(() => import('./components/features/match-review/MatchReview'));
const ReconciliationDetail = lazy(() => import('./components/features/reconciliation/ReconciliationDetail'));
const Reports = lazy(() => import('./components/features/reports/Reports'));
const AdminSettings = lazy(() => import('./components/features/admin/AdminSettings'));
const AgentMonitor = lazy(() => import('./components/features/agents/AgentMonitor'));

// Route-based code splitting
{
  path: '/matches',
  element: (
    <Suspense fallback={<PageSkeleton />}>
      <MatchReview />
    </Suspense>
  )
}
```

### Virtualization

```typescript
// For large data tables
import { FixedSizeList as List } from 'react-window';

const VirtualizedTable: React.FC<VirtualizedTableProps> = ({ data }) => {
  const Row = ({ index, style }) => (
    <div style={style}>
      {/* Row content */}
    </div>
  );

  return (
    <List
      height={600}
      itemCount={data.length}
      itemSize={50}
      width="100%"
    >
      {Row}
    </List>
  );
};
```

### Memoization Strategy

```typescript
// Component memoization
export const MatchTable = React.memo<MatchTableProps>(({ data, onAction }) => {
  // Component implementation
}, (prevProps, nextProps) => {
  return (
    prevProps.data === nextProps.data &&
    prevProps.loading === nextProps.loading
  );
});

// Hook memoization
export const useMatchFilters = () => {
  const [filters, setFilters] = useState(defaultFilters);
  
  const filteredData = useMemo(() => {
    return applyFilters(data, filters);
  }, [data, filters]);
  
  return { filters, setFilters, filteredData };
};
```

## Error Handling Architecture

### Error Boundary Components

```typescript
// components/shared/ErrorBoundary.tsx
export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error boundary caught an error:', error, errorInfo);
    // Log to error reporting service
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || <ErrorFallback error={this.state.error} />;
    }

    return this.props.children;
  }
}
```

### Global Error Handling

```typescript
// hooks/useErrorHandler.ts
export const useErrorHandler = () => {
  const showError = useCallback((error: Error | string) => {
    const message = typeof error === 'string' ? error : error.message;
    toast.error(message);
    
    // Log to monitoring service
    console.error('Application error:', error);
  }, []);

  return { showError };
};
```

## Testing Architecture

### Component Testing Structure

```typescript
// __tests__/
├── components/
│   ├── shared/
│   │   ├── Button.test.tsx
│   │   ├── DataTable.test.tsx
│   │   └── Modal.test.tsx
│   └── features/
│       ├── match-review/
│       │   ├── MatchReview.test.tsx
│       │   └── MatchTable.test.tsx
│       └── reconciliation/
│           └── ReconciliationDetail.test.tsx
├── hooks/
│   ├── useMatches.test.ts
│   └── useWebSocket.test.ts
└── utils/
    └── testUtils.tsx    # Test utilities and providers
```

### Mock Data Structure

```typescript
// __mocks__/
├── data/
│   ├── matches.mock.ts      # Mock match data
│   ├── trades.mock.ts       # Mock trade data
│   └── executions.mock.ts   # Mock execution data
├── services/
│   ├── api.mock.ts          # Mock API responses
│   └── websocket.mock.ts    # Mock WebSocket service
└── handlers/
    └── msw-handlers.ts      # MSW request handlers
```

---

## Implementation Guidelines

### Component Development Standards
1. **TypeScript First**: All components must have proper TypeScript interfaces
2. **Props Interface**: Every component must define its props interface
3. **Error Handling**: Components should handle loading and error states
4. **Accessibility**: Follow WCAG 2.1 AA guidelines
5. **Performance**: Use React.memo for expensive components
6. **Testing**: Minimum 80% test coverage for shared components

### State Management Rules
1. **Local First**: Use local state when possible
2. **React Query**: Use for server state management
3. **Redux Toolkit**: Use for complex client state
4. **WebSocket**: Use custom hooks for real-time data
5. **Persistence**: Use localStorage for user preferences

### File Naming Conventions
- **Components**: PascalCase (e.g., `MatchTable.tsx`)
- **Hooks**: camelCase starting with 'use' (e.g., `useMatches.ts`)
- **Types**: PascalCase with `.types.ts` suffix
- **Utils**: camelCase with `.utils.ts` suffix
- **Constants**: UPPER_SNAKE_CASE in `.constants.ts` files

---
*Last Updated: July 18, 2025*
*Version: 1.0*
