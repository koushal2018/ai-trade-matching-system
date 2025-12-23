---
inclusion: fileMatch
fileMatchPattern: ['**/*.ts', '**/*.tsx', '**/web-portal/**/*']
---

# Frontend Development Standards (CloudScape Edition)

## Technology Stack
- **React 18** with **TypeScript** (strict mode)
- **CloudScape Design System** for UI components (`@cloudscape-design/components`)
- **TanStack Query (React Query)** for server state management
- **Vite** for build tooling and dev server
- **CloudScape Charts** for data visualization (`@cloudscape-design/components` includes AreaChart, BarChart, LineChart, PieChart)

## Package Dependencies
```json
{
  "dependencies": {
    "@cloudscape-design/components": "^3.0",
    "@cloudscape-design/global-styles": "^1.0",
    "@cloudscape-design/design-tokens": "^3.0",
    "@cloudscape-design/collection-hooks": "^1.0",
    "@tanstack/react-query": "^5.0",
    "react": "^18.2",
    "react-dom": "^18.2"
  }
}
```

## Project Structure
```
web-portal/src/
├── components/
│   ├── common/           # Shared UI components (TradeTable, LiveIndicator, StatusBadge)
│   ├── dashboard/        # Dashboard-specific components (ServiceOverview, MetricsPanel)
│   ├── hitl/             # Human-in-the-loop components (ReviewPanel, ApprovalWorkflow)
│   └── layout/           # App shell components (Navigation, TopNav, Breadcrumbs)
├── pages/                # Route-level page components (Dashboard, HITLPanel, AuditTrail)
├── hooks/                # Custom React hooks (useNotifications, useTrades, useWebSocket)
├── services/             # API clients and WebSocket connections
├── types/                # Shared TypeScript type definitions
├── i18n/                 # Internationalization strings (CloudScape supports i18n)
└── config/
    └── navigation.ts     # Side navigation configuration
```

## TypeScript Standards
- **Always use explicit types** for props, state, API responses, and function returns
- **Never use `any`** - use `unknown` with type guards or proper typing
- **Define interfaces** for all component props and data models
- **Use union types** for enums: `'BANK' | 'COUNTERPARTY'` instead of strings
- **Export types** from `types/index.ts` for reuse across components
- **Import CloudScape types** from component packages for prop typing

```typescript
// types/trade.ts
export type SourceType = 'BANK' | 'COUNTERPARTY';
export type TradeStatus = 'MATCHED' | 'PROBABLE_MATCH' | 'REVIEW_REQUIRED' | 'BREAK';
export type StatusIndicatorType = 'success' | 'warning' | 'error' | 'info' | 'pending' | 'in-progress' | 'stopped';

export interface Trade {
  tradeId: string;
  sourceType: SourceType;
  status: TradeStatus;
  notional: number;
  currency: string;
  counterparty: string;
  tradeDate: string;
  maturityDate: string;
  matchScore?: number;
  extractedFields: Record<string, string | number>;
}

export interface TradeMatch {
  bankTrade: Trade;
  counterpartyTrade: Trade;
  matchScore: number;
  discrepancies: Discrepancy[];
}

export interface Discrepancy {
  field: string;
  bankValue: string | number;
  counterpartyValue: string | number;
  severity: 'critical' | 'warning' | 'info';
}
```

## Application Shell Setup

### Root Application with CloudScape
```typescript
// App.tsx
import { FC, useState } from 'react';
import { AppLayout, TopNavigation, SideNavigation, Flashbar } from '@cloudscape-design/components';
import '@cloudscape-design/global-styles/index.css';
import { useNotifications } from './hooks/useNotifications';
import { navigationItems } from './config/navigation';

export const App: FC = () => {
  const [navigationOpen, setNavigationOpen] = useState(true);
  const { notifications, dismissNotification } = useNotifications();

  return (
    <>
      <TopNavigation
        identity={{
          title: 'OTC Trade Matching System',
          href: '/',
          logo: { src: '/logo.svg', alt: 'OTC Trade Matching' }
        }}
        utilities={[
          {
            type: 'button',
            iconName: 'notification',
            ariaLabel: 'Notifications',
            badge: true,
            disableUtilityCollapse: false
          },
          {
            type: 'menu-dropdown',
            text: 'Settings',
            iconName: 'settings',
            items: [
              { id: 'preferences', text: 'Preferences' },
              { id: 'security', text: 'Security' }
            ]
          },
          {
            type: 'menu-dropdown',
            text: 'User',
            description: 'user@example.com',
            iconName: 'user-profile',
            items: [
              { id: 'profile', text: 'Profile' },
              { id: 'signout', text: 'Sign out' }
            ]
          }
        ]}
      />
      <AppLayout
        navigation={
          <SideNavigation
            header={{ text: 'Trade Operations', href: '/' }}
            items={navigationItems}
          />
        }
        navigationOpen={navigationOpen}
        onNavigationChange={({ detail }) => setNavigationOpen(detail.open)}
        notifications={
          <Flashbar
            items={notifications}
            onDismiss={({ detail }) => dismissNotification(detail.itemId)}
          />
        }
        content={<RouterOutlet />}
        toolsHide
      />
    </>
  );
};
```

