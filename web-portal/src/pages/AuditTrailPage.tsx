import { useState } from 'react'
import {
  Box,
  Typography,
  Container,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  InputAdornment,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  Skeleton,
  alpha,
} from '@mui/material'
import {
  History as HistoryIcon,
  Download as ExportIcon,
  Search as SearchIcon,
  Visibility as ViewIcon,
  Close as CloseIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  Info as InfoIcon,
} from '@mui/icons-material'
import { useQuery } from '@tanstack/react-query'
import { auditService } from '../services/auditService'
import GlassButton from '../components/common/GlassButton'
import GlassCard from '../components/common/GlassCard'
import CopyToClipboard from '../components/common/CopyToClipboard'
import { useToast } from '../hooks/useToast'
import { fsiColors } from '../theme'
import type { AuditRecord, AuditActionType } from '../types'

const getActionChipColor = (action: AuditActionType) => {
  switch (action) {
    case 'Upload':
    case 'Invoke':
      return { bg: fsiColors.status.info, text: '#fff' }
    case 'Match Complete':
    case 'TRADE_MATCHED':
      return { bg: fsiColors.status.success, text: '#fff' }
    case 'Exception':
    case 'EXCEPTION_RAISED':
      return { bg: fsiColors.status.error, text: '#fff' }
    case 'Feedback':
    case 'HITL_DECISION':
      return { bg: fsiColors.accent.purple, text: '#fff' }
    default:
      return { bg: fsiColors.text.muted, text: '#fff' }
  }
}

const getStatusIcon = (outcome: string) => {
  switch (outcome) {
    case 'SUCCESS':
      return <SuccessIcon sx={{ fontSize: 18, color: fsiColors.status.success }} />
    case 'FAILURE':
      return <ErrorIcon sx={{ fontSize: 18, color: fsiColors.status.error }} />
    case 'PENDING':
      return <PendingIcon sx={{ fontSize: 18, color: fsiColors.status.warning }} />
    default:
      return <InfoIcon sx={{ fontSize: 18, color: fsiColors.status.info }} />
  }
}

const getStatusColor = (outcome: string) => {
  switch (outcome) {
    case 'SUCCESS':
      return fsiColors.status.success
    case 'FAILURE':
      return fsiColors.status.error
    case 'PENDING':
      return fsiColors.status.warning
    default:
      return fsiColors.status.info
  }
}

