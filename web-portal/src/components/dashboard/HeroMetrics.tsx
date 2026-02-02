import React, { useEffect, useState, useRef } from 'react'
import { Box, Grid, Typography, Avatar, Chip, Tooltip } from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  CheckCircle as SuccessIcon,
  SmartToy as AgentIcon,
  AutoAwesome as SparkleIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  HourglassEmpty as PendingIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material'
import GlassCard from '../common/GlassCard'
import { glowColors } from '../../theme'
import type { MatchingStatusResponse } from '../../types'

interface HeroMetric {
  label: string
  value: number
  suffix?: string
  icon: React.ReactNode
  color: string
  bgColor: string
  trend?: number
  subtitle?: string
  tooltip?: string
}

interface HeroMetricsProps {
  totalTrades: number
  bankTradeCount: number
  counterpartyTradeCount: number
  matchRate: number
  avgLatency: number
  activeAgents: number
  workload: number | string
  matchingStatus?: MatchingStatusResponse
  isLoading?: boolean
}

// Animated counter hook with sparkle effect
function useAnimatedCounter(end: number, duration: number = 2000) {
  const [count, setCount] = useState(0)
  const [showSparkle, setShowSparkle] = useState(false)
  const prevValue = useRef(end)

  useEffect(() => {
    // Detect value change for sparkle effect
    if (prevValue.current !== end && prevValue.current !== 0) {
      setShowSparkle(true)
      setTimeout(() => setShowSparkle(false), 500)
    }
    prevValue.current = end

    let startTime: number
    let animationFrame: number

    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime
      const progress = Math.min((currentTime - startTime) / duration, 1)

      // Easing function for smooth animation
      const easeOutQuart = 1 - Math.pow(1 - progress, 4)
      const currentCount = Math.floor(end * easeOutQuart)

      setCount(currentCount)

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate)
      }
    }

    animationFrame = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(animationFrame)
  }, [end, duration])

  return { count, showSparkle }
}

