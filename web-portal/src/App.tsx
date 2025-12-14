import { Routes, Route, Navigate } from 'react-router-dom'
import { Box } from '@mui/material'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import HITLPanel from './pages/HITLPanel'
import AuditTrail from './pages/AuditTrail'

function App() {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/hitl" element={<HITLPanel />} />
          <Route path="/audit" element={<AuditTrail />} />
        </Routes>
      </Layout>
    </Box>
  )
}

export default App