### Navigation Configuration
```typescript
// config/navigation.ts
import { SideNavigationProps } from '@cloudscape-design/components';

export const navigationItems: SideNavigationProps.Item[] = [
  {
    type: 'section',
    text: 'Dashboard',
    items: [
      { type: 'link', text: 'Overview', href: '/' },
      { type: 'link', text: 'Real-time Monitor', href: '/monitor' }
    ]
  },
  {
    type: 'section',
    text: 'Trade Processing',
    items: [
      { type: 'link', text: 'Upload Confirmations', href: '/upload' },
      { type: 'link', text: 'Matching Queue', href: '/queue' },
      { type: 'link', text: 'Exceptions', href: '/exceptions' }
    ]
  },
  {
    type: 'section',
    text: 'Review',
    items: [
      { type: 'link', text: 'HITL Panel', href: '/hitl' },
      { type: 'link', text: 'Audit Trail', href: '/audit' }
    ]
  },
  { type: 'divider' },
  {
    type: 'link',
    text: 'Documentation',
    href: '/docs',
    external: true,
    externalIconAriaLabel: 'Opens in new tab'
  }
];
```

## Component Patterns

### Functional Components with CloudScape
```typescript
// components/common/TradeCard.tsx
import { FC } from 'react';
import { Container, Header, SpaceBetween, Box, StatusIndicator, Badge, KeyValuePairs } from '@cloudscape-design/components';
import { Trade, TradeStatus, StatusIndicatorType } from '../../types';

interface TradeCardProps {
  trade: Trade;
  onSelect?: (tradeId: string) => void;
  selected?: boolean;
}

const STATUS_MAP: Record<TradeStatus, { type: StatusIndicatorType; label: string }> = {
  MATCHED: { type: 'success', label: 'Matched' },
  PROBABLE_MATCH: { type: 'warning', label: 'Probable Match' },
  REVIEW_REQUIRED: { type: 'pending', label: 'Review Required' },
  BREAK: { type: 'error', label: 'Break' }
};

export const TradeCard: FC<TradeCardProps> = ({ trade, onSelect, selected = false }) => {
  const statusConfig = STATUS_MAP[trade.status];

  return (
    <Container
      header={
        <Header
          variant="h3"
          actions={
            trade.matchScore !== undefined && (
              <Badge color={trade.matchScore >= 85 ? 'green' : trade.matchScore >= 70 ? 'blue' : 'red'}>
                {trade.matchScore}% Match
              </Badge>
            )
          }
        >
          {trade.tradeId}
        </Header>
      }
      footer={
        <Box textAlign="right">
          <StatusIndicator type={statusConfig.type}>{statusConfig.label}</StatusIndicator>
        </Box>
      }
    >
      <SpaceBetween size="s">
        <KeyValuePairs
          columns={2}
          items={[
            { label: 'Source', value: trade.sourceType },
            { label: 'Counterparty', value: trade.counterparty },
            { label: 'Notional', value: `${trade.currency} ${trade.notional.toLocaleString()}` },
            { label: 'Trade Date', value: trade.tradeDate }
          ]}
        />
      </SpaceBetween>
    </Container>
  );
};
```

### Key Component Conventions
- Use **named exports** for components (not default exports)
- Place interfaces **above** the component definition
- Use **optional chaining** (`?.`) for optional callbacks
- Use **CloudScape spacing tokens** via `SpaceBetween` component (not inline styles)
- Apply **Container** for card-like layouts with headers
- Use **StatusIndicator** for all status displays

## CloudScape Component Mapping Reference

| Use Case | CloudScape Component | Notes |
|----------|---------------------|-------|
| Page sections | `Container` | Always with `Header` |
| Vertical spacing | `SpaceBetween` | Use `size` prop: 'xxxs', 'xxs', 'xs', 's', 'm', 'l', 'xl', 'xxl' |
| Horizontal layout | `ColumnLayout` | Use `columns` prop for responsive grids |
| Data tables | `Table` | Built-in sorting, filtering, pagination |
| Forms | `Form`, `FormField` | With validation support |
| Multi-step flows | `Wizard` | For upload and review workflows |
| Status display | `StatusIndicator` | success, warning, error, info, pending, in-progress, stopped |
| Notifications | `Flashbar` | Place in AppLayout `notifications` slot |
| Modals | `Modal` | For confirmations and detail views |
| Side details | `SplitPanel` | For master-detail patterns |
| File upload | `FileUpload` | Built-in drag-drop support |
| Key-value display | `KeyValuePairs` | For trade details |
| Filtering | `PropertyFilter` | Advanced filtering for tables |
| Charts | `AreaChart`, `LineChart`, `BarChart`, `PieChart` | Built-in responsive charts |

