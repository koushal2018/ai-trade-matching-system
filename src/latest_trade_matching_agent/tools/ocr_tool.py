"""
OCR Extraction Tool using AWS Bedrock Claude Sonnet 4

This tool processes images from PDFs and extracts text using AWS Bedrock's
multimodal capabilities with Claude Sonnet 4.

Requirements: 5.2, 5.3
"""

from typing import Type, List, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import boto3
import base64
import json
import logging
from pathlib import Path
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCRToolInput(BaseModel):
    """Input schema for OCR Tool."""
    image_paths: List[str] = Field(
        ...,
        description="List of image file paths (local or S3 URIs) to process with OCR"
    )
    s3_output_bucket: Optional[str] = Field(
        None,
        description="S3 bucket for output text (optional)"
    )
    s3_output_key: Optional[str] = Field(
        None,
        description="S3 key for output text file (optional)"
    )
    save_locally: bool = Field(
        True,
        description="Save extracted text to local file"
    )
    local_output_path: Optional[str] = Field(
        None,
        description="Local path for output text file"
    )
    model_id: str = Field(
        "us.anthropic.claude-sonnet-4-20250514-v1:0",
        description="Bedrock model ID for OCR"
    )
    region_name: str = Field(
        "us-east-1",
        description="AWS region for Bedrock"
    )


class OCRTool(BaseTool):
    name: str = "OCR Text Extraction Tool"
    description: str = (
        "Extracts text from images using AWS Bedrock Claude Sonnet 4 multimodal capabilities. "
        "Processes all pages from a PDF and combines text from multiple images. "
        "Saves extracted text to S3 and/or local storage. "
        "Perfect for extracting trade confirmation details from scanned documents."
    )
    args_schema: Type[BaseModel] = OCRToolInput

    def _run(
        self,
        image_paths: List[str],
        s3_output_bucket: Optional[str] = None,
        s3_output_key: Optional[str] = None,
        save_locally: bool = True,
        local_output_path: Optional[str] = None,
        model_id: str = "us.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name: str = "us-east-1"
    ) -> str:
        """
        Extract text from images using AWS Bedrock Claude Sonnet 4.
        
        Args:
            image_paths: List of image file paths (local or S3 URIs)
            s3_output_bucket: S3 bucket for output (optional)
            s3_output_key: S3 key for output (optional)
            save_locally: Save to local file
            local_output_path: Local output file path
            model_id: Bedrock model ID
            region_name: AWS region
            
        Returns:
            str: Success message with extracted text summary
        """
        try:
            # Initialize AWS clients
            bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
            s3_client = boto3.client('s3', region_name=region_name)
            
            # Get S3 bucket from environment if not provided
            if s3_output_bucket is None:
                s3_output_bucket = os.getenv("S3_BUCKET_NAME", "your-s3-bucket-name")
            
            all_extracted_text = []
            
            logger.info(f"Processing {len(image_paths)} images with OCR")
            
            # Process each image
            for idx, image_path in enumerate(image_paths, start=1):
                logger.info(f"Processing image {idx}/{len(image_paths)}: {image_path}")
                
                # Load image data
                if image_path.startswith('s3://'):
                    # Download from S3
                    s3_parts = image_path[5:].split('/', 1)
                    bucket = s3_parts[0]
                    key = s3_parts[1] if len(s3_parts) > 1 else ""
                    
                    response = s3_client.get_object(Bucket=bucket, Key=key)
                    image_data = response['Body'].read()
                else:
                    # Read local file
                    with open(image_path, 'rb') as f:
                        image_data = f.read()
                
                # Encode image to base64
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                # Determine image format
                image_format = "jpeg"
                if image_path.lower().endswith('.png'):
                    image_format = "png"
                elif image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
                    image_format = "jpeg"
                
                # Prepare Bedrock request
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4096,
                    "temperature": 0.0,  # Deterministic for OCR
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": f"image/{image_format}",
                                        "data": image_base64
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": (
                                        "Please extract ALL text from this image. "
                                        "This is a trade confirmation document. "
                                        "Preserve the layout and structure as much as possible. "
                                        "Include all fields, values, headers, and footers. "
                                        "Be thorough and accurate."
                                    )
                                }
                            ]
                        }
                    ]
                }
                
                # Call Bedrock
                logger.info(f"Calling Bedrock for OCR on page {idx}")
                response = bedrock_runtime.invoke_model(
                    modelId=model_id,
                    body=json.dumps(request_body)
                )
                
                # Parse response
                response_body = json.loads(response['body'].read())
                extracted_text = response_body['content'][0]['text']
                
                # Add page separator
                page_header = f"\n{'='*80}\nPAGE {idx}\n{'='*80}\n\n"
                all_extracted_text.append(page_header + extracted_text)
                
                logger.info(f"Successfully extracted text from page {idx} ({len(extracted_text)} characters)")
            
            # Combine all text
            combined_text = "\n\n".join(all_extracted_text)
            
            # Save to local file if requested
            local_path = None
            if save_locally:
                if local_output_path:
                    local_path = Path(local_output_path)
                else:
                    # Generate default path
                    local_path = Path("./ocr_output") / "extracted_text.txt"
                
                local_path.parent.mkdir(parents=True, exist_ok=True)
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(combined_text)
                logger.info(f"Saved extracted text locally to {local_path}")
            
            # Save to S3 if requested
            s3_location = None
            if s3_output_key:
                s3_client.put_object(
                    Bucket=s3_output_bucket,
                    Key=s3_output_key,
                    Body=combined_text.encode('utf-8'),
                    ContentType='text/plain',
                    Metadata={
                        'total_pages': str(len(image_paths)),
                        'model_id': model_id,
                        'extraction_method': 'bedrock_claude_sonnet_4'
                    }
                )
                s3_location = f"s3://{s3_output_bucket}/{s3_output_key}"
                logger.info(f"Saved extracted text to S3: {s3_location}")
            
            # Prepare success message
            result_message = f"""
✅ OCR Extraction Successful!
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 Total Pages Processed: {len(image_paths)}
📝 Total Characters Extracted: {len(combined_text):,}
🤖 Model: {model_id}
☁️  S3 Location: {s3_location or 'Not saved to S3'}
💾 Local File: {local_path or 'Not saved locally'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Text ready for entity extraction
"""
            
            return result_message
            
        except Exception as e:
            error_msg = f"❌ Error during OCR extraction: {str(e)}"
            logger.error(error_msg)
            return error_msg
