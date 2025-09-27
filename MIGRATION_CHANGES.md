# Migration Changes: From File-Based to EKS Event-Driven Architecture

## Overview

This document outlines all the changes required to migrate the existing AI Trade Matching System from a file-based, local processing model to a cloud-native, event-driven EKS deployment.

## Current vs Target Architecture

### Current Architecture
```
Local Files (./data/BANK/, ./data/COUNTERPARTY/)
    ↓
Manual Execution (crewai run)
    ↓
CrewAI Processing (4 agents)
    ↓
Local TinyDB Storage (./storage/)
    ↓
Local Reports (./data/)
```

### Target Architecture
```
S3 Upload (BANK/, COUNTERPARTY/)
    ↓
S3 Event → SQS → Lambda
    ↓
EKS HTTP API Call
    ↓
CrewAI Processing (4 agents in containers)
    ↓
DynamoDB Storage
    ↓
SNS Notifications + CloudWatch Metrics
```

## 1. Application Code Changes

### 1.1 Main Application Entry Point

**Current**: `src/latest_trade_matching_agent/main.py`
```python
# Current implementation
def run():
    inputs = {
        'document_path': './data/COUNTERPARTY/GCS382857_V1.pdf',
        'unique_identifier': 'GCS382857',
    }

    # Static file path
    crew_instance = LatestTradeMatchingAgent(dynamodb_tools=list(dynamodb_tools))
    result = crew_instance.crew().kickoff(inputs=inputs)
```

**Required Changes**:

```python
# NEW: src/latest_trade_matching_agent/eks_main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio
import boto3
import tempfile
import os
from pathlib import Path
from datetime import datetime
import logging

app = FastAPI(title="Trade Matching System", version="1.0.0")

class ProcessingRequest(BaseModel):
    s3_bucket: str
    s3_key: str
    source_type: str  # "BANK" or "COUNTERPARTY"
    event_time: str
    unique_identifier: str
    metadata: dict = {}

class ProcessingResponse(BaseModel):
    status: str
    message: str
    unique_identifier: str
    processing_id: str

# Global status tracking
processing_status = {}

@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Kubernetes"""
    # Check dependencies (DynamoDB, S3, etc.)
    try:
        # Test DynamoDB connection
        dynamodb = boto3.client('dynamodb')
        dynamodb.list_tables()

        # Test S3 connection
        s3 = boto3.client('s3')
        s3.list_buckets()

        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

@app.post("/process", response_model=ProcessingResponse)
async def process_trade_document(request: ProcessingRequest, background_tasks: BackgroundTasks):
    """
    Process trade document from S3 event trigger
    """
    processing_id = f"{request.unique_identifier}_{int(datetime.utcnow().timestamp())}"

    try:
        # Validate request
        if request.source_type not in ["BANK", "COUNTERPARTY"]:
            raise HTTPException(status_code=400, detail="Invalid source_type. Must be BANK or COUNTERPARTY")

        # Start background processing
        background_tasks.add_task(process_document_async, request, processing_id)

        # Initialize status tracking
        processing_status[processing_id] = {
            "status": "initiated",
            "message": f"Processing started for {request.s3_key}",
            "progress": 0,
            "unique_identifier": request.unique_identifier,
            "started_at": datetime.utcnow().isoformat()
        }

        return ProcessingResponse(
            status="initiated",
            message="Processing initiated successfully",
            unique_identifier=request.unique_identifier,
            processing_id=processing_id
        )

    except Exception as e:
        logger.error(f"Failed to initiate processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate processing: {str(e)}")

@app.get("/status/{processing_id}")
async def get_processing_status(processing_id: str):
    """Get processing status for a specific document"""
    if processing_id not in processing_status:
        raise HTTPException(status_code=404, detail="Processing ID not found")
    return processing_status[processing_id]

async def process_document_async(request: ProcessingRequest, processing_id: str):
    """Background task to process trade document"""
    try:
        # Update status
        processing_status[processing_id].update({
            "status": "downloading",
            "message": "Downloading document from S3",
            "progress": 10
        })

        # Download from S3 to temporary location
        s3_client = boto3.client('s3')
        temp_dir = Path(f"/tmp/processing/{processing_id}")
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Create folder structure based on source type
        local_dir = temp_dir / "data" / request.source_type
        local_dir.mkdir(parents=True, exist_ok=True)

        # Download file
        local_file_path = local_dir / Path(request.s3_key).name
        s3_client.download_file(request.s3_bucket, request.s3_key, str(local_file_path))

        # Update status
        processing_status[processing_id].update({
            "status": "processing",
            "message": "Running CrewAI processing pipeline",
            "progress": 30
        })

        # Set up DynamoDB MCP server
        dynamodb_params = StdioServerParameters(
            command="uvx",
            args=["awslabs.dynamodb-mcp-server@latest"],
            env={
                "DDB-MCP-READONLY": "false",
                "AWS_REGION": os.getenv("AWS_REGION", "us-east-1"),
                "FASTMCP_LOG_LEVEL": "ERROR"
            }
        )

        # Process with CrewAI
        with MCPServerAdapter(dynamodb_params) as dynamodb_tools:
            crew_instance = LatestTradeMatchingAgent(dynamodb_tools=list(dynamodb_tools))

            inputs = {
                'document_path': str(local_file_path),
                'unique_identifier': request.unique_identifier,
                's3_bucket': request.s3_bucket,
                's3_key': request.s3_key,
                'source_type': request.source_type
            }

            # Update status
            processing_status[processing_id].update({
                "status": "processing",
                "message": "CrewAI agents processing document",
                "progress": 60
            })

            # Run the crew
            result = crew_instance.crew().kickoff(inputs=inputs)

            # Update status
            processing_status[processing_id].update({
                "status": "completed",
                "message": "Document processing completed successfully",
                "progress": 100,
                "completed_at": datetime.utcnow().isoformat(),
                "result": str(result)
            })

        # Cleanup temporary files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

        # Send completion notification
        await send_completion_notification(request, processing_id, "success")

    except Exception as e:
        logger.error(f"Processing failed for {processing_id}: {str(e)}")
        processing_status[processing_id].update({
            "status": "failed",
            "message": f"Processing failed: {str(e)}",
            "progress": -1,
            "failed_at": datetime.utcnow().isoformat(),
            "error": str(e)
        })

        # Send failure notification
        await send_completion_notification(request, processing_id, "failure", str(e))

async def send_completion_notification(request: ProcessingRequest, processing_id: str, status: str, error: str = None):
    """Send SNS notification on completion"""
    try:
        sns = boto3.client('sns')
        topic_arn = os.getenv('SNS_TOPIC_ARN')

        if not topic_arn:
            return

        message = {
            "processing_id": processing_id,
            "unique_identifier": request.unique_identifier,
            "source_type": request.source_type,
            "s3_key": request.s3_key,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }

        if error:
            message["error"] = error

        sns.publish(
            TopicArn=topic_arn,
            Subject=f"Trade Processing {status.title()} - {request.source_type}",
            Message=json.dumps(message, indent=2)
        )

    except Exception as e:
        logger.error(f"Failed to send notification: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### 1.2 Task Configuration Changes

**Current**: `src/latest_trade_matching_agent/config/tasks.yaml`
- Tasks expect local file paths
- Fixed S3 bucket references
- Local storage paths

**Required Changes**:

```yaml
# UPDATED: document_processing_task
document_processing_task:
  description: >
    Convert the PDF document at {document_path} to high-quality images.

    **CRITICAL: Use dynamic S3 bucket and paths from request parameters:**
    - S3 Bucket: {s3_bucket}
    - Source PDF S3 Key: {s3_key}
    - Source Type: {source_type}
    - Output S3 prefix: {s3_bucket}/PDFIMAGES/{source_type}/{unique_identifier}/

    **WORKFLOW:**
    1. PDF already downloaded locally to {document_path}
    2. Convert PDF to high-resolution JPEG images (300 DPI)
    3. Save to S3: {s3_bucket}/PDFIMAGES/{source_type}/{unique_identifier}/
    4. Also save locally to /tmp/processing/{unique_identifier}/pdf_images/ for next agent
    5. Use unique_identifier: {unique_identifier} for folder naming

    **OUTPUT REQUIREMENTS:**
    - Convert each page to high-resolution JPEG images for S3
    - MUST save JPEG images locally to /tmp/processing/{unique_identifier}/pdf_images/
    - Use 3-digit padding: page_001.jpg, page_002.jpg, etc.
    - Create metadata.json with file list and conversion details
    - Return S3 folder path for next agent

  expected_output: >
    Confirmation of successful conversion:
    - "Source PDF type: {source_type}"
    - "Images saved to: {s3_bucket}/PDFIMAGES/{source_type}/{unique_identifier}/"
    - "Local images saved to: /tmp/processing/{unique_identifier}/pdf_images/"
    - "Total pages converted: [X]"

# UPDATED: trade_entity_extractor_task
trade_entity_extractor_task:
  description: >
    **CRITICAL DATA EXTRACTION WITH S3 INTEGRATION:**
    Source Type: {source_type}
    S3 Bucket: {s3_bucket}
    S3 Key: {s3_key}

    **MANDATORY WORKFLOW:**
    1. **ACCESS LOCAL IMAGES:**
       - Images saved locally to /tmp/processing/{unique_identifier}/pdf_images/
       - Use OCR tool on local JPEG files

    2. **EXTRACT AND VALIDATE TRADE SOURCE:**
       - TRADE_SOURCE = {source_type} (from request parameters)
       - Validate source type is either "BANK" or "COUNTERPARTY"

    3. **SAVE EXTRACTED DATA TO S3:**
       - Save JSON to: {s3_bucket}/extracted/{source_type}/trade_{unique_identifier}_{timestamp}.json
       - Include all extracted trade data
       - Include metadata: s3_source_key, processing_timestamp, source_type

  expected_output: >
    "Extracted trade data saved to: {s3_bucket}/extracted/{source_type}/trade_{unique_identifier}_{timestamp}.json"
    "TRADE_SOURCE confirmed as: {source_type}"
    "S3 path for next agent: {s3_bucket}/extracted/{source_type}/trade_{unique_identifier}_{timestamp}.json"