## Data Tables with CloudScape

### Trade Table Implementation
```typescript
// components/common/TradeTable.tsx
import { FC, useState } from 'react';
import {
  Table,
  Header,
  Pagination,
  PropertyFilter,
  SpaceBetween,
  Button,
  StatusIndicator,
  Badge,
  CollectionPreferences,
  Box
} from '@cloudscape-design/components';
import { useCollection } from '@cloudscape-design/collection-hooks';
import { Trade, TradeStatus, StatusIndicatorType } from '../../types';

interface TradeTableProps {
  trades: Trade[];
  loading?: boolean;
  onTradeSelect?: (trade: Trade) => void;
  onRefresh?: () => void;
}

const STATUS_MAP: Record<TradeStatus, { type: StatusIndicatorType; label: string }> = {
  MATCHED: { type: 'success', label: 'Matched' },
  PROBABLE_MATCH: { type: 'warning', label: 'Probable Match' },
  REVIEW_REQUIRED: { type: 'pending', label: 'Review Required' },
  BREAK: { type: 'error', label: 'Break' }
};

const COLUMN_DEFINITIONS = [
  {
    id: 'tradeId',
    header: 'Trade ID',
    cell: (item: Trade) => item.tradeId,
    sortingField: 'tradeId',
    isRowHeader: true
  },
  {
    id: 'sourceType',
    header: 'Source',
    cell: (item: Trade) => (
      <Badge color={item.sourceType === 'BANK' ? 'blue' : 'grey'}>
        {item.sourceType}
      </Badge>
    ),
    sortingField: 'sourceType'
  },
  {
    id: 'counterparty',
    header: 'Counterparty',
    cell: (item: Trade) => item.counterparty,
    sortingField: 'counterparty'
  },
  {
    id: 'notional',
    header: 'Notional',
    cell: (item: Trade) => `${item.currency} ${item.notional.toLocaleString()}`,
    sortingField: 'notional'
  },
  {
    id: 'tradeDate',
    header: 'Trade Date',
    cell: (item: Trade) => item.tradeDate,
    sortingField: 'tradeDate'
  },
  {
    id: 'matchScore',
    header: 'Match Score',
    cell: (item: Trade) => (
      item.matchScore !== undefined ? (
        <Badge color={item.matchScore >= 85 ? 'green' : item.matchScore >= 70 ? 'blue' : 'red'}>
          {item.matchScore}%
        </Badge>
      ) : (
        <Box color="text-status-inactive">—</Box>
      )
    ),
    sortingField: 'matchScore'
  },
  {
    id: 'status',
    header: 'Status',
    cell: (item: Trade) => {
      const config = STATUS_MAP[item.status];
      return <StatusIndicator type={config.type}>{config.label}</StatusIndicator>;
    },
    sortingField: 'status'
  }
];

const FILTERING_PROPERTIES = [
  {
    key: 'tradeId',
    propertyLabel: 'Trade ID',
    groupValuesLabel: 'Trade ID values',
    operators: [':', '!:', '=', '!='] as const
  },
  {
    key: 'sourceType',
    propertyLabel: 'Source',
    groupValuesLabel: 'Source values',
    operators: [':', '!:', '=', '!='] as const
  },
  {
    key: 'status',
    propertyLabel: 'Status',
    groupValuesLabel: 'Status values',
    operators: ['=', '!='] as const
  },
  {
    key: 'counterparty',
    propertyLabel: 'Counterparty',
    groupValuesLabel: 'Counterparty values',
    operators: [':', '!:', '=', '!='] as const
  }
];

export const TradeTable: FC<TradeTableProps> = ({
  trades,
  loading = false,
  onTradeSelect,
  onRefresh
}) => {
  const [preferences, setPreferences] = useState({
    pageSize: 20,
    visibleContent: ['tradeId', 'sourceType', 'counterparty', 'notional', 'tradeDate', 'matchScore', 'status']
  });

  const { items, filteredItemsCount, collectionProps, filterProps, paginationProps } = useCollection(
    trades,
    {
      propertyFiltering: {
        filteringProperties: FILTERING_PROPERTIES,
        empty: <EmptyState />,
        noMatch: <NoMatchState onClearFilter={() => filterProps.onChange({ detail: { tokens: [], operation: 'and' } })} />
      },
      pagination: { pageSize: preferences.pageSize },
      sorting: { defaultState: { sortingColumn: COLUMN_DEFINITIONS[0] } },
      selection: {}
    }
  );

  return (
    <Table
      {...collectionProps}
      columnDefinitions={COLUMN_DEFINITIONS}
      items={items}
      loading={loading}
      loadingText="Loading trades..."
      selectionType="single"
      onSelectionChange={({ detail }) => {
        const selectedTrade = detail.selectedItems[0];
        if (selectedTrade && onTradeSelect) {
          onTradeSelect(selectedTrade);
        }
      }}
      header={
        <Header
          counter={`(${filteredItemsCount})`}
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              <Button iconName="refresh" onClick={onRefresh}>
                Refresh
              </Button>
              <Button variant="primary">Process Selected</Button>
            </SpaceBetween>
          }
        >
          Trade Confirmations
        </Header>
      }
      filter={
        <PropertyFilter
          {...filterProps}
          i18nStrings={{
            filteringAriaLabel: 'Filter trades',
            filteringPlaceholder: 'Filter trades by property or value'
          }}
        />
      }
      pagination={<Pagination {...paginationProps} />}
      preferences={
        <CollectionPreferences
          title="Preferences"
          confirmLabel="Confirm"
          cancelLabel="Cancel"
          preferences={preferences}
          onConfirm={({ detail }) => setPreferences(detail as typeof preferences)}
          pageSizePreference={{
            title: 'Page size',
            options: [
              { value: 10, label: '10 trades' },
              { value: 20, label: '20 trades' },
              { value: 50, label: '50 trades' }
            ]
          }}
          visibleContentPreference={{
            title: 'Visible columns',
            options: [
              {
                label: 'Trade properties',
                options: COLUMN_DEFINITIONS.map(col => ({
                  id: col.id,
                  label: col.header as string
                }))
              }
            ]
          }}
        />
      }
      stickyHeader
      stripedRows
      variant="full-page"
    />
  );
};

const EmptyState: FC = () => (
  <Box textAlign="center" color="inherit">
    <SpaceBetween size="m">
      <b>No trades</b>
      <Box variant="p" color="text-body-secondary">
        No trade confirmations have been uploaded yet.
      </Box>
      <Button>Upload Confirmations</Button>
    </SpaceBetween>
  </Box>
);

interface NoMatchStateProps {
  onClearFilter: () => void;
}

const NoMatchState: FC<NoMatchStateProps> = ({ onClearFilter }) => (
  <Box textAlign="center" color="inherit">
    <SpaceBetween size="m">
      <b>No matches</b>
      <Box variant="p" color="text-body-secondary">
        No trades match the current filter criteria.
      </Box>
      <Button onClick={onClearFilter}>Clear filter</Button>
    </SpaceBetween>
  </Box>
);
```