export default function HeroMetrics({ totalTrades, bankTradeCount, counterpartyTradeCount, matchRate, avgLatency, activeAgents, workload, matchingStatus }: HeroMetricsProps) {
  const trades = useAnimatedCounter(totalTrades, 2000)
  const rate = useAnimatedCounter(matchRate * 100, 2500)
  const latency = useAnimatedCounter(avgLatency, 1800)
  const agents = useAnimatedCounter(activeAgents, 1500)
  
  // Handle workload animation - only animate if it's a number
  const workloadValue = typeof workload === 'number' ? workload : 0
  const workloadCounter = useAnimatedCounter(workloadValue, 2000)

  // Animate matching status counts
  // Requirements: 6.7, 6.8, 6.9
  const matched = useAnimatedCounter(matchingStatus?.matched || 0, 2000)
  const unmatched = useAnimatedCounter(matchingStatus?.unmatched || 0, 2000)
  const pending = useAnimatedCounter(matchingStatus?.pending || 0, 2000)
  const exceptions = useAnimatedCounter(matchingStatus?.exceptions || 0, 2000)

  const metrics: HeroMetric[] = [
    {
      label: 'Agent Load',
      value: typeof workload === 'string' ? 0 : workloadCounter.count,
      suffix: typeof workload === 'string' ? '' : '%',
      icon: <SpeedIcon />,
      color: glowColors.warning,
      bgColor: 'rgba(255, 152, 0, 0.1)',
      tooltip: 'Percentage of agent task capacity currently in use',
    },
    {
      label: 'Matched',
      value: matched.count,
      icon: <CheckIcon />,
      color: glowColors.success,
      bgColor: 'rgba(29, 129, 2, 0.1)',
    },
    {
      label: 'Unmatched',
      value: unmatched.count,
      icon: <CloseIcon />,
      color: glowColors.error,
      bgColor: 'rgba(209, 50, 18, 0.1)',
    },
    {
      label: 'Pending',
      value: pending.count,
      icon: <PendingIcon />,
      color: glowColors.info,
      bgColor: 'rgba(9, 114, 211, 0.1)',
    },
    {
      label: 'Exceptions',
      value: exceptions.count,
      icon: <ErrorIcon />,
      color: glowColors.warning,
      bgColor: 'rgba(255, 152, 0, 0.1)',
    },
    {
      label: 'Trades Today',
      value: trades.count,
      icon: <TrendingUpIcon />,
      color: glowColors.primary,
      bgColor: 'rgba(255, 153, 0, 0.1)',
      subtitle: `Bank: ${bankTradeCount} | CP: ${counterpartyTradeCount}`,
      trend: 12.5
    },
    {
      label: 'Match Rate',
      value: rate.count / 100,
      suffix: '%',
      icon: <SuccessIcon />,
      color: glowColors.success,
      bgColor: 'rgba(29, 129, 2, 0.1)',
      trend: 2.3
    },
    {
      label: 'Avg Latency',
      value: latency.count,
      suffix: 'ms',
      icon: <SpeedIcon />,
      color: glowColors.info,
      bgColor: 'rgba(9, 114, 211, 0.1)',
      trend: -8.1
    },
    {
      label: 'Active Agents',
      value: agents.count,
      icon: <AgentIcon />,
      color: glowColors.purple,
      bgColor: 'rgba(156, 39, 176, 0.1)',
    }
  ]

  const sparkleStates = [
    typeof workload === 'number' && workloadCounter.showSparkle,
    matched.showSparkle,
    unmatched.showSparkle,
    pending.showSparkle,
    exceptions.showSparkle,
    trades.showSparkle,
    rate.showSparkle,
    latency.showSparkle,
    agents.showSparkle
  ]

  return (
    <Box sx={{ mb: 4 }}>
      <Grid container spacing={3}>
        {metrics.map((metric, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2.4 }} key={metric.label}>
            <GlassCard
              variant="default"
              glowColor={metric.color}
              hoverEffect="all"
              animateIn
              animationDelay={index * 0.1}
              borderRadius={12}
              sx={{ height: '100%' }}
            >
              <Box sx={{ p: 3, position: 'relative' }}>
                {/* Sparkle effect on value change */}
                {sparkleStates[index] && (
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 16,
                      right: 16,
                      animation: 'sparkle 0.5s ease-out',
                      '@keyframes sparkle': {
                        '0%, 100%': { opacity: 0, transform: 'scale(0.5)' },
                        '50%': { opacity: 1, transform: 'scale(1)' },
                      },
                    }}
                  >
                    <SparkleIcon sx={{ color: metric.color, fontSize: 20 }} />
                  </Box>
                )}

                <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                  <Avatar
                    sx={{
                      bgcolor: metric.bgColor,
                      color: metric.color,
                      width: 48,
                      height: 48,
                      border: `2px solid ${metric.color}30`,
                      transition: 'all 0.15s ease-out',
                    }}
                  >
                    {metric.icon}
                  </Avatar>
                  {metric.trend !== undefined && (
                    <Chip
                      size="small"
                      label={`${metric.trend > 0 ? '+' : ''}${metric.trend}%`}
                      sx={{
                        backgroundColor: metric.trend > 0 ? 'rgba(29, 129, 2, 0.15)' : 'rgba(209, 50, 18, 0.15)',
                        color: metric.trend > 0 ? glowColors.success : glowColors.error,
                        fontWeight: 600,
                        fontSize: '0.75rem',
                        border: `1px solid ${metric.trend > 0 ? glowColors.success : glowColors.error}30`,
                        backdropFilter: 'blur(4px)',
                      }}
                    />
                  )}
                </Box>

                <Typography
                  variant="h2"
                  sx={{
                    fontWeight: 700,
                    color: metric.color,
                    mb: 0.5,
                    fontFamily: '"Amazon Ember", "Helvetica Neue", Helvetica, Arial, sans-serif',
                    textShadow: `0 0 20px ${metric.color}40`,
                    transition: 'all 0.15s ease-out',
                  }}
                >
                  {metric.label === 'Agent Load' && typeof workload === 'string'
                    ? workload
                    : metric.label === 'Match Rate'
                    ? (metric.value * 100).toFixed(1)
                    : metric.value.toLocaleString()
                  }{metric.label === 'Agent Load' && typeof workload === 'string' ? '' : metric.suffix}
                </Typography>

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    fontWeight={500}
                    sx={{ textTransform: 'uppercase', letterSpacing: 0.5 }}
                  >
                    {metric.label}
                  </Typography>
                  {metric.tooltip && (
                    <Tooltip title={metric.tooltip} arrow placement="top">
                      <InfoIcon sx={{ fontSize: 14, color: 'text.secondary', cursor: 'help' }} />
                    </Tooltip>
                  )}
                </Box>

                {/* Subtitle for showing breakdown */}
                {metric.subtitle && (
                  <Typography
                    variant="caption"
                    sx={{ color: 'text.secondary', mt: 0.5, display: 'block' }}
                  >
                    {metric.subtitle}
                  </Typography>
                )}

                {/* Progress indicator */}
                <Box
                  sx={{
                    mt: 2,
                    height: 3,
                    backgroundColor: 'rgba(65, 77, 92, 0.3)',
                    borderRadius: 1.5,
                    overflow: 'hidden',
                  }}
                >
                  <Box
                    sx={{
                      height: '100%',
                      background: `linear-gradient(90deg, ${metric.color} 0%, ${metric.color}80 100%)`,
                      borderRadius: 1.5,
                      width: metric.label === 'Agent Load' && typeof workload === 'string' ? '0%' :
                             metric.label === 'Agent Load' ? `${metric.value}%` :
                             metric.label === 'Match Rate' ? `${metric.value * 100}%` :
                             metric.label === 'Active Agents' ? `${(metric.value / 5) * 100}%` :
                             metric.label === 'Matched' || metric.label === 'Unmatched' ||
                             metric.label === 'Pending' || metric.label === 'Exceptions' ?
                             `${Math.min(100, (metric.value / Math.max(1, totalTrades)) * 100)}%` :
                             '85%',
                      animation: 'progressFill 2s ease-out',
                      '@keyframes progressFill': {
                        '0%': { width: '0%' },
                      },
                    }}
                  />
                </Box>
              </Box>
            </GlassCard>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}
