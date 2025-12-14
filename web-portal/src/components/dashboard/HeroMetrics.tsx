import React, { useEffect, useState } from 'react'
import { Box, Grid, Card, CardContent, Typography, Avatar, Chip } from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  CheckCircle as SuccessIcon,
  SmartToy as AgentIcon,
} from '@mui/icons-material'

interface HeroMetric {
  label: string
  value: number
  suffix?: string
  icon: React.ReactNode
  color: string
  bgColor: string
  trend?: number
}

interface HeroMetricsProps {
  totalTrades: number
  matchRate: number
  avgLatency: number
  activeAgents: number
}

// Animated counter hook
function useAnimatedCounter(end: number, duration: number = 2000) {
  const [count, setCount] = useState(0)

  useEffect(() => {
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

  return count
}

export default function HeroMetrics({ totalTrades, matchRate, avgLatency, activeAgents }: HeroMetricsProps) {
  const animatedTrades = useAnimatedCounter(totalTrades, 2000)
  const animatedMatchRate = useAnimatedCounter(matchRate * 100, 2500) / 100
  const animatedLatency = useAnimatedCounter(avgLatency, 1800)
  const animatedAgents = useAnimatedCounter(activeAgents, 1500)

  const metrics: HeroMetric[] = [
    {
      label: 'Trades Today',
      value: animatedTrades,
      icon: <TrendingUpIcon />,
      color: '#FF9900',
      bgColor: 'rgba(255, 153, 0, 0.1)',
      trend: 12.5
    },
    {
      label: 'Match Rate',
      value: animatedMatchRate,
      suffix: '%',
      icon: <SuccessIcon />,
      color: '#1D8102',
      bgColor: 'rgba(29, 129, 2, 0.1)',
      trend: 2.3
    },
    {
      label: 'Avg Latency',
      value: animatedLatency,
      suffix: 'ms',
      icon: <SpeedIcon />,
      color: '#146EB4',
      bgColor: 'rgba(20, 110, 180, 0.1)',
      trend: -8.1
    },
    {
      label: 'Active Agents',
      value: animatedAgents,
      icon: <AgentIcon />,
      color: '#9C27B0',
      bgColor: 'rgba(156, 39, 176, 0.1)',
    }
  ]

  return (
    <Box sx={{ mb: 4 }}>
      <Grid container spacing={3}>
        {metrics.map((metric, index) => (
          <Grid item xs={12} sm={6} md={3} key={metric.label}>
            <Card
              sx={{
                background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.95) 0%, rgba(35, 42, 49, 0.95) 100%)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(65, 77, 92, 0.3)',
                transition: 'all 0.3s ease-in-out',
                animation: `slideInUp 0.6s ease-out ${index * 0.1}s both`,
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: `0 8px 25px ${metric.color}20`,
                  border: `1px solid ${metric.color}40`,
                },
                '@keyframes slideInUp': {
                  '0%': {
                    opacity: 0,
                    transform: 'translateY(30px)',
                  },
                  '100%': {
                    opacity: 1,
                    transform: 'translateY(0)',
                  },
                },
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                  <Avatar
                    sx={{
                      bgcolor: metric.bgColor,
                      color: metric.color,
                      width: 48,
                      height: 48,
                      border: `2px solid ${metric.color}30`,
                    }}
                  >
                    {metric.icon}
                  </Avatar>
                  {metric.trend && (
                    <Chip
                      size="small"
                      label={`${metric.trend > 0 ? '+' : ''}${metric.trend}%`}
                      sx={{
                        backgroundColor: metric.trend > 0 ? 'rgba(29, 129, 2, 0.15)' : 'rgba(209, 50, 18, 0.15)',
                        color: metric.trend > 0 ? '#1D8102' : '#D13212',
                        fontWeight: 600,
                        fontSize: '0.75rem',
                        border: `1px solid ${metric.trend > 0 ? '#1D8102' : '#D13212'}30`,
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
                  }}
                >
                  {metric.value.toLocaleString()}{metric.suffix}
                </Typography>

                <Typography
                  variant="body2"
                  color="text.secondary"
                  fontWeight={500}
                  sx={{ textTransform: 'uppercase', letterSpacing: 0.5 }}
                >
                  {metric.label}
                </Typography>

                {/* Subtle progress indicator */}
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
                      animation: 'progressFill 2s ease-out',
                      width: metric.label === 'Match Rate' ? `${animatedMatchRate}%` : 
                             metric.label === 'Active Agents' ? `${(animatedAgents / 5) * 100}%` :
                             '85%',
                      '@keyframes progressFill': {
                        '0%': { width: '0%' },
                      },
                    }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}