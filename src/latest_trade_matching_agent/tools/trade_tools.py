from crewai.tools import BaseTool
from crewai import LLM
from typing import Type, Dict, Any
from pydantic import BaseModel, Field
import json
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
import base64
from pdf2image import convert_from_path
from PIL import Image
import io
import tempfile
import os
import litellm

class TradeStorageInput(BaseModel):
    """Input schema for TradeStorageTool."""
    trade_data: Dict[str, Any] = Field(..., description="Trade data in JSON format")
    file_path: str = Field(..., description="File path to determine routing logic")

class TradeStorageTool(BaseTool):
    name: str = "TradeStorageTool"
    description: str = "Stores trade data in TinyDB (local NoSQL database) based on file path routing"
    args_schema: Type[BaseModel] = TradeStorageInput

    def _run(self, trade_data: Dict[str, Any], file_path: str) -> str:
        try:
            # Determine database file based on file path
            if "/BANK/" in file_path:
                db_file = "./storage/bank_trade_data.db"
                table_name = "bank_trades"
            elif "/COUNTERPARTY/" in file_path:
                db_file = "./storage/counterparty_trade_data.db"
                table_name = "counterparty_trades"
            else:
                return f"Error: Cannot determine storage location from file path: {file_path}"
            
            # Ensure storage directory exists
            os.makedirs(os.path.dirname(db_file), exist_ok=True)
            
            # Initialize TinyDB with caching for better performance
            db = TinyDB(db_file, storage=CachingMiddleware(JSONStorage))
            table = db.table(table_name)
            
            # Prepare comprehensive item for DynamoDB storage with flexible schema
            # Extract trade ID from various possible locations in the nested structure
            trade_id = (
                trade_data.get('trade_id') or 
                trade_data.get('tradeId') or
                (trade_data.get('document_metadata', {}).get('trade_id')) or
                (trade_data.get('confirmation_details', {}).get('trade_id')) or
                'unknown'
            )
            
            # Use trade_id as internal_reference (primary key) 
            internal_ref = str(trade_id)
            
            # Store the COMPLETE extracted data structure as-is
            # This preserves all the comprehensive information extracted by the vision model
            item = {
                'internal_reference': internal_ref,  # Primary key
                'complete_trade_data': trade_data,  # Store entire extracted JSON
                'file_path': file_path,
                'processed_at': int(__import__('time').time()),
                
                # Extract key fields for easy querying while preserving full data
                'trade_id': trade_id,
                'commodity': trade_data.get('commodity', 'NOT_FOUND'),
                'trade_date': trade_data.get('trade_date', 'NOT_FOUND'),
                'effective_date': trade_data.get('effective_date', 'NOT_FOUND'),
                'termination_date': trade_data.get('termination_date', 'NOT_FOUND'),
                'parties': trade_data.get('parties', {}),
                
                # Extract fixed price if available
                'fixed_price': trade_data.get('fixed_price', {}),
                'floating_amount_details': trade_data.get('floating_amount_details', {}),
                'total_notional_quantity': trade_data.get('total_notional_quantity', {}),
                'match_status': 'unmatched',  # Default status for matching
            }
            
            # Check for duplicates using TinyDB query
            Trade = Query()
            existing_trade = table.search(
                (Trade.internal_reference == internal_ref) | 
                (Trade.trade_id == trade_id)
            )
            
            if existing_trade:
                # Update existing trade
                table.update(item, Trade.internal_reference == internal_ref)
                action = "updated"
            else:
                # Insert new trade
                doc_id = table.insert(item)
                action = "inserted"
                
                # IMMEDIATELY ATTEMPT MATCHING
                # Look for pending trades from the opposite source
                opposite_source = 'bank' if '/COUNTERPARTY/' in file_path else 'counterparty'
                opposite_db_file = f"./storage/{opposite_source}_trade_data.db"
                
                if os.path.exists(opposite_db_file):
                    opposite_db = TinyDB(opposite_db_file, storage=CachingMiddleware(JSONStorage))
                    opposite_table = opposite_db.table(f"{opposite_source}_trades")
                    
                    # Search for potential matches
                    potential_matches = opposite_table.search(
                        (Trade.match_status == 'unmatched') &
                        (Trade.trade_date == item.get('trade_date', ''))
                    )
                    
                    if potential_matches:
                        # Found potential match - update both trades
                        match_id = f"MATCH_{int(__import__('time').time())}"
                        
                        # Update current trade
                        table.update({'match_status': 'matched', 'match_id': match_id}, doc_ids=[doc_id])
                        
                        # Update matched trade
                        matched_trade = potential_matches[0]
                        opposite_table.update(
                            {'match_status': 'matched', 'match_id': match_id},
                            doc_ids=[matched_trade.doc_id]
                        )
                        
                        action = f"inserted and MATCHED with {opposite_source} trade"
                    else:
                        action = f"inserted - PENDING (awaiting {opposite_source} confirmation)"
                    
                    opposite_db.close()
                else:
                    action = f"inserted - PENDING (no {opposite_source} trades yet)"
            
            # Get total records count
            total_records = len(table.all())
            
            # Close database connection
            db.close()
            
            result = {
                "status": "success",
                "database": db_file,
                "table": table_name,
                "trade_id": trade_id,
                "action": action,
                "message": f"Trade data {action} successfully in {table_name}",
                "total_records": total_records
            }
            
            return json.dumps(result, indent=2)
            
        except FileNotFoundError as e:
            return f"File system error: {str(e)}"
        except Exception as e:
            return f"Error storing trade data: {str(e)}"


