import React from 'react'
import { Box, IconButton, Typography, Tooltip } from '@mui/material'
import {
  ContentCopy as CopyIcon,
  Check as CheckIcon,
} from '@mui/icons-material'
import { useCopyToClipboard } from '../../hooks/useCopyToClipboard'
import { useToast } from '../../hooks/useToast'
import { glowColors } from '../../theme'

export interface CopyToClipboardProps {
  /** The text to copy */
  text: string
  /** Display label (optional, shows before the text) */
  label?: string
  /** Whether to truncate the displayed text */
  truncate?: boolean
  /** Maximum characters to show when truncated */
  maxLength?: number
  /** Show toast notification on copy */
  showToast?: boolean
  /** Custom toast message */
  toastMessage?: string
  /** Size of the component */
  size?: 'small' | 'medium'
  /** Show only the copy icon (no text display) */
  iconOnly?: boolean
  /** Custom styles */
  sx?: object
}

/**
 * CopyToClipboard Component
 *
 * Displays text with a copy button that copies to clipboard.
 * Shows a checkmark animation and optional toast notification on success.
 *
 * @example
 * <CopyToClipboard
 *   text={sessionId}
 *   label="Session ID"
 *   truncate
 *   showToast
 * />
 */
export const CopyToClipboard: React.FC<CopyToClipboardProps> = ({
  text,
  label,
  truncate = false,
  maxLength = 20,
  showToast = true,
  toastMessage,
  size = 'medium',
  iconOnly = false,
  sx,
}) => {
  const { copied, copy } = useCopyToClipboard(2000)
  const { success: toastSuccess } = useToast()

  const handleCopy = async () => {
    const result = await copy(text)
    if (result && showToast) {
      toastSuccess(toastMessage || `${label || 'Text'} copied to clipboard`)
    }
  }

  const displayText = truncate && text.length > maxLength
    ? `${text.substring(0, maxLength)}...`
    : text

  const iconSize = size === 'small' ? 14 : 16
  const buttonSize = size === 'small' ? 24 : 28

  if (iconOnly) {
    return (
      <Tooltip title={copied ? 'Copied!' : 'Copy'}>
        <IconButton
          onClick={handleCopy}
          size="small"
          sx={{
            width: buttonSize,
            height: buttonSize,
            transition: 'all 0.15s ease-out',
            '&:hover': {
              backgroundColor: 'rgba(255, 153, 0, 0.1)',
            },
            ...sx,
          }}
        >
          {copied ? (
            <CheckIcon
              sx={{
                fontSize: iconSize,
                color: glowColors.success,
                animation: 'scaleIn 0.2s ease-out',
                '@keyframes scaleIn': {
                  '0%': { transform: 'scale(0.5)', opacity: 0 },
                  '100%': { transform: 'scale(1)', opacity: 1 },
                },
              }}
            />
          ) : (
            <CopyIcon sx={{ fontSize: iconSize, color: 'text.secondary' }} />
          )}
        </IconButton>
      </Tooltip>
    )
  }

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        ...sx,
      }}
    >
      {label && (
        <Typography
          variant={size === 'small' ? 'caption' : 'body2'}
          sx={{
            color: 'text.secondary',
            fontWeight: 500,
            flexShrink: 0,
          }}
        >
          {label}:
        </Typography>
      )}

      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 0.5,
          backgroundColor: 'rgba(20, 25, 30, 0.5)',
          backdropFilter: 'blur(4px)',
          borderRadius: '6px',
          border: '1px solid rgba(65, 77, 92, 0.3)',
          padding: size === 'small' ? '4px 8px' : '6px 10px',
          transition: 'all 0.15s ease-out',
          cursor: 'pointer',
          '&:hover': {
            borderColor: 'rgba(255, 153, 0, 0.3)',
            backgroundColor: 'rgba(255, 153, 0, 0.05)',
          },
        }}
        onClick={handleCopy}
      >
        <Tooltip title={text} placement="top" arrow>
          <Typography
            variant={size === 'small' ? 'caption' : 'body2'}
            sx={{
              fontFamily: 'monospace',
              color: '#FFFFFF',
              userSelect: 'none',
            }}
          >
            {displayText}
          </Typography>
        </Tooltip>

        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: iconSize + 4,
            height: iconSize + 4,
          }}
        >
          {copied ? (
            <CheckIcon
              sx={{
                fontSize: iconSize,
                color: glowColors.success,
                animation: 'scaleIn 0.2s ease-out',
                '@keyframes scaleIn': {
                  '0%': { transform: 'scale(0.5)', opacity: 0 },
                  '100%': { transform: 'scale(1)', opacity: 1 },
                },
              }}
            />
          ) : (
            <CopyIcon
              sx={{
                fontSize: iconSize,
                color: 'text.secondary',
                transition: 'color 0.15s ease-out',
              }}
            />
          )}
        </Box>
      </Box>
    </Box>
  )
}

export default CopyToClipboard
