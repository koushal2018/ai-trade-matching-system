import { useState } from 'react'
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  TextField,
  Box,
  Chip,
  Paper,
  Divider,
} from '@mui/material'
import { Check as ApproveIcon, Close as RejectIcon } from '@mui/icons-material'
import type { HITLReview } from '../../types'

interface TradeComparisonCardProps {
  review: HITLReview
  onApprove: (reason?: string) => void
  onReject: (reason?: string) => void
  isSubmitting: boolean
}

export default function TradeComparisonCard({
  review,
  onApprove,
  onReject,
  isSubmitting,
}: TradeComparisonCardProps) {
  const [reason, setReason] = useState('')

  const tradeFields = [
    { key: 'Trade_ID', label: 'Trade ID' },
    { key: 'trade_date', label: 'Trade Date' },
    { key: 'notional', label: 'Notional' },
    { key: 'currency', label: 'Currency' },
    { key: 'counterparty', label: 'Counterparty' },
    { key: 'product_type', label: 'Product Type' },
    { key: 'effective_date', label: 'Effective Date' },
    { key: 'maturity_date', label: 'Maturity Date' },
  ]

  const hasDifference = (field: string) => field in review.differences

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">Trade Comparison</Typography>
          <Box>
            <Chip
              label={`Score: ${(review.matchScore * 100).toFixed(0)}%`}
              color={review.matchScore >= 0.7 ? 'warning' : 'error'}
              sx={{ mr: 1 }}
            />
            {review.reasonCodes.map((code) => (
              <Chip key={code} label={code} size="small" sx={{ mr: 0.5 }} />
            ))}
          </Box>
        </Box>


        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Field</TableCell>
                <TableCell>Bank Value</TableCell>
                <TableCell>Counterparty Value</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tradeFields.map(({ key, label }) => {
                const bankValue = review.bankTrade[key as keyof typeof review.bankTrade]
                const cpValue = review.counterpartyTrade[key as keyof typeof review.counterpartyTrade]
                const isDiff = hasDifference(key)
                return (
                  <TableRow key={key} sx={{ bgcolor: isDiff ? 'error.light' : 'inherit' }}>
                    <TableCell>{label}</TableCell>
                    <TableCell>{String(bankValue ?? '-')}</TableCell>
                    <TableCell>{String(cpValue ?? '-')}</TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={isDiff ? 'Mismatch' : 'Match'}
                        color={isDiff ? 'error' : 'success'}
                      />
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </TableContainer>

        <Divider sx={{ my: 3 }} />

        <Grid container spacing={2} alignItems="flex-end">
          <Grid item xs={12} md={8}>
            <TextField
              fullWidth
              label="Decision Reason (optional)"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              multiline
              rows={2}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <Box display="flex" gap={1} justifyContent="flex-end">
              <Button
                variant="contained"
                color="success"
                startIcon={<ApproveIcon />}
                onClick={() => onApprove(reason)}
                disabled={isSubmitting}
              >
                Approve
              </Button>
              <Button
                variant="contained"
                color="error"
                startIcon={<RejectIcon />}
                onClick={() => onReject(reason)}
                disabled={isSubmitting}
              >
                Reject
              </Button>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  )
}