## Data Fetching with React Query

### Custom Hooks Pattern
```typescript
// hooks/useTrades.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchTrades, updateTradeStatus, uploadConfirmation } from '../services/api';
import { Trade, SourceType, TradeStatus } from '../types';

// Query hook for fetching trades
export const useTrades = (sourceType?: SourceType) => {
  return useQuery({
    queryKey: ['trades', sourceType],
    queryFn: () => fetchTrades(sourceType),
    staleTime: 30000,
    refetchInterval: 60000
  });
};

// Query hook for single trade
export const useTrade = (tradeId: string) => {
  return useQuery({
    queryKey: ['trades', 'detail', tradeId],
    queryFn: () => fetchTradeById(tradeId),
    enabled: !!tradeId
  });
};

// Mutation hook for status updates
export const useUpdateTradeStatus = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tradeId, status }: { tradeId: string; status: TradeStatus }) =>
      updateTradeStatus(tradeId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trades'] });
    }
  });
};

// Mutation hook for file upload
export const useUploadConfirmation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => uploadConfirmation(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trades'] });
    }
  });
};
```

### Query Key Conventions
- Use **array format**: `['resource', param1, param2]`
- Include **all dependencies** that affect the query
- Keep keys **consistent** across the application
- Use `'detail'` segment for single-item queries

## API Service Layer
```typescript
// services/api.ts
import { Trade, SourceType, TradeStatus, TradeMatch } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

export const fetchTrades = async (sourceType?: SourceType): Promise<Trade[]> => {
  const url = sourceType
    ? `${API_BASE}/trades?source=${sourceType}`
    : `${API_BASE}/trades`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch trades: ${response.statusText}`);
  }
  return response.json();
};

export const fetchTradeById = async (tradeId: string): Promise<Trade> => {
  const response = await fetch(`${API_BASE}/trades/${tradeId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch trade: ${response.statusText}`);
  }
  return response.json();
};

