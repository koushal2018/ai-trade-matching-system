import { Box, Typography } from '@mui/material'

export default function TradeMatchingUpload() {
  return (
    <Box
      sx={{
        animation: 'fadeIn 0.6s ease-out',
        '@keyframes fadeIn': {
          '0%': { opacity: 0, transform: 'translateY(20px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
      }}
    >
      <Typography 
        variant="h4" 
        gutterBottom 
        sx={{ 
          fontWeight: 700,
          background: 'linear-gradient(135deg, #FF9900 0%, #146EB4 100%)',
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          mb: 4
        }}
      >
        Trade Matching Upload
      </Typography>

      <Typography variant="body1" color="text.secondary">
        Upload trade confirmation PDFs from both bank and counterparty sides for automated matching.
      </Typography>
    </Box>
  )
}