class TradeRetrievalInput(BaseModel):
    """Input schema for TradeRetrievalTool."""
    source: str = Field(..., description="Source type: 'bank', 'counterparty', or 'all'")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Optional filters for querying")

class TradeRetrievalTool(BaseTool):
    name: str = "TradeRetrievalTool"
    description: str = "Retrieves trade data from TinyDB for matching analysis"
    args_schema: Type[BaseModel] = TradeRetrievalInput

    def _run(self, source: str, filters: Dict[str, Any] = None) -> str:
        try:
            results = {}
            
            if filters is None:
                filters = {}
            
            # Determine which databases to query
            databases_to_query = []
            if source.lower() in ['bank', 'all']:
                databases_to_query.append(('./storage/bank_trade_data.db', 'bank_trades', 'bank'))
            if source.lower() in ['counterparty', 'all']:
                databases_to_query.append(('./storage/counterparty_trade_data.db', 'counterparty_trades', 'counterparty'))
            
            for db_file, table_name, source_type in databases_to_query:
                if not os.path.exists(db_file):
                    results[source_type] = {"error": f"Database file not found: {db_file}"}
                    continue
                
                db = TinyDB(db_file, storage=CachingMiddleware(JSONStorage))
                table = db.table(table_name)
                
                # Apply filters if provided
                if filters:
                    Trade = Query()
                    query_conditions = []
                    
                    for key, value in filters.items():
                        if key == 'trade_date':
                            query_conditions.append(Trade.trade_date == value)
                        elif key == 'match_status':
                            query_conditions.append(Trade.match_status == value)
                        elif key == 'commodity':
                            query_conditions.append(Trade.commodity == value)
                        elif key == 'trade_id':
                            query_conditions.append(Trade.trade_id == value)
                    
                    if query_conditions:
                        # Combine conditions with AND
                        combined_query = query_conditions[0]
                        for condition in query_conditions[1:]:
                            combined_query = combined_query & condition
                        
                        trades = table.search(combined_query)
                    else:
                        trades = table.all()
                else:
                    trades = table.all()
                
                results[source_type] = {
                    "total_trades": len(trades),
                    "trades": trades,
                    "database": db_file,
                    "table": table_name
                }
                
                db.close()
            
            return json.dumps(results, indent=2, default=str)
            
        except Exception as e:
            return f"Error retrieving trade data: {str(e)}"


class MatchingStatusInput(BaseModel):
    """Input schema for MatchingStatusTool."""
    generate_report: bool = Field(default=True, description="Whether to generate a detailed report")

