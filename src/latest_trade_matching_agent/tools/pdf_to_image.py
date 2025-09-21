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
        output_format: str = "JPEG",
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
            
            # Get source name and create subfolder
            source_name = Path(pdf_path).stem
            subfolder_name = f"{source_name}_images"
            subfolder_path = output_path / subfolder_name
            subfolder_path.mkdir(parents=True, exist_ok=True)
            
            # Save folder name for reference
            folder_name_file = output_path / "folder_name.txt"
            with open(folder_name_file, 'w') as f:
                f.write(subfolder_name)
            
            # Convert PDF to images
            logger.info(f"Converting PDF to images at {dpi} DPI")
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                first_page=first_page,
                last_page=last_page
            )
            
            # Save images locally with .jpg extension
            saved_locations = []
            for i, image in enumerate(images, start=1):
                page_num = (first_page or 1) + i - 1
                filename = f"{source_name}_page_{page_num}.jpg"
                filepath = subfolder_path / filename
                image.save(filepath, "JPEG")
                saved_locations.append(str(filepath))
                logger.info(f"Saved page {page_num} to {filepath}")
            
            # Prepare success message
            result_message = f"""
✅ PDF Conversion Successful!
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 Source: {pdf_path}
📊 Total Pages: {len(images)}
🎯 DPI: {dpi}
📸 Format: JPEG
💾 Local Files: {len(saved_locations)} files
   Folder: {subfolder_path}
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ready for OCR processing
"""
            
            return result_message
            
        except Exception as e:
            error_msg = f"❌ Error converting PDF to images: {str(e)}"
            logger.error(error_msg)
            return error_msg