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
} from '@mui/material'
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  RateReview as ReviewIcon,
  History as HistoryIcon,
  SmartToy as AIIcon,
  Upload as UploadIcon,
} from '@mui/icons-material'
import { useNavigate, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { agentService } from '../services/agentService'
import LiveIndicator, { LiveTimestamp } from './common/LiveIndicator'

const drawerWidth = 240

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { text: 'Upload', icon: <UploadIcon />, path: '/upload' },
  { text: 'HITL Reviews', icon: <ReviewIcon />, path: '/hitl' },
  { text: 'Audit Trail', icon: <HistoryIcon />, path: '/audit' },
]

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  const { data: agents } = useQuery({
    queryKey: ['agentStatus'],
    queryFn: agentService.getAgentStatus,
    refetchInterval: 5000,
  })

  const activeAgentCount = agents?.filter(agent => agent.status === 'HEALTHY').length || 0
  const hasHealthyAgents = activeAgentCount > 0

  const handleDrawerToggle = () => setMobileOpen(!mobileOpen)

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Enhanced Header */}
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Avatar
          sx={{
            width: 48,
            height: 48,
            bgcolor: 'primary.main',
            mb: 2,
            mx: 'auto',
            background: 'linear-gradient(135deg, #FF9900 0%, #E6890A 100%)',
            boxShadow: '0 4px 12px rgba(255, 153, 0, 0.3)',
          }}
        >
          <AIIcon />
        </Avatar>
        <Typography variant="h6" fontWeight={700} color="text.primary" gutterBottom>
          Trade Matching
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block" mb={1}>
          Powered by AI Agents
        </Typography>
        <LiveIndicator status={hasHealthyAgents ? 'HEALTHY' : 'OFFLINE'} size="small" />
      </Box>

      <Divider sx={{ borderColor: 'rgba(65, 77, 92, 0.3)' }} />

      {/* Navigation */}
      <List sx={{ flexGrow: 1, px: 1, py: 2 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
              sx={{
                borderRadius: 2,
                mx: 1,
                '&.Mui-selected': {
                  backgroundColor: 'rgba(255, 153, 0, 0.12)',
                  borderLeft: '3px solid #FF9900',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 153, 0, 0.16)',
                  },
                },
              }}
            >
              <ListItemIcon sx={{ color: location.pathname === item.path ? 'primary.main' : 'text.secondary' }}>
                {item.text === 'Dashboard' ? (
                  <Badge badgeContent={activeAgentCount} color="primary" max={9}>
                    {item.icon}
                  </Badge>
                ) : (
                  item.icon
                )}
              </ListItemIcon>
              <ListItemText 
                primary={item.text}
                primaryTypographyProps={{
                  fontWeight: location.pathname === item.path ? 600 : 400,
                  color: location.pathname === item.path ? 'primary.main' : 'text.primary'
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {/* Footer */}
      <Box sx={{ p: 2, borderTop: '1px solid rgba(65, 77, 92, 0.3)' }}>
        <LiveTimestamp />
      </Box>
    </Box>
  )


  return (
    <>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Box display="flex" alignItems="center" gap={2} flexGrow={1}>
            <AIIcon sx={{ color: 'primary.main' }} />
            <Typography variant="h6" noWrap component="div">
              AI Trade Matching Portal
            </Typography>
            <LiveIndicator status={hasHealthyAgents ? 'HEALTHY' : 'OFFLINE'} size="small" />
          </Box>
          <LiveTimestamp />
        </Toolbar>
      </AppBar>
      <Box component="nav" sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}>
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          mt: 8,
        }}
      >
        {children}
      </Box>
    </>
  )
}
