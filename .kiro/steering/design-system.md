---
inclusion: always
---

# AWS-Inspired Design System Rules

## Design System Structure

### 1. Token Definitions

**Location**: `web-portal/src/theme.ts`
**Format**: Material-UI theme configuration with AWS-inspired tokens

```typescript
// Color tokens defined in theme.ts
const awsTokens = {
  colors: {
    primary: '#FF9900',      // AWS Orange
    secondary: '#146EB4',    // AWS Light Blue
    background: '#0F1419',   // AWS Background
    surface: '#1C2127',      // AWS Surface
    text: {
      primary: '#FFFFFF',
      secondary: '#9BA7B4',
      disabled: '#687078'
    }
  },
  spacing: 8, // 8px base unit
  borderRadius: 8
}
```

### 2. Component Library

**Location**: `web-portal/src/components/`
**Architecture**: React functional components with Material-UI base
**Structure**:
```
components/
├── Layout.tsx              # Main layout wrapper
├── dashboard/              # Dashboard-specific components
│   ├── AgentHealthPanel.tsx
│   ├── ProcessingMetricsPanel.tsx
│   └── MatchingResultsPanel.tsx
└── [feature]/              # Feature-specific components
```

### 3. Frameworks & Libraries

- **UI Framework**: React 18.3.1 with TypeScript
- **Styling**: Material-UI v5.15.20 with Emotion
- **Build System**: Vite 5.3.1
- **State Management**: TanStack Query v5.45.1
- **Routing**: React Router DOM v6.23.1
- **Charts**: Recharts v2.12.7

### 4. Asset Management

**Icons**: Material-UI Icons (`@mui/icons-material`)
**Assets**: Stored in `public/` directory
**Optimization**: Vite handles bundling and optimization

### 5. Icon System

**Library**: Material-UI Icons
**Usage Pattern**:
```typescript
import { Dashboard as DashboardIcon } from '@mui/icons-material'
```
**Convention**: Import with descriptive alias

### 6. Styling Approach

**Method**: Material-UI `sx` prop with theme tokens
**Global Styles**: Defined in theme.ts
**Responsive**: Material-UI breakpoint system

```typescript
// Example styling pattern
<Box sx={{ 
  backgroundColor: 'background.paper',
  border: '1px solid',
  borderColor: 'divider',
  borderRadius: 1,
  p: 3
}}>
```

## AWS Design System Implementation

### Color Palette

#### Primary Colors
- **AWS Orange**: `#FF9900` - Primary actions, highlights, active states
- **AWS Dark Blue**: `#232F3E` - Headers, navigation, app bar
- **AWS Light Blue**: `#146EB4` - Links, secondary actions
- **AWS Squid Ink**: `#16191F` - Dark backgrounds

#### Semantic Colors
- **Success**: `#1D8102` - Matched trades, healthy agent status
- **Warning**: `#FF9900` - Pending reviews, degraded status
- **Error**: `#D13212` - Breaks, critical issues, unhealthy status
- **Info**: `#0972D3` - Information, neutral status

#### Neutral Colors (Official AWS Grayscale)
- **Gray 900**: `#0F1419` - Main application background (darkest)
- **Gray 800**: `#1C2127` - Card backgrounds, elevated surfaces
- **Gray 700**: `#232A31` - Modal backgrounds, tooltips
- **Gray 600**: `#414D5C` - Subtle borders, dividers
- **Gray 500**: `#687078` - Disabled text, captions
- **Gray 400**: `#9BA7B4` - Secondary text, labels
- **Gray 300**: `#AEBAC7` - Placeholder text
- **Gray 200**: `#C1CDD9` - Light borders
- **Gray 100**: `#D5E0EC` - Light backgrounds
- **Gray 50**: `#E9F0F7` - Lightest backgrounds
- **White**: `#FFFFFF` - Primary text content, pure white

### Typography

#### Font Stack
- **Primary**: `"Amazon Ember", "Helvetica Neue", Helvetica, Arial, sans-serif`
- **Monospace**: `"Amazon Ember Mono", "Courier New", monospace`

#### Type Scale (Material-UI variants)
- **h1**: 28px, font-weight: 700 - Page titles
- **h2**: 24px, font-weight: 600 - Section headers
- **h3**: 20px, font-weight: 600 - Subsection headers
- **h4**: 18px, font-weight: 600 - Card titles
- **h5**: 16px, font-weight: 600 - Component titles
- **h6**: 14px, font-weight: 600 - Small headers
- **body1**: 14px, font-weight: 400 - Primary body text
- **body2**: 12px, font-weight: 400 - Secondary body text
- **caption**: 11px, font-weight: 400 - Captions, metadata

### Spacing System

**Base Unit**: 8px (Material-UI default)
**Scale**: xs(4px), sm(8px), md(16px), lg(24px), xl(32px), 2xl(48px), 3xl(64px)

### Component Specifications

#### Cards (MuiCard)
```typescript
{
  backgroundColor: '#1C2127',
  border: '1px solid #414D5C',
  borderRadius: '8px',
  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
  backdropFilter: 'blur(10px)', // Glassmorphism effect
}
```

#### Buttons (MuiButton)
```typescript
// Primary Button
{
  backgroundColor: '#FF9900',
  color: '#FFFFFF',
  borderRadius: '4px',
  fontWeight: 600,
  padding: '8px 16px',
  '&:hover': {
    backgroundColor: '#E6890A',
    transform: 'translateY(-1px)',
    boxShadow: '0 4px 12px rgba(255, 153, 0, 0.3)',
  }
}
```

