# Trade Matching Upload - Cloudscape Design System Migration Requirements

## Document Info

| Field | Value |
|-------|-------|
| Component | `TradeMatchingUpload.tsx` |
| Current Library | Material UI (MUI) |
| Target Library | Cloudscape Design System with Generative AI Patterns |
| Date | December 2024 |

---

## 1. Current State Analysis

### Current Implementation

The existing `TradeMatchingUpload.tsx` is a placeholder component using Material UI:

```tsx
// Current MUI components used:
- Box (layout container with animation)
- Typography (heading and body text)
```

### Current Features
- Page title with gradient styling (AWS Orange #FF9900 to AWS Blue #146EB4)
- Fade-in animation on mount
- Basic descriptive text

### Missing Features (per UX Specification)
Based on `docs/otc_trade_matching_ux.md`, the following features need implementation:

| Feature | Status |
|---------|--------|
| Dual file upload (Bank & Counterparty) | Not implemented |
| Workflow ID / Session ID / Trace ID display | Not implemented |
| Processing status panel with stages | Not implemented |
| "Invoke on Demand" button | Not implemented |
| Result section with match status | Not implemented |
| Exception/error display section | Not implemented |
| Real-time status updates | Not implemented |

---

## 2. Cloudscape Component Mapping

### Direct MUI to Cloudscape Replacements

| MUI Component | Cloudscape Component | Package |
|---------------|---------------------|---------|
| `Box` | `Box`, `Container`, `SpaceBetween` | `@cloudscape-design/components` |
| `Typography` (h4) | `Header` | `@cloudscape-design/components` |
| `Typography` (body1) | `Box` with `variant="p"` | `@cloudscape-design/components` |

### Required Cloudscape Components for Full Implementation

| Feature | Cloudscape Component(s) | Notes |
|---------|------------------------|-------|
| Page Layout | `AppLayout`, `ContentLayout`, `Header` | Standard page structure |
| File Upload (x2) | `FileUpload` | Drag-and-drop support built-in |
| Upload Containers | `Container`, `ColumnLayout` | Side-by-side layout |
| Workflow IDs | `KeyValuePairs` | Display workflow metadata |
| Status Panel | `Steps` + `StatusIndicator` | Progressive steps pattern |
| Invoke Button | `Button` with `iconName="gen-ai"` | Generative AI affordance |
| Results Display | `Container`, `Table`, `Box` | Match comparison |
| Exception Display | `Alert`, `Flashbar` | Error/warning messages |
| Loading States | `LoadingBar` (GenAI), `Spinner` | AI processing feedback |

---

## 3. Generative AI Pattern Requirements

### 3.1 Progressive Steps Pattern (Critical)

The processing status panel aligns perfectly with Cloudscape's [Progressive Steps Pattern](https://cloudscape.design/patterns/genai/progressive-steps/).

**Implementation Requirements:**

| Building Block | Application |
|----------------|-------------|
| **Header** | "Trade Matching Workflow" |
| **Main Steps** | S3 Upload → PDF Extraction → Trade Entries → Exception Comparison |
| **Sub-steps** | Individual file processing details |
| **Status Hub** | Multiple status indicators per step |
| **Step Details** | Popovers with agent response details |
| **Input Requests** | "Invoke on Demand" dialog |

**Status Indicator Mapping:**

| Current Status | Cloudscape StatusIndicator `type` |
|----------------|----------------------------------|
| Pending (Gray) | `"pending"` |
| In Progress (Blue) | `"in-progress"` |
| Complete (Green) | `"success"` |
| Error (Red) | `"error"` |

**Best Practices to Follow:**
- Show time estimates for operations >10 seconds
- Limit sub-step nesting to 4 levels maximum
- Avoid loading states under 1 second (causes flickering)
- Enable detail access through popovers

### 3.2 Generative AI Loading States

Apply the [GenAI Loading States Pattern](https://cloudscape.design/patterns/genai/genai-loading-states/) for agent processing:

| Phase | Visual Treatment |
|-------|------------------|
| Processing (prompt handling) | Avatar with loading text |
| Generation (output appearing) | Streaming text or LoadingBar |
| Complex content (tables, code) | LoadingBar component |

**Loading Message Guidelines:**
- Use: "Generating comparison results..."
- Use: "Loading trade entries..."
- Avoid end punctuation in loading messages
- Maintain sentence case

### 3.3 Ingress Pattern

Apply the [Ingress Pattern](https://cloudscape.design/patterns/genai/ingress/) for the "Invoke on Demand" button:

```tsx
<Button
  variant="primary"
  iconName="gen-ai"
  iconAlign="left"
>
  Invoke Comparison Agent
</Button>
```

**Guidelines:**
- Use sparkle icon (`gen-ai`) for AI-triggered actions
- Only one primary button per page section
- Use "submit" for user queries, "responses" for AI replies

---

## 4. Generative AI Components Required

Install the GenAI components package:

```bash
npm install @cloudscape-design/chat-components
```

### Components from `@cloudscape-design/chat-components`

| Component | Use Case |
|-----------|----------|
| `Avatar` | AI agent visual representation in status/results |
| `LoadingBar` | Indeterminate loading during agent processing |
| `ChatBubble` | Display agent responses in exception section |
| `SupportPromptGroup` | Suggested actions (optional enhancement) |

### Example Avatar Usage

```tsx
import { Avatar } from '@cloudscape-design/chat-components';

<Avatar
  ariaLabel="AI Agent"
  color="gen-ai"
  iconName="gen-ai"
  loading={isProcessing}
  loadingText="Processing documents..."
/>
```

---

## 5. Figma Design Resources

### Official Cloudscape Figma Resources

| Resource | Link |
|----------|------|
| Cloudscape Figma Community | [figma.com/@cloudscape](https://www.figma.com/@cloudscape) |
| CDS Component Library 2.0.1 | [Figma Community File](https://www.figma.com/community/file/1448695453848536664/cds-component-library-2-0-1) |

### Figma Components to Use

| Feature | Figma Component |
|---------|-----------------|
| Page Layout | App Layout template |
| File Upload | File Upload component |
| Status Indicators | Status Indicator variants |
| Steps | Steps component |
| Buttons | Button (with gen-ai icon variant) |
| Alerts | Alert / Flashbar components |
| Cards/Containers | Container component |

### Figma Design Tokens

The Cloudscape Figma library includes:
- Variable-based styling
- Light/dark mode switching
- Color palettes (AWS branded)
- Typography (Open Sans)
- Iconography including GenAI sparkle icons

---

## 6. Package Dependencies

### Required Packages

```json
{
  "dependencies": {
    "@cloudscape-design/components": "^3.x",
    "@cloudscape-design/global-styles": "^1.x",
    "@cloudscape-design/chat-components": "^1.x",
    "@cloudscape-design/design-tokens": "^3.x"
  }
}
```

### Setup Requirements

```tsx
// App.tsx or index.tsx
import "@cloudscape-design/global-styles/index.css";
```

---

## 7. Component Architecture Recommendation

### Proposed File Structure

```
src/pages/TradeMatching/
├── TradeMatchingUpload.tsx      # Main page component
├── components/
│   ├── FileUploadSection.tsx    # Dual file upload (Bank/Counterparty)
│   ├── WorkflowHeader.tsx       # Workflow/Session/Trace IDs
│   ├── ProcessingSteps.tsx      # Progressive steps status panel
│   ├── InvokeButton.tsx         # GenAI invoke button
│   ├── ResultsSection.tsx       # Match results display
│   └── ExceptionPanel.tsx       # Error/exception display
├── hooks/
│   ├── useWorkflow.ts           # Workflow state management
│   └── useAgentStatus.ts        # Real-time agent status
└── types/
    └── trade-matching.types.ts  # TypeScript interfaces
```

### Main Component Structure

```tsx
<AppLayout
  content={
    <ContentLayout
      header={<Header variant="h1">AI Trade Matching System</Header>}
    >
      <SpaceBetween size="l">
        {/* Dual File Upload */}
        <ColumnLayout columns={2}>
          <FileUploadSection side="bank" />
          <FileUploadSection side="counterparty" />
        </ColumnLayout>

        {/* Workflow Metadata */}
        <WorkflowHeader />

        {/* Processing Status - Progressive Steps Pattern */}
        <ProcessingSteps />

        {/* Results Section */}
        <ResultsSection />

        {/* Exception Panel */}
        <ExceptionPanel />
      </SpaceBetween>
    </ContentLayout>
  }
/>
```

---

## 8. Migration Checklist

### Phase 1: Foundation
- [ ] Install Cloudscape packages
- [ ] Set up global styles
- [ ] Replace MUI Box with Cloudscape AppLayout/ContentLayout
- [ ] Replace MUI Typography with Cloudscape Header/Box

### Phase 2: File Upload
- [ ] Implement Cloudscape FileUpload components (x2)
- [ ] Add drag-and-drop support
- [ ] Configure accepted file types (PDF, DOCX)
- [ ] Add upload progress indicators
- [ ] Implement S3 presigned URL integration

### Phase 3: Workflow Display
- [ ] Add KeyValuePairs for Workflow/Session/Trace IDs
- [ ] Style with Container component

### Phase 4: Progressive Steps (GenAI Pattern)
- [ ] Implement Steps component for main stages
- [ ] Add StatusIndicator for each step
- [ ] Implement sub-steps with Tree View (if needed)
- [ ] Add popovers for step details
- [ ] Integrate real-time status updates (WebSocket)

### Phase 5: GenAI Components
- [ ] Add Avatar for AI agent representation
- [ ] Implement LoadingBar for agent processing
- [ ] Add "Invoke on Demand" Button with gen-ai icon
- [ ] Apply streaming pattern for results

### Phase 6: Results & Exceptions
- [ ] Create results Container with Table for comparison
- [ ] Add match status display (MATCHED/MISMATCHED/PARTIAL)
- [ ] Implement confidence score display
- [ ] Add Flashbar/Alert for exceptions

### Phase 7: Polish
- [ ] Implement responsive design (tablet/mobile breakpoints)
- [ ] Add dark mode support
- [ ] Accessibility testing
- [ ] Performance optimization

---

## 9. References

### Cloudscape Documentation
- [Cloudscape Design System](https://cloudscape.design/)
- [Components Overview](https://cloudscape.design/components/)
- [Generative AI Components](https://cloudscape.design/components/genai-components/)

### Generative AI Patterns
- [Progressive Steps Pattern](https://cloudscape.design/patterns/genai/progressive-steps/)
- [Ingress Pattern](https://cloudscape.design/patterns/genai/ingress/)
- [GenAI Loading States](https://cloudscape.design/patterns/genai/genai-loading-states/)
- [Generative AI Chat Pattern](https://cloudscape.design/patterns/genai/generative-AI-chat/)

### Figma Resources
- [Cloudscape Figma Community](https://www.figma.com/@cloudscape)
- [CDS Component Library 2.0.1](https://www.figma.com/community/file/1448695453848536664/cds-component-library-2-0-1)
- [Design Resources Guide](https://cloudscape.design/get-started/resources/design-resources/)

---

## 10. Notes

### Why Cloudscape for This Project?

1. **AWS Native**: Cloudscape is built by AWS for AWS products, ensuring design consistency
2. **GenAI First-Class Support**: Dedicated components and patterns for AI experiences
3. **Accessibility**: WCAG 2.1 AA compliant out of the box
4. **Enterprise Ready**: Used by hundreds of AWS services in production
5. **Open Source**: MIT licensed, community maintained

### Animation Migration

The current MUI fade-in animation should be handled via:
- Cloudscape's built-in transition support
- CSS custom properties from design tokens
- Or removed in favor of Cloudscape's standard page load behavior