# UPDATED: reporting_task
reporting_task:
  description: >
    **CRITICAL: Store in correct DynamoDB table based on source type**

    **TABLE SELECTION (MANDATORY):**
    - Source Type: {source_type}
    - IF source_type = "BANK" → Store in table: {dynamodb_bank_table}
    - IF source_type = "COUNTERPARTY" → Store in table: {dynamodb_counterparty_table}

    **WORKFLOW:**
    1. Get JSON from S3 path provided by previous agent
    2. Parse trade data from JSON
    3. Validate source_type matches {source_type}
    4. Store in correct DynamoDB table based on source_type
    5. Use Trade_ID as primary key
    6. Include processing metadata (s3_source, processing_timestamp)

  expected_output: >
    "Successfully stored {source_type} trade in correct DynamoDB table"
    "Table used: [BankTradeData/CounterpartyTradeData]"
    "Record key: [Trade_ID]"

# UPDATED: matching_task
matching_task:
  description: >
    **ENHANCED MATCHING WITH CLOUD STORAGE:**

    **TABLES TO MATCH:**
    - Bank trades: {dynamodb_bank_table}
    - Counterparty trades: {dynamodb_counterparty_table}

    **WORKFLOW:**
    1. Verify data integrity across both DynamoDB tables
    2. Perform intelligent matching between bank and counterparty trades
    3. Generate comprehensive matching report
    4. Save report to S3: {s3_bucket}/reports/matching_report_{unique_identifier}_{timestamp}.md
    5. Send summary via SNS if configured

  expected_output: >
    "Matching completed between {dynamodb_bank_table} and {dynamodb_counterparty_table}"
    "Report saved to: {s3_bucket}/reports/matching_report_{unique_identifier}_{timestamp}.md"
    "Match rate: [X%]"
```

### 1.3 PDF Processing Tool Changes

**Current**: `src/latest_trade_matching_agent/tools/pdf_to_image.py`
- Hard-coded S3 bucket names
- Fixed local paths

**Required Changes**:

```python
# UPDATED: src/latest_trade_matching_agent/tools/pdf_to_image.py

class PDFToImageInput(BaseModel):
    """Input schema for PDFToImageTool."""
    pdf_path: str = Field(
        description="Path to the PDF file (local path)"
    )
    s3_output_bucket: str = Field(
        description="S3 bucket for output images (from request parameters)"
    )
    s3_output_prefix: str = Field(
        description="S3 prefix/folder for output images (e.g., PDFIMAGES/BANK/unique_id)"
    )
    source_type: str = Field(
        description="Source type: BANK or COUNTERPARTY"
    )
    unique_identifier: str = Field(
        description="Unique identifier for this processing request"
    )
    dpi: int = Field(200, description="DPI for image quality")
    output_format: str = Field("JPEG", description="Output image format")

