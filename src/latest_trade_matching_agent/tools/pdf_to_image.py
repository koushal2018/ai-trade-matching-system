from typing import Type, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from pdf2image import convert_from_path
import os
from pathlib import Path
import logging
import boto3
import tempfile
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFToImageInput(BaseModel):
    """Input schema for PDFToImageTool."""
    pdf_path: str = Field(
        description="Path to the PDF file (local path or S3 URI like s3://bucket/key)"
    )
    s3_output_bucket: str = Field(
        default="your-s3-bucket-name",
        description="S3 bucket for output images"
    )
    s3_output_prefix: str = Field(
        "PDFIMAGES/TEMP",
        description="S3 prefix/folder for output images (e.g., PDFIMAGES/TEMP)"
    )
    dpi: int = Field(
        200, 
        description="DPI for image quality (200 for OCR, 150 for thumbnails)"
    )
    output_format: str = Field(
        "JPEG", 
        description="Output image format (PNG, JPEG, TIFF)"
    )
    first_page: Optional[int] = Field(
        None, 
        description="First page to convert (1-based)"
    )
    last_page: Optional[int] = Field(
        None, 
        description="Last page to convert (1-based)"
    )
    save_locally: bool = Field(
        True,
        description="Also save images locally (in addition to S3)"
    )
    local_output_folder: str = Field(
        "./pdf_images",
        description="Local folder for images if save_locally is True"
    )
    unique_identifier: str = Field(
        "",
        description="Unique identifier for creating separate folders per trade"
    )
    
class PDFToImageTool(BaseTool):
    name: str = "PDF to Image Converter"
    description: str = (
        "Converts PDF documents to images and saves them to S3 and locally. "
        "Supports local files and S3 URIs as input. "
        "Perfect for preparing documents for OCR processing in the trade matching pipeline."
    )
    args_schema: Type[BaseModel] = PDFToImageInput

    def _run(
        self, 
        pdf_path: str,
        s3_output_bucket: str = None,
        s3_output_prefix: str = "PDFIMAGES/TEMP",
        dpi: int = 200,
        output_format: str = "JPEG",
        first_page: Optional[int] = None,
        last_page: Optional[int] = None,
        save_locally: bool = True,
        local_output_folder: str = "./pdf_images",
        unique_identifier: str = ""
    ) -> str:
        """
        Convert PDF to images and upload to S3 while also saving locally.
        Returns the S3 location and local folder path.
        """
        try:
            # Get S3 bucket from environment or use provided value
            if s3_output_bucket is None:
                s3_output_bucket = os.getenv("S3_BUCKET_NAME", "your-s3-bucket-name")
            
            # Initialize S3 client
            s3_client = boto3.client('s3')
            
            # Handle S3 URIs for input
            if pdf_path.startswith('s3://'):
                # Parse S3 URI
                s3_parts = pdf_path[5:].split('/', 1)
                bucket = s3_parts[0]
                key = s3_parts[1] if len(s3_parts) > 1 else ""
                
                # Download from S3 to temp file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                s3_client.download_file(bucket, key, temp_file.name)
                local_pdf_path = temp_file.name
                source_name = Path(key).stem
            else:
                local_pdf_path = pdf_path
                source_name = Path(pdf_path).stem
            
            # Generate timestamp for unique folder name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create S3 folder path
            s3_folder = f"{s3_output_prefix}/{source_name}_{timestamp}"
            
            # Convert PDF to images
            logger.info(f"Converting PDF to images at {dpi} DPI")
            images = convert_from_path(
                local_pdf_path,
                dpi=dpi,
                first_page=first_page,
                last_page=last_page
            )
            
            # Clean up temp file if S3 input
            if pdf_path.startswith('s3://'):
                os.unlink(local_pdf_path)
            
            # Save images to S3 and locally
            s3_locations = []
            local_locations = []
            
            # Create local output directory with unique identifier
            if save_locally:
                if unique_identifier:
                    local_path = Path(local_output_folder) / unique_identifier
                else:
                    local_path = Path(local_output_folder)
                local_path.mkdir(parents=True, exist_ok=True)
            
            for i, image in enumerate(images, start=1):
                page_num = (first_page or 1) + i - 1
                filename = f"{source_name}_page_{page_num:03d}.png"
                
                # Save locally first
                if save_locally:
                    local_file_path = local_path / f"{source_name}_page_{page_num:03d}.jpg"
                    image.save(local_file_path, "JPEG", quality=95)
                    local_locations.append(str(local_file_path))
                    logger.info(f"Saved page {page_num} locally to {local_file_path}")
                
                # Convert image to bytes for S3
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_img:
                    image.save(tmp_img.name, "JPEG", quality=95)
                    
                    # Upload to S3
                    s3_key = f"{s3_folder}/{source_name}_page_{page_num:03d}.jpg"
                    with open(tmp_img.name, 'rb') as img_data:
                        s3_client.put_object(
                            Bucket=s3_output_bucket,
                            Key=s3_key,
                            Body=img_data,
                            ContentType='image/jpeg',
                            Metadata={
                                'source_pdf': pdf_path,
                                'page_number': str(page_num),
                                'dpi': str(dpi),
                                'conversion_timestamp': timestamp
                            }
                        )
                    
                    s3_locations.append(f"s3://{s3_output_bucket}/{s3_key}")
                    logger.info(f"Uploaded page {page_num} to S3: {s3_key}")
                    
                    # Clean up temp file
                    os.unlink(tmp_img.name)
            
            # Create metadata file in S3
            metadata = {
                'source_pdf': pdf_path,
                'conversion_timestamp': timestamp,
                'total_pages': len(images),
                'dpi': dpi,
                'output_format': 'JPEG',
                's3_folder': f"s3://{s3_output_bucket}/{s3_folder}/",
                'image_files': [Path(loc).name for loc in s3_locations]
            }
            
            metadata_key = f"{s3_folder}/metadata.json"
            s3_client.put_object(
                Bucket=s3_output_bucket,
                Key=metadata_key,
                Body=json.dumps(metadata, indent=2),
                ContentType='application/json'
            )
            
            # Prepare success message
            result_message = f"""
✅ PDF Conversion Successful!
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 Source: {pdf_path}
📊 Total Pages: {len(images)}
🎯 DPI: {dpi}
📸 Format: JPEG (S3) / JPEG (Local)
☁️  S3 Location: s3://{s3_output_bucket}/{s3_folder}/
💾 Local Files: {len(local_locations)} files in {local_path if save_locally else local_output_folder}
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Images ready for OCR processing
"""
            
            return result_message
            
        except Exception as e:
            error_msg = f"❌ Error converting PDF to images: {str(e)}"
            logger.error(error_msg)
            return error_msg