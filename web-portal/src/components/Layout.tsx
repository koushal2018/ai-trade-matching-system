import { useState, ReactNode } from 'react'
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Badge,
  Avatar,
  Divider,
  Menu,
  MenuItem,
  Tooltip,
  Chip,
  alpha,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  RateReview as ReviewIcon,
  History as HistoryIcon,
  SmartToy as AIIcon,
  Upload as UploadIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
  KeyboardArrowDown as ArrowDownIcon,
  Speed as MonitorIcon,
  Queue as QueueIcon,
  Warning as ExceptionsIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  HelpOutline as HelpIcon,
} from '@mui/icons-material'
import { useNavigate, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { agentService } from '../services/agentService'
import { useAuth } from '../contexts/AuthContext'
import LiveIndicator, { LiveTimestamp } from './common/LiveIndicator'
import { fsiColors, fsiGradients } from '../theme'

const drawerWidth = 280

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard', description: 'Overview & metrics' },
  { text: 'Upload Trades', icon: <UploadIcon />, path: '/upload', description: 'Upload confirmations' },
  { text: 'Matching Queue', icon: <QueueIcon />, path: '/queue', description: 'Pending matches' },
  { text: 'HITL Reviews', icon: <ReviewIcon />, path: '/hitl', description: 'Human review queue' },
  { text: 'Exceptions', icon: <ExceptionsIcon />, path: '/exceptions', description: 'Error handling' },
  { text: 'Real-time Monitor', icon: <MonitorIcon />, path: '/monitor', description: 'Live agent activity' },
  { text: 'Audit Trail', icon: <HistoryIcon />, path: '/audit', description: 'Activity history' },
]

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(null)
  const navigate = useNavigate()
  const location = useLocation()
  const { user, isAuthenticated, signOut } = useAuth()

  const { data: agents } = useQuery({
    queryKey: ['agentStatus'],
    queryFn: agentService.getAgentStatus,
    refetchInterval: 5000,
  })

  const activeAgentCount = agents?.filter(agent => agent.status === 'HEALTHY').length || 0
  const hasHealthyAgents = activeAgentCount > 0

  const handleDrawerToggle = () => setMobileOpen(!mobileOpen)
  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => setUserMenuAnchor(event.currentTarget)
  const handleUserMenuClose = () => setUserMenuAnchor(null)

  const handleSignOut = async () => {
    handleUserMenuClose()
    await signOut()
    navigate('/login')
  }

  const getUserInitials = () => {
    if (user?.username) {
      const parts = user.username.split('@')[0].split('.')
      if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase()
      }
      return user.username.substring(0, 2).toUpperCase()
    }
    return 'U'
  }

  const getDisplayName = () => {
    if (user?.username) {
      const namePart = user.username.split('@')[0]
      return namePart.split('.').map(p => p.charAt(0).toUpperCase() + p.slice(1)).join(' ')
    }
    return 'User'
  }

  const drawer = (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: fsiGradients.backgroundCard,
      }}
    >
      {/* System Status Header */}
      <Box
        sx={{
          p: 3,
          background: `linear-gradient(180deg, ${fsiColors.navy[800]} 0%, transparent 100%)`,
        }}
      >
        <Box sx={{ mb: 2 }}>
          <Typography
            variant="subtitle1"
            sx={{
              fontWeight: 700,
              color: fsiColors.text.primary,
              letterSpacing: '-0.02em',
              lineHeight: 1.2,
            }}
          >
            AI Agents
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: fsiColors.orange.main,
              fontWeight: 600,
              letterSpacing: '0.05em',
            }}
          >
            POWERED BY BEDROCK
          </Typography>
        </Box>

        {/* System Status */}
        <Box
          sx={{
            p: 1.5,
            borderRadius: 2,
            bgcolor: alpha(fsiColors.navy[600], 0.5),
            border: `1px solid ${fsiColors.navy[400]}30`,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="caption" sx={{ color: fsiColors.text.secondary }}>
              {activeAgentCount} agents active
            </Typography>
            <Chip
              size="small"
              label="Live"
              sx={{
                height: 20,
                fontSize: '0.65rem',
                fontWeight: 600,
                bgcolor: hasHealthyAgents ? `${fsiColors.status.success}20` : `${fsiColors.status.error}20`,
                color: hasHealthyAgents ? fsiColors.status.success : fsiColors.status.error,
                border: `1px solid ${hasHealthyAgents ? fsiColors.status.success : fsiColors.status.error}40`,
              }}
            />
          </Box>
        </Box>
      </Box>

      <Divider sx={{ borderColor: `${fsiColors.navy[400]}20` }} />

      {/* Navigation */}
      <Box sx={{ flexGrow: 1, py: 2, overflowY: 'auto' }}>
        <Typography
          variant="overline"
          sx={{
            px: 3,
            py: 1,
            display: 'block',
            color: fsiColors.text.muted,
            fontSize: '0.65rem',
            letterSpacing: '0.1em',
          }}
        >
          Navigation
        </Typography>
        <List sx={{ px: 1.5 }}>
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path
            return (
              <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
                <ListItemButton
                  selected={isActive}
                  onClick={() => navigate(item.path)}
                  sx={{
                    borderRadius: 2,
                    py: 1.25,
                    px: 2,
                    transition: 'all 0.2s ease',
                    '&.Mui-selected': {
                      background: `linear-gradient(90deg, ${alpha(fsiColors.orange.main, 0.15)} 0%, transparent 100%)`,
                      borderLeft: `3px solid ${fsiColors.orange.main}`,
                      '&:hover': {
                        background: `linear-gradient(90deg, ${alpha(fsiColors.orange.main, 0.2)} 0%, transparent 100%)`,
                      },
                    },
                    '&:hover': {
                      bgcolor: alpha(fsiColors.navy[500], 0.5),
                    },
                  }}
                >
                  <ListItemIcon
                    sx={{
                      minWidth: 40,
                      color: isActive ? fsiColors.orange.main : fsiColors.text.secondary,
                    }}
                  >
                    {item.text === 'Dashboard' ? (
                      <Badge
                        badgeContent={activeAgentCount}
                        color="primary"
                        max={9}
                        sx={{
                          '& .MuiBadge-badge': {
                            bgcolor: fsiColors.orange.main,
                            color: '#fff',
                            fontSize: '0.65rem',
                            minWidth: 18,
                            height: 18,
                          },
                        }}
                      >
                        {item.icon}
                      </Badge>
                    ) : (
                      item.icon
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={item.text}
                    secondary={item.description}
                    primaryTypographyProps={{
                      fontSize: '0.875rem',
                      fontWeight: isActive ? 600 : 500,
                      color: isActive ? fsiColors.orange.main : fsiColors.text.primary,
                    }}
                    secondaryTypographyProps={{
                      fontSize: '0.7rem',
                      color: fsiColors.text.muted,
                      sx: { mt: 0.25 },
                    }}
                  />
                </ListItemButton>
              </ListItem>
            )
          })}
        </List>
      </Box>

      {/* Footer with AWS Branding */}
      <Box
        sx={{
          p: 2,
          borderTop: `1px solid ${fsiColors.navy[400]}20`,
          background: `linear-gradient(180deg, transparent 0%, ${fsiColors.navy[800]} 100%)`,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
          <LiveTimestamp />
        </Box>
        <Typography
          variant="caption"
          sx={{
            color: fsiColors.text.muted,
            fontSize: '0.65rem',
            display: 'block',
            textAlign: 'center',
          }}
        >
          Powered by Amazon Bedrock
        </Typography>
      </Box>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Top AppBar */}
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          bgcolor: fsiColors.navy[900],
          borderBottom: `1px solid ${fsiColors.navy[400]}20`,
          backdropFilter: 'blur(12px)',
        }}
      >
        <Toolbar sx={{ minHeight: { xs: 64, sm: 70 } }}>
          {/* Mobile menu toggle */}
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>

          {/* Logo and Title */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexGrow: 1 }}>
            <Box
              sx={{
                display: { xs: 'none', sm: 'flex' },
                alignItems: 'center',
                gap: 1.5,
              }}
            >
              <Box
                sx={{
                  width: 36,
                  height: 36,
                  borderRadius: 1.5,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: `linear-gradient(135deg, ${fsiColors.orange.main} 0%, ${fsiColors.orange.dark} 100%)`,
                  boxShadow: `0 2px 12px ${fsiColors.orange.glow}`,
                }}
              >
                <AIIcon sx={{ color: '#fff', fontSize: 22 }} />
              </Box>
              <Box>
                <Typography
                  variant="h6"
                  sx={{
                    fontWeight: 700,
                    color: fsiColors.text.primary,
                    letterSpacing: '-0.02em',
                    lineHeight: 1.1,
                  }}
                >
                  AWS FSI - OTC Trade Matching
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    color: fsiColors.text.muted,
                    fontSize: '0.7rem',
                  }}
                >
                  Generative AI for Financial Services
                </Typography>
              </Box>
            </Box>

            {/* Center - Status indicator */}
            <Box
              sx={{
                display: { xs: 'none', md: 'flex' },
                alignItems: 'center',
                gap: 1,
                ml: 4,
                px: 2,
                py: 0.75,
                borderRadius: 2,
                bgcolor: alpha(fsiColors.navy[600], 0.5),
                border: `1px solid ${fsiColors.navy[400]}30`,
              }}
            >
              <LiveIndicator status={hasHealthyAgents ? 'HEALTHY' : 'OFFLINE'} size="small" />
              <Typography variant="caption" sx={{ color: fsiColors.text.secondary }}>
                System {hasHealthyAgents ? 'Operational' : 'Degraded'}
              </Typography>
            </Box>
          </Box>

          {/* Right side actions */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {/* Timestamp */}
            <Box sx={{ display: { xs: 'none', lg: 'block' }, mr: 1 }}>
              <LiveTimestamp />
            </Box>

            {/* Notification icon */}
            <Tooltip title="Notifications">
              <IconButton
                sx={{
                  color: fsiColors.text.secondary,
                  '&:hover': {
                    bgcolor: alpha(fsiColors.orange.main, 0.1),
                    color: fsiColors.orange.main,
                  },
                }}
              >
                <Badge badgeContent={3} color="error">
                  <NotificationsIcon />
                </Badge>
              </IconButton>
            </Tooltip>

            {/* Help icon */}
            <Tooltip title="Help">
              <IconButton
                sx={{
                  color: fsiColors.text.secondary,
                  '&:hover': {
                    bgcolor: alpha(fsiColors.orange.main, 0.1),
                    color: fsiColors.orange.main,
                  },
                }}
              >
                <HelpIcon />
              </IconButton>
            </Tooltip>

            {/* Settings icon */}
            <Tooltip title="Settings">
              <IconButton
                sx={{
                  color: fsiColors.text.secondary,
                  mr: 1,
                  '&:hover': {
                    bgcolor: alpha(fsiColors.orange.main, 0.1),
                    color: fsiColors.orange.main,
                  },
                }}
              >
                <SettingsIcon />
              </IconButton>
            </Tooltip>

            <Divider orientation="vertical" flexItem sx={{ mx: 1, borderColor: `${fsiColors.navy[400]}30` }} />

            {/* User Menu */}
            {isAuthenticated ? (
              <>
                <Tooltip title="Account">
                  <Box
                    onClick={handleUserMenuOpen}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1.5,
                      cursor: 'pointer',
                      py: 0.75,
                      px: 1.5,
                      borderRadius: 2,
                      bgcolor: alpha(fsiColors.navy[600], 0.5),
                      border: `1px solid ${fsiColors.navy[400]}30`,
                      transition: 'all 0.2s ease',
                      '&:hover': {
                        bgcolor: alpha(fsiColors.navy[500], 0.5),
                        borderColor: `${fsiColors.orange.main}40`,
                        boxShadow: `0 0 16px ${fsiColors.orange.glow}`,
                      },
                    }}
                  >
                    <Avatar
                      sx={{
                        width: 32,
                        height: 32,
                        fontSize: '0.85rem',
                        fontWeight: 700,
                        background: `linear-gradient(135deg, ${fsiColors.orange.main} 0%, ${fsiColors.orange.dark} 100%)`,
                        boxShadow: `0 2px 8px ${fsiColors.orange.glow}`,
                      }}
                    >
                      {getUserInitials()}
                    </Avatar>
                    <Box sx={{ display: { xs: 'none', lg: 'block' } }}>
                      <Typography
                        variant="body2"
                        sx={{
                          fontWeight: 600,
                          color: fsiColors.text.primary,
                          lineHeight: 1.2,
                        }}
                      >
                        {getDisplayName()}
                      </Typography>
                      <Typography
                        variant="caption"
                        sx={{
                          color: fsiColors.text.muted,
                          fontSize: '0.65rem',
                        }}
                      >
                        AWS FSI User
                      </Typography>
                    </Box>
                    <ArrowDownIcon
                      sx={{
                        fontSize: 18,
                        color: fsiColors.text.secondary,
                        transition: 'transform 0.2s ease',
                        transform: userMenuAnchor ? 'rotate(180deg)' : 'rotate(0deg)',
                      }}
                    />
                  </Box>
                </Tooltip>

                {/* User Dropdown Menu */}
                <Menu
                  anchorEl={userMenuAnchor}
                  open={Boolean(userMenuAnchor)}
                  onClose={handleUserMenuClose}
                  transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                  anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
                  PaperProps={{
                    sx: {
                      mt: 1.5,
                      minWidth: 240,
                      bgcolor: fsiColors.navy[700],
                      backgroundImage: `linear-gradient(135deg, ${fsiColors.navy[700]} 0%, ${fsiColors.navy[800]} 100%)`,
                      backdropFilter: 'blur(16px)',
                      border: `1px solid ${fsiColors.navy[400]}40`,
                      borderRadius: 2,
                      boxShadow: `0 8px 32px rgba(0, 0, 0, 0.4), 0 0 24px ${fsiColors.orange.glow}`,
                      overflow: 'visible',
                      '&::before': {
                        content: '""',
                        display: 'block',
                        position: 'absolute',
                        top: 0,
                        right: 20,
                        width: 10,
                        height: 10,
                        bgcolor: fsiColors.navy[700],
                        transform: 'translateY(-50%) rotate(45deg)',
                        border: `1px solid ${fsiColors.navy[400]}40`,
                        borderBottom: 'none',
                        borderRight: 'none',
                      },
                    },
                  }}
                >
                  {/* User Info Header */}
                  <Box sx={{ px: 2.5, py: 2, borderBottom: `1px solid ${fsiColors.navy[400]}30` }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar
                        sx={{
                          width: 48,
                          height: 48,
                          fontSize: '1.1rem',
                          fontWeight: 700,
                          background: `linear-gradient(135deg, ${fsiColors.orange.main} 0%, ${fsiColors.orange.dark} 100%)`,
                          boxShadow: `0 4px 12px ${fsiColors.orange.glow}`,
                        }}
                      >
                        {getUserInitials()}
                      </Avatar>
                      <Box>
                        <Typography variant="body1" fontWeight={600} color="text.primary">
                          {getDisplayName()}
                        </Typography>
                        <Typography variant="caption" sx={{ color: fsiColors.text.muted }}>
                          {user?.username || 'user@aws.com'}
                        </Typography>
                      </Box>
                    </Box>
                    <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                      <Chip
                        size="small"
                        label="Authenticated"
                        sx={{
                          height: 22,
                          fontSize: '0.7rem',
                          fontWeight: 600,
                          bgcolor: `${fsiColors.status.success}20`,
                          color: fsiColors.status.success,
                          border: `1px solid ${fsiColors.status.success}40`,
                        }}
                      />
                      <Chip
                        size="small"
                        label="Admin"
                        sx={{
                          height: 22,
                          fontSize: '0.7rem',
                          fontWeight: 600,
                          bgcolor: `${fsiColors.accent.purple}20`,
                          color: fsiColors.accent.purple,
                          border: `1px solid ${fsiColors.accent.purple}40`,
                        }}
                      />
                    </Box>
                  </Box>

                  {/* Menu Items */}
                  <Box sx={{ py: 1 }}>
                    <MenuItem
                      onClick={handleUserMenuClose}
                      sx={{
                        py: 1.5,
                        px: 2.5,
                        '&:hover': {
                          bgcolor: alpha(fsiColors.navy[500], 0.5),
                        },
                      }}
                    >
                      <ListItemIcon>
                        <PersonIcon sx={{ color: fsiColors.text.secondary, fontSize: 20 }} />
                      </ListItemIcon>
                      <Typography variant="body2" color="text.primary">
                        Profile Settings
                      </Typography>
                    </MenuItem>

                    <MenuItem
                      onClick={handleUserMenuClose}
                      sx={{
                        py: 1.5,
                        px: 2.5,
                        '&:hover': {
                          bgcolor: alpha(fsiColors.navy[500], 0.5),
                        },
                      }}
                    >
                      <ListItemIcon>
                        <SettingsIcon sx={{ color: fsiColors.text.secondary, fontSize: 20 }} />
                      </ListItemIcon>
                      <Typography variant="body2" color="text.primary">
                        Preferences
                      </Typography>
                    </MenuItem>
                  </Box>

                  <Divider sx={{ borderColor: `${fsiColors.navy[400]}30` }} />

                  <Box sx={{ py: 1 }}>
                    <MenuItem
                      onClick={handleSignOut}
                      sx={{
                        py: 1.5,
                        px: 2.5,
                        '&:hover': {
                          bgcolor: alpha(fsiColors.status.error, 0.1),
                        },
                      }}
                    >
                      <ListItemIcon>
                        <LogoutIcon sx={{ color: fsiColors.status.error, fontSize: 20 }} />
                      </ListItemIcon>
                      <Typography variant="body2" sx={{ color: fsiColors.status.error }}>
                        Sign Out
                      </Typography>
                    </MenuItem>
                  </Box>
                </Menu>
              </>
            ) : (
              <Box
                onClick={() => navigate('/login')}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  cursor: 'pointer',
                  py: 0.75,
                  px: 2.5,
                  borderRadius: 2,
                  background: `linear-gradient(135deg, ${fsiColors.orange.main} 0%, ${fsiColors.orange.dark} 100%)`,
                  boxShadow: `0 2px 12px ${fsiColors.orange.glow}`,
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    transform: 'translateY(-1px)',
                    boxShadow: `0 4px 20px ${fsiColors.orange.glow}`,
                  },
                  '&:active': {
                    transform: 'translateY(0)',
                  },
                }}
              >
                <PersonIcon sx={{ fontSize: 18, color: '#fff' }} />
                <Typography
                  variant="body2"
                  sx={{
                    fontWeight: 600,
                    color: '#fff',
                  }}
                >
                  Sign In
                </Typography>
              </Box>
            )}
          </Box>
        </Toolbar>
      </AppBar>

      {/* Sidebar Drawer */}
      <Box component="nav" sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}>
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              bgcolor: fsiColors.navy[800],
              borderRight: `1px solid ${fsiColors.navy[400]}20`,
            },
          }}
        >
          {drawer}
        </Drawer>

        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              bgcolor: fsiColors.navy[800],
              borderRight: `1px solid ${fsiColors.navy[400]}20`,
              mt: '70px',
              height: 'calc(100% - 70px)',
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          minHeight: '100vh',
          pt: { xs: '64px', sm: '70px' },
          bgcolor: fsiColors.navy[900],
          backgroundImage: fsiGradients.meshGradient,
          backgroundAttachment: 'fixed',
        }}
      >
        <Box sx={{ p: { xs: 2, sm: 3 } }}>{children}</Box>
      </Box>
    </Box>
  )
}
