import React from 'react'
import { Box, BoxProps } from '@mui/material'

export type SkeletonVariant = 'card' | 'table-row' | 'metric-card' | 'chart' | 'text' | 'avatar' | 'button'

export interface SkeletonLoaderProps extends Omit<BoxProps, 'children'> {
  /** Skeleton variant */
  variant?: SkeletonVariant
  /** Width override */
  width?: number | string
  /** Height override */
  height?: number | string
  /** Number of items to render (for table-row and text variants) */
  count?: number
  /** Animation enabled */
  animate?: boolean
}

const baseSkeletonStyles = {
  backgroundColor: 'rgba(65, 77, 92, 0.2)',
  borderRadius: '8px',
  position: 'relative' as const,
  overflow: 'hidden' as const,
}

const shimmerAnimation = {
  '&::after': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundImage: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.06) 50%, transparent 100%)',
    backgroundSize: '200% 100%',
    animation: 'shimmer 1.5s linear infinite',
  },
  '@keyframes shimmer': {
    '0%': { backgroundPosition: '-200% 0' },
    '100%': { backgroundPosition: '200% 0' },
  },
}

/**
 * SkeletonLoader Component
 *
 * Provides loading placeholder animations with glassmorphism styling.
 *
 * @example
 * // Card skeleton
 * <SkeletonLoader variant="card" />
 *
 * // Multiple text lines
 * <SkeletonLoader variant="text" count={3} />
 *
 * // Metric card
 * <SkeletonLoader variant="metric-card" />
 */
export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  variant = 'card',
  width,
  height,
  count = 1,
  animate = true,
  sx,
  ...rest
}) => {
  const animationStyles = animate ? shimmerAnimation : {}

  // Render based on variant
  switch (variant) {
    case 'card':
      return (
        <Box
          sx={{
            ...baseSkeletonStyles,
            ...animationStyles,
            width: width || '100%',
            height: height || 200,
            background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.6) 0%, rgba(35, 42, 49, 0.6) 100%)',
            border: '1px solid rgba(65, 77, 92, 0.2)',
            ...sx,
          }}
          {...rest}
        />
      )

    case 'metric-card':
      return (
        <Box
          sx={{
            ...baseSkeletonStyles,
            width: width || '100%',
            height: height || 140,
            padding: 3,
            background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.6) 0%, rgba(35, 42, 49, 0.6) 100%)',
            border: '1px solid rgba(65, 77, 92, 0.2)',
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            ...sx,
          }}
          {...rest}
        >
          {/* Icon placeholder */}
          <Box
            sx={{
              ...baseSkeletonStyles,
              ...animationStyles,
              width: 48,
              height: 48,
              borderRadius: '50%',
            }}
          />
          {/* Value placeholder */}
          <Box
            sx={{
              ...baseSkeletonStyles,
              ...animationStyles,
              width: '60%',
              height: 32,
              borderRadius: '4px',
            }}
          />
          {/* Label placeholder */}
          <Box
            sx={{
              ...baseSkeletonStyles,
              ...animationStyles,
              width: '40%',
              height: 14,
              borderRadius: '4px',
            }}
          />
        </Box>
      )

    case 'table-row':
      return (
        <>
          {Array.from({ length: count }).map((_, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                padding: 2,
                borderBottom: '1px solid rgba(65, 77, 92, 0.2)',
                ...sx,
              }}
              {...rest}
            >
              {/* Cells */}
              {[0.15, 0.2, 0.25, 0.2, 0.1].map((widthPercent, cellIndex) => (
                <Box
                  key={cellIndex}
                  sx={{
                    ...baseSkeletonStyles,
                    ...animationStyles,
                    width: `${widthPercent * 100}%`,
                    height: 20,
                    borderRadius: '4px',
                  }}
                />
              ))}
            </Box>
          ))}
        </>
      )

    case 'chart':
      return (
        <Box
          sx={{
            ...baseSkeletonStyles,
            width: width || '100%',
            height: height || 300,
            background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.6) 0%, rgba(35, 42, 49, 0.6) 100%)',
            border: '1px solid rgba(65, 77, 92, 0.2)',
            padding: 3,
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            ...sx,
          }}
          {...rest}
        >
          {/* Title */}
          <Box
            sx={{
              ...baseSkeletonStyles,
              ...animationStyles,
              width: '30%',
              height: 20,
              borderRadius: '4px',
            }}
          />
          {/* Chart area */}
          <Box
            sx={{
              flex: 1,
              display: 'flex',
              alignItems: 'flex-end',
              gap: 1,
              paddingTop: 2,
            }}
          >
            {/* Bar chart skeleton */}
            {[0.4, 0.6, 0.8, 0.5, 0.7, 0.9, 0.6, 0.75].map((heightPercent, i) => (
              <Box
                key={i}
                sx={{
                  ...baseSkeletonStyles,
                  ...animationStyles,
                  flex: 1,
                  height: `${heightPercent * 100}%`,
                  borderRadius: '4px 4px 0 0',
                }}
              />
            ))}
          </Box>
        </Box>
      )

    case 'text':
      return (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, ...sx }} {...rest}>
          {Array.from({ length: count }).map((_, index) => (
            <Box
              key={index}
              sx={{
                ...baseSkeletonStyles,
                ...animationStyles,
                width: index === count - 1 ? '60%' : '100%',
                height: height || 16,
                borderRadius: '4px',
              }}
            />
          ))}
        </Box>
      )

    case 'avatar':
      return (
        <Box
          sx={{
            ...baseSkeletonStyles,
            ...animationStyles,
            width: width || 48,
            height: height || 48,
            borderRadius: '50%',
            ...sx,
          }}
          {...rest}
        />
      )

    case 'button':
      return (
        <Box
          sx={{
            ...baseSkeletonStyles,
            ...animationStyles,
            width: width || 120,
            height: height || 40,
            borderRadius: '8px',
            ...sx,
          }}
          {...rest}
        />
      )

    default:
      return (
        <Box
          sx={{
            ...baseSkeletonStyles,
            ...animationStyles,
            width: width || '100%',
            height: height || 100,
            ...sx,
          }}
          {...rest}
        />
      )
  }
}

