# Complete Changes Guide: File-Based to EKS Event-Driven Migration

## Table of Contents
1. [Overview](#overview)
2. [Before/After Architecture](#beforeafter-architecture)
3. [File-by-File Changes](#file-by-file-changes)
4. [New Files to Create](#new-files-to-create)
5. [Infrastructure Changes](#infrastructure-changes)
6. [Configuration Changes](#configuration-changes)
7. [Implementation Checklist](#implementation-checklist)
8. [Testing Verification](#testing-verification)

## Overview

This document provides a complete guide for transforming the AI Trade Matching System from a file-based, manual execution model to a cloud-native, event-driven architecture on Amazon EKS.

### Migration Summary
- **From**: Local file processing with manual execution (`crewai run`)
- **To**: S3 event-triggered processing with auto-scaling on EKS
- **Database**: TinyDB → DynamoDB
- **Storage**: Local files → S3 buckets
- **Execution**: Manual → Event-driven via Lambda + EKS API

## Before/After Architecture

### Current Architecture
```
Local Files (./data/BANK/, ./data/COUNTERPARTY/)
    ↓ (manual execution)
crewai run (main.py)
    ↓
CrewAI Agents (4 agents)
    ↓
TinyDB Storage (./storage/)
    ↓
Local Reports (./data/)
```

### Target Architecture
```
S3 Upload (BANK/, COUNTERPARTY/)
    ↓ (automatic)
S3 Event → SQS → Lambda
    ↓ (HTTP API call)
EKS Pods (FastAPI + CrewAI)
    ↓
DynamoDB Tables
    ↓
SNS Notifications + S3 Reports
```

## File-by-File Changes

### 1. Main Application Entry Point

#### BEFORE: `src/latest_trade_matching_agent/main.py`
```python
# Current implementation - MANUAL EXECUTION
def run():
    # Static inputs - HARDCODED
    inputs = {
        'document_path': './data/COUNTERPARTY/GCS382857_V1.pdf',  # FIXED PATH
        'unique_identifier': 'GCS382857',  # FIXED ID
    }

    # Local DynamoDB server
    dynamodb_params = StdioServerParameters(
        command="uvx",
        args=["awslabs.dynamodb-mcp-server@latest"],
        env={
            "DDB-MCP-READONLY": "false",
            "AWS_PROFILE": "default",  # LOCAL PROFILE
            "AWS_REGION": "us-east-1",
            "FASTMCP_LOG_LEVEL": "ERROR"
        }
    )

    # Direct execution - NO API
    with MCPServerAdapter(dynamodb_params) as dynamodb_tools:
        crew_instance = LatestTradeMatchingAgent(dynamodb_tools=list(dynamodb_tools))
        result = crew_instance.crew().kickoff(inputs=inputs)  # SYNCHRONOUS

    print("\nCrew execution completed successfully!")
    return result

if __name__ == "__main__":
    run()  # DIRECT EXECUTION
```

#### AFTER: `src/latest_trade_matching_agent/eks_main.py` (NEW FILE)
```python
# New implementation - EVENT-DRIVEN API
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio
import boto3
import tempfile
import os
from pathlib import Path
from datetime import datetime
import logging
import json
from latest_trade_matching_agent.crew_fixed import LatestTradeMatchingAgent
from mcp import StdioServerParameters
from crewai_tools import MCPServerAdapter

app = FastAPI(title="Trade Matching System", version="1.0.0")

# REQUEST MODEL - DYNAMIC INPUTS
class ProcessingRequest(BaseModel):
    s3_bucket: str          # DYNAMIC S3 BUCKET
    s3_key: str            # DYNAMIC FILE PATH
    source_type: str       # BANK or COUNTERPARTY
    event_time: str        # EVENT TIMESTAMP
    unique_identifier: str # DYNAMIC ID
    metadata: dict = {}    # ADDITIONAL METADATA

class ProcessingResponse(BaseModel):
    status: str
    message: str
    unique_identifier: str
    processing_id: str

# GLOBAL STATUS TRACKING
processing_status = {}

# KUBERNETES HEALTH CHECKS
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes liveness probe"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Kubernetes readiness probe"""
    try:
        # Test AWS service connectivity
        dynamodb = boto3.client('dynamodb')
        dynamodb.list_tables()

        s3 = boto3.client('s3')
        s3.list_buckets()

        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

# EVENT-DRIVEN PROCESSING ENDPOINT
@app.post("/process", response_model=ProcessingResponse)
async def process_trade_document(request: ProcessingRequest, background_tasks: BackgroundTasks):
    """Process trade document from S3 event trigger"""
    processing_id = f"{request.unique_identifier}_{int(datetime.utcnow().timestamp())}"

    try:
        # VALIDATION
        if request.source_type not in ["BANK", "COUNTERPARTY"]:
            raise HTTPException(status_code=400, detail="Invalid source_type")

        # ASYNCHRONOUS BACKGROUND PROCESSING
        background_tasks.add_task(process_document_async, request, processing_id)

        # STATUS TRACKING
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

# STATUS MONITORING ENDPOINT
@app.get("/status/{processing_id}")
async def get_processing_status(processing_id: str):
    """Get processing status for a specific document"""
    if processing_id not in processing_status:
        raise HTTPException(status_code=404, detail="Processing ID not found")
    return processing_status[processing_id]

# BACKGROUND PROCESSING FUNCTION
async def process_document_async(request: ProcessingRequest, processing_id: str):
    """Background task to process trade document"""
    try:
        # DOWNLOAD FROM S3
        processing_status[processing_id].update({
            "status": "downloading",
            "message": "Downloading document from S3",
            "progress": 10
        })

        s3_client = boto3.client('s3')
        temp_dir = Path(f"/tmp/processing/{processing_id}")
        temp_dir.mkdir(parents=True, exist_ok=True)

        # CREATE DYNAMIC FOLDER STRUCTURE
        local_dir = temp_dir / "data" / request.source_type
        local_dir.mkdir(parents=True, exist_ok=True)

        local_file_path = local_dir / Path(request.s3_key).name
        s3_client.download_file(request.s3_bucket, request.s3_key, str(local_file_path))

        # CREWAI PROCESSING
        processing_status[processing_id].update({
            "status": "processing",
            "message": "Running CrewAI processing pipeline",
            "progress": 30
        })

        # CLOUD DYNAMODB CONFIGURATION
        dynamodb_params = StdioServerParameters(
            command="uvx",
            args=["awslabs.dynamodb-mcp-server@latest"],
            env={
                "DDB-MCP-READONLY": "false",
                "AWS_REGION": os.getenv("AWS_REGION", "us-east-1"),
                "FASTMCP_LOG_LEVEL": "ERROR"
            }
        )

        # ENHANCED CREWAI EXECUTION
        with MCPServerAdapter(dynamodb_params) as dynamodb_tools:
            crew_instance = LatestTradeMatchingAgent(
                dynamodb_tools=list(dynamodb_tools),
                request_context=request.dict()  # INJECT REQUEST CONTEXT
            )

            # DYNAMIC INPUTS FROM REQUEST
            inputs = {
                'document_path': str(local_file_path),
                'unique_identifier': request.unique_identifier,
                's3_bucket': request.s3_bucket,
                's3_key': request.s3_key,
                'source_type': request.source_type
            }

            processing_status[processing_id].update({
                "status": "processing",
                "message": "CrewAI agents processing document",
                "progress": 60
            })

            result = crew_instance.crew().kickoff(inputs=inputs)

            processing_status[processing_id].update({
                "status": "completed",
                "message": "Document processing completed successfully",
                "progress": 100,
                "completed_at": datetime.utcnow().isoformat(),
                "result": str(result)
            })

        # CLEANUP
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

        # NOTIFICATION
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

        await send_completion_notification(request, processing_id, "failure", str(e))

# SNS NOTIFICATION FUNCTION
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

# APPLICATION STARTUP
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### 2. CrewAI Configuration Updates

#### BEFORE: `src/latest_trade_matching_agent/crew_fixed.py`
```python
# Current implementation - STATIC CONFIGURATION
@CrewBase
class LatestTradeMatchingAgent:
    """LatestTradeMatchingAgent crew"""
    agents: List[BaseAgent]
    tasks: List[Task]

    def __init__(self, dynamodb_tools: Optional[List] = None):
        """Initialize with static configuration"""
        self.dynamodb_tools = dynamodb_tools or []
        # NO REQUEST CONTEXT

    @agent
    def document_processor(self) -> Agent:
        return Agent(
            config=self.agents_config['document_processor'],
            llm=llm,
            tools=[pdf_tool, file_writer],  # FIXED TOOLS
            verbose=True,
            max_rpm=2,  # HARDCODED LIMITS
            max_iter=3,
            max_execution_time=180,
            multimodal=True
        )
```

#### AFTER: `src/latest_trade_matching_agent/crew_fixed.py` (UPDATED)
```python
# Updated implementation - DYNAMIC CONFIGURATION
import os
from typing import List, Optional, Dict, Any

@CrewBase
class LatestTradeMatchingAgent:
    """Enhanced LatestTradeMatchingAgent crew for EKS deployment"""

    def __init__(self,
                 dynamodb_tools: Optional[List] = None,
                 request_context: Optional[Dict[str, Any]] = None):  # NEW: REQUEST CONTEXT
        """Initialize with request context from EKS API"""
        self.dynamodb_tools = dynamodb_tools or []
        self.request_context = request_context or {}  # DYNAMIC CONTEXT

        # ENVIRONMENT-BASED CONFIGURATION
        self.config = {
            's3_bucket': os.getenv('S3_BUCKET_NAME',
                                 self.request_context.get('s3_bucket', 'trade-documents-production')),
            'dynamodb_bank_table': os.getenv('DYNAMODB_BANK_TABLE', 'BankTradeData'),
            'dynamodb_counterparty_table': os.getenv('DYNAMODB_COUNTERPARTY_TABLE', 'CounterpartyTradeData'),
            'max_rpm': int(os.getenv('MAX_RPM', '10')),  # CONFIGURABLE LIMITS
            'max_execution_time': int(os.getenv('MAX_EXECUTION_TIME', '1200')),
            'aws_region': os.getenv('AWS_REGION', 'us-east-1')
        }

    @agent
    def document_processor(self) -> Agent:
        return Agent(
            config=self.agents_config['document_processor'],
            llm=llm,
            tools=[PDFToImageTool(), FileWriterTool()],  # ENHANCED TOOLS
            verbose=True,
            max_rpm=self.config['max_rpm'],  # DYNAMIC LIMITS
            max_iter=3,
            max_execution_time=self.config['max_execution_time'],
            multimodal=True
        )

    @task
    def document_processing_task(self) -> Task:
        # INJECT REQUEST CONTEXT INTO TASK
        task_config = self.tasks_config['document_processing_task'].copy()

        if self.request_context:
            # FORMAT TASK DESCRIPTION WITH DYNAMIC VALUES
            task_config['description'] = task_config['description'].format(
                **self.request_context,
                **self.config
            )

        return Task(
            config=task_config,
            agent=self.document_processor()
        )

    # REQUEST CONTEXT SETTER
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
            max_rpm=self.config['max_rpm'],  # DYNAMIC CONFIGURATION
            share_crew=False,
            # ADD MONITORING CALLBACKS
            step_callback=self._step_callback,
            task_callback=self._task_callback
        )

    # MONITORING CALLBACKS
    def _step_callback(self, step):
        """Callback for monitoring step execution"""
        logger.info(f"Crew step executed: {step}")

    def _task_callback(self, task):
        """Callback for monitoring task completion"""
        logger.info(f"Task completed: {task.description[:100]}...")
```

### 3. Task Configuration Updates

#### BEFORE: `src/latest_trade_matching_agent/config/tasks.yaml`
```yaml
# Current implementation - STATIC PATHS
document_processing_task:
  description: >
    Convert the PDF document at {document_path} to high-quality images.

    **CRITICAL: Determine output location from source PDF path:**
    - IF PDF is in .../BANK/... folder → Save images to s3://YOUR_S3_BUCKET/PDFIMAGES/BANK/[document_name]_[timestamp]/
    - IF PDF is in .../COUNTERPARTY/... folder → Save images to s3://YOUR_S3_BUCKET/PDFIMAGES/COUNTERPARTY/[document_name]_[timestamp]/
    # HARDCODED BUCKET NAME ^^^

    **WORKFLOW:**
    1. Parse the {document_path} to identify if it contains /BANK/ or /COUNTERPARTY/
    # STATIC PATH PARSING ^^^
    2. Set output S3 prefix based on source folder
    3. Convert PDF to high-resolution JPEG images (300 DPI)
    4. Save to S3 AND MUST also save locally to ./pdf_images/{unique_identifier}/ for next agent
    # FIXED LOCAL PATH ^^^
```

#### AFTER: `src/latest_trade_matching_agent/config/tasks.yaml` (UPDATED)
```yaml
# Updated implementation - DYNAMIC CONFIGURATION
document_processing_task:
  description: >
    Convert the PDF document at {document_path} to high-quality images.

    **CRITICAL: Use dynamic S3 bucket and paths from request parameters:**
    - S3 Bucket: {s3_bucket}                    # DYNAMIC FROM REQUEST
    - Source PDF S3 Key: {s3_key}              # DYNAMIC FROM REQUEST
    - Source Type: {source_type}               # DYNAMIC FROM REQUEST
    - Output S3 prefix: {s3_bucket}/PDFIMAGES/{source_type}/{unique_identifier}/
    # ALL DYNAMIC VALUES ^^^

    **WORKFLOW:**
    1. PDF already downloaded locally to {document_path}
    # NO PATH PARSING NEEDED ^^^
    2. Convert PDF to high-resolution JPEG images (300 DPI)
    3. Save to S3: {s3_bucket}/PDFIMAGES/{source_type}/{unique_identifier}/
    # DYNAMIC S3 PATH ^^^
    4. Also save locally to /tmp/processing/{unique_identifier}/pdf_images/ for next agent
    # CONTAINER-FRIENDLY PATH ^^^
    5. Use unique_identifier: {unique_identifier} for folder naming

    **OUTPUT REQUIREMENTS:**
    - Convert each page to high-resolution JPEG images for S3
    - MUST save JPEG images locally to /tmp/processing/{unique_identifier}/pdf_images/
    # KUBERNETES TEMP STORAGE ^^^
    - Use 3-digit padding: page_001.jpg, page_002.jpg, etc.
    - Create metadata.json with file list and conversion details
    - Return S3 folder path for next agent

  expected_output: >
    Confirmation of successful conversion:
    - "Source PDF type: {source_type}"          # DYNAMIC SOURCE
    - "Images saved to: {s3_bucket}/PDFIMAGES/{source_type}/{unique_identifier}/"
    # DYNAMIC S3 PATH ^^^
    - "Local images saved to: /tmp/processing/{unique_identifier}/pdf_images/"
    # CONTAINER PATH ^^^
    - "Total pages converted: [X]"

# UPDATED: trade_entity_extractor_task
trade_entity_extractor_task:
  description: >
    **CRITICAL DATA EXTRACTION WITH S3 INTEGRATION:**
    Source Type: {source_type}              # FROM REQUEST
    S3 Bucket: {s3_bucket}                 # FROM REQUEST
    S3 Key: {s3_key}                       # FROM REQUEST

    **MANDATORY WORKFLOW:**
    1. **ACCESS LOCAL IMAGES:**
       - Images saved locally to /tmp/processing/{unique_identifier}/pdf_images/
       # CONTAINER TEMP STORAGE ^^^
       - Use OCR tool on local JPEG files

    2. **EXTRACT AND VALIDATE TRADE SOURCE:**
       - TRADE_SOURCE = {source_type} (from request parameters)
       # NO GUESSING - EXPLICIT FROM REQUEST ^^^
       - Validate source type is either "BANK" or "COUNTERPARTY"

    3. **SAVE EXTRACTED DATA TO S3:**
       - Save JSON to: {s3_bucket}/extracted/{source_type}/trade_{unique_identifier}_{timestamp}.json
       # DYNAMIC S3 PATH ^^^
       - Include all extracted trade data
       - Include metadata: s3_source_key, processing_timestamp, source_type

  expected_output: >
    "Extracted trade data saved to: {s3_bucket}/extracted/{source_type}/trade_{unique_identifier}_{timestamp}.json"
    # DYNAMIC S3 PATH ^^^
    "TRADE_SOURCE confirmed as: {source_type}"
    "S3 path for next agent: {s3_bucket}/extracted/{source_type}/trade_{unique_identifier}_{timestamp}.json"

# UPDATED: reporting_task
reporting_task:
  description: >
    **CRITICAL: Store in correct DynamoDB table based on source type**

    **TABLE SELECTION (MANDATORY):**
    - Source Type: {source_type}                           # FROM REQUEST
    - IF source_type = "BANK" → Store in table: {dynamodb_bank_table}
    # DYNAMIC TABLE NAME ^^^
    - IF source_type = "COUNTERPARTY" → Store in table: {dynamodb_counterparty_table}
    # DYNAMIC TABLE NAME ^^^

    **WORKFLOW:**
    1. Get JSON from S3 path provided by previous agent
    2. Parse trade data from JSON
    3. Validate source_type matches {source_type}        # EXPLICIT VALIDATION
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
    - Bank trades: {dynamodb_bank_table}           # DYNAMIC TABLE NAME
    - Counterparty trades: {dynamodb_counterparty_table}  # DYNAMIC TABLE NAME

    **WORKFLOW:**
    1. Verify data integrity across both DynamoDB tables
    2. Perform intelligent matching between bank and counterparty trades
    3. Generate comprehensive matching report
    4. Save report to S3: {s3_bucket}/reports/matching_report_{unique_identifier}_{timestamp}.md
    # DYNAMIC S3 PATH ^^^
    5. Send summary via SNS if configured

  expected_output: >
    "Matching completed between {dynamodb_bank_table} and {dynamodb_counterparty_table}"
    # DYNAMIC TABLE NAMES ^^^
    "Report saved to: {s3_bucket}/reports/matching_report_{unique_identifier}_{timestamp}.md"
    # DYNAMIC S3 PATH ^^^
    "Match rate: [X%]"
```

### 4. PDF Processing Tool Updates

#### BEFORE: `src/latest_trade_matching_agent/tools/pdf_to_image.py`
```python
# Current implementation - HARDCODED S3 SETTINGS
class PDFToImageInput(BaseModel):
    """Input schema for PDFToImageTool."""
    pdf_path: str = Field(
        description="Path to the PDF file (local path or S3 URI like s3://bucket/key)"
    )
    s3_output_bucket: str = Field(
        default="your-s3-bucket-name",      # HARDCODED DEFAULT
        description="S3 bucket for output images"
    )
    s3_output_prefix: str = Field(
        "PDFIMAGES/TEMP",                   # HARDCODED PREFIX
        description="S3 prefix/folder for output images (e.g., PDFIMAGES/TEMP)"
    )
    # NO SOURCE TYPE OR UNIQUE ID FIELDS

def _run(
    self,
    pdf_path: str,
    s3_output_bucket: str = None,
    s3_output_prefix: str = "PDFIMAGES/TEMP",  # HARDCODED
    dpi: int = 200,
    output_format: str = "JPEG",
    # ... other params
) -> str:
    try:
        # Get S3 bucket from environment or use provided value
        if s3_output_bucket is None:
            s3_output_bucket = os.getenv("S3_BUCKET_NAME", "your-s3-bucket-name")
            # FALLBACK TO HARDCODED VALUE ^^^
```

#### AFTER: `src/latest_trade_matching_agent/tools/pdf_to_image.py` (UPDATED)
```python
# Updated implementation - DYNAMIC CONFIGURATION
class PDFToImageInput(BaseModel):
    """Input schema for PDFToImageTool."""
    pdf_path: str = Field(
        description="Path to the PDF file (local path)"
    )
    s3_output_bucket: str = Field(
        description="S3 bucket for output images (from request parameters)"  # REQUIRED
    )
    s3_output_prefix: str = Field(
        description="S3 prefix/folder for output images (e.g., PDFIMAGES/BANK/unique_id)"  # DYNAMIC
    )
    source_type: str = Field(
        description="Source type: BANK or COUNTERPARTY"  # NEW FIELD
    )
    unique_identifier: str = Field(
        description="Unique identifier for this processing request"  # NEW FIELD
    )
    dpi: int = Field(200, description="DPI for image quality")
    output_format: str = Field("JPEG", description="Output image format")

class PDFToImageTool(BaseTool):
    name: str = "PDF to Image Converter"
    description: str = (
        "Converts PDF documents to images and saves them to S3 and locally. "
        "Uses dynamic S3 bucket and path configuration from request parameters."  # UPDATED
    )
    args_schema: Type[BaseModel] = PDFToImageInput

    def _run(
        self,
        pdf_path: str,
        s3_output_bucket: str,          # REQUIRED PARAMETER
        s3_output_prefix: str,          # REQUIRED PARAMETER
        source_type: str,               # NEW PARAMETER
        unique_identifier: str,         # NEW PARAMETER
        dpi: int = 200,
        output_format: str = "JPEG"
    ) -> str:
        """Convert PDF to images and upload to S3 while saving locally"""
        try:
            # VALIDATION - NO DEFAULTS
            if not all([s3_output_bucket, s3_output_prefix, source_type, unique_identifier]):
                raise ValueError("Missing required parameters: s3_output_bucket, s3_output_prefix, source_type, or unique_identifier")

            if source_type not in ["BANK", "COUNTERPARTY"]:
                raise ValueError(f"Invalid source_type: {source_type}. Must be BANK or COUNTERPARTY")

            # S3 CLIENT
            s3_client = boto3.client('s3')

            # GENERATE TIMESTAMP
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # CREATE DYNAMIC S3 FOLDER PATH
            s3_folder = f"{s3_output_prefix}/{unique_identifier}_{timestamp}"

            # CREATE CONTAINER-FRIENDLY LOCAL PATH
            local_path = Path(f"/tmp/processing/{unique_identifier}/pdf_images")
            local_path.mkdir(parents=True, exist_ok=True)

            # CONVERT PDF TO IMAGES
            logger.info(f"Converting PDF to images at {dpi} DPI")
            images = convert_from_path(pdf_path, dpi=dpi)

            s3_locations = []
            local_locations = []

            for i, image in enumerate(images, start=1):
                # SAVE LOCALLY WITH UNIQUE IDENTIFIER
                local_file_path = local_path / f"{unique_identifier}_page_{i:03d}.jpg"
                image.save(local_file_path, "JPEG", quality=95)
                local_locations.append(str(local_file_path))

                # SAVE TO S3 WITH ENHANCED METADATA
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
                                'source_type': source_type,           # NEW METADATA
                                'unique_identifier': unique_identifier,  # NEW METADATA
                                'dpi': str(dpi),
                                'conversion_timestamp': timestamp
                            }
                        )

                    s3_locations.append(f"s3://{s3_output_bucket}/{s3_key}")
                    os.unlink(tmp_img.name)

            # CREATE ENHANCED METADATA
            metadata = {
                'source_pdf': pdf_path,
                'source_type': source_type,                    # NEW FIELD
                'unique_identifier': unique_identifier,        # NEW FIELD
                'conversion_timestamp': timestamp,
                'total_pages': len(images),
                'dpi': dpi,
                's3_bucket': s3_output_bucket,                # NEW FIELD
                's3_folder': f"s3://{s3_output_bucket}/{s3_folder}/",
                'local_folder': str(local_path),              # NEW FIELD
                'image_files': [Path(loc).name for loc in s3_locations]
            }

            # SAVE METADATA TO S3
            metadata_key = f"{s3_folder}/metadata.json"
            s3_client.put_object(
                Bucket=s3_output_bucket,
                Key=metadata_key,
                Body=json.dumps(metadata, indent=2),
                ContentType='application/json'
            )

            # SAVE METADATA LOCALLY
            with open(local_path / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)

            # ENHANCED RESULT MESSAGE
            result_message = f"""
✅ PDF Conversion Successful!
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 Source: {pdf_path}
📊 Total Pages: {len(images)}
🎯 DPI: {dpi}
📸 Format: JPEG
☁️  S3 Location: s3://{s3_output_bucket}/{s3_folder}/
💾 Local Path: {local_path}
🏷️  Source Type: {source_type}            # NEW INFO
🆔 Unique ID: {unique_identifier}          # NEW INFO
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Images ready for OCR processing
Local path for next agent: {local_path}    # EXPLICIT PATH FOR NEXT AGENT
"""

            return result_message

        except Exception as e:
            error_msg = f"❌ Error converting PDF to images: {str(e)}"
            logger.error(error_msg)
            return error_msg
```

## New Files to Create

### 1. Container Configuration

#### NEW: `Dockerfile`
```dockerfile
# Multi-stage build for optimized image
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Set working directory
WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY *.py ./

# Install additional EKS dependencies
RUN pip install fastapi uvicorn prometheus-client

# Create necessary directories
RUN mkdir -p /tmp/processing /app/logs

# Create non-root user for security
RUN useradd -m -u 1000 trader && \
    chown -R trader:trader /app /tmp/processing

USER trader

# Add local bin to PATH
ENV PATH=/root/.local/bin:$PATH

# Expose ports
EXPOSE 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Start application
CMD ["python", "src/latest_trade_matching_agent/eks_main.py"]
```

#### NEW: `requirements-eks.txt`
```txt
# Existing dependencies
crewai>=0.80.0
crewai-tools>=0.14.0
openai>=1.0.0
litellm>=1.0.0
anthropic>=0.39.0
tinydb>=4.8.0
pdf2image>=1.17.0
Pillow>=10.0.0
reportlab>=4.0.0
boto3>=1.34.0
botocore>=1.34.0
python-dotenv>=1.0.0
pyyaml>=6.0.0
pydantic>=2.0.0
requests>=2.31.0

# NEW: EKS-specific dependencies
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
prometheus-client>=0.19.0
structlog>=23.2.0
kubernetes>=28.1.0

# NEW: Enhanced monitoring
opentelemetry-api>=1.21.0
opentelemetry-sdk>=1.21.0
opentelemetry-instrumentation-fastapi>=0.42b0
opentelemetry-exporter-prometheus>=1.12.0rc1

# NEW: Enhanced security
cryptography>=41.0.0
python-multipart>=0.0.6

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=5.0.0
httpx>=0.25.0  # For FastAPI testing
```

### 2. Kubernetes Manifests

#### NEW: `k8s/namespace.yaml`
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: trading
  labels:
    name: trading
    # Pod Security Standards
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
---
# Network Policy for namespace isolation
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: trading
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
# Allow egress to AWS services
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-aws-services
  namespace: trading
spec:
  podSelector:
    matchLabels:
      app: trade-matching-system
  policyTypes:
  - Egress
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS to AWS services
    - protocol: TCP
      port: 53   # DNS
    - protocol: UDP
      port: 53   # DNS
```

#### NEW: `k8s/configmap.yaml`
```yaml
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
  CREW_MEMORY: "false"
  CREW_VERBOSE: "true"

  # LLM Configuration
  BEDROCK_MODEL: "bedrock/amazon.nova-pro-v1:0"
  LITELLM_LOG: "ERROR"

  # Monitoring Configuration
  METRICS_PORT: "9090"
  HEALTH_CHECK_PORT: "8080"
  PROMETHEUS_ENABLED: "true"

  # Storage Configuration
  TEMP_STORAGE_PATH: "/tmp/processing"
  MAX_TEMP_SIZE: "10Gi"
```

#### NEW: `k8s/secrets.yaml`
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: trade-matching-secrets
  namespace: trading
type: Opaque
stringData:
  # SNS Configuration (will be base64 encoded)
  sns-topic-arn: "arn:aws:sns:us-east-1:ACCOUNT_ID:trade-processing-notifications"

  # LLM API Keys (optional, if not using IAM roles)
  openai-api-key: "sk-your-openai-key-here"
  anthropic-api-key: "your-anthropic-key-here"

  # Database Connection (if needed)
  database-url: "your-database-connection-string"
---
# External Secrets Operator integration (optional)
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: trading
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: trade-matching-sa
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: trade-secrets
  namespace: trading
spec:
  refreshInterval: 15s
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: trade-matching-external-secrets
    creationPolicy: Owner
  data:
  - secretKey: openai-api-key
    remoteRef:
      key: trade-matching/openai
      property: api-key
  - secretKey: sns-topic-arn
    remoteRef:
      key: trade-matching/aws
      property: sns-topic-arn
```

#### NEW: `k8s/deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trade-matching-system
  namespace: trading
  labels:
    app: trade-matching-system
    version: v1.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: trade-matching-system
  template:
    metadata:
      labels:
        app: trade-matching-system
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: trade-matching-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: trade-processor
        image: ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/trade-matching-system:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
          name: http
          protocol: TCP
        - containerPort: 9090
          name: metrics
          protocol: TCP
        env:
        # AWS Configuration
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

        # Application Configuration
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: trade-matching-config
              key: LOG_LEVEL
        - name: MAX_WORKERS
          valueFrom:
            configMapKeyRef:
              name: trade-matching-config
              key: MAX_WORKERS
        - name: PROCESSING_TIMEOUT
          valueFrom:
            configMapKeyRef:
              name: trade-matching-config
              key: PROCESSING_TIMEOUT

        # CrewAI Configuration
        - name: MAX_RPM
          valueFrom:
            configMapKeyRef:
              name: trade-matching-config
              key: MAX_RPM
        - name: MAX_EXECUTION_TIME
          valueFrom:
            configMapKeyRef:
              name: trade-matching-config
              key: MAX_EXECUTION_TIME
        - name: BEDROCK_MODEL
          valueFrom:
            configMapKeyRef:
              name: trade-matching-config
              key: BEDROCK_MODEL

        # Secrets
        - name: SNS_TOPIC_ARN
          valueFrom:
            secretKeyRef:
              name: trade-matching-secrets
              key: sns-topic-arn
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: trade-matching-secrets
              key: openai-api-key
              optional: true

        # Monitoring
        - name: METRICS_PORT
          valueFrom:
            configMapKeyRef:
              name: trade-matching-config
              key: METRICS_PORT
        - name: HEALTH_CHECK_PORT
          valueFrom:
            configMapKeyRef:
              name: trade-matching-config
              key: HEALTH_CHECK_PORT

        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
            ephemeral-storage: "5Gi"
          limits:
            memory: "4Gi"
            cpu: "2000m"
            ephemeral-storage: "10Gi"

        volumeMounts:
        - name: temp-storage
          mountPath: /tmp/processing
        - name: logs
          mountPath: /app/logs

        livenessProbe:
          httpGet:
            path: /health
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
          successThreshold: 1

        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
            scheme: HTTP
          initialDelaySeconds: 15
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
          successThreshold: 1

        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
          readOnlyRootFilesystem: false  # False due to temp file processing
          runAsNonRoot: true
          runAsUser: 1000

      volumes:
      - name: temp-storage
        emptyDir:
          sizeLimit: 10Gi
      - name: logs
        emptyDir:
          sizeLimit: 1Gi

      # Pod-level security
      terminationGracePeriodSeconds: 60
      dnsPolicy: ClusterFirst
      restartPolicy: Always
```

#### NEW: `k8s/service.yaml`
```yaml
apiVersion: v1
kind: Service
metadata:
  name: trade-matching-service
  namespace: trading
  labels:
    app: trade-matching-system
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-internal: "true"
spec:
  type: LoadBalancer
  selector:
    app: trade-matching-system
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 8080
  - name: metrics
    protocol: TCP
    port: 9090
    targetPort: 9090
---
# Internal service for Lambda access
apiVersion: v1
kind: Service
metadata:
  name: trade-matching-internal
  namespace: trading
  labels:
    app: trade-matching-system
spec:
  type: ClusterIP
  selector:
    app: trade-matching-system
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 8080
```

#### NEW: `k8s/hpa.yaml`
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: trade-matching-hpa
  namespace: trading
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: trade-matching-system
  minReplicas: 3
  maxReplicas: 20
  metrics:
  # CPU-based scaling
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  # Memory-based scaling
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  # Custom metrics (if Prometheus adapter is installed)
  - type: Pods
    pods:
      metric:
        name: trade_active_processing
      target:
        type: AverageValue
        averageValue: "5"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Max
```

### 3. Monitoring and Observability

#### NEW: `src/monitoring/metrics.py`
```python
"""Prometheus metrics for trade processing system"""
from prometheus_client import Counter, Histogram, Gauge, start_http_server, CollectorRegistry
import logging
import time
from functools import wraps
from typing import Optional
import os

# Create custom registry to avoid conflicts
REGISTRY = CollectorRegistry()

# Document processing metrics
DOCUMENTS_PROCESSED = Counter(
    'trade_documents_processed_total',
    'Total documents processed',
    ['source_type', 'status'],
    registry=REGISTRY
)

PROCESSING_DURATION = Histogram(
    'trade_processing_duration_seconds',
    'Time spent processing documents',
    ['source_type', 'agent'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1200, 1800],
    registry=REGISTRY
)

ACTIVE_PROCESSING = Gauge(
    'trade_active_processing',
    'Currently processing documents',
    registry=REGISTRY
)

CREW_AGENT_DURATION = Histogram(
    'crew_agent_duration_seconds',
    'Agent processing time',
    ['agent_name', 'task_name'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
    registry=REGISTRY
)

ERROR_COUNT = Counter(
    'trade_processing_errors_total',
    'Total processing errors',
    ['error_type', 'source_type'],
    registry=REGISTRY
)

S3_OPERATIONS = Counter(
    'trade_s3_operations_total',
    'S3 operations performed',
    ['operation', 'status'],
    registry=REGISTRY
)

DYNAMODB_OPERATIONS = Counter(
    'trade_dynamodb_operations_total',
    'DynamoDB operations performed',
    ['table', 'operation', 'status'],
    registry=REGISTRY
)

HTTP_REQUESTS = Counter(
    'trade_http_requests_total',
    'HTTP requests received',
    ['method', 'endpoint', 'status_code'],
    registry=REGISTRY
)

HTTP_REQUEST_DURATION = Histogram(
    'trade_http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    registry=REGISTRY
)

def track_processing_time(source_type: str, agent_name: str = "unknown"):
    """Decorator to track processing time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            ACTIVE_PROCESSING.inc()

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
                ACTIVE_PROCESSING.dec()
        return wrapper
    return decorator

def track_agent_execution(agent_name: str, task_name: str):
    """Decorator to track individual agent execution time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                CREW_AGENT_DURATION.labels(
                    agent_name=agent_name,
                    task_name=task_name
                ).observe(duration)
        return wrapper
    return decorator

def track_s3_operation(operation: str):
    """Decorator to track S3 operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                S3_OPERATIONS.labels(
                    operation=operation,
                    status='success'
                ).inc()
                return result
            except Exception as e:
                S3_OPERATIONS.labels(
                    operation=operation,
                    status='error'
                ).inc()
                raise
        return wrapper
    return decorator

def track_dynamodb_operation(table: str, operation: str):
    """Decorator to track DynamoDB operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                DYNAMODB_OPERATIONS.labels(
                    table=table,
                    operation=operation,
                    status='success'
                ).inc()
                return result
            except Exception as e:
                DYNAMODB_OPERATIONS.labels(
                    table=table,
                    operation=operation,
                    status='error'
                ).inc()
                raise
        return wrapper
    return decorator

def start_metrics_server(port: int = 9090, registry: Optional[CollectorRegistry] = None):
    """Start Prometheus metrics server"""
    if registry is None:
        registry = REGISTRY

    start_http_server(port, registry=registry)
    logging.info(f"Metrics server started on port {port}")

# FastAPI middleware for HTTP metrics
class MetricsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        path = scope["path"]

        start_time = time.time()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                duration = time.time() - start_time

                HTTP_REQUESTS.labels(
                    method=method,
                    endpoint=path,
                    status_code=status_code
                ).inc()

                HTTP_REQUEST_DURATION.labels(
                    method=method,
                    endpoint=path
                ).observe(duration)

            await send(message)

        await self.app(scope, receive, send_wrapper)
```

#### NEW: `src/monitoring/logging.py`
```python
"""Structured logging configuration for Kubernetes"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
import structlog
import os

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process_id': os.getpid(),
            'thread_id': record.thread,
            'thread_name': record.threadName
        }

        # Add Kubernetes context
        log_entry.update({
            'namespace': os.getenv('POD_NAMESPACE', 'unknown'),
            'pod_name': os.getenv('POD_NAME', 'unknown'),
            'container_name': os.getenv('CONTAINER_NAME', 'trade-processor'),
            'node_name': os.getenv('NODE_NAME', 'unknown')
        })

        # Add extra fields from record
        extra_fields = [
            'unique_identifier', 'source_type', 'processing_id',
            's3_bucket', 's3_key', 'agent_name', 'task_name'
        ]

        for field in extra_fields:
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            log_entry['exception_type'] = record.exc_info[0].__name__ if record.exc_info[0] else None

        return json.dumps(log_entry, default=str)

def setup_logging(log_level: str = "INFO"):
    """Setup structured logging for Kubernetes environment"""

    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create JSON handler for stdout
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
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('fastapi').setLevel(logging.INFO)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

class TradeProcessingLogger:
    """Context-aware logger for trade processing"""

    def __init__(self, unique_identifier: str, source_type: str, processing_id: Optional[str] = None):
        self.logger = structlog.get_logger(__name__)
        self.context = {
            'unique_identifier': unique_identifier,
            'source_type': source_type
        }
        if processing_id:
            self.context['processing_id'] = processing_id

    def bind(self, **kwargs) -> 'TradeProcessingLogger':
        """Create new logger with additional context"""
        new_context = {**self.context, **kwargs}
        new_logger = TradeProcessingLogger(
            self.context['unique_identifier'],
            self.context['source_type'],
            self.context.get('processing_id')
        )
        new_logger.context = new_context
        return new_logger

    def _log(self, level: str, message: str, **kwargs):
        """Log with context"""
        bound_logger = self.logger.bind(**self.context, **kwargs)
        getattr(bound_logger, level)(message)

    def info(self, message: str, **kwargs):
        self._log('info', message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log('error', message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log('warning', message, **kwargs)

    def debug(self, message: str, **kwargs):
        self._log('debug', message, **kwargs)

    def critical(self, message: str, **kwargs):
        self._log('critical', message, **kwargs)

# Health check logging
def log_health_check(endpoint: str, status: str, duration: float):
    """Log health check results"""
    logger = structlog.get_logger("health_check")
    logger.info(
        "Health check completed",
        endpoint=endpoint,
        status=status,
        duration_ms=round(duration * 1000, 2)
    )

# Performance logging
def log_performance_metric(metric_name: str, value: float, unit: str = "ms", **context):
    """Log performance metrics"""
    logger = structlog.get_logger("performance")
    logger.info(
        "Performance metric",
        metric_name=metric_name,
        value=value,
        unit=unit,
        **context
    )
```

### 4. Enhanced Configuration Management

#### NEW: `src/config/settings.py`
```python
"""Application settings with environment-based configuration"""
import os
from pydantic import BaseSettings, Field, validator
from typing import Optional, List
import json

class Settings(BaseSettings):
    """Application settings with validation"""

    # AWS Configuration
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    s3_bucket_name: str = Field(env="S3_BUCKET_NAME")
    dynamodb_bank_table: str = Field(default="BankTradeData", env="DYNAMODB_BANK_TABLE")
    dynamodb_counterparty_table: str = Field(default="CounterpartyTradeData", env="DYNAMODB_COUNTERPARTY_TABLE")

    # SNS Configuration
    sns_topic_arn: Optional[str] = Field(default=None, env="SNS_TOPIC_ARN")

    # Application Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    max_workers: int = Field(default=4, env="MAX_WORKERS")
    processing_timeout: int = Field(default=1800, env="PROCESSING_TIMEOUT")  # 30 minutes

    # CrewAI Configuration
    max_rpm: int = Field(default=10, env="MAX_RPM")
    max_execution_time: int = Field(default=1200, env="MAX_EXECUTION_TIME")  # 20 minutes
    crew_memory: bool = Field(default=False, env="CREW_MEMORY")
    crew_verbose: bool = Field(default=True, env="CREW_VERBOSE")

    # LLM Configuration
    bedrock_model: str = Field(default="bedrock/amazon.nova-pro-v1:0", env="BEDROCK_MODEL")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    litellm_log: str = Field(default="ERROR", env="LITELLM_LOG")

    # Monitoring Configuration
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    health_check_port: int = Field(default=8080, env="HEALTH_CHECK_PORT")
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")

    # Storage Configuration
    temp_storage_path: str = Field(default="/tmp/processing", env="TEMP_STORAGE_PATH")
    max_temp_size: str = Field(default="10Gi", env="MAX_TEMP_SIZE")

    # Kubernetes Configuration
    pod_namespace: Optional[str] = Field(default=None, env="POD_NAMESPACE")
    pod_name: Optional[str] = Field(default=None, env="POD_NAME")
    container_name: Optional[str] = Field(default=None, env="CONTAINER_NAME")
    node_name: Optional[str] = Field(default=None, env="NODE_NAME")

    # Security Configuration
    allowed_source_types: List[str] = Field(default=["BANK", "COUNTERPARTY"])
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    allowed_file_extensions: List[str] = Field(default=[".pdf", ".PDF"])

    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Invalid log level. Must be one of: {valid_levels}')
        return v.upper()

    @validator('max_rpm')
    def validate_max_rpm(cls, v):
        if v <= 0:
            raise ValueError('max_rpm must be positive')
        return v

    @validator('processing_timeout')
    def validate_processing_timeout(cls, v):
        if v <= 0 or v > 3600:  # Max 1 hour
            raise ValueError('processing_timeout must be between 1 and 3600 seconds')
        return v

    @validator('bedrock_model')
    def validate_bedrock_model(cls, v):
        valid_prefixes = ['bedrock/', 'anthropic/', 'openai/']
        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError(f'Invalid model format. Must start with one of: {valid_prefixes}')
        return v

    @property
    def is_kubernetes(self) -> bool:
        """Check if running in Kubernetes environment"""
        return self.pod_namespace is not None

    @property
    def temp_dir(self) -> str:
        """Get temporary directory for processing"""
        return self.temp_storage_path

    def get_dynamodb_table(self, source_type: str) -> str:
        """Get DynamoDB table name for source type"""
        if source_type == "BANK":
            return self.dynamodb_bank_table
        elif source_type == "COUNTERPARTY":
            return self.dynamodb_counterparty_table
        else:
            raise ValueError(f"Invalid source_type: {source_type}")

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False
        validate_assignment = True

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings"""
    return settings

# Configuration validation function
def validate_configuration():
    """Validate configuration and dependencies"""
    errors = []

    # Check required AWS settings
    if not settings.s3_bucket_name:
        errors.append("S3_BUCKET_NAME is required")

    # Check DynamoDB settings
    if not settings.dynamodb_bank_table:
        errors.append("DYNAMODB_BANK_TABLE is required")
    if not settings.dynamodb_counterparty_table:
        errors.append("DYNAMODB_COUNTERPARTY_TABLE is required")

    # Check LLM configuration
    if not settings.openai_api_key and not settings.anthropic_api_key:
        # In production, we might use IAM roles for Bedrock
        if not settings.bedrock_model.startswith('bedrock/'):
            errors.append("At least one LLM API key or Bedrock model must be configured")

    # Check Kubernetes configuration in K8s environment
    if settings.is_kubernetes:
        if not settings.pod_name:
            errors.append("POD_NAME should be set in Kubernetes environment")

    if errors:
        raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")

    return True
```

### 5. Database Migration Scripts

#### NEW: `src/database/dynamodb_migration.py`
```python
"""Migration script from TinyDB to DynamoDB"""
import boto3
from tinydb import TinyDB
import json
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, Any, List
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Handles migration from TinyDB to DynamoDB"""

    def __init__(self, region: str = 'us-east-1'):
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.dynamodb_client = boto3.client('dynamodb', region_name=region)
        self.bank_table = self.dynamodb.Table('BankTradeData')
        self.counterparty_table = self.dynamodb.Table('CounterpartyTradeData')

    def check_tables_exist(self) -> Dict[str, bool]:
        """Check if DynamoDB tables exist"""
        tables = {}

        try:
            self.dynamodb_client.describe_table(TableName='BankTradeData')
            tables['BankTradeData'] = True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                tables['BankTradeData'] = False
            else:
                raise

        try:
            self.dynamodb_client.describe_table(TableName='CounterpartyTradeData')
            tables['CounterpartyTradeData'] = True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                tables['CounterpartyTradeData'] = False
            else:
                raise

        return tables

    def create_tables_if_not_exist(self):
        """Create DynamoDB tables if they don't exist"""
        tables_status = self.check_tables_exist()

        if not tables_status.get('BankTradeData', False):
            self._create_bank_table()
            logger.info("Created BankTradeData table")

        if not tables_status.get('CounterpartyTradeData', False):
            self._create_counterparty_table()
            logger.info("Created CounterpartyTradeData table")

    def _create_bank_table(self):
        """Create BankTradeData table"""
        self.dynamodb.create_table(
            TableName='BankTradeData',
            KeySchema=[
                {
                    'AttributeName': 'Trade_ID',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'Trade_ID',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            StreamSpecification={
                'StreamEnabled': True,
                'StreamViewType': 'NEW_AND_OLD_IMAGES'
            },
            Tags=[
                {
                    'Key': 'Environment',
                    'Value': 'production'
                },
                {
                    'Key': 'Application',
                    'Value': 'trade-matching'
                },
                {
                    'Key': 'Source',
                    'Value': 'bank'
                }
            ]
        )

    def _create_counterparty_table(self):
        """Create CounterpartyTradeData table"""
        self.dynamodb.create_table(
            TableName='CounterpartyTradeData',
            KeySchema=[
                {
                    'AttributeName': 'Trade_ID',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'Trade_ID',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            StreamSpecification={
                'StreamEnabled': True,
                'StreamViewType': 'NEW_AND_OLD_IMAGES'
            },
            Tags=[
                {
                    'Key': 'Environment',
                    'Value': 'production'
                },
                {
                    'Key': 'Application',
                    'Value': 'trade-matching'
                },
                {
                    'Key': 'Source',
                    'Value': 'counterparty'
                }
            ]
        )

    def migrate_tinydb_to_dynamodb(self, tinydb_path: str = "./storage") -> Dict[str, int]:
        """Migrate existing TinyDB data to DynamoDB"""

        tinydb_path = Path(tinydb_path)
        migrated_counts = {'bank': 0, 'counterparty': 0, 'errors': 0}

        # Migrate bank trades
        bank_db_path = tinydb_path / "bank_trade_data.db"
        if bank_db_path.exists():
            try:
                bank_db = TinyDB(str(bank_db_path))
                for record in bank_db.all():
                    try:
                        # Add migration metadata
                        migrated_record = self._prepare_record_for_migration(record, 'BANK')

                        self.bank_table.put_item(Item=migrated_record)
                        migrated_counts['bank'] += 1

                        logger.debug(f"Migrated bank record: {record.get('Trade_ID', 'unknown')}")

                    except Exception as e:
                        logger.error(f"Failed to migrate bank record {record.get('Trade_ID', 'unknown')}: {e}")
                        migrated_counts['errors'] += 1

                bank_db.close()
                logger.info(f"Migrated {migrated_counts['bank']} bank trades")

            except Exception as e:
                logger.error(f"Failed to open bank TinyDB: {e}")

        # Migrate counterparty trades
        counterparty_db_path = tinydb_path / "counterparty_trade_data.db"
        if counterparty_db_path.exists():
            try:
                counterparty_db = TinyDB(str(counterparty_db_path))
                for record in counterparty_db.all():
                    try:
                        # Add migration metadata
                        migrated_record = self._prepare_record_for_migration(record, 'COUNTERPARTY')

                        self.counterparty_table.put_item(Item=migrated_record)
                        migrated_counts['counterparty'] += 1

                        logger.debug(f"Migrated counterparty record: {record.get('Trade_ID', 'unknown')}")

                    except Exception as e:
                        logger.error(f"Failed to migrate counterparty record {record.get('Trade_ID', 'unknown')}: {e}")
                        migrated_counts['errors'] += 1

                counterparty_db.close()
                logger.info(f"Migrated {migrated_counts['counterparty']} counterparty trades")

            except Exception as e:
                logger.error(f"Failed to open counterparty TinyDB: {e}")

        return migrated_counts

    def _prepare_record_for_migration(self, record: Dict[str, Any], source_type: str) -> Dict[str, Any]:
        """Prepare TinyDB record for DynamoDB migration"""
        migrated_record = record.copy()

        # Add migration metadata
        migrated_record.update({
            'migration_timestamp': datetime.utcnow().isoformat(),
            'migrated_from': 'tinydb',
            'TRADE_SOURCE': source_type,
            'migration_version': '1.0'
        })

        # Ensure Trade_ID exists
        if 'Trade_ID' not in migrated_record or not migrated_record['Trade_ID']:
            # Generate a Trade_ID if missing
            migrated_record['Trade_ID'] = f"MIGRATED_{source_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
            logger.warning(f"Generated Trade_ID for record without ID: {migrated_record['Trade_ID']}")

        # Clean up None values (DynamoDB doesn't like them)
        cleaned_record = {}
        for key, value in migrated_record.items():
            if value is not None:
                # Convert empty strings to None and skip
                if value == "":
                    continue
                cleaned_record[key] = value

        return cleaned_record

    def validate_migration(self) -> Dict[str, Any]:
        """Validate migrated data"""
        validation_results = {}

        try:
            # Count records in DynamoDB
            bank_response = self.bank_table.scan(Select='COUNT')
            bank_count = bank_response['Count']

            counterparty_response = self.counterparty_table.scan(Select='COUNT')
            counterparty_count = counterparty_response['Count']

            validation_results = {
                'bank_trades_in_dynamodb': bank_count,
                'counterparty_trades_in_dynamodb': counterparty_count,
                'total_trades': bank_count + counterparty_count,
                'validation_timestamp': datetime.utcnow().isoformat()
            }

            # Sample some records to verify structure
            if bank_count > 0:
                sample_bank = self.bank_table.scan(Limit=1)['Items'][0]
                validation_results['sample_bank_record'] = sample_bank

            if counterparty_count > 0:
                sample_counterparty = self.counterparty_table.scan(Limit=1)['Items'][0]
                validation_results['sample_counterparty_record'] = sample_counterparty

            logger.info(f"Migration validation: {bank_count} bank trades, {counterparty_count} counterparty trades")

        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            validation_results['error'] = str(e)

        return validation_results

    def backup_tinydb(self, tinydb_path: str = "./storage", backup_path: str = "./storage/backup") -> bool:
        """Create backup of TinyDB files before migration"""
        try:
            tinydb_path = Path(tinydb_path)
            backup_path = Path(backup_path)
            backup_path.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Backup bank DB
            bank_db_path = tinydb_path / "bank_trade_data.db"
            if bank_db_path.exists():
                backup_bank_path = backup_path / f"bank_trade_data_{timestamp}.db"
                import shutil
                shutil.copy2(bank_db_path, backup_bank_path)
                logger.info(f"Backed up bank DB to {backup_bank_path}")

            # Backup counterparty DB
            counterparty_db_path = tinydb_path / "counterparty_trade_data.db"
            if counterparty_db_path.exists():
                backup_counterparty_path = backup_path / f"counterparty_trade_data_{timestamp}.db"
                import shutil
                shutil.copy2(counterparty_db_path, backup_counterparty_path)
                logger.info(f"Backed up counterparty DB to {backup_counterparty_path}")

            return True

        except Exception as e:
            logger.error(f"Failed to backup TinyDB files: {e}")
            return False

def main():
    """Main migration function"""
    logging.basicConfig(level=logging.INFO)

    migrator = DatabaseMigrator()

    print("Starting TinyDB to DynamoDB migration...")

    # Step 1: Create backup
    print("Step 1: Creating backup of TinyDB files...")
    if migrator.backup_tinydb():
        print("✅ Backup created successfully")
    else:
        print("❌ Backup failed - stopping migration")
        return

    # Step 2: Check/create tables
    print("Step 2: Checking DynamoDB tables...")
    migrator.create_tables_if_not_exist()
    print("✅ DynamoDB tables ready")

    # Step 3: Migrate data
    print("Step 3: Migrating data...")
    migration_results = migrator.migrate_tinydb_to_dynamodb()
    print(f"✅ Migration completed:")
    print(f"   - Bank trades: {migration_results['bank']}")
    print(f"   - Counterparty trades: {migration_results['counterparty']}")
    print(f"   - Errors: {migration_results['errors']}")

    # Step 4: Validate migration
    print("Step 4: Validating migration...")
    validation_results = migrator.validate_migration()
    if 'error' not in validation_results:
        print("✅ Migration validation successful")
        print(f"   - Total records in DynamoDB: {validation_results['total_trades']}")
    else:
        print(f"❌ Validation failed: {validation_results['error']}")

    print("Migration process completed!")

if __name__ == "__main__":
    main()
```

## Infrastructure Changes

### 1. AWS CloudFormation Templates

#### NEW: `cloudformation/s3-infrastructure.yaml`
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'S3 Event-driven infrastructure for trade document processing'

Parameters:
  Environment:
    Type: String
    Default: production
    AllowedValues: [development, staging, production]
    Description: Deployment environment

  EKSClusterName:
    Type: String
    Default: trade-matching-cluster
    Description: Name of the EKS cluster

  AlertEmail:
    Type: String
    Description: Email address for alerts and notifications
    AllowedPattern: '^[^\s@]+@[^\s@]+\.[^\s@]+$'

  BucketNamePrefix:
    Type: String
    Default: trade-documents
    Description: Prefix for S3 bucket name

Resources:
  # KMS Key for encryption
  TradeDocumentsKMSKey:
    Type: AWS::KMS::Key
    Properties:
      Description: 'KMS key for trade documents encryption'
      KeyPolicy:
        Statement:
          - Sid: Enable IAM User Permissions
            Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${AWS::AccountId}:root'
            Action: 'kms:*'
            Resource: '*'
          - Sid: Allow S3 Service
            Effect: Allow
            Principal:
              Service: s3.amazonaws.com
            Action:
              - 'kms:Decrypt'
              - 'kms:GenerateDataKey'
            Resource: '*'
          - Sid: Allow Lambda Service
            Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action:
              - 'kms:Decrypt'
              - 'kms:GenerateDataKey'
            Resource: '*'
      Tags:
        - Key: Environment
          Value: !Ref Environment
        - Key: Application
          Value: trade-matching

  TradeDocumentsKMSKeyAlias:
    Type: AWS::KMS::Alias
    Properties:
      AliasName: !Sub 'alias/trade-documents-${Environment}'
      TargetKeyId: !Ref TradeDocumentsKMSKey

  # S3 Bucket for trade documents
  TradeDocumentsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${BucketNamePrefix}-${Environment}-${AWS::AccountId}'
      VersioningConfiguration:
        Status: Enabled

      # Lifecycle configuration
      LifecycleConfiguration:
        Rules:
          - Id: MoveToIA
            Status: Enabled
            Transitions:
              - StorageClass: STANDARD_IA
                TransitionInDays: 30
          - Id: MoveToGlacier
            Status: Enabled
            Transitions:
              - StorageClass: GLACIER
                TransitionInDays: 90
          - Id: DeleteOldVersions
            Status: Enabled
            NoncurrentVersionExpirationInDays: 365

      # Security configuration
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true

      # Server-side encryption
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: aws:kms
              KMSMasterKeyID: !Ref TradeDocumentsKMSKey
            BucketKeyEnabled: true

      # Intelligent tiering
      IntelligentTieringConfigurations:
        - Id: EntireBucket
          Status: Enabled
          OptionalFields:
            - BucketKeyStatus

      # Event notifications
      NotificationConfiguration:
        QueueConfigurations:
          # Bank document events
          - Event: s3:ObjectCreated:*
            Queue: !GetAtt BankDocumentQueue.Arn
            Filter:
              S3Key:
                Rules:
                  - Name: prefix
                    Value: "BANK/"
                  - Name: suffix
                    Value: ".pdf"

          # Counterparty document events
          - Event: s3:ObjectCreated:*
            Queue: !GetAtt CounterpartyDocumentQueue.Arn
            Filter:
              S3Key:
                Rules:
                  - Name: prefix
                    Value: "COUNTERPARTY/"
                  - Name: suffix
                    Value: ".pdf"

          # Failed processing notifications
          - Event: s3:ObjectCreated:*
            Queue: !GetAtt FailedProcessingQueue.Arn
            Filter:
              S3Key:
                Rules:
                  - Name: prefix
                    Value: "FAILED/"

      Tags:
        - Key: Environment
          Value: !Ref Environment
        - Key: Application
          Value: trade-matching

  # S3 Bucket Policy
  TradeDocumentsBucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref TradeDocumentsBucket
      PolicyDocument:
        Statement:
          - Sid: DenyInsecureConnections
            Effect: Deny
            Principal: '*'
            Action: 's3:*'
            Resource:
              - !GetAtt TradeDocumentsBucket.Arn
              - !Sub '${TradeDocumentsBucket}/*'
            Condition:
              Bool:
                'aws:SecureTransport': 'false'
          - Sid: AllowEKSServiceAccount
            Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${AWS::AccountId}:role/EKSTradeMatchingRole'
            Action:
              - 's3:GetObject'
              - 's3:PutObject'
              - 's3:DeleteObject'
            Resource: !Sub '${TradeDocumentsBucket}/*'

  # SQS Queues for different document types
  BankDocumentQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub 'bank-documents-${Environment}'
      VisibilityTimeoutSeconds: 900  # 15 minutes
      MessageRetentionPeriod: 1209600  # 14 days
      DelaySeconds: 0
      KmsMasterKeyId: !Ref TradeDocumentsKMSKey
      RedrivePolicy:
        deadLetterTargetArn: !GetAtt BankDocumentDLQ.Arn
        maxReceiveCount: 3
      Tags:
        - Key: Environment
          Value: !Ref Environment
        - Key: DocumentType
          Value: Bank

  CounterpartyDocumentQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub 'counterparty-documents-${Environment}'
      VisibilityTimeoutSeconds: 900
      MessageRetentionPeriod: 1209600
      DelaySeconds: 0
      KmsMasterKeyId: !Ref TradeDocumentsKMSKey
      RedrivePolicy:
        deadLetterTargetArn: !GetAtt CounterpartyDocumentDLQ.Arn
        maxReceiveCount: 3
      Tags:
        - Key: Environment
          Value: !Ref Environment
        - Key: DocumentType
          Value: Counterparty

  FailedProcessingQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub 'failed-processing-${Environment}'
      VisibilityTimeoutSeconds: 300
      MessageRetentionPeriod: 1209600
      KmsMasterKeyId: !Ref TradeDocumentsKMSKey
      Tags:
        - Key: Environment
          Value: !Ref Environment
        - Key: Purpose
          Value: FailedProcessing

  # Dead Letter Queues
  BankDocumentDLQ:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub 'bank-documents-dlq-${Environment}'
      MessageRetentionPeriod: 1209600
      KmsMasterKeyId: !Ref TradeDocumentsKMSKey

  CounterpartyDocumentDLQ:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub 'counterparty-documents-dlq-${Environment}'
      MessageRetentionPeriod: 1209600
      KmsMasterKeyId: !Ref TradeDocumentsKMSKey

  # Queue Policies
  BankQueuePolicy:
    Type: AWS::SQS::QueuePolicy
    Properties:
      Queues:
        - !Ref BankDocumentQueue
      PolicyDocument:
        Statement:
          - Effect: Allow
            Principal:
              Service: s3.amazonaws.com
            Action: sqs:SendMessage
            Resource: !GetAtt BankDocumentQueue.Arn
            Condition:
              ArnEquals:
                aws:SourceArn: !GetAtt TradeDocumentsBucket.Arn

  CounterpartyQueuePolicy:
    Type: AWS::SQS::QueuePolicy
    Properties:
      Queues:
        - !Ref CounterpartyDocumentQueue
      PolicyDocument:
        Statement:
          - Effect: Allow
            Principal:
              Service: s3.amazonaws.com
            Action: sqs:SendMessage
            Resource: !GetAtt CounterpartyDocumentQueue.Arn
            Condition:
              ArnEquals:
                aws:SourceArn: !GetAtt TradeDocumentsBucket.Arn

  # SNS Topics for notifications
  ProcessingNotificationsTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: !Sub 'trade-processing-notifications-${Environment}'
      DisplayName: Trade Processing Notifications
      KmsMasterKeyId: !Ref TradeDocumentsKMSKey

  ProcessingNotificationsSubscription:
    Type: AWS::SNS::Subscription
    Properties:
      Protocol: email
      TopicArn: !Ref ProcessingNotificationsTopic
      Endpoint: !Ref AlertEmail

  # CloudWatch Log Groups
  LambdaLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub '/aws/lambda/trade-document-processor-${Environment}'
      RetentionInDays: 30
      KmsKeyId: !GetAtt TradeDocumentsKMSKey.Arn

  # CloudWatch Alarms
  HighQueueDepthAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub 'trade-documents-high-queue-depth-${Environment}'
      AlarmDescription: High number of unprocessed documents
      MetricName: ApproximateNumberOfVisibleMessages
      Namespace: AWS/SQS
      Statistic: Average
      Period: 300
      EvaluationPeriods: 3
      Threshold: 100
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: QueueName
          Value: !GetAtt BankDocumentQueue.QueueName
      AlarmActions:
        - !Ref ProcessingNotificationsTopic

  DocumentProcessingFailureRate:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub 'trade-documents-failure-rate-${Environment}'
      AlarmDescription: High failure rate in document processing
      MetricName: NumberOfMessagesSent
      Namespace: AWS/SQS
      Statistic: Sum
      Period: 300
      EvaluationPeriods: 2
      Threshold: 10
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: QueueName
          Value: !GetAtt FailedProcessingQueue.QueueName
      AlarmActions:
        - !Ref ProcessingNotificationsTopic

  # CloudWatch Dashboard
  TradingDashboard:
    Type: AWS::CloudWatch::Dashboard
    Properties:
      DashboardName: !Sub 'TradeDocumentProcessing-${Environment}'
      DashboardBody: !Sub |
        {
          "widgets": [
            {
              "type": "metric",
              "x": 0,
              "y": 0,
              "width": 12,
              "height": 6,
              "properties": {
                "metrics": [
                  ["AWS/SQS", "NumberOfMessagesSent", "QueueName", "${BankDocumentQueue.QueueName}"],
                  [".", ".", ".", "${CounterpartyDocumentQueue.QueueName}"]
                ],
                "period": 300,
                "stat": "Sum",
                "region": "${AWS::Region}",
                "title": "Documents Received by Source"
              }
            },
            {
              "type": "metric",
              "x": 12,
              "y": 0,
              "width": 12,
              "height": 6,
              "properties": {
                "metrics": [
                  ["AWS/SQS", "ApproximateNumberOfVisibleMessages", "QueueName", "${BankDocumentQueue.QueueName}"],
                  [".", ".", ".", "${CounterpartyDocumentQueue.QueueName}"]
                ],
                "period": 300,
                "stat": "Average",
                "region": "${AWS::Region}",
                "title": "Queue Depth"
              }
            }
          ]
        }

Outputs:
  BucketName:
    Description: 'S3 bucket for trade documents'
    Value: !Ref TradeDocumentsBucket
    Export:
      Name: !Sub '${AWS::StackName}-bucket-name'

  BankQueueUrl:
    Description: 'SQS queue URL for bank documents'
    Value: !Ref BankDocumentQueue
    Export:
      Name: !Sub '${AWS::StackName}-bank-queue-url'

  CounterpartyQueueUrl:
    Description: 'SQS queue URL for counterparty documents'
    Value: !Ref CounterpartyDocumentQueue
    Export:
      Name: !Sub '${AWS::StackName}-counterparty-queue-url'

  SNSTopicArn:
    Description: 'SNS topic ARN for notifications'
    Value: !Ref ProcessingNotificationsTopic
    Export:
      Name: !Sub '${AWS::StackName}-sns-topic-arn'

  KMSKeyId:
    Description: 'KMS key ID for encryption'
    Value: !Ref TradeDocumentsKMSKey
    Export:
      Name: !Sub '${AWS::StackName}-kms-key-id'
```

## Implementation Checklist

### Phase 1: Pre-Migration Setup ✅
- [ ] **Backup existing data**
  - [ ] Create backup of `./storage/` directory
  - [ ] Export existing TinyDB data to JSON
  - [ ] Document current file locations in `./data/`

- [ ] **AWS Infrastructure Setup**
  - [ ] Deploy S3 infrastructure CloudFormation stack
  - [ ] Deploy DynamoDB tables CloudFormation stack
  - [ ] Verify S3 bucket permissions and encryption
  - [ ] Test SQS queue configuration

- [ ] **EKS Cluster Setup**
  - [ ] Create EKS cluster using eksctl
  - [ ] Install required add-ons (ALB Controller, EBS CSI)
  - [ ] Configure OIDC provider for service accounts
  - [ ] Create IAM roles for EKS workloads

### Phase 2: Application Changes ✅
- [ ] **Create new files**
  - [ ] `src/latest_trade_matching_agent/eks_main.py` (FastAPI wrapper)
  - [ ] `src/config/settings.py` (configuration management)
  - [ ] `src/monitoring/metrics.py` (Prometheus metrics)
  - [ ] `src/monitoring/logging.py` (structured logging)
  - [ ] `src/database/dynamodb_migration.py` (migration script)

- [ ] **Update existing files**
  - [ ] `src/latest_trade_matching_agent/crew_fixed.py` (add request context)
  - [ ] `src/latest_trade_matching_agent/config/tasks.yaml` (dynamic configuration)
  - [ ] `src/latest_trade_matching_agent/tools/pdf_to_image.py` (S3 integration)
  - [ ] `requirements.txt` → `requirements-eks.txt` (add FastAPI, uvicorn)

- [ ] **Container Configuration**
  - [ ] Create `Dockerfile` with multi-stage build
  - [ ] Build and test container locally
  - [ ] Push to ECR repository

### Phase 3: Kubernetes Deployment ✅
- [ ] **Create Kubernetes manifests**
  - [ ] `k8s/namespace.yaml` (namespace and network policies)
  - [ ] `k8s/configmap.yaml` (application configuration)
  - [ ] `k8s/secrets.yaml` (sensitive configuration)
  - [ ] `k8s/deployment.yaml` (application deployment)
  - [ ] `k8s/service.yaml` (service and load balancer)
  - [ ] `k8s/hpa.yaml` (horizontal pod autoscaler)

- [ ] **Deploy to EKS**
  - [ ] Apply Kubernetes manifests
  - [ ] Verify pod health and readiness
  - [ ] Test health check endpoints
  - [ ] Validate service connectivity

### Phase 4: Lambda Integration ✅
- [ ] **Lambda Function**
  - [ ] Create Lambda function for SQS processing
  - [ ] Configure environment variables
  - [ ] Set up SQS event triggers
  - [ ] Test Lambda-to-EKS connectivity

- [ ] **Event Flow Testing**
  - [ ] Upload test PDF to S3
  - [ ] Verify S3 event → SQS → Lambda → EKS flow
  - [ ] Check processing status via API
  - [ ] Validate DynamoDB data storage

### Phase 5: Data Migration ✅
- [ ] **Database Migration**
  - [ ] Run `python src/database/dynamodb_migration.py`
  - [ ] Validate migrated data in DynamoDB
  - [ ] Verify data integrity and completeness
  - [ ] Test CrewAI agents with DynamoDB

- [ ] **File Migration**
  - [ ] Upload existing PDFs to S3 bucket structure
  - [ ] Organize files by source type (BANK/COUNTERPARTY)
  - [ ] Verify S3 event triggering for migrated files

### Phase 6: Monitoring Setup ✅
- [ ] **Observability Stack**
  - [ ] Deploy CloudWatch Container Insights
  - [ ] Configure Prometheus and Grafana (optional)
  - [ ] Set up CloudWatch dashboards
  - [ ] Configure alerting rules

- [ ] **Testing and Validation**
  - [ ] Run end-to-end processing tests
  - [ ] Perform load testing
  - [ ] Validate monitoring and alerting
  - [ ] Test error scenarios and recovery

### Phase 7: Go-Live ✅
- [ ] **Production Readiness**
  - [ ] Review security configurations
  - [ ] Validate backup and disaster recovery
  - [ ] Test scaling scenarios
  - [ ] Document operational procedures

- [ ] **Cutover**
  - [ ] Stop file-based processing
  - [ ] Enable S3 event processing
  - [ ] Monitor initial production usage
  - [ ] Address any issues immediately

## Testing Verification

### 1. Unit Tests
```bash
# Run updated unit tests
pytest tests/test_eks_integration.py -v
pytest tests/test_dynamodb_migration.py -v
pytest tests/test_s3_integration.py -v
```

### 2. Integration Tests
```bash
# Test complete end-to-end flow
python tests/integration/test_e2e_processing.py

# Test S3 event simulation
python tests/integration/test_s3_events.py

# Test Lambda integration
python tests/integration/test_lambda_eks.py
```

### 3. Load Testing
```bash
# Upload multiple files concurrently
python tests/load/concurrent_upload_test.py --files 50 --workers 10

# Monitor system performance
kubectl top pods -n trading
aws cloudwatch get-metric-statistics --namespace TradeMatching/EKS
```

### 4. Manual Verification Steps

#### Test S3 Upload Processing
```bash
# 1. Upload test file
aws s3 cp test-bank-trade.pdf s3://trade-documents-production-ACCOUNT/BANK/2024/01/01/

# 2. Check SQS queue
aws sqs get-queue-attributes --queue-url QUEUE_URL --attribute-names ApproximateNumberOfMessages

# 3. Monitor Lambda logs
aws logs tail /aws/lambda/trade-document-processor-production --follow

# 4. Check EKS processing
kubectl logs -f deployment/trade-matching-system -n trading

# 5. Verify DynamoDB storage
aws dynamodb scan --table-name BankTradeData --limit 5

# 6. Check processing status
curl http://LOAD_BALANCER_URL/status/PROCESSING_ID
```

#### Test Error Scenarios
```bash
# 1. Upload invalid file
echo "not a pdf" > invalid.pdf
aws s3 cp invalid.pdf s3://trade-documents-production-ACCOUNT/BANK/2024/01/01/

# 2. Upload oversized file (>50MB)
dd if=/dev/zero of=large.pdf bs=1M count=100
aws s3 cp large.pdf s3://trade-documents-production-ACCOUNT/BANK/2024/01/01/

# 3. Test DLQ processing
aws sqs receive-message --queue-url DLQ_URL

# 4. Verify error notifications
# Check SNS email notifications
```

This comprehensive changes guide provides everything needed to migrate from the current file-based system to a production-ready, event-driven EKS deployment with proper monitoring, security, and scalability.