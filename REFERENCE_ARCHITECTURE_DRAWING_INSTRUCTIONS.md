# Reference Architecture Drawing Instructions
## AI-Powered Trade Reconciliation System

### Overview
This document provides detailed instructions for creating a professional reference architecture diagram for the AI-powered trade reconciliation system. The diagram should illustrate the complete solution flow from user interface to data processing, highlighting AI agents, AWS services, and data flows.

---

## 1. DIAGRAM LAYOUT & STRUCTURE

### **Canvas Setup**
- **Orientation**: Landscape (16:10 or 4:3 ratio)
- **Sections**: Organize into 4 horizontal layers from top to bottom:
  1. **Presentation Layer** (User Interface)
  2. **Application Layer** (API & Business Logic)  
  3. **AI Processing Layer** (Agents & Workflows)
  4. **Data Layer** (Storage & Persistence)
- **Color Scheme**: Use professional colors:
  - AWS Orange (#FF9900) for AWS services
  - Blue (#2196F3) for custom applications
  - Green (#4CAF50) for AI/ML components
  - Gray (#757575) for data stores
  - Red (#F44336) for security/auth components

---

## 2. PRESENTATION LAYER (TOP)

### **Components to Draw:**

#### **Web Browser**
- **Shape**: Rectangle with rounded corners
- **Icon**: Browser icon with address bar
- **Label**: "Trade Reconciliation Portal"
- **Details**: 
  - URL: "https://trade-recon.company.com"
  - Users: "Trade Operations Team"

#### **React Frontend Application**
- **Shape**: Large rectangle containing smaller components
- **Label**: "React TypeScript Frontend"
- **Sub-components** (arrange as cards within):
  - Authentication Module
  - Dashboard (with charts icon)
  - Document Upload Interface
  - Trade Management Console
  - Agent Monitor
  - Reconciliation Reports
- **Hosting**: Connect to "AWS Amplify" box below
- **Key Features Text**: 
  - "Real-time dashboards"
  - "Document drag-and-drop"
  - "Interactive trade matching"
  - "AI agent monitoring"

#### **Mobile/Tablet Access** (Optional)
- **Shape**: Mobile device outline
- **Label**: "Responsive Web Access"
- **Connection**: Dotted line to main frontend

---

## 3. APPLICATION LAYER (SECOND LEVEL)

### **Left Side - API Gateway & Auth:**

#### **AWS API Gateway**
- **Shape**: Rectangle with AWS service icon
- **Label**: "Amazon API Gateway"
- **Endpoints** (list inside box):
  - `/dashboard` - GET
  - `/documents` - POST
  - `/trades` - GET/POST
  - `/matches` - GET/PUT
  - `/reconciliation/{id}` - GET
  - `/reports` - GET/POST
  - `/agents/status` - GET
- **Features**: "CORS, Authentication, Rate Limiting"

#### **Authentication Service**
- **Shape**: Shield-shaped rectangle
- **Label**: "AWS Cognito / IAM"
- **Details**: "JWT Tokens, Role-based Access"

### **Center - Lambda Functions:**

#### **Main API Handler**
- **Shape**: Rectangle with Lambda icon
- **Label**: "Trade API Handler"
- **Language**: "Python 3.9"
- **Responsibilities**:
  - Request routing
  - Data validation
  - Response formatting
  - Error handling

#### **Document Processor**
- **Shape**: Rectangle with Lambda icon  
- **Label**: "PDF Processing Lambda"
- **Triggers**: "S3 Upload Events"
- **AI Services**: Connected to Textract/Rekognition

#### **Agent Orchestrator**
- **Shape**: Rectangle with Lambda icon
- **Label**: "Strands Agent Runtime"
- **Framework**: "Strands AI Framework"
- **Purpose**: "Workflow orchestration"

### **Right Side - External Services:**

#### **AWS Textract**
- **Shape**: Rectangle with AWS AI icon
- **Label**: "Amazon Textract"
- **Purpose**: "Document text extraction"

#### **AWS Rekognition**
- **Shape**: Rectangle with AWS AI icon  
- **Label**: "Amazon Rekognition"
- **Purpose**: "Table/form detection"

---

## 4. AI PROCESSING LAYER (THIRD LEVEL)

### **Main Agent Container:**

#### **Trade Reconciliation Agent**
- **Shape**: Large rounded rectangle with AI brain icon
- **Label**: "Trade Reconciliation Agent (Strands)"
- **Framework**: "Python + Strands AI Framework"

#### **Specialized Tools** (arranged as smaller boxes within agent):

**Matching Tools:**
- `fetch_unmatched_trades()`
- `find_potential_matches()`
- `compute_similarity()`
- `update_match_status()`

**Reconciliation Tools:**
- `compare_fields()`
- `determine_overall_status()`
- `update_reconciliation_status()`

**Reporting Tools:**
- `generate_reconciliation_report()`
- `store_report()`
- `fetch_reconciliation_results()`

#### **Workflow Stages** (horizontal flow with arrows):
1. **Document Processing** → 2. **Trade Matching** → 3. **Field Reconciliation** → 4. **Report Generation**

#### **Configuration Objects** (small boxes connected to agent):
- **MatcherConfig**: Thresholds, weights
- **ReconcilerConfig**: Tolerances, critical fields  
- **ReportConfig**: Output formats, destinations

---

## 5. DATA LAYER (BOTTOM)

### **Left Side - Operational Data:**

#### **DynamoDB Tables** (arrange as connected database cylinders):

**BankTradeData Table**
- **Shape**: Cylinder with DynamoDB icon
- **Key Attributes**: trade_id, trade_date, counterparty, notional
- **Indexes**: GSI on trade_date, counterparty

**CounterpartyTradeData Table**
- **Shape**: Cylinder with DynamoDB icon  
- **Key Attributes**: trade_id, trade_date, counterparty, notional
- **Indexes**: GSI on trade_date, counterparty

**TradeMatches Table**
- **Shape**: Cylinder with DynamoDB icon
- **Key Attributes**: match_id, bank_trade_id, counterparty_trade_id
- **Status Fields**: match_confidence, reconciliation_status

### **Center - Document Storage:**

#### **S3 Bucket**
- **Shape**: Bucket icon with folder structure
- **Label**: "fab-otc-reconciliation-deployment"
- **Folder Structure**:
  ```
  /BANK/
    ├── processed/
    ├── pending/
    └── failed/
  /COUNTERPARTY/  
    ├── processed/
    ├── pending/
    └── failed/
  /REPORTS/
    ├── daily/
    ├── monthly/
    └── ad-hoc/
  ```

### **Right Side - Monitoring & Logs:**

#### **CloudWatch**
- **Shape**: Rectangle with monitoring icon
- **Components**:
  - Logs: Lambda execution logs
  - Metrics: API performance, error rates
  - Alarms: Processing failures, high latency
  - Dashboards: Business KPIs

#### **AWS X-Ray** (Optional)
- **Shape**: Rectangle with tracing icon
- **Purpose**: "Distributed tracing"

---

## 6. DATA FLOW ARROWS & ANNOTATIONS

### **Primary User Flow** (Blue arrows with numbers):
1. **User uploads documents** → Frontend → API Gateway → S3
2. **S3 triggers processing** → Lambda → AI Services → Extract trade data
3. **Store extracted data** → DynamoDB tables
4. **Agent triggers matching** → Strands Agent → Similarity algorithms
5. **Create matches** → Update TradeMatches table
6. **Reconcile field differences** → Generate detailed comparisons
7. **Create reports** → Store in S3 → Display in dashboard

### **Real-time Updates** (Green dotted arrows):
- Agent status → Frontend dashboard
- Processing progress → Real-time UI updates
- Error notifications → User alerts

### **Administrative Flows** (Orange arrows):
- Configuration updates
- System monitoring
- Log analysis
- Performance metrics

---

## 7. TECHNICAL ANNOTATIONS

### **Add Technical Details as Side Boxes:**

#### **Performance Metrics**
- API Response Time: < 500ms
- Document Processing: 2-5 min per file
- Matching Accuracy: 95%+ with 0.85 threshold
- Concurrent Users: Up to 50

#### **Security Features**
- TLS 1.3 encryption in transit
- IAM role-based access control
- DynamoDB encryption at rest
- S3 bucket policies with least privilege
- JWT token validation

#### **Scalability**
- Lambda auto-scaling (0-1000 concurrent)
- DynamoDB on-demand scaling
- API Gateway rate limiting: 1000 req/sec
- S3 virtually unlimited storage

#### **Integration Points**
- External trade systems (future)
- Compliance reporting systems
- Risk management platforms
- Audit trail systems

---

## 8. LEGEND & ANNOTATIONS

### **Create a Legend Box (Bottom Right):**

#### **Symbols:**
- 🔄 Synchronous API calls
- ⚡ Asynchronous processing  
- 📊 Real-time data flow
- 🔐 Authenticated requests
- 🤖 AI/ML processing
- 📁 Data persistence
- ⚠️ Error handling

#### **Colors:**
- **Blue**: Custom applications
- **Orange**: AWS managed services
- **Green**: AI/ML components  
- **Gray**: Data storage
- **Red**: Security components

#### **Line Styles:**
- **Solid**: Primary data flow
- **Dashed**: Control/configuration
- **Dotted**: Monitoring/logging

---

## 9. QUALITY ASSURANCE CHECKLIST

### **Before Finalizing:**
- [ ] All AWS services are correctly labeled and colored
- [ ] Data flows are clearly indicated with numbered steps
- [ ] All major components are properly connected
- [ ] Technical specifications are included
- [ ] Security boundaries are clearly marked
- [ ] Scalability aspects are highlighted
- [ ] AI agent workflow is detailed
- [ ] Error handling paths are shown
- [ ] Monitoring and logging are represented
- [ ] Future integration points are indicated

### **Professional Presentation:**
- [ ] Consistent fonts and sizing
- [ ] Proper alignment and spacing
- [ ] Clear visual hierarchy
- [ ] Professional color scheme
- [ ] Readable at different zoom levels
- [ ] Title and versioning information
- [ ] Company branding (if applicable)

---

## 10. RECOMMENDED TOOLS

### **Professional Diagramming Tools:**
1. **Lucidchart** - Best for AWS architecture diagrams
2. **Draw.io (diagrams.net)** - Free with AWS stencils
3. **Microsoft Visio** - Professional enterprise option
4. **AWS Architecture Center** - Official AWS diagram tool
5. **CloudCraft** - 3D AWS architecture diagrams

### **AWS Official Resources:**
- AWS Architecture Icons (SVG/PNG)
- AWS Well-Architected Framework symbols
- AWS Solution Architecture templates

---

## 11. FINAL OUTPUT SPECIFICATIONS

### **Deliverables:**
1. **High-Resolution Architecture Diagram** (PNG/PDF)
2. **Editable Source File** (native format)
3. **Component Description Document** (this guide)
4. **Technical Specification Summary**

### **File Naming Convention:**
- `trade_reconciliation_architecture_v1.0.pdf`
- `trade_reconciliation_architecture_v1.0.vsdx` (or native format)
- `trade_reconciliation_technical_specs.pdf`

This comprehensive reference architecture will effectively communicate the sophisticated AI-powered trade reconciliation solution to stakeholders, technical teams, and compliance audiences.
