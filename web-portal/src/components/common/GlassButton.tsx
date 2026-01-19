import React, { forwardRef, useState, useRef } from 'react'
import { Button, ButtonProps, CircularProgress, Box } from '@mui/material'
import { Check as CheckIcon } from '@mui/icons-material'
import { glowColors } from '../../theme'

export interface GlassButtonProps extends Omit<ButtonProps, 'variant'> {
  /** Button variant */
  variant?: 'contained' | 'outlined' | 'text' | 'glass'
  /** Show loading spinner */
  loading?: boolean
  /** Show success checkmark animation */
  success?: boolean
  /** Duration to show success state before reverting (ms) */
  successDuration?: number
  /** Enable ripple effect on click */
  enableRipple?: boolean
  /** Custom glow color */
  glowColor?: string
  /** Button size */
  size?: 'small' | 'medium' | 'large'
}

/**
 * GlassButton Component
 *
 * Enhanced button with glassmorphism styling, loading states,
 * success animations, and ripple effects.
 *
 * @example
 * <GlassButton variant="glass" loading={isLoading} onClick={handleClick}>
 *   Submit
 * </GlassButton>
 */
export const GlassButton = forwardRef<HTMLButtonElement, GlassButtonProps>(
  (
    {
      variant = 'contained',
      loading = false,
      success = false,
      successDuration = 2000,
      enableRipple = true,
      glowColor = glowColors.primary,
      size = 'medium',
      children,
      disabled,
      onClick,
      sx,
      ...rest
    },
    ref
  ) => {
    const [showSuccess, setShowSuccess] = useState(false)
    const [ripples, setRipples] = useState<Array<{ x: number; y: number; id: number }>>([])
    const buttonRef = useRef<HTMLButtonElement>(null)
    const rippleId = useRef(0)

    // Handle success state
    React.useEffect(() => {
      if (success) {
        setShowSuccess(true)
        const timer = setTimeout(() => {
          setShowSuccess(false)
        }, successDuration)
        return () => clearTimeout(timer)
      }
    }, [success, successDuration])

    // Handle ripple effect
    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      if (enableRipple && buttonRef.current) {
        const rect = buttonRef.current.getBoundingClientRect()
        const x = e.clientX - rect.left
        const y = e.clientY - rect.top
        const newRipple = { x, y, id: rippleId.current++ }
        setRipples((prev) => [...prev, newRipple])

        // Remove ripple after animation
        setTimeout(() => {
          setRipples((prev) => prev.filter((r) => r.id !== newRipple.id))
        }, 600)
      }

      if (onClick && !loading && !disabled) {
        onClick(e)
      }
    }

    const isDisabled = disabled || loading

    // Size configurations
    const sizeStyles = {
      small: { py: 0.75, px: 2, fontSize: '0.8125rem' },
      medium: { py: 1, px: 2.5, fontSize: '0.875rem' },
      large: { py: 1.5, px: 3, fontSize: '1rem' },
    }

    // Glass variant styles
    const glassVariantStyles =
      variant === 'glass'
        ? {
            background: 'linear-gradient(135deg, rgba(28, 33, 39, 0.8) 0%, rgba(35, 42, 49, 0.8) 100%)',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
            border: `1px solid rgba(65, 77, 92, 0.4)`,
            color: '#FFFFFF',
            '&:hover': {
              background: 'linear-gradient(135deg, rgba(35, 42, 49, 0.9) 0%, rgba(45, 52, 59, 0.9) 100%)',
              borderColor: `${glowColor}50`,
              boxShadow: `0 4px 16px ${glowColor}25`,
              transform: 'translateY(-1px) scale(1.02)',
            },
            '&:active': {
              transform: 'translateY(0) scale(0.98)',
            },
          }
        : {}

    return (
      <Button
        ref={(node) => {
          // Handle both refs
          ;(buttonRef as React.MutableRefObject<HTMLButtonElement | null>).current = node
          if (typeof ref === 'function') {
            ref(node)
          } else if (ref) {
            ref.current = node
          }
        }}
        variant={variant === 'glass' ? 'contained' : variant}
        disabled={isDisabled}
        onClick={handleClick}
        sx={{
          position: 'relative',
          overflow: 'hidden',
          ...sizeStyles[size],
          ...glassVariantStyles,
          '&.Mui-disabled': {
            opacity: 0.6,
          },
          ...sx,
        }}
        {...rest}
      >
        {/* Ripple effects */}
        {ripples.map((ripple) => (
          <Box
            key={ripple.id}
            sx={{
              position: 'absolute',
              left: ripple.x,
              top: ripple.y,
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: 'rgba(255, 255, 255, 0.4)',
              transform: 'translate(-50%, -50%)',
              animation: 'buttonRipple 0.6s ease-out',
              pointerEvents: 'none',
              '@keyframes buttonRipple': {
                '0%': {
                  transform: 'translate(-50%, -50%) scale(0)',
                  opacity: 0.6,
                },
                '100%': {
                  transform: 'translate(-50%, -50%) scale(20)',
                  opacity: 0,
                },
              },
            }}
          />
        ))}

        {/* Content */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 1,
            opacity: loading || showSuccess ? 0 : 1,
            transition: 'opacity 0.2s ease',
          }}
        >
          {children}
        </Box>

        {/* Loading spinner */}
        {loading && (
          <Box
            sx={{
              position: 'absolute',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CircularProgress
              size={size === 'small' ? 16 : size === 'large' ? 24 : 20}
              sx={{ color: 'inherit' }}
            />
          </Box>
        )}

        {/* Success checkmark */}
        {showSuccess && !loading && (
          <Box
            sx={{
              position: 'absolute',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              animation: 'scaleIn 0.3s ease-out',
              '@keyframes scaleIn': {
                '0%': {
                  opacity: 0,
                  transform: 'scale(0.5)',
                },
                '100%': {
                  opacity: 1,
                  transform: 'scale(1)',
                },
              },
            }}
          >
            <CheckIcon
              sx={{
                fontSize: size === 'small' ? 16 : size === 'large' ? 24 : 20,
                color: glowColors.success,
              }}
            />
          </Box>
        )}
      </Button>
    )
  }
)

GlassButton.displayName = 'GlassButton'

export default GlassButton
