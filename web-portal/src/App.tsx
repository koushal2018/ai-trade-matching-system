import { useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import {
  AppLayout,
  TopNavigation,
  SideNavigation,
  Flashbar,
  HelpPanel,
  Box,
  Link,
} from '@cloudscape-design/components'
import type {
  SideNavigationProps,
  TopNavigationProps,
} from '@cloudscape-design/components'
import { useNavigate, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import HITLPanel from './pages/HITLPanel'
import AuditTrail from './pages/AuditTrail'
import TradeMatchingUpload from './pages/TradeMatchingUpload'
import { useNotifications } from './hooks/useNotifications'
import { navigationItems } from './config/navigation'

// Help content based on current page
const getHelpContent = (pathname: string) => {
  switch (pathname) {
    case '/upload':
      return {
        header: 'Upload Trade Confirmations',
        content: (
          <>
            <Box variant="p">
              Upload trade confirmation PDFs from both bank and counterparty sides. The system
              will automatically process and match the trade details using AI agents.
            </Box>
            <Box variant="h4" padding={{ top: 'm' }}>
              File Requirements
            </Box>
            <Box variant="p">
              <ul>
                <li>File format: PDF only</li>
                <li>Maximum file size: 10 MB</li>
                <li>Both bank and counterparty confirmations required</li>
              </ul>
            </Box>
            <Box variant="h4" padding={{ top: 'm' }}>
              Processing Workflow
            </Box>
            <Box variant="p">
              Once uploaded, the system will:
              <ol>
                <li>Extract text from PDFs using AI</li>
                <li>Extract structured trade data</li>
                <li>Match trades between bank and counterparty</li>
                <li>Flag any exceptions for review</li>
              </ol>
            </Box>
            <Box variant="p" padding={{ top: 'm' }}>
              <Link external href="/docs/upload-guide">
                Learn more about uploading trade confirmations
              </Link>
            </Box>
          </>
        ),
      }
    case '/audit':
      return {
        header: 'Audit Trail',
        content: (
          <>
            <Box variant="p">
              View the complete history of trade matching operations, including uploads,
              processing steps, match results, and user actions.
            </Box>
            <Box variant="h4" padding={{ top: 'm' }}>
              Filtering and Search
            </Box>
            <Box variant="p">
              Use the property filter to narrow down audit entries by:
              <ul>
                <li>Date range</li>
                <li>Action type (Upload, Match, Exception)</li>
                <li>Status (Success, Failed, Pending)</li>
                <li>User</li>
                <li>Session ID</li>
              </ul>
            </Box>
            <Box variant="h4" padding={{ top: 'm' }}>
              Exporting Data
            </Box>
            <Box variant="p">
              Click the "Export CSV" button to download audit entries for external analysis or
              compliance reporting.
            </Box>
            <Box variant="p" padding={{ top: 'm' }}>
              <Link external href="/docs/audit-trail">
                Learn more about the audit trail
              </Link>
            </Box>
          </>
        ),
      }
    case '/dashboard':
      return {
        header: 'Dashboard Overview',
        content: (
          <>
            <Box variant="p">
              Monitor real-time agent processing status, view recent matching results, and track
              system health metrics.
            </Box>
            <Box variant="h4" padding={{ top: 'm' }}>
              Agent Status
            </Box>
            <Box variant="p">
              The dashboard displays the current status of all AI agents:
              <ul>
                <li>PDF Adapter Agent - Text extraction from PDFs</li>
                <li>Trade Extraction Agent - Structured data extraction</li>
                <li>Trade Matching Agent - Fuzzy matching with confidence scoring</li>
                <li>Exception Management Agent - Error triage and routing</li>
              </ul>
            </Box>
            <Box variant="h4" padding={{ top: 'm' }}>
              Real-time Updates
            </Box>
            <Box variant="p">
              The dashboard automatically refreshes every 30 seconds to show the latest processing
              status and metrics.
            </Box>
            <Box variant="p" padding={{ top: 'm' }}>
              <Link external href="/docs/dashboard">
                Learn more about the dashboard
              </Link>
            </Box>
          </>
        ),
      }
    default:
      return {
        header: 'OTC Trade Matching System',
        content: (
          <>
            <Box variant="p">
              AI-powered trade reconciliation platform for matching OTC derivative trade
              confirmations between financial institutions and counterparties.
            </Box>
            <Box variant="h4" padding={{ top: 'm' }}>
              Getting Started
            </Box>
            <Box variant="p">
              <ol>
                <li>Navigate to Upload Confirmations</li>
                <li>Upload bank and counterparty PDFs</li>
                <li>Monitor agent processing status</li>
                <li>Review matching results</li>
                <li>Handle exceptions if needed</li>
              </ol>
            </Box>
            <Box variant="p" padding={{ top: 'm' }}>
              <Link external href="/docs/getting-started">
                View complete documentation
              </Link>
            </Box>
          </>
        ),
      }
  }
}

function App() {
  const [navigationOpen, setNavigationOpen] = useState(true)
  const [toolsOpen, setToolsOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { notifications, dismissNotification } = useNotifications()

  const handleNavigationChange = ({ detail }: { detail: { open: boolean } }) => {
    setNavigationOpen(detail.open)
  }

  const handleToolsChange = ({ detail }: { detail: { open: boolean } }) => {
    setToolsOpen(detail.open)
  }

  const handleNavigationFollow = (event: CustomEvent<SideNavigationProps.FollowDetail>) => {
    event.preventDefault()
    navigate(event.detail.href)
  }

  const helpContent = getHelpContent(location.pathname)

  const topNavigationUtilities: TopNavigationProps.Utility[] = [
    {
      type: 'button',
      iconName: 'notification',
      ariaLabel: 'Notifications',
      badge: notifications.length > 0,
    },
    {
      type: 'button',
      iconName: 'status-info',
      ariaLabel: 'Help',
      onClick: () => setToolsOpen(!toolsOpen),
    },
    {
      type: 'menu-dropdown',
      text: 'Settings',
      iconName: 'settings',
      items: [
        { id: 'preferences', text: 'Preferences' },
        { id: 'theme', text: 'Theme' },
      ],
    },
    {
      type: 'menu-dropdown',
      text: 'User',
      iconName: 'user-profile',
      items: [
        { id: 'profile', text: 'Profile' },
        { id: 'preferences', text: 'Preferences' },
        { id: 'signout', text: 'Sign out' },
      ],
    },
  ]

  return (
    <>
      <TopNavigation
        identity={{
          title: 'OTC Trade Matching System',
          href: '/',
          logo: {
            src: '/logo.svg',
            alt: 'Trade Matching',
          },
        }}
        utilities={topNavigationUtilities}
      />
      <AppLayout
        navigation={
          <SideNavigation
            activeHref={location.pathname}
            items={navigationItems}
            onFollow={handleNavigationFollow}
          />
        }
        navigationOpen={navigationOpen}
        onNavigationChange={handleNavigationChange}
        notifications={
          <Flashbar
            items={notifications.map((notification) => ({
              ...notification,
              onDismiss: () => dismissNotification(notification.id!),
            }))}
          />
        }
        tools={
          <HelpPanel header={<Box variant="h2">{helpContent.header}</Box>}>
            {helpContent.content}
          </HelpPanel>
        }
        toolsOpen={toolsOpen}
        onToolsChange={handleToolsChange}
        content={
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/upload" element={<TradeMatchingUpload />} />
            <Route path="/hitl" element={<HITLPanel />} />
            <Route path="/audit" element={<AuditTrail />} />
          </Routes>
        }
      />
    </>
  )
}

export default App