class MatchingStatusTool(BaseTool):
    name: str = "MatchingStatusTool"
    description: str = "Check matching status and generate reports for all trades"
    args_schema: Type[BaseModel] = MatchingStatusInput

    def _run(self, generate_report: bool = True) -> str:
        try:
            status = {
                'timestamp': __import__('time').strftime('%Y-%m-%d %H:%M:%S'),
                'bank_trades': {'total': 0, 'matched': 0, 'pending': 0},
                'counterparty_trades': {'total': 0, 'matched': 0, 'pending': 0},
                'matches': [],
                'pending_trades': []
            }
            
            # Check bank trades
            if os.path.exists('./storage/bank_trade_data.db'):
                db = TinyDB('./storage/bank_trade_data.db', storage=CachingMiddleware(JSONStorage))
                table = db.table('bank_trades')
                all_trades = table.all()
                
                status['bank_trades']['total'] = len(all_trades)
                for trade in all_trades:
                    if trade.get('match_status') == 'matched':
                        status['bank_trades']['matched'] += 1
                    else:
                        status['bank_trades']['pending'] += 1
                        status['pending_trades'].append({
                            'source': 'bank',
                            'trade_id': trade.get('trade_id'),
                            'trade_date': trade.get('trade_date'),
                            'status': 'PENDING - Awaiting counterparty confirmation'
                        })
                db.close()
            
            # Check counterparty trades
            if os.path.exists('./storage/counterparty_trade_data.db'):
                db = TinyDB('./storage/counterparty_trade_data.db', storage=CachingMiddleware(JSONStorage))
                table = db.table('counterparty_trades')
                all_trades = table.all()
                
                status['counterparty_trades']['total'] = len(all_trades)
                for trade in all_trades:
                    if trade.get('match_status') == 'matched':
                        status['counterparty_trades']['matched'] += 1
                    else:
                        status['counterparty_trades']['pending'] += 1
                        status['pending_trades'].append({
                            'source': 'counterparty',
                            'trade_id': trade.get('trade_id'),
                            'trade_date': trade.get('trade_date'),
                            'status': 'PENDING - Awaiting bank confirmation'
                        })
                db.close()
            
            # Generate report
            if generate_report:
                report = f"""
TRADE MATCHING STATUS REPORT
============================
Generated: {status['timestamp']}

SUMMARY:
--------
Bank Trades:
  Total: {status['bank_trades']['total']}
  Matched: {status['bank_trades']['matched']}
  Pending: {status['bank_trades']['pending']}

Counterparty Trades:
  Total: {status['counterparty_trades']['total']}
  Matched: {status['counterparty_trades']['matched']}
  Pending: {status['counterparty_trades']['pending']}

Match Rate: {self._calculate_match_rate(status):.1f}%

PENDING TRADES:
--------------"""
                if status['pending_trades']:
                    for trade in status['pending_trades']:
                        report += f"\n  • {trade['source'].upper()}: {trade['trade_id']} - {trade['status']}"
                else:
                    report += "\n  None - All trades matched!"
                
                report += "\n\nRECOMMENDATIONS:\n"
                if status['pending_trades']:
                    report += "• Monitor for incoming confirmations from counterparties\n"
                    report += "• Follow up on aged pending trades (>24 hours)\n"
                else:
                    report += "• All trades successfully matched - no action required\n"
                
                return report
            
            return json.dumps(status, indent=2)
            
        except Exception as e:
            return f"Error generating matching status: {str(e)}"
    
    def _calculate_match_rate(self, status):
        """Calculate overall match rate"""
        total_matched = status['bank_trades']['matched'] + status['counterparty_trades']['matched']
        total_trades = status['bank_trades']['total'] + status['counterparty_trades']['total']
        
        if total_trades == 0:
            return 0.0
        
        # Each match involves 2 trades, so divide matched by 2
        return (total_matched / total_trades) * 100

class PDFExtractorInput(BaseModel):
    """Input schema for PDFExtractorTool."""
    file_path: str = Field(..., description="Local path to PDF file")

