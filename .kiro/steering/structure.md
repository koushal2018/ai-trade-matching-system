# Project Structure

## Root Directory Organization

```
├── README.md                           # Main project documentation
├── deploy.sh                          # Main deployment script
├── client-deployment/                 # Client deployment artifacts
├── trade-reconciliation-frontend/     # React TypeScript frontend
├── strandsagents/                     # AI agents using Strands framework
└── config/                           # Configuration files
```

## Frontend Structure (`trade-reconciliation-frontend/`)

```
├── src/
│   ├── components/                    # React components
│   │   ├── auth/                     # Authentication components
│   │   ├── common/                   # Reusable UI components
│   │   ├── layout/                   # Layout components
│   │   └── pages/                    # Page-level components
│   │       └── agent-monitor/        # AI agent monitoring UI
│   ├── services/                     # API service layers
│   │   ├── api/                      # Base API services
│   │   └── agent/                    # Agent-specific services
│   ├── types/                        # TypeScript type definitions
│   ├── hooks/                        # Custom React hooks
│   ├── context/                      # React context providers
│   ├── utils/                        # Utility functions
│   └── config/                       # Frontend configuration
├── public/                           # Static assets
└── package.json                      # Dependencies and scripts
```

## Backend Structure (`client-deployment/`)

```
├── cloudformation/                   # Infrastructure as Code
│   ├── master-template.yaml         # Main CloudFormation stack
│   ├── core-infrastructure.yaml    # Core AWS resources
│   ├── api-lambda.yaml             # API Gateway and Lambda
│   ├── frontend-amplify.yaml       # Amplify hosting
│   ├── authentication.yaml         # Cognito authentication
│   ├── monitoring.yaml             # CloudWatch monitoring
│   └── backup-dr.yaml              # Backup and disaster recovery
├── lambda/                          # Lambda function code
│   ├── api_handler/                # Main API handler
│   │   ├── handlers/               # Route-specific handlers
│   │   └── index.js               # Main Lambda entry point
│   ├── document_processor/         # Document processing Lambda
│   └── reconciliation_engine/      # Reconciliation Lambda
└── infrastructure/                  # Additional infrastructure
    └── cloudformation/             # Alternative CloudFormation templates
```

## AI Agents Structure (`strandsagents/`)

```
├── agents.py                        # Core Strands tools (@tool decorators)
├── enhanced_agents.py              # Enhanced agent implementations
├── trade_reconciliation_agent.py   # Main orchestration agent
├── models.py                       # Data models and configurations
├── enhanced_tools.py              # Extended tool implementations
├── enhanced_config.py             # Configuration management
├── enhanced_workflow.py           # Workflow orchestration
├── ai_providers/                   # AI provider adapters
│   ├── base.py                     # Base provider interface
│   ├── bedrock_adapter.py         # Amazon Bedrock integration
│   ├── huggingface_adapter.py     # HuggingFace integration
│   └── sagemaker_adapter.py       # SageMaker integration
├── run_*.py                        # Execution scripts
└── test_*.py                       # Test files
```

## Key Architectural Patterns

### Component Organization
- **Frontend**: Feature-based component organization with shared common components
- **Backend**: Handler-based Lambda organization with separation of concerns
- **AI Agents**: Tool-based architecture using Strands framework decorators

### Configuration Management
- Environment-specific configuration in `.env` files
- AWS resource configuration through CloudFormation parameters
- AI agent configuration through Python models and classes

### Data Flow
1. **Frontend** → API Gateway → Lambda handlers
2. **Lambda handlers** → DynamoDB/S3 for data persistence
3. **AI Agents** → AWS services for processing and orchestration
4. **Reports** → S3 storage → Frontend download

### Naming Conventions
- **Files**: kebab-case for directories, camelCase for TypeScript, snake_case for Python
- **Components**: PascalCase for React components
- **Functions**: camelCase for JavaScript, snake_case for Python
- **AWS Resources**: PascalCase in CloudFormation templates
- **Environment Variables**: UPPER_SNAKE_CASE

### Import Patterns
- **Frontend**: Relative imports for local components, absolute for external libraries
- **Backend**: CommonJS require() for Lambda compatibility
- **AI Agents**: Standard Python imports with proper module organization