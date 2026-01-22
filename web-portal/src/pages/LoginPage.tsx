import { useState, FormEvent } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  Box,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton,
} from '@mui/material'
import {
  Visibility,
  VisibilityOff,
  SmartToy as AIIcon,
  Email as EmailIcon,
  Lock as LockIcon,
} from '@mui/icons-material'
import { useAuth } from '../contexts/AuthContext'
import GlassCard from '../components/common/GlassCard'
import GlassButton from '../components/common/GlassButton'
import { fsiColors } from '../theme'

export const LoginPage = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const from = (location.state as { from?: string })?.from || '/dashboard'

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      await signIn(username, password)
      navigate(from, { replace: true })
    } catch (err) {
      console.error('Login error:', err)
      if (err instanceof Error) {
        if (err.message.includes('User does not exist')) {
          setError('User not found. Please check your email address.')
        } else if (err.message.includes('Incorrect username or password')) {
          setError('Invalid email or password. Please try again.')
        } else if (err.message.includes('Password change required')) {
          setError(err.message)
        } else if (err.message.includes('not configured')) {
          setError('Authentication service not configured. Please contact support.')
        } else {
          setError(err.message || 'Login failed. Please try again.')
        }
      } else {
        setError('Login failed. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Box
      sx={{
        width: '100%',
        maxWidth: 440,
        mx: 'auto',
        px: 2,
      }}
    >
      <GlassCard
        variant="elevated"
        sx={{
          p: 4,
          textAlign: 'center',
        }}
      >
        {/* Logo and Branding */}
        <Box
          sx={{
            width: 64,
            height: 64,
            borderRadius: 3,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: `linear-gradient(135deg, ${fsiColors.orange.main} 0%, ${fsiColors.orange.dark} 100%)`,
            boxShadow: `0 8px 24px ${fsiColors.orange.glow}`,
            mx: 'auto',
            mb: 3,
          }}
        >
          <AIIcon sx={{ color: '#fff', fontSize: 36 }} />
        </Box>

        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            color: fsiColors.text.primary,
            mb: 1,
            letterSpacing: '-0.02em',
          }}
        >
          Welcome Back
        </Typography>

        <Typography
          variant="body2"
          sx={{
            color: fsiColors.text.secondary,
            mb: 4,
          }}
        >
          Sign in to AWS FSI Trade Matching System
        </Typography>

        {/* Error Alert */}
        {error && (
          <Alert
            severity="error"
            onClose={() => setError(null)}
            sx={{
              mb: 3,
              bgcolor: `${fsiColors.status.error}15`,
              color: fsiColors.status.error,
              border: `1px solid ${fsiColors.status.error}40`,
              '& .MuiAlert-icon': {
                color: fsiColors.status.error,
              },
            }}
          >
            {error}
          </Alert>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Email Address"
            type="email"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={isLoading}
            autoComplete="username"
            sx={{
              mb: 2.5,
              '& .MuiOutlinedInput-root': {
                bgcolor: `${fsiColors.navy[800]}80`,
                '& fieldset': {
                  borderColor: `${fsiColors.navy[400]}40`,
                },
                '&:hover fieldset': {
                  borderColor: `${fsiColors.orange.main}50`,
                },
                '&.Mui-focused fieldset': {
                  borderColor: fsiColors.orange.main,
                },
              },
              '& .MuiInputLabel-root': {
                color: fsiColors.text.secondary,
                '&.Mui-focused': {
                  color: fsiColors.orange.main,
                },
              },
              '& .MuiOutlinedInput-input': {
                color: fsiColors.text.primary,
              },
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <EmailIcon sx={{ color: fsiColors.text.muted }} />
                </InputAdornment>
              ),
            }}
          />

          <TextField
            fullWidth
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isLoading}
            autoComplete="current-password"
            sx={{
              mb: 3,
              '& .MuiOutlinedInput-root': {
                bgcolor: `${fsiColors.navy[800]}80`,
                '& fieldset': {
                  borderColor: `${fsiColors.navy[400]}40`,
                },
                '&:hover fieldset': {
                  borderColor: `${fsiColors.orange.main}50`,
                },
                '&.Mui-focused fieldset': {
                  borderColor: fsiColors.orange.main,
                },
              },
              '& .MuiInputLabel-root': {
                color: fsiColors.text.secondary,
                '&.Mui-focused': {
                  color: fsiColors.orange.main,
                },
              },
              '& .MuiOutlinedInput-input': {
                color: fsiColors.text.primary,
              },
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <LockIcon sx={{ color: fsiColors.text.muted }} />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                    sx={{ color: fsiColors.text.muted }}
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <GlassButton
            type="submit"
            variant="contained"
            fullWidth
            disabled={!username || !password || isLoading}
            sx={{ py: 1.5 }}
          >
            {isLoading ? (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CircularProgress size={20} sx={{ color: '#fff' }} />
                <span>Signing in...</span>
              </Box>
            ) : (
              'Sign In'
            )}
          </GlassButton>
        </form>

        {/* Footer */}
        <Box sx={{ mt: 4, pt: 3, borderTop: `1px solid ${fsiColors.navy[400]}20` }}>
          <Typography
            variant="caption"
            sx={{
              color: fsiColors.text.muted,
              display: 'block',
            }}
          >
            Powered by Amazon Bedrock
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: fsiColors.text.muted,
              fontSize: '0.7rem',
            }}
          >
            AWS Financial Services Industry
          </Typography>
        </Box>
      </GlassCard>
    </Box>
  )
}
