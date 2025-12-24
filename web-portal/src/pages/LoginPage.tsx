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
      setError('Invalid username or password. Please try again.')
      console.error('Login error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Box
      padding={{ vertical: 'xxxl', horizontal: 'l' }}
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="100vh"
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
