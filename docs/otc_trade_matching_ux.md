AI Trade Matching System
UI/UX Specification Document
Project	OTC Derivative Trade Confirmation Automation
Version	1.0
Date	December 2024
Author	Koushal Dutt / AWS
1. Overview
This document outlines the UI specifications for the AI Trade Matching System web application. The system enables banks to upload trade confirmation documents (from both Bank and Counterparty sides) and leverages AWS Bedrock agents to automatically extract, match, and reconcile trade details.
2. Page Layout Structure
2.1 Header Section
•	AWS logo positioned top-left
•	Application title: "AI Trade Matching System" - centered
•	User profile/logout controls - top-right (optional)
•	Background color: AWS Orange (#FF9900) or Dark Navy (#232F3E)
2.2 Upload Section
Two side-by-side file upload areas:
Bank Upload	Counterparty Upload
Label: "Upload - Bank"
Action: Drag & drop or click to upload
Formats: PDF, DOCX
Destination: S3 bucket (bank folder)	Label: "Upload - Counterparty"
Action: Drag & drop or click to upload
Formats: PDF, DOCX
Destination: S3 bucket (counterparty folder)
2.3 Workflow Control Bar
Horizontal bar containing workflow identifiers and controls:
Element	Description
Workflow ID	Auto-generated unique identifier (e.g., "WF-2024-001")
Session ID	Current session identifier for the agent interaction
Trace ID	AWS X-Ray trace ID for debugging/monitoring
2.4 Processing Status Panel
Vertical list showing each processing stage with real-time status updates:
Stage	Status Display	Description
S3 Upload	Receiving S3 URIs	Files uploaded to S3, URIs returned
PDF Extraction	Agent Status	Textract/Bedrock extracting document content
Trade Entries	Agent Status	Parsing structured trade data from documents
Exception Comparison	Agent Status	Comparing bank vs counterparty trade details
Agent Status Values
•	Pending - Gray icon, waiting to start
•	In Progress - Blue spinner, actively processing
•	Complete - Green checkmark, successfully finished
•	Error - Red X icon, failed with error
"Invoke on Demand" Button
Located next to the Exception Comparison row. Allows manual trigger of the comparison agent when automatic processing isn't desired.
2.5 Result Section
Large text area displaying the final matching result:
•	Match Status: MATCHED / MISMATCHED / PARTIAL MATCH
•	Comparison summary table (side-by-side field comparison)
•	Confidence score percentage
•	Timestamp of completion
2.6 Exception Section
Displays any errors, warnings, or exceptions from the agent processing. Format: "Message - Anything from this Agent" showing the agent name and detailed error message.
3. Technical Specifications
3.1 Frontend Stack
•	Framework: React.js with TypeScript
•	UI Library: AWS Amplify UI or Material-UI with AWS theme
•	State Management: React Context or Redux Toolkit
•	File Upload: react-dropzone for drag-and-drop
•	Styling: Tailwind CSS or styled-components
3.2 Backend Integration
Endpoint	Method	Purpose
/api/upload	POST	Upload files to S3 via presigned URL
/api/workflow	POST	Initialize new workflow/session
/api/invoke	POST	Invoke Bedrock agent manually
/api/status	GET (WebSocket)	Real-time processing status updates
/api/result	GET	Retrieve final matching result
3.3 AWS Services Integration
•	Amazon S3: Document storage (separate prefixes for bank/counterparty)
•	Amazon Bedrock AgentCore: AI agent orchestration
•	Amazon Textract: PDF/document text extraction
•	Amazon API Gateway: REST API endpoints
•	AWS Lambda: Serverless compute for business logic
•	Amazon DynamoDB: Workflow state persistence
•	Amazon CloudWatch: Logging and monitoring
•	AWS X-Ray: Distributed tracing
4. User Workflow
1.	User uploads Bank trade confirmation PDF
2.	User uploads Counterparty trade confirmation PDF
3.	System generates Workflow ID, Session ID, and Trace ID
4.	S3 upload status updates to "Complete" with URIs
5.	PDF Extraction agent processes documents
6.	Trade Entries agent parses structured data
7.	User clicks "Invoke on Demand" (or automatic trigger)
8.	Exception Comparison agent runs matching logic
9.	Result displayed with match status and details
10.	Any exceptions/errors shown in Exception section
5. UI Component Details
5.1 File Upload Component
Property	Value
Accepted formats	.pdf, .docx
Max file size	10 MB
Upload indicator	Progress bar with percentage
Success state	Green border, checkmark, filename displayed
Error state	Red border, error message below
5.2 Status Indicator Component
State	Icon	Color
Pending	Circle outline	Gray (#9CA3AF)
In Progress	Spinning loader	AWS Blue (#0972D3)
Complete	Checkmark	Green (#10B981)
Error	X mark	Red (#EF4444)
6. Responsive Design Requirements
•	Desktop (1200px+): Full side-by-side layout as wireframed
•	Tablet (768-1199px): Upload areas stack vertically, status panel remains horizontal
•	Mobile (below 768px): All sections stack vertically, collapsible status panel
7. Security Considerations
•	AWS Cognito for user authentication
•	S3 presigned URLs for secure file upload
•	IAM roles with least-privilege access
•	HTTPS/TLS encryption in transit
•	S3 server-side encryption at rest
•	Audit logging via CloudTrail
8. Acceptance Criteria
•	Both file upload zones functional with drag-and-drop
•	Real-time status updates for all processing stages
•	"Invoke on Demand" button triggers agent comparison
•	Result section displays match status with details
•	Exception section shows agent errors when applicable
•	All workflow IDs (Workflow, Session, Trace) displayed correctly
•	Responsive design works across device sizes
•	AWS branding/styling consistent throughout
