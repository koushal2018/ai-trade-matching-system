# React Hooks

This directory contains custom React hooks for the Trade Matching UI.

## Available Hooks

### `useAgentStatus`

Hook for fetching and polling agent status using React Query.

**Features:**
- Automatic polling every 30 seconds during active processing
- Caching with 10-second stale time
- Error handling with retry logic (3 retries with exponential backoff)
- Loading and error states
- Automatically stops polling when processing is complete

**Usage:**
```typescript
import { useAgentStatus } from './hooks/useAgentStatus'

function MyComponent() {
  const { data, isLoading, isError, error } = useAgentStatus(sessionId)
  
  if (isLoading) return <Spinner />
  if (isError) return <Alert type="error">{error.message}</Alert>
  
  return (
    <div>
      <p>Overall Status: {data.overallStatus}</p>
      <p>PDF Adapter: {data.agents.pdfAdapter.status}</p>
      {/* ... */}
    </div>
  )
}
```

**Parameters:**
- `sessionId: string | null` - Workflow session ID (null to disable query)

**Returns:**
- React Query result with `WorkflowStatusResponse` data

---

### `useAgentWebSocket`

Hook for managing WebSocket connection for real-time agent status updates.

**Features:**
- Automatic connection when sessionId is provided
- Exponential backoff reconnection (1s, 2s, 4s, 8s, max 30s)
- Fallback to polling after 3 failed reconnection attempts
- Updates React Query cache on message receipt
- Connection state tracking
- Manual reconnect function

**Usage:**
```typescript
import { useAgentWebSocket } from './hooks/useAgentWebSocket'
import { useNotifications } from './hooks/useNotifications'

function MyComponent() {
  const { addNotification } = useNotifications()
  
  const { connectionState, reconnect, isConnected, isFallback } = useAgentWebSocket(
    sessionId,
    (state, message) => {
      // Handle connection state changes
      if (state === 'fallback') {
        addNotification({
          type: 'warning',
          header: 'Real-time updates unavailable',
          content: message,
          dismissible: true,
        })
      } else if (state === 'connected') {
        addNotification({
          type: 'success',
          header: 'Connected',
          content: message,
          dismissible: true,
        })
      }
    }
  )
  
  return (
    <div>
      <StatusIndicator type={isConnected ? 'success' : 'warning'}>
        {connectionState}
      </StatusIndicator>
      {isFallback && (
        <Button onClick={reconnect}>Retry Connection</Button>
      )}
    </div>
  )
}
```

**Parameters:**
- `sessionId: string | null` - Workflow session ID (null to disable WebSocket)
- `onConnectionChange?: (state: ConnectionState, message: string) => void` - Callback for connection state changes

**Returns:**
- `connectionState: ConnectionState` - Current connection state
- `reconnect: () => void` - Function to manually trigger reconnection
- `isConnected: boolean` - Whether WebSocket is connected
- `isFallback: boolean` - Whether using polling fallback

**WebSocket Message Types:**
- `AGENT_STATUS_UPDATE` - Full agent status update
- `STEP_UPDATE` - Individual step status update
- `RESULT_AVAILABLE` - Match result is available
- `EXCEPTION` - New exception occurred

---

### `useNotifications`

Hook for managing Flashbar notifications.

**Features:**
- Add notifications with auto-dismiss for success messages
- Dismiss individual notifications
- Clear all notifications

**Usage:**
```typescript
import { useNotifications } from './hooks/useNotifications'

function MyComponent() {
  const { notifications, addNotification, dismissNotification } = useNotifications()
  
  const handleSuccess = () => {
    addNotification({
      type: 'success',
      header: 'Upload successful',
      content: 'Your file has been uploaded.',
      dismissible: true,
    })
  }
  
  return (
    <AppLayout
      notifications={<Flashbar items={notifications} />}
      content={/* ... */}
    />
  )
}
```

---

## Integration Example

Here's how to use both hooks together for real-time updates:

```typescript
import { useAgentStatus, useAgentWebSocket, useNotifications } from './hooks'

function TradeMatchingPage() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const { addNotification } = useNotifications()
  
  // Fetch agent status with polling fallback
  const { data: agentStatus, isLoading } = useAgentStatus(sessionId)
  
  // WebSocket for real-time updates
  const { isConnected, isFallback, reconnect } = useAgentWebSocket(
    sessionId,
    (state, message) => {
      if (state === 'fallback') {
        addNotification({
          type: 'warning',
          header: 'Using polling mode',
          content: message,
          dismissible: true,
          action: <Button onClick={reconnect}>Retry Connection</Button>,
        })
      } else if (state === 'connected') {
        addNotification({
          type: 'success',
          header: 'Real-time updates enabled',
          content: message,
          dismissible: true,
        })
      }
    }
  )
  
  return (
    <ContentLayout>
      <AgentProcessingSection 
        sessionId={sessionId} 
        agentStatus={agentStatus}
        isConnected={isConnected}
      />
    </ContentLayout>
  )
}
```

## Testing

Tests are located in `__tests__/` subdirectory. Run tests with:

```bash
npm test -- hooks
```