class PDFExtractorTool(BaseTool):
    name: str = "PDFExtractorTool"
    description: str = "Extracts structured trade data from local PDF files using vision language model"
    args_schema: Type[BaseModel] = PDFExtractorInput

    def __init__(self):
        super().__init__()
        # Initialize s3_client in _run method to avoid Pydantic field issues

    def _get_local_pdf_path(self, file_path: str) -> str:
        """Get local PDF file path"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            return file_path
            
        except Exception as e:
            raise Exception(f"Failed to access local PDF: {str(e)}")

    def _pdf_to_images(self, pdf_path: str) -> list:
        """Convert ALL PDF pages to images for complete extraction"""
        try:
            # Process ALL pages to capture complete trade details
            images = convert_from_path(pdf_path, dpi=200)
            print(f"Processing {len(images)} pages from PDF")
            return images
        except Exception as e:
            raise Exception(f"Failed to convert PDF to images: {str(e)}")

    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL image to base64 string"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        return base64.b64encode(image_bytes).decode('utf-8')

    def _extract_trade_data_with_vision(self, image_base64: str, page_num: int = 1) -> str:
        """Extract trade data using GPT-4o Vision model"""
        
        # Create comprehensive prompt that captures ALL document content
        text_prompt = """You are a comprehensive financial document digitization system. Your task is to extract and structure EVERY piece of information from this trade confirmation document.

CRITICAL: You must capture ALL sections and details including:

**COMPLETE DOCUMENT DIGITIZATION:**
- Read the ENTIRE document from top to bottom
- Extract ALL numerical values, dates, percentages, prices, quantities
- Capture ALL section headings and their complete content
- Include ALL party details, contact information, addresses
- Extract ALL terms, conditions, and specifications
- Capture ALL calculation methods, formulas, and procedures

**SECTIONS TO FULLY EXTRACT:**
- Header information and document metadata
- Party details (From/To sections with full contact info)
- General Terms (all dates, quantities, commodities)
- Fixed Amount Details (prices, payers, currencies)
- Floating Amount Details (reference prices, calculation methods)
- Settlement terms and conditions
- Calculation Agent provisions
- Account Details and payment instructions
- Additional Provisions and special terms
- Signature requirements and confirmations
- ALL other sections present in the document

**EXTRACTION REQUIREMENTS:**
- Preserve exact values, dates, and technical specifications
- Maintain relationships between related information
- Include units of measurement, currencies, and percentages
- Capture procedural and operational details
- Extract contact details, addresses, and reference numbers

Be exhaustive - capture every piece of data that exists in this document. Structure it logically but comprehensively.

Return ONLY a valid JSON object containing all the trade data you extract. Structure the JSON logically with appropriate field names that reflect the content you find. Use nested objects where it makes sense (e.g., for party information, pricing details, dates, etc.).

Format dates as YYYY-MM-DD where possible. Include units and currencies with numeric values where relevant. Be creative and comprehensive with your field names to capture all the meaningful information.

Return only the JSON, no other text or explanations."""

        try:
            # Call GPT-4o directly with litellm for vision processing
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": text_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                ]
            }]
            
            response = litellm.completion(
                model="gpt-4o",
                messages=messages,
                temperature=0.1,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Vision extraction error: {str(e)}"

    def _run(self, file_path: str) -> str:
        try:
            # Get local PDF path
            pdf_path = self._get_local_pdf_path(file_path)
            
            # Convert PDF to images for vision processing
            images = self._pdf_to_images(pdf_path)
            
            if not images:
                return f"Error: No images extracted from PDF at {file_path}"
            
            # Process ALL pages to get complete trade information
            all_extracted_data = []
            
            for i, page_image in enumerate(images):
                page_image_base64 = self._image_to_base64(page_image)
                
                # Extract data from each page
                page_data = self._extract_trade_data_with_vision(page_image_base64, page_num=i+1)
                
                if page_data and page_data != "Vision extraction error":
                    all_extracted_data.append(f"=== PAGE {i+1} ===\n{page_data}")
            
            # Combine all pages data
            if all_extracted_data:
                combined_result = "\n\n".join(all_extracted_data)
                return f"Extracted content from {file_path} ({len(images)} pages):\n{combined_result}"
            else:
                return f"Error: No valid data extracted from any page of {file_path}"
            
        except Exception as e:
            return f"Error extracting from {file_path}: {str(e)}"
        except Exception as e:
            return f"Error processing PDF: {str(e)}"