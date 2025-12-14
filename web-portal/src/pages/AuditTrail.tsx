import { useState } from 'react'
import {
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  MenuItem,
  Button,
  Box,
} from '@mui/material'
import { DataGrid, GridColDef, GridPaginationModel } from '@mui/x-data-grid'
import { Download as DownloadIcon } from '@mui/icons-material'
import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { auditService, AuditQueryParams } from '../services/auditService'
import type { AuditActionType, AuditRecord } from '../types'

const actionTypes: AuditActionType[] = [
  'PDF_PROCESSED',
  'TRADE_EXTRACTED',
  'TRADE_MATCHED',
  'EXCEPTION_RAISED',
  'HITL_DECISION',
  'AGENT_STARTED',
  'AGENT_STOPPED',
]

const columns: GridColDef<AuditRecord>[] = [
  {
    field: 'timestamp',
    headerName: 'Timestamp',
    width: 180,
    valueFormatter: (value: string) => format(new Date(value), 'yyyy-MM-dd HH:mm:ss'),
  },
  { field: 'agentName', headerName: 'Agent', width: 150 },
  { field: 'actionType', headerName: 'Action', width: 150 },
  { field: 'tradeId', headerName: 'Trade ID', width: 130 },
  {
    field: 'outcome',
    headerName: 'Outcome',
    width: 100,
    renderCell: (params) => (
      <Box
        sx={{
          color: params.value === 'SUCCESS' ? 'success.main' : params.value === 'FAILURE' ? 'error.main' : 'warning.main',
          fontWeight: 'bold',
        }}
      >
        {params.value}
      </Box>
    ),
  },
  {
    field: 'immutableHash',
    headerName: 'Hash',
    width: 200,
    valueFormatter: (value: string) => value?.substring(0, 16) + '...',
  },
]


export default function AuditTrail() {
  const [filters, setFilters] = useState<AuditQueryParams>({
    page: 0,
    pageSize: 25,
  })
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 25,
  })

  const { data, isLoading } = useQuery({
    queryKey: ['auditRecords', filters],
    queryFn: () => auditService.getAuditRecords(filters),
  })

  const handleFilterChange = (field: keyof AuditQueryParams, value: string) => {
    setFilters((prev) => ({ ...prev, [field]: value || undefined }))
  }

  const handlePaginationChange = (model: GridPaginationModel) => {
    setPaginationModel(model)
    setFilters((prev) => ({ ...prev, page: model.page, pageSize: model.pageSize }))
  }

  const handleExport = async (format: 'json' | 'csv' | 'xml') => {
    const blob = await auditService.exportAuditRecords(filters, format)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit_trail_${new Date().toISOString()}.${format}`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <>
      <Typography variant="h4" gutterBottom>
        Audit Trail
      </Typography>
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={2}>
              <TextField
                fullWidth
                type="date"
                label="Start Date"
                InputLabelProps={{ shrink: true }}
                onChange={(e) => handleFilterChange('startDate', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <TextField
                fullWidth
                type="date"
                label="End Date"
                InputLabelProps={{ shrink: true }}
                onChange={(e) => handleFilterChange('endDate', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <TextField
                fullWidth
                label="Agent ID"
                onChange={(e) => handleFilterChange('agentId', e.target.value)}
              />
            </Grid>

            <Grid item xs={12} sm={6} md={2}>
              <TextField
                fullWidth
                select
                label="Action Type"
                defaultValue=""
                onChange={(e) => handleFilterChange('actionType', e.target.value as AuditActionType)}
              >
                <MenuItem value="">All</MenuItem>
                {actionTypes.map((type) => (
                  <MenuItem key={type} value={type}>
                    {type}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={12} md={4}>
              <Box display="flex" gap={1} justifyContent="flex-end">
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={() => handleExport('csv')}
                >
                  CSV
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={() => handleExport('json')}
                >
                  JSON
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={() => handleExport('xml')}
                >
                  XML
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
      <Card>
        <DataGrid
          rows={data?.records || []}
          columns={columns}
          loading={isLoading}
          getRowId={(row) => row.auditId}
          paginationModel={paginationModel}
          onPaginationModelChange={handlePaginationChange}
          pageSizeOptions={[10, 25, 50, 100]}
          rowCount={data?.total || 0}
          paginationMode="server"
          autoHeight
          disableRowSelectionOnClick
        />
      </Card>
    </>
  )
}