class PDFToImageTool(BaseTool):
    name: str = "PDF to Image Converter"
    description: str = (
        "Converts PDF documents to images and saves them to S3 and locally. "
        "Uses dynamic S3 bucket and path configuration from request parameters."
    )
    args_schema: Type[BaseModel] = PDFToImageInput

    def _run(
        self,
        pdf_path: str,
        s3_output_bucket: str,
        s3_output_prefix: str,
        source_type: str,
        unique_identifier: str,
        dpi: int = 200,
        output_format: str = "JPEG"
    ) -> str:
        """Convert PDF to images and upload to S3 while saving locally"""
        try:
            # Validate inputs
            if not all([s3_output_bucket, s3_output_prefix, source_type, unique_identifier]):
                raise ValueError("Missing required parameters: s3_output_bucket, s3_output_prefix, source_type, or unique_identifier")

            if source_type not in ["BANK", "COUNTERPARTY"]:
                raise ValueError(f"Invalid source_type: {source_type}. Must be BANK or COUNTERPARTY")

            # Initialize S3 client
            s3_client = boto3.client('s3')

            # Generate timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Create S3 folder path
            s3_folder = f"{s3_output_prefix}/{unique_identifier}_{timestamp}"

            # Create local output directory
            local_path = Path(f"/tmp/processing/{unique_identifier}/pdf_images")
            local_path.mkdir(parents=True, exist_ok=True)

            # Convert PDF to images
            logger.info(f"Converting PDF to images at {dpi} DPI")
            images = convert_from_path(pdf_path, dpi=dpi)

            s3_locations = []
            local_locations = []

            for i, image in enumerate(images, start=1):
                # Save locally
                local_file_path = local_path / f"{unique_identifier}_page_{i:03d}.jpg"
                image.save(local_file_path, "JPEG", quality=95)
                local_locations.append(str(local_file_path))

                # Save to S3
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_img:
                    image.save(tmp_img.name, "JPEG", quality=95)

                    s3_key = f"{s3_folder}/{unique_identifier}_page_{i:03d}.jpg"
                    with open(tmp_img.name, 'rb') as img_data:
                        s3_client.put_object(
                            Bucket=s3_output_bucket,
                            Key=s3_key,
                            Body=img_data,
                            ContentType='image/jpeg',
                            Metadata={
                                'source_pdf': pdf_path,
                                'page_number': str(i),
                                'source_type': source_type,
                                'unique_identifier': unique_identifier,
                                'dpi': str(dpi),
                                'conversion_timestamp': timestamp
                            }
                        )

                    s3_locations.append(f"s3://{s3_output_bucket}/{s3_key}")
                    os.unlink(tmp_img.name)

            # Create metadata
            metadata = {
                'source_pdf': pdf_path,
                'source_type': source_type,
                'unique_identifier': unique_identifier,
                'conversion_timestamp': timestamp,
                'total_pages': len(images),
                'dpi': dpi,
                's3_bucket': s3_output_bucket,
                's3_folder': f"s3://{s3_output_bucket}/{s3_folder}/",
                'local_folder': str(local_path),
                'image_files': [Path(loc).name for loc in s3_locations]
            }

            # Save metadata to S3
            metadata_key = f"{s3_folder}/metadata.json"
            s3_client.put_object(
                Bucket=s3_output_bucket,
                Key=metadata_key,
                Body=json.dumps(metadata, indent=2),
                ContentType='application/json'
            )

            # Save metadata locally
            with open(local_path / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)

            result_message = f"""
✅ PDF Conversion Successful!
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 Source: {pdf_path}
📊 Total Pages: {len(images)}
🎯 DPI: {dpi}
📸 Format: JPEG
☁️  S3 Location: s3://{s3_output_bucket}/{s3_folder}/
💾 Local Path: {local_path}
🏷️  Source Type: {source_type}
🆔 Unique ID: {unique_identifier}
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Images ready for OCR processing
Local path for next agent: {local_path}
"""

            return result_message

        except Exception as e:
            error_msg = f"❌ Error converting PDF to images: {str(e)}"
            logger.error(error_msg)
            return error_msg
```

### 1.4 Environment Configuration Changes

**Current**: `.env` file with local settings

**Required**: New environment configuration for Kubernetes

```bash
# NEW: k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: trade-matching-config
  namespace: trading
data:
  # AWS Configuration
  AWS_REGION: "us-east-1"

  # S3 Configuration
  S3_BUCKET_NAME: "trade-documents-production"

  # DynamoDB Configuration
  DYNAMODB_BANK_TABLE: "BankTradeData"
  DYNAMODB_COUNTERPARTY_TABLE: "CounterpartyTradeData"

  # Application Configuration
  LOG_LEVEL: "INFO"
  MAX_WORKERS: "4"
  PROCESSING_TIMEOUT: "1800"  # 30 minutes

  # CrewAI Configuration
  MAX_RPM: "10"
  MAX_EXECUTION_TIME: "1200"  # 20 minutes per agent

  # Monitoring
  METRICS_PORT: "9090"
  HEALTH_CHECK_PORT: "8080"
---
apiVersion: v1
kind: Secret
metadata:
  name: trade-matching-secrets
  namespace: trading
type: Opaque
data:
  # Base64 encoded values
  sns-topic-arn: <base64-encoded-sns-topic-arn>
  openai-api-key: <base64-encoded-openai-key>
```

### 1.5 Agent Configuration Updates

**Current**: Agents configured for local processing

**Required Changes** in `src/latest_trade_matching_agent/crew_fixed.py`:

```python
# UPDATED: crew_fixed.py

import os
from typing import List, Optional, Dict, Any