#### Status Chips (MuiChip)
- **Success**: `#1D8102` background - Healthy agents, matched trades
- **Warning**: `#FF9900` background - Degraded agents, pending reviews
- **Error**: `#D13212` background - Unhealthy agents, breaks

#### Navigation (AppBar & Drawer)
- **AppBar**: `#232F3E` background with blur effect
- **Drawer**: `#232F3E` background, `#FF9900` accent for active items
- **Selected State**: Orange left border + background tint

### Layout Patterns

#### Grid System
- **Container**: Material-UI Grid with 16px spacing
- **Breakpoints**: xs(0px), sm(600px), md(900px), lg(1200px), xl(1536px)
- **Responsive**: Mobile-first approach

#### Dashboard Layout
```typescript
<Grid container spacing={3}>
  <Grid item xs={12}>           {/* Full width panels */}
  <Grid item xs={12} md={6}>    {/* Half width on desktop */}
</Grid>
```

### Data Visualization

#### Chart Colors (Recharts)
- Primary: `#FF9900` (AWS Orange)
- Secondary: `#146EB4` (AWS Light Blue)
- Success: `#1D8102`
- Warning: `#FF9900`
- Error: `#D13212`
- Neutral: `#9BA7B4`

### Interaction States

#### Hover Effects
```typescript
'&:hover': {
  backgroundColor: 'rgba(255, 255, 255, 0.08)',
  transition: 'all 0.15s ease-in-out'
}
```

#### Focus States
```typescript
'&:focus': {
  outline: '2px solid #FF9900',
  outlineOffset: '2px'
}
```

#### Loading States
- Linear progress bars with AWS Orange
- Skeleton loaders with surface colors
- Spinner components with primary color

### Accessibility Standards

- **WCAG 2.1 AA** compliance required
- **Contrast Ratios**: Minimum 4.5:1 for normal text, 3:1 for large text
- **Focus Management**: Visible focus indicators on all interactive elements
- **Screen Readers**: Proper ARIA labels and semantic HTML
- **Keyboard Navigation**: Full keyboard accessibility

### Trade Matching Domain Patterns

#### Agent Status Indicators
```typescript
const statusConfig = {
  HEALTHY: { color: '#1D8102', icon: 'CheckCircle' },
  DEGRADED: { color: '#FF9900', icon: 'Warning' },
  UNHEALTHY: { color: '#D13212', icon: 'Error' },
  OFFLINE: { color: '#687078', icon: 'OfflinePin' }
}
```

#### Trade Classification Colors
- **MATCHED**: `#1D8102` - Successful matches
- **PROBABLE_MATCH**: `#FF9900` - Requires review
- **REVIEW_REQUIRED**: `#FF9900` - Manual intervention needed
- **BREAK**: `#D13212` - Failed matches

#### Metrics Display
- **Latency**: Show in milliseconds with color coding
- **Throughput**: Trades per hour with trend indicators
- **Error Rates**: Percentage with threshold-based colors
- **Token Usage**: Input/output token counts for LLM monitoring

### Official AWS Design Principles

Based on the official AWS Design Documentation:

#### Core Philosophy
- **"We tell stories with data"** - Data visualization should be clear, accessible, and meaningful
- **Audience-first approach** - Consider your audience, message, and context before making design decisions
- **Simplicity over complexity** - Complex messaging may warrant simpler choices, bold/snappy lines allow for more freedom

#### Color Strategy
- **Anchor Colors**: Use Gray 50 as the primary anchor color (more mutable alternative to black)
- **Color Harmony**: Employ monochromatic, analogous, and split complementary color schemes
- **Context Matters**: Consider where designs will be viewed (presentations, social media, dashboards)
- **Hierarchy**: Use color to create hierarchy and highlight key information

#### Data Visualization Guidelines
- **Accessibility First**: Ensure all charts and graphs meet WCAG 2.1 AA standards
- **Color Coding**: Use consistent color coding across all visualizations
- **Progressive Disclosure**: Show the most important information first
- **Interactive Elements**: Provide hover states and tooltips for detailed information

### Implementation Guidelines

1. **Always use theme tokens** instead of hardcoded colors
2. **Prefer sx prop** over styled components for simple styling
3. **Use Material-UI components** as base, customize with theme
4. **Implement responsive design** with Material-UI breakpoints
5. **Follow AWS design principles** for enterprise applications
6. **Maintain dark theme** as primary experience with Gray 50 anchor
7. **Ensure accessibility** in all custom components (WCAG 2.1 AA)
8. **Use consistent spacing** with 8px base unit
9. **Apply glassmorphism effects** sparingly for modern feel
10. **Test with real data** from DynamoDB tables
11. **Prioritize data storytelling** - make metrics meaningful and actionable
12. **Use color harmony principles** - monochromatic, analogous, split complementary
13. **Consider context** - dashboard vs presentation vs mobile views
14. **Create clear hierarchy** with color, typography, and spacing

### File Organization

```
web-portal/src/
├── theme.ts                 # Central theme configuration
├── components/
│   ├── Layout.tsx          # Main layout wrapper
│   ├── dashboard/          # Dashboard components
│   └── common/             # Reusable components
├── pages/                  # Route components
├── services/               # API services
├── types/                  # TypeScript definitions
└── utils/                  # Helper functions
```

### Integration with Figma

When implementing Figma designs:
1. **Extract design tokens** from Figma variables
2. **Map to Material-UI theme** structure
3. **Replace Tailwind classes** with sx props
4. **Maintain visual parity** with Figma screenshots
5. **Use existing components** where possible
6. **Follow AWS design patterns** for consistency