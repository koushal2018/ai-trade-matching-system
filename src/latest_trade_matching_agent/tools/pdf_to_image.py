from typing import Type, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from pdf2image import convert_from_path
import os
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFToImageInput(BaseModel):
    """Input schema for PDFToImageTool."""
    pdf_path: str = Field(
        description="Path to the PDF file on disk"
    )
    output_folder: str = Field(
        "./pdf_images", 
        description="Folder to save the generated images locally"
    )
    dpi: int = Field(
        200, 
        description="DPI for image quality (200 for OCR, 150 for thumbnails)"
    )
    output_format: str = Field(
        "PNG", 
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
    
class PDFToImageTool(BaseTool):
    name: str = "PDF to Image Converter"
    description: str = (
        "Converts PDF documents to images locally. "
        "Perfect for preparing documents for OCR processing."
    )
    args_schema: Type[BaseModel] = PDFToImageInput

    
    def _run(
        self, 
        pdf_path: str,
        output_folder: str = "./pdf_images",
        dpi: int = 200,
        output_format: str = "PNG",
        first_page: Optional[int] = None,
        last_page: Optional[int] = None
    ) -> str:
        """
        Convert PDF to images locally.
        Returns a detailed summary of the conversion process.
        """
        try:
            # Create output directory
            output_path = Path(output_folder)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Get source name
            source_name = Path(pdf_path).stem
            
            # Convert PDF to images
            logger.info(f"Converting PDF to images at {dpi} DPI")
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                first_page=first_page,
                last_page=last_page
            )
            
            # Save images locally
            saved_locations = []
            for i, image in enumerate(images, start=1):
                page_num = (first_page or 1) + i - 1
                filename = f"{source_name}_page_{page_num}.{output_format.lower()}"
                filepath = os.path.join(output_folder, filename)
                image.save(filepath, output_format)
                saved_locations.append(filepath)
                logger.info(f"Saved page {page_num} to {filepath}")
            
            # Prepare success message
            result_message = f"""
✅ PDF Conversion Successful!
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 Source: {pdf_path}
📊 Total Pages: {len(images)}
🎯 DPI: {dpi}
📸 Format: {output_format}
💾 Local Files: {len(saved_locations)} files
   Folder: {output_folder}
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ready for OCR processing
"""
            
            return result_message
            
        except Exception as e:
            error_msg = f"❌ Error converting PDF to images: {str(e)}"
            logger.error(error_msg)
            return error_msg