class LatestTradeMatchingAgent:
    """Enhanced LatestTradeMatchingAgent crew for EKS deployment"""

    def __init__(self,
                 dynamodb_tools: Optional[List] = None,
                 request_context: Optional[Dict[str, Any]] = None):
        """
        Initialize with request context from EKS API

        Args:
            dynamodb_tools: List of MCP tools from DynamoDB adapter
            request_context: Request parameters (s3_bucket, source_type, etc.)
        """
        self.dynamodb_tools = dynamodb_tools or []
        self.request_context = request_context or {}

        # Get configuration from environment
        self.config = {
            's3_bucket': os.getenv('S3_BUCKET_NAME',
                                 self.request_context.get('s3_bucket', 'trade-documents-production')),
            'dynamodb_bank_table': os.getenv('DYNAMODB_BANK_TABLE', 'BankTradeData'),
            'dynamodb_counterparty_table': os.getenv('DYNAMODB_COUNTERPARTY_TABLE', 'CounterpartyTradeData'),
            'max_rpm': int(os.getenv('MAX_RPM', '10')),
            'max_execution_time': int(os.getenv('MAX_EXECUTION_TIME', '1200')),
            'aws_region': os.getenv('AWS_REGION', 'us-east-1')
        }

        if self.dynamodb_tools:
            logger.info(f"Initialized with {len(self.dynamodb_tools)} DynamoDB tools")

    @agent
    def document_processor(self) -> Agent:
        return Agent(
            config=self.agents_config['document_processor'],
            llm=llm,
            tools=[PDFToImageTool(), FileWriterTool()],
            verbose=True,
            max_rpm=self.config['max_rpm'],
            max_iter=3,
            max_execution_time=self.config['max_execution_time'],
            multimodal=True
        )

    @task
    def document_processing_task(self) -> Task:
        # Inject request context into task
        task_config = self.tasks_config['document_processing_task'].copy()

        # Format task description with request context
        if self.request_context:
            task_config['description'] = task_config['description'].format(
                **self.request_context,
                **self.config
            )

        return Task(
            config=task_config,
            agent=self.document_processor()
        )

    @task
    def research_task(self) -> Task:
        task_config = self.tasks_config['trade_entity_extractor_task'].copy()

        if self.request_context:
            task_config['description'] = task_config['description'].format(
                **self.request_context,
                **self.config
            )

        return Task(
            config=task_config,
            agent=self.trade_entity_extractor()
        )

    @task
    def reporting_task(self) -> Task:
        task_config = self.tasks_config['reporting_task'].copy()

        if self.request_context:
            task_config['description'] = task_config['description'].format(
                **self.request_context,
                **self.config
            )

        return Task(
            config=task_config,
            agent=self.reporting_analyst()
        )

    @task
    def matching_task(self) -> Task:
        task_config = self.tasks_config['matching_task'].copy()

        if self.request_context:
            task_config['description'] = task_config['description'].format(
                **self.request_context,
                **self.config
            )

        return Task(
            config=task_config,
            agent=self.matching_analyst()
        )

    def set_request_context(self, context: Dict[str, Any]):
        """Update request context for dynamic task configuration"""
        self.request_context = context

    @crew
    def crew(self) -> Crew:
        """Creates the enhanced LatestTradeMatchingAgent crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=False,
            verbose=True,
            max_rpm=self.config['max_rpm'],
            share_crew=False,
            # Add execution callbacks for monitoring
            step_callback=self._step_callback,
            task_callback=self._task_callback
        )

    def _step_callback(self, step):
        """Callback for monitoring step execution"""
        logger.info(f"Crew step executed: {step}")

    def _task_callback(self, task):
        """Callback for monitoring task completion"""
        logger.info(f"Task completed: {task.description[:100]}...")
```

## 2. Infrastructure Changes

### 2.1 Database Migration: TinyDB → DynamoDB

**Current**: Local TinyDB files in `./storage/`

**Required**: DynamoDB tables with proper schema

```python
# NEW: src/database/dynamodb_migration.py

import boto3
from tinydb import TinyDB
import json
from datetime import datetime

class DatabaseMigrator:
    def __init__(self, region='us-east-1'):
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.bank_table = self.dynamodb.Table('BankTradeData')
        self.counterparty_table = self.dynamodb.Table('CounterpartyTradeData')

    def migrate_tinydb_to_dynamodb(self, tinydb_path: str):
        """Migrate existing TinyDB data to DynamoDB"""

        # Read existing TinyDB data
        bank_db = TinyDB(f"{tinydb_path}/bank_trade_data.db")
        counterparty_db = TinyDB(f"{tinydb_path}/counterparty_trade_data.db")

        migrated_count = 0

        # Migrate bank trades
        for record in bank_db.all():
            try:
                # Add migration metadata
                record['migration_timestamp'] = datetime.utcnow().isoformat()
                record['migrated_from'] = 'tinydb'
                record['TRADE_SOURCE'] = 'BANK'

                self.bank_table.put_item(Item=record)
                migrated_count += 1

            except Exception as e:
                print(f"Failed to migrate bank record {record.get('Trade_ID', 'unknown')}: {e}")

        # Migrate counterparty trades
        for record in counterparty_db.all():
            try:
                record['migration_timestamp'] = datetime.utcnow().isoformat()
                record['migrated_from'] = 'tinydb'
                record['TRADE_SOURCE'] = 'COUNTERPARTY'

                self.counterparty_table.put_item(Item=record)
                migrated_count += 1

            except Exception as e:
                print(f"Failed to migrate counterparty record {record.get('Trade_ID', 'unknown')}: {e}")

        bank_db.close()
        counterparty_db.close()

        return migrated_count

    def validate_migration(self):
        """Validate migrated data"""
        bank_count = self.bank_table.scan(Select='COUNT')['Count']
        counterparty_count = self.counterparty_table.scan(Select='COUNT')['Count']

        print(f"Bank trades in DynamoDB: {bank_count}")
        print(f"Counterparty trades in DynamoDB: {counterparty_count}")

        return bank_count, counterparty_count
```

### 2.2 Storage Migration: Local Files → S3

**Current**: Local file storage in `./data/`, `./storage/`, `./pdf_images/`

**Required**: S3 bucket structure and migration

```python
# NEW: src/storage/s3_migration.py

import boto3
import os
from pathlib import Path
import mimetypes

class S3Migrator:
    def __init__(self, bucket_name: str, region='us-east-1'):
        self.s3_client = boto3.client('s3', region_name=region)
        self.bucket_name = bucket_name

    def migrate_local_files_to_s3(self, local_data_path: str = "./data"):
        """Migrate existing local files to S3"""

        local_path = Path(local_data_path)
        migrated_files = []

        # Migrate BANK folder
        bank_path = local_path / "BANK"
        if bank_path.exists():
            for pdf_file in bank_path.glob("*.pdf"):
                s3_key = f"BANK/{datetime.now().strftime('%Y/%m/%d')}/{pdf_file.name}"
                self._upload_file(pdf_file, s3_key)
                migrated_files.append(s3_key)

        # Migrate COUNTERPARTY folder
        counterparty_path = local_path / "COUNTERPARTY"
        if counterparty_path.exists():
            for pdf_file in counterparty_path.glob("*.pdf"):
                s3_key = f"COUNTERPARTY/{datetime.now().strftime('%Y/%m/%d')}/{pdf_file.name}"
                self._upload_file(pdf_file, s3_key)
                migrated_files.append(s3_key)

        return migrated_files

    def _upload_file(self, local_file: Path, s3_key: str):
        """Upload single file to S3"""
        try:
            content_type = mimetypes.guess_type(str(local_file))[0] or 'application/octet-stream'

            self.s3_client.upload_file(
                str(local_file),
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'Metadata': {
                        'original-path': str(local_file),
                        'migration-timestamp': datetime.utcnow().isoformat(),
                        'migrated-from': 'local-file-system'
                    }
                }
            )

            print(f"Uploaded {local_file} to s3://{self.bucket_name}/{s3_key}")

        except Exception as e:
            print(f"Failed to upload {local_file}: {e}")
```

## 3. Deployment Changes

### 3.1 Container Configuration

**Required**: New files for containerization

```dockerfile
# NEW: Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    gcc \
    g++ \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for EKS
RUN pip install fastapi uvicorn prometheus-client

# Copy application code
COPY src/ ./src/
COPY *.py ./

# Create necessary directories
RUN mkdir -p /tmp/processing /app/logs

# Create non-root user for security
RUN useradd -m -u 1000 trader && \
    chown -R trader:trader /app /tmp/processing

USER trader

# Expose ports
EXPOSE 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Start application
CMD ["python", "src/latest_trade_matching_agent/eks_main.py"]
```

### 3.2 Kubernetes Manifests

**Required**: New Kubernetes deployment files

```yaml
# NEW: k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: trading
  labels:
    name: trading
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted

---
# NEW: k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trade-matching-system
  namespace: trading
  labels:
    app: trade-matching-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: trade-matching-system
  template:
    metadata:
      labels:
        app: trade-matching-system
    spec:
      serviceAccountName: trade-matching-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: trade-processor
        image: ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/trade-matching-system:latest
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 9090
          name: metrics
        env:
        - name: AWS_REGION
          valueFrom:
            configMapKeyRef:
              name: trade-matching-config
              key: AWS_REGION
        - name: S3_BUCKET_NAME
          valueFrom:
            configMapKeyRef:
              name: trade-matching-config
              key: S3_BUCKET_NAME
        - name: DYNAMODB_BANK_TABLE
          valueFrom:
            configMapKeyRef:
              name: trade-matching-config
              key: DYNAMODB_BANK_TABLE
        - name: DYNAMODB_COUNTERPARTY_TABLE
          valueFrom:
            configMapKeyRef:
              name: trade-matching-config
              key: DYNAMODB_COUNTERPARTY_TABLE
        - name: SNS_TOPIC_ARN
          valueFrom:
            secretKeyRef:
              name: trade-matching-secrets
              key: sns-topic-arn
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        volumeMounts:
        - name: temp-storage
          mountPath: /tmp/processing
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 5
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
          readOnlyRootFilesystem: false
      volumes:
      - name: temp-storage
        emptyDir:
          sizeLimit: 10Gi
```

## 4. Configuration Management Changes

### 4.1 Environment-Based Configuration

**Current**: Single `.env` file

**Required**: Environment-specific configurations

```python
# NEW: src/config/settings.py

import os
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # AWS Configuration
    aws_region: str = "us-east-1"
    s3_bucket_name: str
    dynamodb_bank_table: str = "BankTradeData"
    dynamodb_counterparty_table: str = "CounterpartyTradeData"

    # SNS Configuration
    sns_topic_arn: Optional[str] = None

    # Application Configuration
    log_level: str = "INFO"
    max_workers: int = 4
    processing_timeout: int = 1800

    # CrewAI Configuration
    max_rpm: int = 10
    max_execution_time: int = 1200

    # LLM Configuration
    bedrock_model: str = "bedrock/amazon.nova-pro-v1:0"
    openai_api_key: Optional[str] = None

    # Monitoring
    metrics_port: int = 9090
    health_check_port: int = 8080

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
```

### 4.2 Secrets Management

**Current**: Plain text in `.env`

**Required**: Kubernetes secrets integration

```python
# NEW: src/config/secrets.py

import os
import boto3
import json
from typing import Dict, Any

class SecretsManager:
    def __init__(self):
        self.secrets_client = boto3.client('secretsmanager')

    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Get secret from AWS Secrets Manager"""
        try:
            response = self.secrets_client.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except Exception as e:
            print(f"Failed to get secret {secret_name}: {e}")
            return {}

    def get_kubernetes_secret(self, key: str) -> str:
        """Get secret from Kubernetes environment"""
        return os.getenv(key, "")