export const updateTradeStatus = async (
  tradeId: string,
  status: TradeStatus
): Promise<Trade> => {
  const response = await fetch(`${API_BASE}/trades/${tradeId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  });
  if (!response.ok) {
    throw new Error(`Failed to update trade status: ${response.statusText}`);
  }
  return response.json();
};

export const uploadConfirmation = async (file: File): Promise<{ uploadId: string }> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData
  });
  if (!response.ok) {
    throw new Error(`Failed to upload confirmation: ${response.statusText}`);
  }
  return response.json();
};

export const fetchMatches = async (): Promise<TradeMatch[]> => {
  const response = await fetch(`${API_BASE}/matches`);
  if (!response.ok) {
    throw new Error(`Failed to fetch matches: ${response.statusText}`);
  }
  return response.json();
};
```

## WebSocket Integration
```typescript
// services/websocket.ts
import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';

interface WebSocketMessage {
  type: 'TRADE_UPDATE' | 'MATCH_COMPLETE' | 'EXCEPTION_RAISED' | 'AGENT_STATUS';
  payload: unknown;
}

export const useTradeWebSocket = () => {
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8080/ws';
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
    };

    wsRef.current.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);

      switch (message.type) {
        case 'TRADE_UPDATE':
          queryClient.invalidateQueries({ queryKey: ['trades'] });
          break;
        case 'MATCH_COMPLETE':
          queryClient.invalidateQueries({ queryKey: ['trades'] });
          queryClient.invalidateQueries({ queryKey: ['matches'] });
          break;
        case 'EXCEPTION_RAISED':
          queryClient.invalidateQueries({ queryKey: ['exceptions'] });
          break;
        case 'AGENT_STATUS':
          queryClient.invalidateQueries({ queryKey: ['agents'] });
          break;
      }
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected, reconnecting...');
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }, [queryClient]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, [connect]);

  return wsRef;
};
```

## Notifications System with Flashbar
```typescript
// hooks/useNotifications.ts
import { useState, useCallback } from 'react';
import { FlashbarProps } from '@cloudscape-design/components';

type NotificationType = 'success' | 'error' | 'warning' | 'info' | 'in-progress';

interface AddNotificationParams {
  type: NotificationType;
  header: string;
  content?: string;
  dismissible?: boolean;
  dismissLabel?: string;
  action?: FlashbarProps.MessageDefinition['action'];
}

export const useNotifications = () => {
  const [notifications, setNotifications] = useState<FlashbarProps.MessageDefinition[]>([]);

  const addNotification = useCallback(({
    type,
    header,
    content,
    dismissible = true,
    dismissLabel = 'Dismiss',
    action
  }: AddNotificationParams) => {
    const id = `notification-${Date.now()}`;

    setNotifications(prev => [
      ...prev,
      {
        id,
        type,
        header,
        content,
        dismissible,
        dismissLabel,
        action,
        onDismiss: () => dismissNotification(id)
      }
    ]);

    // Auto-dismiss success notifications after 5 seconds
    if (type === 'success') {
      setTimeout(() => dismissNotification(id), 5000);
    }

    return id;
  }, []);

  const dismissNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  return {
    notifications,
    addNotification,
    dismissNotification,
    clearAllNotifications
  };
};
```

## File Upload Component
```typescript
// components/common/ConfirmationUpload.tsx
import { FC, useState } from 'react';
import {
  Container,
  Header,
  FileUpload,
  SpaceBetween,
  Button,
  ColumnLayout,
  Alert,
  ProgressBar
} from '@cloudscape-design/components';
import { useUploadConfirmation } from '../../hooks/useTrades';

interface ConfirmationUploadProps {
  onUploadComplete?: () => void;
}

export const ConfirmationUpload: FC<ConfirmationUploadProps> = ({ onUploadComplete }) => {
  const [bankFiles, setBankFiles] = useState<File[]>([]);
  const [counterpartyFiles, setCounterpartyFiles] = useState<File[]>([]);
  const { mutate: upload, isPending, isError, error } = useUploadConfirmation();

  const handleUpload = () => {
    const allFiles = [...bankFiles, ...counterpartyFiles];
    allFiles.forEach(file => {
      upload(file, {
        onSuccess: () => {
          setBankFiles([]);
          setCounterpartyFiles([]);
          onUploadComplete?.();
        }
      });
    });
  };

  return (
    <Container
      header={
        <Header
          variant="h2"
          description="Upload trade confirmation PDFs from both parties for matching"
          actions={
            <Button
              variant="primary"
              onClick={handleUpload}
              disabled={bankFiles.length === 0 && counterpartyFiles.length === 0}
              loading={isPending}
            >
              Start Processing
            </Button>
          }
        >
          Upload Trade Confirmations
        </Header>
      }
    >
      <SpaceBetween size="l">
        {isError && (
          <Alert type="error" header="Upload failed">
            {error?.message || 'An error occurred during upload'}
          </Alert>
        )}

        {isPending && (
          <ProgressBar
            value={50}
            label="Processing uploads"
            description="Extracting trade details..."
            status="in-progress"
          />
        )}

        <ColumnLayout columns={2}>
          <FileUpload
            onChange={({ detail }) => setBankFiles(detail.value)}
            value={bankFiles}
            i18nStrings={{
              uploadButtonText: (multiple) => multiple ? 'Choose files' : 'Choose file',
              dropzoneText: (multiple) => multiple ? 'Drop bank confirmations here' : 'Drop bank confirmation here',
              removeFileAriaLabel: (index) => `Remove file ${index + 1}`,
              limitShowFewer: 'Show fewer files',
              limitShowMore: 'Show more files',
              errorIconAriaLabel: 'Error'
            }}
            accept=".pdf"
            multiple
            showFileLastModified
            showFileSize
            constraintText="Accepted file types: PDF. Maximum file size: 10 MB."
          />

          <FileUpload
            onChange={({ detail }) => setCounterpartyFiles(detail.value)}
            value={counterpartyFiles}
            i18nStrings={{
              uploadButtonText: (multiple) => multiple ? 'Choose files' : 'Choose file',
              dropzoneText: (multiple) => multiple ? 'Drop counterparty confirmations here' : 'Drop counterparty confirmation here',
              removeFileAriaLabel: (index) => `Remove file ${index + 1}`,
              limitShowFewer: 'Show fewer files',
              limitShowMore: 'Show more files',
              errorIconAriaLabel: 'Error'
            }}
            accept=".pdf"
            multiple
            showFileLastModified
            showFileSize
            constraintText="Accepted file types: PDF. Maximum file size: 10 MB."
          />
        </ColumnLayout>
      </SpaceBetween>
    </Container>
  );
};
```

## Dashboard with Charts
```typescript
// pages/Dashboard.tsx
import { FC } from 'react';
import {
  ContentLayout,
  Header,
  Container,
  SpaceBetween,
  ColumnLayout,
  Box,
  StatusIndicator,
  PieChart,
  AreaChart
} from '@cloudscape-design/components';
import { useTrades } from '../hooks/useTrades';

export const Dashboard: FC = () => {
  const { data: trades = [], isLoading } = useTrades();

  // Calculate metrics
  const statusCounts = trades.reduce((acc, trade) => {
    acc[trade.status] = (acc[trade.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const pieChartData = [
    { title: 'Matched', value: statusCounts['MATCHED'] || 0, color: '#1d8102' },
    { title: 'Probable Match', value: statusCounts['PROBABLE_MATCH'] || 0, color: '#ff9900' },
    { title: 'Review Required', value: statusCounts['REVIEW_REQUIRED'] || 0, color: '#8d6605' },
    { title: 'Break', value: statusCounts['BREAK'] || 0, color: '#d91515' }
  ];

  return (
    <ContentLayout
      header={
        <Header
          variant="h1"
          description="Real-time overview of trade confirmation matching"
        >
          OTC Trade Matching Dashboard
        </Header>
      }
    >
      <SpaceBetween size="l">
        {/* Key Metrics */}
        <Container header={<Header variant="h2">Processing Status</Header>}>
          <ColumnLayout columns={4} variant="text-grid">
            <MetricCard
              label="Total Trades"
              value={trades.length}
              status="info"
            />
            <MetricCard
              label="Matched"
              value={statusCounts['MATCHED'] || 0}
              status="success"
            />
            <MetricCard
              label="Pending Review"
              value={(statusCounts['PROBABLE_MATCH'] || 0) + (statusCounts['REVIEW_REQUIRED'] || 0)}
              status="warning"
            />
            <MetricCard
              label="Breaks"
              value={statusCounts['BREAK'] || 0}
              status="error"
            />
          </ColumnLayout>
        </Container>

        {/* Charts Row */}
        <ColumnLayout columns={2}>
          <Container header={<Header variant="h2">Status Distribution</Header>}>
            <PieChart
              data={pieChartData}
              detailPopoverContent={(datum) => [
                { key: 'Count', value: datum.value },
                { key: 'Percentage', value: `${((datum.value / trades.length) * 100).toFixed(1)}%` }
              ]}
              segmentDescription={(datum, sum) =>
                `${datum.title}: ${datum.value} (${((datum.value / sum) * 100).toFixed(0)}%)`
              }
              i18nStrings={{
                detailsValue: 'Value',
                detailsPercentage: 'Percentage',
                filterLabel: 'Filter displayed data',
                filterPlaceholder: 'Filter data',
                filterSelectedAriaLabel: 'selected',
                legendAriaLabel: 'Legend',
                chartAriaRoleDescription: 'pie chart'
              }}
              ariaLabel="Trade status distribution"
              hideFilter
              size="medium"
            />
          </Container>

          <Container header={<Header variant="h2">Processing Trend</Header>}>
            <AreaChart
              series={[
                {
                  title: 'Processed',
                  type: 'area',
                  data: [
                    { x: new Date('2024-01-01'), y: 10 },
                    { x: new Date('2024-01-02'), y: 25 },
                    { x: new Date('2024-01-03'), y: 45 },
                    { x: new Date('2024-01-04'), y: 38 },
                    { x: new Date('2024-01-05'), y: 52 }
                  ]
                }
              ]}
              xDomain={[new Date('2024-01-01'), new Date('2024-01-05')]}
              yDomain={[0, 60]}
              i18nStrings={{
                xTickFormatter: (date) => date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                yTickFormatter: (value) => value.toString()
              }}
              ariaLabel="Processing trend"
              height={250}
              hideFilter
            />
          </Container>
        </ColumnLayout>

        {/* Agent Status */}
        <Container header={<Header variant="h2">Agent Status</Header>}>
          <ColumnLayout columns={4} variant="text-grid">
            <AgentStatusCard name="PDF Adapter" status="success" lastRun="2 min ago" />
            <AgentStatusCard name="Trade Extractor" status="in-progress" lastRun="Running..." />
            <AgentStatusCard name="Trade Matcher" status="pending" lastRun="Queued" />
            <AgentStatusCard name="Exception Handler" status="stopped" lastRun="Idle" />
          </ColumnLayout>
        </Container>
      </SpaceBetween>
    </ContentLayout>
  );
};

interface MetricCardProps {
  label: string;
  value: number;
  status: 'success' | 'warning' | 'error' | 'info';
}

const MetricCard: FC<MetricCardProps> = ({ label, value, status }) => (
  <div>
    <Box variant="awsui-key-label">{label}</Box>
    <Box variant="awsui-value-large">
      <StatusIndicator type={status}>{value.toLocaleString()}</StatusIndicator>
    </Box>
  </div>
);

interface AgentStatusCardProps {
  name: string;
  status: 'success' | 'in-progress' | 'pending' | 'stopped' | 'error';
  lastRun: string;
}

const AgentStatusCard: FC<AgentStatusCardProps> = ({ name, status, lastRun }) => (
  <div>
    <Box variant="awsui-key-label">{name}</Box>
    <SpaceBetween size="xxs">
      <StatusIndicator type={status}>
        {status === 'success' ? 'Healthy' :
         status === 'in-progress' ? 'Running' :
         status === 'pending' ? 'Pending' :
         status === 'stopped' ? 'Idle' : 'Error'}
      </StatusIndicator>
      <Box variant="small" color="text-body-secondary">{lastRun}</Box>
    </SpaceBetween>
  </div>
);
```

## Split Panel for Detail Views
```typescript
// components/common/TradeDetailPanel.tsx
import { FC } from 'react';
import {
  SplitPanel,
  SpaceBetween,
  KeyValuePairs,
  StatusIndicator,
  Table,
  Header,
  Badge,
  ColumnLayout,
  Box
} from '@cloudscape-design/components';
import { Trade, TradeMatch, Discrepancy } from '../../types';

interface TradeDetailPanelProps {
  trade: Trade | null;
  match?: TradeMatch;
}

export const TradeDetailPanel: FC<TradeDetailPanelProps> = ({ trade, match }) => {
  if (!trade) {
    return (
      <SplitPanel header="Trade Details" hidePreferencesButton>
        <Box textAlign="center" color="text-body-secondary" padding="l">
          Select a trade to view details
        </Box>
      </SplitPanel>
    );
  }

  return (
    <SplitPanel header={`Trade: ${trade.tradeId}`} hidePreferencesButton>
      <SpaceBetween size="l">
        <KeyValuePairs
          columns={3}
          items={[
            { label: 'Trade ID', value: trade.tradeId },
            { label: 'Source', value: <Badge>{trade.sourceType}</Badge> },
            { label: 'Status', value: <StatusIndicator type="success">{trade.status}</StatusIndicator> },
            { label: 'Counterparty', value: trade.counterparty },
            { label: 'Notional', value: `${trade.currency} ${trade.notional.toLocaleString()}` },
            { label: 'Trade Date', value: trade.tradeDate },
            { label: 'Maturity Date', value: trade.maturityDate },
            { label: 'Match Score', value: trade.matchScore ? `${trade.matchScore}%` : '—' }
          ]}
        />

        {match && match.discrepancies.length > 0 && (
          <Table
            header={<Header variant="h3">Discrepancies</Header>}
            columnDefinitions={[
              { id: 'field', header: 'Field', cell: (item: Discrepancy) => item.field },
              { id: 'bankValue', header: 'Bank Value', cell: (item: Discrepancy) => String(item.bankValue) },
              { id: 'counterpartyValue', header: 'Counterparty Value', cell: (item: Discrepancy) => String(item.counterpartyValue) },
              {
                id: 'severity',
                header: 'Severity',
                cell: (item: Discrepancy) => (
                  <StatusIndicator
                    type={item.severity === 'critical' ? 'error' : item.severity === 'warning' ? 'warning' : 'info'}
                  >
                    {item.severity}
                  </StatusIndicator>
                )
              }
            ]}
            items={match.discrepancies}
            variant="embedded"
          />
        )}

        {/* Extracted Fields */}
        <SpaceBetween size="s">
          <Header variant="h3">Extracted Fields</Header>
          <ColumnLayout columns={2} variant="text-grid">
            {Object.entries(trade.extractedFields).map(([key, value]) => (
              <div key={key}>
                <Box variant="awsui-key-label">{key}</Box>
                <div>{String(value)}</div>
              </div>
            ))}
          </ColumnLayout>
        </SpaceBetween>
      </SpaceBetween>
    </SplitPanel>
  );
};
```

## CloudScape Styling Guidelines

### DO NOT Use Inline Styles
CloudScape components are pre-styled. Avoid custom CSS except for specific overrides.

```typescript
// ❌ WRONG - Don't use inline styles
<div style={{ padding: '16px', backgroundColor: '#f0f0f0' }}>
  Content
</div>

// ✅ CORRECT - Use CloudScape components
<Container>
  <SpaceBetween size="m">
    Content
  </SpaceBetween>
</Container>
```

### Spacing with SpaceBetween
```typescript
// Use SpaceBetween for vertical/horizontal spacing
<SpaceBetween size="l" direction="vertical">
  <Container>First</Container>
  <Container>Second</Container>
</SpaceBetween>

// Available sizes: 'xxxs' | 'xxs' | 'xs' | 's' | 'm' | 'l' | 'xl' | 'xxl'
```

### Grid Layouts with ColumnLayout
```typescript
// Use ColumnLayout for responsive grids
<ColumnLayout columns={4} variant="text-grid">
  <div>Column 1</div>
  <div>Column 2</div>
  <div>Column 3</div>
  <div>Column 4</div>
</ColumnLayout>

// Variants: 'default' | 'text-grid'
```

### Box Component for Text Styling
```typescript
// Use Box for text variants
<Box variant="h1">Heading 1</Box>
<Box variant="p">Paragraph text</Box>
<Box variant="small">Small text</Box>
<Box variant="awsui-key-label">Label</Box>
<Box variant="awsui-value-large">Large value</Box>

// Colors
<Box color="text-body-secondary">Muted text</Box>
<Box color="text-status-error">Error text</Box>
<Box color="text-status-success">Success text</Box>
```

## Accessibility Requirements
- **WCAG 2.1 AA compliance** - CloudScape components are pre-built for accessibility
- All CloudScape components include **ARIA attributes** automatically
- Use `ariaLabel` props where required by CloudScape components
- Use `i18nStrings` for internationalization of component labels
- CloudScape maintains **color contrast ratios** automatically
- **Keyboard navigation** is built into all interactive components
- Test with **screen readers** for critical workflows

## Visual Modes
CloudScape supports visual modes without custom theming:

```typescript
// Enable dark mode via CSS class on body
document.body.classList.add('awsui-dark-mode');

// Enable compact mode
document.body.classList.add('awsui-compact-mode');
```

## Development Commands
```bash
npm run dev      # Start Vite dev server (port 5173)
npm run build    # Production build with type checking
npm run lint     # Run ESLint
npm run preview  # Preview production build locally
```

## Testing Approach
- Use **Vitest** for unit tests
- Use **@cloudscape-design/test-utils-core** for component testing
- Run tests with `--run` flag for CI/CD: `npm run test -- --run`
- Avoid watch mode in automated environments

```typescript
// Example test with CloudScape test utilities
import { createWrapper } from '@cloudscape-design/test-utils-core';
import { render } from '@testing-library/react';
import { TradeTable } from './TradeTable';

test('renders trade table', () => {
  const { container } = render(<TradeTable trades={mockTrades} />);
  const wrapper = createWrapper(container);
  const table = wrapper.findTable();
  
  expect(table).toBeTruthy();
  expect(table!.findRows()).toHaveLength(mockTrades.length);
});
```

## Performance Considerations
- CloudScape Table uses **built-in virtualization** for large datasets
- Use **React.lazy** and Suspense for route-based code splitting
- Leverage **useCollection hook** for efficient filtering/sorting
- CloudScape components are **optimized for performance** out of the box

## Domain-Specific Patterns

### Trade Status Display
Use consistent status mapping with CloudScape StatusIndicator:

| Status | Type | Color Indicator |
|--------|------|-----------------|
| `MATCHED` (≥85%) | `success` | Green |
| `PROBABLE_MATCH` (70-84%) | `warning` | Yellow |
| `REVIEW_REQUIRED` (50-69%) | `pending` | Orange |
| `BREAK` (<50%) | `error` | Red |

### Real-Time Updates
- Use **Flashbar** for real-time notifications in AppLayout
- Display agent status with **StatusIndicator** components
- Show **last updated timestamp** using Box with small variant
- Use **WebSocket integration** to trigger React Query invalidations

### Error Handling
- Display errors using **Alert** component within containers
- Use **Flashbar** for transient error notifications
- Provide retry mechanisms with **Button** actions
- Log errors to console for debugging

```typescript
// Error display pattern
{isError && (
  <Alert
    type="error"
    header="Failed to load trades"
    action={<Button onClick={refetch}>Retry</Button>}
  >
    {error?.message || 'An unexpected error occurred'}
  </Alert>
)}
```