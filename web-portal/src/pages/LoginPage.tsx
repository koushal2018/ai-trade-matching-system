import { useState, FormEvent } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  Container,
  Header,
  FormField,
  Input,
  Button,
  SpaceBetween,
  Alert,
  Box,
} from '@cloudscape-design/components'
import { useAuth } from '../contexts/AuthContext'

export const LoginPage = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
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
      // Show more specific error message
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
      padding={{ vertical: 'xxxl', horizontal: 'l' }}
    >
      <Container
        header={
          <Header variant="h1" description="Sign in to access the OTC Trade Matching System">
            Sign In
          </Header>
        }
      >
        <form onSubmit={handleSubmit}>
          <SpaceBetween size="l">
            {error && (
              <Alert type="error" dismissible onDismiss={() => setError(null)}>
                {error}
              </Alert>
            )}

            <FormField label="Username" stretch>
              <Input
                value={username}
                onChange={({ detail }) => setUsername(detail.value)}
                placeholder="Enter your username"
                type="text"
                autoComplete="username"
                disabled={isLoading}
              />
            </FormField>

            <FormField label="Password" stretch>
              <Input
                value={password}
                onChange={({ detail }) => setPassword(detail.value)}
                placeholder="Enter your password"
                type="password"
                autoComplete="current-password"
                disabled={isLoading}
              />
            </FormField>

            <Button
              variant="primary"
              formAction="submit"
              loading={isLoading}
              disabled={!username || !password}
              fullWidth
            >
              Sign In
            </Button>
          </SpaceBetween>
        </form>
      </Container>
    </Box>
  )
}
