# Trade Reconciliation System Architecture

The following diagram illustrates the architecture of the Trade Reconciliation System:

```mermaid
graph TD
    subgraph "Frontend Application"
        UI[React Frontend]
    end
    
    subgraph "API Layer"
        API[API Gateway]
        APIHandler[API Handler Lambda]
    end
    
    subgraph "Processing Layer"
        DocProc[Document Processor Lambda]
        RecEngine[Reconciliation Engine Lambda]
    end
    
    subgraph "Storage Layer"
        DocBucket[(S3 Document Bucket)]
        ReportBucket[(S3 Report Bucket)]
        BankTable[(DynamoDB Bank Trades)]
        CPTable[(DynamoDB Counterparty Trades)]
        MatchTable[(DynamoDB Match Results)]
    end
    
    %% Frontend to API connections
    UI -->|REST API Calls| API
    API -->|Proxy Requests| APIHandler
    
    %% API Handler connections
    APIHandler -->|Read/Write| DocBucket
    APIHandler -->|Read/Write| ReportBucket
    APIHandler -->|Query| BankTable
    APIHandler -->|Query| CPTable
    APIHandler -->|Query| MatchTable
    APIHandler -->|Invoke| RecEngine
    
    %% Document processing flow
    DocBucket -->|S3 Event| DocProc
    DocProc -->|Extract & Store| BankTable
    DocProc -->|Extract & Store| CPTable
    
    %% Reconciliation flow
    RecEngine -->|Read Trades| BankTable
    RecEngine -->|Read Trades| CPTable
    RecEngine -->|Store Matches| MatchTable
    RecEngine -->|Store Reports| ReportBucket
    
    %% Document upload flow
    UI -->|Upload Documents| DocBucket
    
    %% Legend
    classDef aws fill:#FF9900,stroke:#232F3E,color:#232F3E
    classDef lambda fill:#009900,stroke:#232F3E,color:white
    classDef storage fill:#3B48CC,stroke:#232F3E,color:white
    
    class API,DocBucket,ReportBucket,BankTable,CPTable,MatchTable aws
    class APIHandler,DocProc,RecEngine lambda
    class DocBucket,ReportBucket,BankTable,CPTable,MatchTable storage
```

## Data Flow

1. **Document Upload Flow**:
   - User uploads bank and counterparty trade documents through the frontend
   - Files are stored in the S3 Document Bucket
   - S3 triggers the Document Processor Lambda
   - Document Processor extracts trade data and stores it in DynamoDB tables

2. **Reconciliation Flow**:
   - User selects documents and initiates reconciliation through the frontend
   - API Gateway routes the request to the API Handler Lambda
   - API Handler invokes the Reconciliation Engine Lambda
   - Reconciliation Engine compares trades and identifies matches/discrepancies
   - Match results are stored in DynamoDB and a report is generated in S3

3. **Results Retrieval Flow**:
   - User requests reconciliation results through the frontend
   - API Gateway routes the request to the API Handler Lambda
   - API Handler retrieves match data from DynamoDB and reports from S3
   - Results are displayed in the frontend