/**
 * Skeleton group for common layout patterns
 */
export const SkeletonGroup: React.FC<{
  variant: 'metric-cards' | 'table' | 'dashboard'
  count?: number
}> = ({ variant, count = 4 }) => {
  switch (variant) {
    case 'metric-cards':
      return (
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
          {Array.from({ length: count }).map((_, i) => (
            <Box key={i} sx={{ flex: '1 1 200px', minWidth: 200 }}>
              <SkeletonLoader variant="metric-card" />
            </Box>
          ))}
        </Box>
      )

    case 'table':
      return (
        <Box
          sx={{
            background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.6) 0%, rgba(35, 42, 49, 0.6) 100%)',
            border: '1px solid rgba(65, 77, 92, 0.2)',
            borderRadius: '12px',
            overflow: 'hidden',
          }}
        >
          {/* Table header */}
          <Box
            sx={{
              display: 'flex',
              gap: 2,
              padding: 2,
              backgroundColor: 'rgba(35, 42, 49, 0.5)',
              borderBottom: '1px solid rgba(65, 77, 92, 0.3)',
            }}
          >
            {[0.15, 0.2, 0.25, 0.2, 0.1].map((w, i) => (
              <Box
                key={i}
                sx={{
                  ...baseSkeletonStyles,
                  ...shimmerAnimation,
                  width: `${w * 100}%`,
                  height: 14,
                  borderRadius: '4px',
                }}
              />
            ))}
          </Box>
          {/* Table rows */}
          <SkeletonLoader variant="table-row" count={count} />
        </Box>
      )

    case 'dashboard':
      return (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {/* Hero metrics */}
          <SkeletonGroup variant="metric-cards" count={4} />
          {/* Content sections */}
          <Box sx={{ display: 'flex', gap: 3 }}>
            <Box sx={{ flex: 2 }}>
              <SkeletonLoader variant="chart" />
            </Box>
            <Box sx={{ flex: 1 }}>
              <SkeletonLoader variant="card" height={300} />
            </Box>
          </Box>
        </Box>
      )

    default:
      return null
  }
}

export default SkeletonLoader
