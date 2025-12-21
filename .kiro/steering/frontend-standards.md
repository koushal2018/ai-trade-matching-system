---
inclusion: fileMatch
fileMatchPattern: "web-portal/**/*.{ts,tsx}"
---

# Frontend Development Standards

## Technology Stack
- React 18 with TypeScript
- Material-UI (MUI) v5 for components
- TanStack Query (React Query) for data fetching
- Vite for build tooling
- Recharts for data visualization

## Project Structure
```
web-portal/
├── src/
│   ├── components/    # Reusable UI components
│   ├── pages/         # Route-level components
│   ├── hooks/         # Custom React hooks
│   ├── services/      # API client functions
│   ├── types/         # TypeScript type definitions
│   └── utils/         # Utility functions
```

## TypeScript Requirements
- All new code must use TypeScript
- Define explicit types for props, state, and API responses
- Avoid `any` type - use `unknown` with type guards if needed

## Component Pattern
```typescript
import { FC } from 'react';
import { Box, Typography } from '@mui/material';

interface TradeCardProps {
  tradeId: string;
  sourceType: 'BANK' | 'COUNTERPARTY';
  status: string;
  onSelect?: (tradeId: string) => void;
}

export const TradeCard: FC<TradeCardProps> = ({
  tradeId,
  sourceType,
  status,
  onSelect
}) => {
  return (
    <Box onClick={() => onSelect?.(tradeId)}>
      <Typography variant="h6">{tradeId}</Typography>
      {/* ... */}
    </Box>
  );
};
```

## Data Fetching with React Query
```typescript
import { useQuery } from '@tanstack/react-query';
import { fetchTrades } from '../services/api';

export const useTrades = (sourceType: string) => {
  return useQuery({
    queryKey: ['trades', sourceType],
    queryFn: () => fetchTrades(sourceType),
    staleTime: 30000, // 30 seconds
  });
};
```

## Commands
```bash
npm run dev      # Start dev server
npm run build    # Production build
npm run lint     # ESLint check
npm run test     # Run Vitest tests (use --run for single execution)
```

## Accessibility
- Follow WCAG 2.1 AA guidelines
- Use semantic HTML elements
- Include proper ARIA labels
- Ensure keyboard navigation works