export default function AuditTrailPage() {
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(10)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedRecord, setSelectedRecord] = useState<AuditRecord | null>(null)
  const { success } = useToast()

  const { data, isLoading } = useQuery({
    queryKey: ['auditRecords', page, rowsPerPage],
    queryFn: () =>
      auditService.getAuditRecords({
        page,
        pageSize: rowsPerPage,
      }),
  })

  const filteredRecords = (data?.records || []).filter((record) => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      record.sessionId.toLowerCase().includes(query) ||
      record.actionType.toLowerCase().includes(query) ||
      (record.user || '').toLowerCase().includes(query) ||
      record.outcome.toLowerCase().includes(query)
    )
  })

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage)
  }

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10))
    setPage(0)
  }

  const handleExportCSV = () => {
    const headers = ['Timestamp', 'Session ID', 'Action', 'User', 'Status', 'Audit ID']
    const csvRows = [
      headers.join(','),
      ...filteredRecords.map((item) =>
        [
          new Date(item.timestamp).toISOString(),
          item.sessionId,
          item.actionType,
          item.user || item.agentName || '',
          item.outcome,
          item.auditId,
        ]
          .map((field) => `"${field}"`)
          .join(',')
      ),
    ]

    const csvContent = csvRows.join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `audit_trail_${new Date().toISOString()}.csv`
    link.click()
    URL.revokeObjectURL(url)

    success(`Exported ${filteredRecords.length} audit records to CSV`)
  }

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {/* Page Header */}
      <Box
        sx={{
          mb: 4,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: 2,
        }}
      >
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
            <Typography
              variant="overline"
              sx={{
                color: fsiColors.orange.main,
                letterSpacing: '0.15em',
                fontWeight: 600,
              }}
            >
              COMPLIANCE & HISTORY
            </Typography>
            <Chip
              icon={<HistoryIcon sx={{ fontSize: 14 }} />}
              label={`${data?.total || 0} Records`}
              size="small"
              sx={{
                height: 22,
                fontSize: '0.7rem',
                fontWeight: 600,
                bgcolor: `${fsiColors.accent.cyan}20`,
                color: fsiColors.accent.cyan,
                border: `1px solid ${fsiColors.accent.cyan}40`,
                '& .MuiChip-icon': {
                  color: fsiColors.accent.cyan,
                },
              }}
            />
          </Box>
          <Typography
            variant="h4"
            fontWeight={700}
            sx={{
              mb: 1,
              color: fsiColors.text.primary,
              letterSpacing: '-0.02em',
            }}
          >
            Audit Trail
          </Typography>
          <Typography
            variant="body2"
            sx={{ color: fsiColors.text.secondary, maxWidth: 500 }}
          >
            View and filter audit trail of all trade matching operations and agent activity
          </Typography>
        </Box>

        <GlassButton
          variant="contained"
          onClick={handleExportCSV}
          startIcon={<ExportIcon />}
        >
          Export CSV
        </GlassButton>
      </Box>

      {/* Main Content */}
      <GlassCard variant="default" sx={{ p: 0, overflow: 'hidden' }}>
        {/* Search & Filter Bar */}
        <Box
          sx={{
            p: 2,
            borderBottom: `1px solid ${fsiColors.navy[400]}20`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 2,
            flexWrap: 'wrap',
          }}
        >
          <Typography variant="h6" fontWeight={600} sx={{ color: fsiColors.text.primary }}>
            Audit Entries
          </Typography>
          <TextField
            placeholder="Search by session, action, user..."
            size="small"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            sx={{
              minWidth: 300,
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
              '& .MuiOutlinedInput-input': {
                color: fsiColors.text.primary,
              },
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ color: fsiColors.text.muted }} />
                </InputAdornment>
              ),
            }}
          />
        </Box>

        {/* Table */}
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ color: fsiColors.text.secondary, fontWeight: 600, borderColor: `${fsiColors.navy[400]}20` }}>
                  Timestamp
                </TableCell>
                <TableCell sx={{ color: fsiColors.text.secondary, fontWeight: 600, borderColor: `${fsiColors.navy[400]}20` }}>
                  Session ID
                </TableCell>
                <TableCell sx={{ color: fsiColors.text.secondary, fontWeight: 600, borderColor: `${fsiColors.navy[400]}20` }}>
                  Action
                </TableCell>
                <TableCell sx={{ color: fsiColors.text.secondary, fontWeight: 600, borderColor: `${fsiColors.navy[400]}20` }}>
                  User / Agent
                </TableCell>
                <TableCell sx={{ color: fsiColors.text.secondary, fontWeight: 600, borderColor: `${fsiColors.navy[400]}20` }}>
                  Status
                </TableCell>
                <TableCell sx={{ color: fsiColors.text.secondary, fontWeight: 600, borderColor: `${fsiColors.navy[400]}20` }} align="right">
                  Actions
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                [...Array(5)].map((_, i) => (
                  <TableRow key={i}>
                    {[...Array(6)].map((_, j) => (
                      <TableCell key={j} sx={{ borderColor: `${fsiColors.navy[400]}20` }}>
                        <Skeleton variant="text" sx={{ bgcolor: `${fsiColors.navy[600]}50` }} />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : filteredRecords.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 6, borderColor: `${fsiColors.navy[400]}20` }}>
                    <Typography variant="body1" sx={{ color: fsiColors.text.muted }}>
                      No audit entries found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredRecords.map((record) => {
                  const actionColor = getActionChipColor(record.actionType)
                  return (
                    <TableRow
                      key={record.auditId}
                      sx={{
                        '&:hover': {
                          bgcolor: alpha(fsiColors.navy[500], 0.3),
                        },
                      }}
                    >
                      <TableCell sx={{ color: fsiColors.text.primary, borderColor: `${fsiColors.navy[400]}20` }}>
                        {new Date(record.timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell sx={{ borderColor: `${fsiColors.navy[400]}20` }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography
                            variant="body2"
                            sx={{
                              color: fsiColors.orange.main,
                              fontFamily: 'monospace',
                              cursor: 'pointer',
                              '&:hover': { textDecoration: 'underline' },
                            }}
                          >
                            {record.sessionId.substring(0, 8)}...
                          </Typography>
                          <CopyToClipboard
                            text={record.sessionId}
                            label="Session ID"
                            iconOnly
                            size="small"
                          />
                        </Box>
                      </TableCell>
                      <TableCell sx={{ borderColor: `${fsiColors.navy[400]}20` }}>
                        <Chip
                          label={record.actionType}
                          size="small"
                          sx={{
                            height: 24,
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            bgcolor: `${actionColor.bg}20`,
                            color: actionColor.bg,
                            border: `1px solid ${actionColor.bg}40`,
                          }}
                        />
                      </TableCell>
                      <TableCell sx={{ color: fsiColors.text.primary, borderColor: `${fsiColors.navy[400]}20` }}>
                        {record.user || record.agentName || '—'}
                      </TableCell>
                      <TableCell sx={{ borderColor: `${fsiColors.navy[400]}20` }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getStatusIcon(record.outcome)}
                          <Typography
                            variant="body2"
                            sx={{ color: getStatusColor(record.outcome), fontWeight: 500 }}
                          >
                            {record.outcome}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right" sx={{ borderColor: `${fsiColors.navy[400]}20` }}>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => setSelectedRecord(record)}
                            sx={{
                              color: fsiColors.text.secondary,
                              '&:hover': {
                                bgcolor: alpha(fsiColors.orange.main, 0.1),
                                color: fsiColors.orange.main,
                              },
                            }}
                          >
                            <ViewIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        <TablePagination
          component="div"
          count={data?.total || 0}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={[5, 10, 25, 50]}
          sx={{
            borderTop: `1px solid ${fsiColors.navy[400]}20`,
            color: fsiColors.text.secondary,
            '& .MuiTablePagination-selectIcon': {
              color: fsiColors.text.secondary,
            },
          }}
        />
      </GlassCard>

      {/* Detail Dialog */}
      <Dialog
        open={!!selectedRecord}
        onClose={() => setSelectedRecord(null)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            bgcolor: fsiColors.navy[700],
            backgroundImage: `linear-gradient(135deg, ${fsiColors.navy[700]} 0%, ${fsiColors.navy[800]} 100%)`,
            border: `1px solid ${fsiColors.navy[400]}40`,
            borderRadius: 3,
          },
        }}
      >
        <DialogTitle
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: `1px solid ${fsiColors.navy[400]}20`,
          }}
        >
          <Typography variant="h6" fontWeight={600} sx={{ color: fsiColors.text.primary }}>
            Audit Entry Details
          </Typography>
          <IconButton onClick={() => setSelectedRecord(null)} sx={{ color: fsiColors.text.secondary }}>
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          {selectedRecord && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {/* Basic Info */}
              <Box>
                <Typography variant="subtitle2" sx={{ color: fsiColors.text.muted, mb: 1 }}>
                  BASIC INFORMATION
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                  <Box>
                    <Typography variant="caption" sx={{ color: fsiColors.text.muted }}>Audit ID</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" sx={{ color: fsiColors.text.primary, fontFamily: 'monospace' }}>
                        {selectedRecord.auditId}
                      </Typography>
                      <CopyToClipboard text={selectedRecord.auditId} iconOnly size="small" />
                    </Box>
                  </Box>
                  <Box>
                    <Typography variant="caption" sx={{ color: fsiColors.text.muted }}>Session ID</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" sx={{ color: fsiColors.orange.main, fontFamily: 'monospace' }}>
                        {selectedRecord.sessionId}
                      </Typography>
                      <CopyToClipboard text={selectedRecord.sessionId} iconOnly size="small" />
                    </Box>
                  </Box>
                  <Box>
                    <Typography variant="caption" sx={{ color: fsiColors.text.muted }}>Timestamp</Typography>
                    <Typography variant="body2" sx={{ color: fsiColors.text.primary }}>
                      {new Date(selectedRecord.timestamp).toLocaleString()}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" sx={{ color: fsiColors.text.muted }}>User / Agent</Typography>
                    <Typography variant="body2" sx={{ color: fsiColors.text.primary }}>
                      {selectedRecord.user || selectedRecord.agentName || '—'}
                    </Typography>
                  </Box>
                </Box>
              </Box>

              {/* Immutable Hash */}
              <Box>
                <Typography variant="subtitle2" sx={{ color: fsiColors.text.muted, mb: 1 }}>
                  IMMUTABLE HASH
                </Typography>
                <Box
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    bgcolor: `${fsiColors.navy[800]}80`,
                    border: `1px solid ${fsiColors.navy[400]}30`,
                  }}
                >
                  <Typography
                    variant="body2"
                    sx={{
                      color: fsiColors.text.secondary,
                      fontFamily: 'monospace',
                      wordBreak: 'break-all',
                    }}
                  >
                    {selectedRecord.immutableHash}
                  </Typography>
                </Box>
              </Box>

              {/* Match Result */}
              {selectedRecord.matchResult && (
                <Box>
                  <Typography variant="subtitle2" sx={{ color: fsiColors.text.muted, mb: 1 }}>
                    MATCH RESULTS
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Chip
                      label={selectedRecord.matchResult.matchStatus}
                      sx={{
                        bgcolor:
                          selectedRecord.matchResult.matchStatus === 'MATCHED'
                            ? `${fsiColors.status.success}20`
                            : `${fsiColors.status.error}20`,
                        color:
                          selectedRecord.matchResult.matchStatus === 'MATCHED'
                            ? fsiColors.status.success
                            : fsiColors.status.error,
                        fontWeight: 600,
                      }}
                    />
                    <Typography variant="body2" sx={{ color: fsiColors.text.primary }}>
                      Confidence: {selectedRecord.matchResult.confidenceScore}%
                    </Typography>
                  </Box>
                </Box>
              )}

              {/* Additional Details */}
              {selectedRecord.details && Object.keys(selectedRecord.details).length > 0 && (
                <Box>
                  <Typography variant="subtitle2" sx={{ color: fsiColors.text.muted, mb: 1 }}>
                    ADDITIONAL DETAILS
                  </Typography>
                  <Box
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      bgcolor: `${fsiColors.navy[800]}80`,
                      border: `1px solid ${fsiColors.navy[400]}30`,
                    }}
                  >
                    <Typography
                      component="pre"
                      variant="body2"
                      sx={{
                        color: fsiColors.text.secondary,
                        fontFamily: 'monospace',
                        fontSize: '0.75rem',
                        whiteSpace: 'pre-wrap',
                        m: 0,
                      }}
                    >
                      {JSON.stringify(selectedRecord.details, null, 2)}
                    </Typography>
                  </Box>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
      </Dialog>
    </Container>
  )
}
