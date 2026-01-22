import { useState, useEffect, useRef } from 'react'
import {
  Box,
  Typography,
  Container as MuiContainer,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
} from '@mui/material'
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Delete as ClearIcon,
  FiberManualRecord as DotIcon,
} from '@mui/icons-material'
import { useQuery } from '@tanstack/react-query'
import { agentService } from '../services/agentService'
import GlassCard from '../components/common/GlassCard'
import StatusPulse from '../components/common/StatusPulse'
import { fsiColors } from '../theme'
import type { AgentHealth } from '../types'

interface ActivityEvent {
  id: string
  timestamp: Date
  agentName: string
  eventType: 'processing' | 'completed' | 'error' | 'waiting'
  message: string
  sessionId?: string
  details?: Record<string, unknown>
}

// Simulated event generator for demo purposes
const generateMockEvent = (agents: AgentHealth[]): ActivityEvent => {
  const eventTypes: ActivityEvent['eventType'][] = ['processing', 'completed', 'waiting']
  const eventType = eventTypes[Math.floor(Math.random() * eventTypes.length)]
  const agent = agents[Math.floor(Math.random() * agents.length)]

  const messages: Record<string, string[]> = {
    processing: [
      'Extracting text from PDF document...',
      'Parsing trade confirmation fields...',
      'Comparing trade attributes...',
      'Calculating confidence scores...',
      'Validating extracted data...',
    ],
    completed: [
      'Successfully matched trade TRD-2024-' + Math.floor(Math.random() * 9999),
      'Trade extraction completed with 98% confidence',
      'PDF processing finished - 3 pages extracted',
      'Exception resolved automatically',
      'HITL review submitted successfully',
    ],
    waiting: [
      'Waiting for counterparty document...',
      'Queued for matching engine...',
      'Pending human review...',
      'Awaiting upstream agent completion...',
    ],
    error: [
      'Failed to parse date field',
      'Low confidence match detected',
      'Timeout waiting for response',
    ],
  }

  return {
    id: `evt-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    timestamp: new Date(),
    agentName: agent?.agentName || 'System',
    eventType,
    message: messages[eventType][Math.floor(Math.random() * messages[eventType].length)],
    sessionId: `sess-${Math.random().toString(36).substr(2, 8)}`,
  }
}

export default function RealTimeMonitor() {
  const [isLive, setIsLive] = useState(true)
  const [events, setEvents] = useState<ActivityEvent[]>([])
  const eventContainerRef = useRef<HTMLDivElement>(null)

  const { data: agents } = useQuery<AgentHealth[]>({
    queryKey: ['agentStatus'],
    queryFn: agentService.getAgentStatus,
    refetchInterval: isLive ? 5000 : false,
  })

  // Generate mock events for demo
  useEffect(() => {
    if (!isLive || !agents || agents.length === 0) return

    const interval = setInterval(() => {
      const newEvent = generateMockEvent(agents)
      setEvents(prev => [newEvent, ...prev].slice(0, 100)) // Keep last 100 events
    }, 2000 + Math.random() * 3000) // Random interval 2-5 seconds

    return () => clearInterval(interval)
  }, [isLive, agents])

  // Auto-scroll to top when new events arrive
  useEffect(() => {
    if (eventContainerRef.current && isLive) {
      eventContainerRef.current.scrollTop = 0
    }
  }, [events, isLive])

  const handleClearEvents = () => {
    setEvents([])
  }

  const getEventColor = (type: ActivityEvent['eventType']) => {
    switch (type) {
      case 'processing': return fsiColors.status.info
      case 'completed': return fsiColors.status.success
      case 'error': return fsiColors.status.error
      case 'waiting': return fsiColors.status.warning
      default: return fsiColors.text.muted
    }
  }

  const getEventLabel = (type: ActivityEvent['eventType']) => {
    switch (type) {
      case 'processing': return 'Processing'
      case 'completed': return 'Completed'
      case 'error': return 'Error'
      case 'waiting': return 'Waiting'
      default: return 'Unknown'
    }
  }

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    })
  }

  // Calculate system stats
  const healthyAgents = agents?.filter(a => a.status === 'HEALTHY').length || 0
  const totalAgents = agents?.length || 0
  const avgLatency = agents && agents.length > 0
    ? Math.round(agents.reduce((sum, a) => sum + (a.metrics?.latencyMs || 0), 0) / agents.length)
    : 0
  const totalThroughput = agents?.reduce((sum, a) => sum + (a.metrics?.throughput || 0), 0) || 0

  return (
    <MuiContainer maxWidth="xl" sx={{ py: 4 }}>
      {/* Page Header */}
      <Box
        sx={{
          mb: 4,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          animation: 'fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
          '@keyframes fadeIn': {
            '0%': { opacity: 0, transform: 'translateY(-16px)' },
            '100%': { opacity: 1, transform: 'translateY(0)' },
          },
        }}
      >
        <Box>
          <Typography
            variant="overline"
            sx={{
              color: fsiColors.orange.main,
              letterSpacing: '0.15em',
              fontWeight: 600,
              display: 'block',
              mb: 0.5,
            }}
          >
            LIVE MONITORING
          </Typography>
          <Typography
            variant="h3"
            fontWeight={700}
            sx={{
              mb: 1,
              color: fsiColors.text.primary,
              letterSpacing: '-0.02em',
            }}
          >
            Real-time Monitor
          </Typography>
          <Typography variant="body1" sx={{ color: fsiColors.text.secondary }}>
            Live activity stream from AI agents
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <StatusPulse
            status={isLive ? 'healthy' : 'offline'}
            label={isLive ? 'Live' : 'Paused'}
          />
          <Tooltip title={isLive ? 'Pause stream' : 'Resume stream'}>
            <IconButton
              onClick={() => setIsLive(!isLive)}
              sx={{
                bgcolor: 'rgba(255, 153, 0, 0.1)',
                '&:hover': { bgcolor: 'rgba(255, 153, 0, 0.2)' },
              }}
            >
              {isLive ? <PauseIcon sx={{ color: '#FF9900' }} /> : <PlayIcon sx={{ color: '#FF9900' }} />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Clear events">
            <IconButton
              onClick={handleClearEvents}
              sx={{
                bgcolor: 'rgba(255, 255, 255, 0.05)',
                '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.1)' },
              }}
            >
              <ClearIcon sx={{ color: 'text.secondary' }} />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* System Stats Bar */}
      <GlassCard variant="elevated" animateIn sx={{ mb: 4, p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" fontWeight={700} color="primary.main">
              {healthyAgents}/{totalAgents}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Agents Online
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" fontWeight={700} color="success.main">
              {avgLatency}ms
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Avg Latency
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" fontWeight={700} color="info.main">
              {totalThroughput}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Ops/min
            </Typography>
          </Box>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" fontWeight={700} color="warning.main">
              {events.length}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Events Captured
            </Typography>
          </Box>
        </Box>
      </GlassCard>

      {/* Main Content Grid */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' }, gap: 3 }}>
        {/* Activity Stream */}
        <GlassCard variant="default" animateIn animationDelay={0.1} sx={{ p: 0 }}>
          <Box sx={{ p: 2, borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
            <Typography variant="h6" fontWeight={600}>
              Activity Stream
            </Typography>
          </Box>
          {isLive && (
            <LinearProgress
              sx={{
                height: 2,
                bgcolor: 'rgba(255,153,0,0.1)',
                '& .MuiLinearProgress-bar': {
                  bgcolor: '#FF9900',
                },
              }}
            />
          )}
          <Box
            ref={eventContainerRef}
            sx={{
              height: 500,
              overflowY: 'auto',
              '&::-webkit-scrollbar': { width: 8 },
              '&::-webkit-scrollbar-track': { bgcolor: 'rgba(255,255,255,0.05)' },
              '&::-webkit-scrollbar-thumb': {
                bgcolor: 'rgba(255,255,255,0.2)',
                borderRadius: 4,
              },
            }}
          >
            {events.length === 0 ? (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <Typography color="text.secondary">
                  {isLive ? 'Waiting for events...' : 'Stream paused. Click play to resume.'}
                </Typography>
              </Box>
            ) : (
              events.map((event, index) => (
                <Box
                  key={event.id}
                  sx={{
                    p: 2,
                    borderBottom: '1px solid rgba(255,255,255,0.05)',
                    animation: index === 0 ? 'slideIn 0.3s ease-out' : undefined,
                    '@keyframes slideIn': {
                      '0%': { opacity: 0, transform: 'translateX(-20px)' },
                      '100%': { opacity: 1, transform: 'translateX(0)' },
                    },
                    '&:hover': {
                      bgcolor: 'rgba(255,255,255,0.03)',
                    },
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                    <DotIcon sx={{ color: getEventColor(event.eventType), fontSize: 12, mt: 0.5 }} />
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                        <Typography variant="body2" fontWeight={600} color="text.primary">
                          {event.agentName}
                        </Typography>
                        <Chip
                          label={getEventLabel(event.eventType)}
                          size="small"
                          sx={{
                            height: 20,
                            fontSize: '0.7rem',
                            bgcolor: `${getEventColor(event.eventType)}20`,
                            color: getEventColor(event.eventType),
                            border: `1px solid ${getEventColor(event.eventType)}40`,
                          }}
                        />
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                        {event.message}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Typography variant="caption" color="text.disabled">
                          {formatTime(event.timestamp)}
                        </Typography>
                        {event.sessionId && (
                          <Typography variant="caption" color="text.disabled" sx={{ fontFamily: 'monospace' }}>
                            {event.sessionId}
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  </Box>
                </Box>
              ))
            )}
          </Box>
        </GlassCard>

        {/* Agent Status Panel */}
        <GlassCard variant="default" animateIn animationDelay={0.2} sx={{ p: 0 }}>
          <Box sx={{ p: 2, borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
            <Typography variant="h6" fontWeight={600}>
              Agent Status
            </Typography>
          </Box>
          <Box sx={{ p: 2 }}>
            {agents?.map((agent) => (
              <Box
                key={agent.agentId}
                sx={{
                  p: 2,
                  mb: 2,
                  borderRadius: 2,
                  bgcolor: 'rgba(255,255,255,0.03)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  '&:last-child': { mb: 0 },
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="body2" fontWeight={600}>
                    {agent.agentName}
                  </Typography>
                  <StatusPulse
                    status={agent.status === 'HEALTHY' ? 'healthy' : agent.status === 'DEGRADED' ? 'degraded' : 'unhealthy'}
                    size="small"
                  />
                </Box>
                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
                  <Box>
                    <Typography variant="caption" color="text.disabled">
                      Latency
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {agent.metrics?.latencyMs || 0}ms
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.disabled">
                      Throughput
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {agent.metrics?.throughput || 0}/min
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.disabled">
                      Success Rate
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {((agent.metrics?.successRate || 0) * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.disabled">
                      Active Tasks
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {agent.activeTasks || 0}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            ))}
          </Box>
        </GlassCard>
      </Box>
    </MuiContainer>
  )
}
