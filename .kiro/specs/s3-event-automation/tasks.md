# Implementation Plan

- [x] 1. Create Lambda function for S3 event processing
  - [x] 1.1 Create the S3 event processor Lambda function
    - Create `deployment/s3_event_processor/s3_event_processor.py`
    - Implement S3 event parsing and validation
    - Implement source_type inference from S3 key path
    - Implement document_id extraction from S3 key
    - Implement correlation_id generation (`corr_{12-char-hex}`)
    - Implement AgentCore Runtime invocation with SigV4 signing
    - Add error handling with retry logic (3 attempts, exponential backoff)
    - Add CloudWatch logging with correlation_id, document_id, source_type
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 4.1, 4.2_

  - [x] 1.2 Write property test for source type inference
    - **Property 1: Source Type Inference Correctness**
    - **Validates: Requirements 1.1, 1.2**

  - [x] 1.3 Write property test for non-PDF filtering
    - **Property 3: Non-PDF Filtering**
    - **Validates: Requirements 1.4**

  - [x] 1.4 Write property test for correlation ID format
    - **Property 5: Correlation ID Format**
    - **Validates: Requirements 4.1**

  - [x] 1.5 Write property test for invalid event robustness
    - **Property 4: Invalid Event Robustness**
    - **Validates: Requirements 2.2**

- [x] 2. Create event payload data model
  - [x] 2.1 Create EventPayload dataclass with validation
    - Create `deployment/s3_event_processor/models.py`
    - Implement EventPayload dataclass with document_path, source_type, document_id, correlation_id
    - Implement validation for required fields
    - Implement to_dict() method for JSON serialization
    - _Requirements: 5.1, 5.2, 5.3, 6.2_

  - [x] 2.2 Write property test for payload round-trip serialization
    - **Property 7: Event Payload Round-Trip Serialization**
    - **Validates: Requirements 6.1**

  - [x] 2.3 Write property test for payload validation
    - **Property 8: Validation Rejects Incomplete Payloads**
    - **Validates: Requirements 6.2**

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Create CloudFormation infrastructure
  - [x] 4.1 Create CloudFormation template for Lambda and IAM
    - Create `deployment/s3_event_processor/template.yaml`
    - Define `AWS::Lambda::Function` with Python 3.11 runtime
    - Configure 60 second timeout and 256 MB memory
    - Set environment variables: AGENTCORE_RUNTIME_ARN, S3_BUCKET_NAME, AWS_REGION
    - Define `AWS::IAM::Role` execution role with trust policy for Lambda
    - Define `AWS::IAM::Policy` with permissions for:
      - `bedrock-agentcore:InvokeAgent` on the runtime ARN
      - `s3:GetObject` on the S3 bucket
      - `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
      - `cloudwatch:PutMetricData`
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 4.2 Add S3 bucket notification to CloudFormation
    - Define `AWS::Lambda::Permission` for S3 to invoke Lambda
    - Define `AWS::S3::Bucket` notification configuration with:
      - Filter for `BANK/*.pdf` uploads
      - Filter for `COUNTERPARTY/*.pdf` uploads
    - Use `Custom::S3BucketNotification` or update existing bucket
    - _Requirements: 3.4_

- [x] 5. Create Lambda deployment package
  - [x] 5.1 Create requirements.txt for Lambda dependencies
    - Create `deployment/s3_event_processor/requirements.txt`
    - Include boto3, botocore, httpx for AgentCore invocation
    - _Requirements: 3.1_

  - [x] 5.2 Create deployment script
    - Create `deployment/s3_event_processor/deploy.sh`
    - Package Lambda code with dependencies into ZIP file
    - Upload to S3 or use inline code
    - Deploy CloudFormation stack using AWS CLI
    - _Requirements: 3.1_

- [x] 6. Add CloudWatch metrics emission
  - [x] 6.1 Implement CloudWatch metrics in Lambda
    - Add metrics for S3EventsProcessed, MessagesPublished, ProcessingErrors, NonPdfEventsSkipped
    - Use boto3 CloudWatch client to emit metrics
    - _Requirements: 4.3_

- [x] 7. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