```

## 5. Monitoring and Observability Changes

### 5.1 Metrics and Logging

**Required**: Enhanced monitoring integration

```python
# NEW: src/monitoring/metrics.py

from prometheus_client import Counter, Histogram, Gauge, start_http_server
import logging
import time
from functools import wraps

# Prometheus metrics
DOCUMENTS_PROCESSED = Counter(
    'trade_documents_processed_total',
    'Total documents processed',
    ['source_type', 'status']
)

PROCESSING_DURATION = Histogram(
    'trade_processing_duration_seconds',
    'Time spent processing documents',
    ['source_type', 'agent']
)

ACTIVE_PROCESSING = Gauge(
    'trade_active_processing',
    'Currently processing documents'
)

CREW_AGENT_DURATION = Histogram(
    'crew_agent_duration_seconds',
    'Agent processing time',
    ['agent_name', 'task_name']
)

ERROR_COUNT = Counter(
    'trade_processing_errors_total',
    'Total processing errors',
    ['error_type', 'source_type']
)

def track_processing_time(source_type: str, agent_name: str = "unknown"):
    """Decorator to track processing time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                DOCUMENTS_PROCESSED.labels(
                    source_type=source_type,
                    status='success'
                ).inc()
                return result
            except Exception as e:
                DOCUMENTS_PROCESSED.labels(
                    source_type=source_type,
                    status='error'
                ).inc()
                ERROR_COUNT.labels(
                    error_type=type(e).__name__,
                    source_type=source_type
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                PROCESSING_DURATION.labels(
                    source_type=source_type,
                    agent=agent_name
                ).observe(duration)
        return wrapper
    return decorator

def start_metrics_server(port: int = 9090):
    """Start Prometheus metrics server"""
    start_http_server(port)
    logging.info(f"Metrics server started on port {port}")
```

### 5.2 Structured Logging

**Required**: JSON-formatted logging for CloudWatch

```python
# NEW: src/monitoring/logging.py

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add extra fields
        if hasattr(record, 'unique_identifier'):
            log_entry['unique_identifier'] = record.unique_identifier
        if hasattr(record, 'source_type'):
            log_entry['source_type'] = record.source_type
        if hasattr(record, 'processing_id'):
            log_entry['processing_id'] = record.processing_id

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

def setup_logging(log_level: str = "INFO"):
    """Setup structured logging"""

    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create new handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    # Configure root logger
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Configure specific loggers
    logging.getLogger('crewai').setLevel(logging.INFO)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

class TradeProcessingLogger:
    """Context-aware logger for trade processing"""

    def __init__(self, unique_identifier: str, source_type: str, processing_id: str = None):
        self.logger = logging.getLogger(__name__)
        self.unique_identifier = unique_identifier
        self.source_type = source_type
        self.processing_id = processing_id

    def _log(self, level: str, message: str, **kwargs):
        """Log with context"""
        extra = {
            'unique_identifier': self.unique_identifier,
            'source_type': self.source_type,
            **kwargs
        }
        if self.processing_id:
            extra['processing_id'] = self.processing_id

        getattr(self.logger, level)(message, extra=extra)

    def info(self, message: str, **kwargs):
        self._log('info', message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log('error', message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log('warning', message, **kwargs)

    def debug(self, message: str, **kwargs):
        self._log('debug', message, **kwargs)
```

## 6. Testing Changes

### 6.1 Test Environment Updates

**Required**: New test configurations for cloud environment

```python
# NEW: tests/test_eks_integration.py

import pytest
import boto3
from moto import mock_s3, mock_dynamodb, mock_sns
import json
from pathlib import Path
from src.latest_trade_matching_agent.eks_main import app
from fastapi.testclient import TestClient

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def mock_aws_services():
    with mock_s3(), mock_dynamodb(), mock_sns():
        # Setup mock S3
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-trade-documents')

        # Setup mock DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

        # Create bank table
        bank_table = dynamodb.create_table(
            TableName='BankTradeData',
            KeySchema=[{'AttributeName': 'Trade_ID', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'Trade_ID', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        # Create counterparty table
        cp_table = dynamodb.create_table(
            TableName='CounterpartyTradeData',
            KeySchema=[{'AttributeName': 'Trade_ID', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'Trade_ID', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        yield {
            's3': s3,
            'dynamodb': dynamodb,
            'bank_table': bank_table,
            'cp_table': cp_table
        }

def test_health_check(test_client):
    """Test health check endpoint"""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_process_document_endpoint(test_client, mock_aws_services):
    """Test document processing endpoint"""

    # Upload test PDF to mock S3
    test_pdf_content = b'%PDF-1.4 test content'
    mock_aws_services['s3'].put_object(
        Bucket='test-trade-documents',
        Key='BANK/2024/01/01/test-trade.pdf',
        Body=test_pdf_content
    )

    request_data = {
        "s3_bucket": "test-trade-documents",
        "s3_key": "BANK/2024/01/01/test-trade.pdf",
        "source_type": "BANK",
        "event_time": "2024-01-01T10:30:00.000Z",
        "unique_identifier": "test-trade-001"
    }

    response = test_client.post("/process", json=request_data)
    assert response.status_code == 200

    response_data = response.json()
    assert response_data["status"] == "initiated"
    assert "processing_id" in response_data

def test_status_endpoint(test_client, mock_aws_services):
    """Test status checking endpoint"""

    # First initiate processing
    request_data = {
        "s3_bucket": "test-trade-documents",
        "s3_key": "BANK/2024/01/01/test-trade.pdf",
        "source_type": "BANK",
        "event_time": "2024-01-01T10:30:00.000Z",
        "unique_identifier": "test-trade-001"
    }

    process_response = test_client.post("/process", json=request_data)
    processing_id = process_response.json()["processing_id"]

    # Check status
    status_response = test_client.get(f"/status/{processing_id}")
    assert status_response.status_code == 200

    status_data = status_response.json()
    assert "status" in status_data
    assert "message" in status_data
```

## 7. Migration Strategy and Rollback Plan

### 7.1 Phased Migration Approach

```bash
# NEW: scripts/migration.sh

#!/bin/bash

set -e

echo "Starting migration from file-based to EKS deployment..."

# Phase 1: Infrastructure Setup
echo "Phase 1: Setting up infrastructure..."
./scripts/setup-infrastructure.sh

# Phase 2: Data Migration
echo "Phase 2: Migrating data..."
python src/database/dynamodb_migration.py
python src/storage/s3_migration.py

# Phase 3: Application Deployment
echo "Phase 3: Deploying application..."
./scripts/deploy-application.sh

# Phase 4: Validation
echo "Phase 4: Validating deployment..."
./scripts/validate-deployment.sh

echo "Migration completed successfully!"
```

### 7.2 Rollback Procedures

```bash
# NEW: scripts/rollback.sh

#!/bin/bash

set -e

echo "Starting rollback to file-based system..."

# Stop EKS application
kubectl delete deployment trade-matching-system -n trading

# Export DynamoDB data back to TinyDB
python src/database/rollback_migration.py

# Download S3 files back to local storage
python src/storage/rollback_s3.py

# Restore original configuration
cp .env.backup .env
cp src/latest_trade_matching_agent/main.py.backup src/latest_trade_matching_agent/main.py

echo "Rollback completed. System restored to file-based operation."
```

## Summary of Key Changes

### Critical Application Changes:
1. **New FastAPI wrapper** (`eks_main.py`) for HTTP API
2. **Dynamic configuration** injection into tasks and agents
3. **S3 integration** throughout the PDF processing pipeline
4. **DynamoDB replacement** for TinyDB storage
5. **Environment-based configuration** management
6. **Structured logging** and metrics integration

### Infrastructure Changes:
1. **EKS cluster** with auto-scaling capabilities
2. **S3 event-driven** architecture with Lambda triggers
3. **DynamoDB tables** with proper partitioning
4. **SNS notifications** for processing status
5. **CloudWatch monitoring** and alerting

### Deployment Changes:
1. **Container-based** deployment with Docker
2. **Kubernetes manifests** for orchestration
3. **Secrets management** via Kubernetes/AWS
4. **Multi-environment** configuration support
5. **CI/CD pipeline** integration ready

This comprehensive migration transforms your system from a local, file-based solution into a production-ready, cloud-native application capable of handling enterprise-scale trade processing workloads.