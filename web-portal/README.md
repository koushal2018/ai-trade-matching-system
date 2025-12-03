# Trade Matching Web Portal

React-based web portal for the AI Trade Matching System. Provides real-time monitoring, HITL (Human-in-the-Loop) interactions, and comprehensive audit trails.

## Features

- **Dashboard**: Real-time agent health status, processing metrics, and matching results
- **HITL Panel**: Review and approve/reject uncertain trade matches
- **Audit Trail**: Complete operation history with filtering and export

## Tech Stack

- React 18 with TypeScript
- Vite for build tooling
- Material-UI (MUI) for components
- React Query for data fetching
- Recharts for visualizations
- WebSocket for real-time updates

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
cd web-portal
npm install
```

### Development

```bash
npm run dev
```

The app will be available at http://localhost:3000

### Build

```bash
npm run build
```

### Environment Variables

Create a `.env` file:

```env
VITE_API_URL=/api
VITE_WS_URL=ws://localhost:8000/ws
```

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── dashboard/       # Dashboard-specific components
│   ├── hitl/            # HITL panel components
│   └── Layout.tsx       # Main layout wrapper
├── pages/               # Page components
│   ├── Dashboard.tsx
│   ├── HITLPanel.tsx
│   └── AuditTrail.tsx
├── services/            # API and WebSocket services
├── types/               # TypeScript type definitions
├── App.tsx              # Main app component
├── main.tsx             # Entry point
└── theme.ts             # MUI theme configuration
```

## API Integration

The portal expects a backend API with the following endpoints:

- `GET /api/agents/status` - Agent health status
- `GET /api/metrics/processing` - Processing metrics
- `GET /api/hitl/pending` - Pending HITL reviews
- `POST /api/hitl/{reviewId}/decision` - Submit HITL decision
- `GET /api/audit` - Audit trail records
- `GET /api/audit/export` - Export audit records
- `WS /ws` - WebSocket for real-time updates
