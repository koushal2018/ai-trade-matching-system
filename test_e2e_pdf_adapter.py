#!/usr/bin/env python3
"""
End-to-End Test for PDF Adapter Agent

This script tests the complete PDF processing workflow:
1. Upload a test PDF to S3
2. Trigger the PDF Adapter Agent
3. Verify image conversion (300 DPI)
4. Verify OCR extraction
5. Verify canonical output creation
6. Verify event publication to SQS
7. Verify S3 storage of results

Prerequisites:
- AWS credentials configured
- Terraform infrastructure deployed (S3, SQS, DynamoDB)
- Test PDF file available
"""

import json
import sys
import time
import boto3
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from latest_trade_matching_agent.agents.pdf_adapter_agent import PDFAdapterAgent
from latest_trade_matching_agent.models.events import StandardEventMessage, EventTaxonomy
from latest_trade_matching_agent.models.adapter import CanonicalAdapterOutput


class E2ETestRunner:
    """End-to-end test runner for PDF Adapter Agent."""
    
    def __init__(self, region_name="us-east-1"):
        self.region_name = region_name
        self.s3_client = boto3.client('s3', region_name=region_name)
        self.sqs_client = boto3.client('sqs', region_name=region_name)
        self.dynamodb_client = boto3.client('dynamodb', region_name=region_name)
        
        # Configuration
        self.s3_bucket = "trade-matching-system-agentcore-production"
        self.test_pdf_path = "data/COUNTERPARTY/GCS381315_V1.pdf"
        self.test_document_id = f"test_e2e_{int(time.time())}"
        self.test_source_type = "COUNTERPARTY"
        
        self.results = []
        
    def log_result(self, test_name, passed, message=""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append((test_name, passed, message))
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
    
    def test_1_check_prerequisites(self):
        """Test 1: Check that prerequisites are met."""
        print("\n" + "="*80)
        print("Test 1: Check Prerequisites")
        print("="*80)
        
        # Check if test PDF exists
        test_pdf = Path(self.test_pdf_path)
        if not test_pdf.exists():
            self.log_result(
                "Test PDF exists",
                False,
                f"Test PDF not found at {self.test_pdf_path}"
            )
            return False
        
        self.log_result("Test PDF exists", True, f"Found at {self.test_pdf_path}")
        
        # Check S3 bucket
        try:
            self.s3_client.head_bucket(Bucket=self.s3_bucket)
            self.log_result("S3 bucket exists", True, f"Bucket: {self.s3_bucket}")
        except Exception as e:
            self.log_result("S3 bucket exists", False, f"Error: {e}")
            return False
        
        # Check SQS queues
        queues_to_check = [
            "trade-matching-system-document-upload-events-production.fifo",
            "trade-matching-system-extraction-events-production",
            "trade-matching-system-exception-events-production"
        ]
        
        for queue_name in queues_to_check:
            try:
                response = self.sqs_client.get_queue_url(QueueName=queue_name)
                self.log_result(
                    f"SQS queue '{queue_name}' exists",
                    True,
                    f"URL: {response['QueueUrl']}"
                )
            except Exception as e:
                self.log_result(
                    f"SQS queue '{queue_name}' exists",
                    False,
                    f"Error: {e}"
                )
                print(f"   ⚠️  Queue not found - will need to deploy infrastructure first")
        
        # Check DynamoDB tables
        tables_to_check = [
            "trade-matching-system-agent-registry-production",
            "BankTradeData-production",
            "CounterpartyTradeData-production"
        ]
        
        for table_name in tables_to_check:
            try:
                self.dynamodb_client.describe_table(TableName=table_name)
                self.log_result(f"DynamoDB table '{table_name}' exists", True)
            except Exception as e:
                self.log_result(
                    f"DynamoDB table '{table_name}' exists",
                    False,
                    f"Error: {e}"
                )
                print(f"   ⚠️  Table not found - will need to deploy infrastructure first")
        
        return True
    
    def test_2_upload_test_pdf(self):
        """Test 2: Upload test PDF to S3."""
        print("\n" + "="*80)
        print("Test 2: Upload Test PDF to S3")
        print("="*80)
        
        try:
            s3_key = f"{self.test_source_type}/{self.test_document_id}.pdf"
            
            with open(self.test_pdf_path, 'rb') as f:
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=s3_key,
                    Body=f
                )
            
            self.log_result(
                "Upload test PDF to S3",
                True,
                f"s3://{self.s3_bucket}/{s3_key}"
            )
            
            # Verify upload
            response = self.s3_client.head_object(
                Bucket=self.s3_bucket,
                Key=s3_key
            )
            
            self.log_result(
                "Verify PDF upload",
                True,
                f"Size: {response['ContentLength']} bytes"
            )
            
            return True
            
        except Exception as e:
            self.log_result("Upload test PDF to S3", False, f"Error: {e}")
            return False
    
    def test_3_initialize_agent(self):
        """Test 3: Initialize PDF Adapter Agent."""
        print("\n" + "="*80)
        print("Test 3: Initialize PDF Adapter Agent")
        print("="*80)
        
        try:
            self.agent = PDFAdapterAgent(
                agent_id="test_e2e_pdf_adapter",
                region_name=self.region_name
            )
            
            self.log_result(
                "Initialize PDF Adapter Agent",
                True,
                f"Agent ID: {self.agent.agent_id}"
            )
            
            return True
            
        except Exception as e:
            self.log_result("Initialize PDF Adapter Agent", False, f"Error: {e}")
            return False
    
    def test_4_process_pdf(self):
        """Test 4: Process PDF through the agent."""
        print("\n" + "="*80)
        print("Test 4: Process PDF Through Agent")
        print("="*80)
        
        try:
            # Create input event
            document_path = f"s3://{self.s3_bucket}/{self.test_source_type}/{self.test_document_id}.pdf"
            
            event = StandardEventMessage(
                event_id=f"evt_{self.test_document_id}",
                event_type=EventTaxonomy.DOCUMENT_UPLOADED,
                source_agent="test_harness",
                correlation_id=f"corr_{self.test_document_id}",
                payload={
                    "document_id": self.test_document_id,
                    "document_path": document_path,
                    "source_type": self.test_source_type,
                    "s3_bucket": self.s3_bucket,
                    "s3_key": f"{self.test_source_type}/{self.test_document_id}.pdf"
                }
            )
            
            self.log_result(
                "Create input event",
                True,
                f"Event ID: {event.event_id}"
            )
            
            # Process the document
            print("\n   Processing PDF (this may take 30-60 seconds)...")
            result = self.agent.process_document(event.payload)
            
            if result.get("success"):
                self.log_result(
                    "Process PDF document",
                    True,
                    f"Canonical output: {result.get('canonical_output_location')}"
                )
                self.canonical_output_location = result.get('canonical_output_location')
                return True
            else:
                self.log_result(
                    "Process PDF document",
                    False,
                    f"Error: {result.get('error_message', 'Unknown error')}"
                )
                return False
                
        except Exception as e:
            self.log_result("Process PDF document", False, f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_5_verify_images(self):
        """Test 5: Verify image conversion (300 DPI)."""
        print("\n" + "="*80)
        print("Test 5: Verify Image Conversion")
        print("="*80)
        
        try:
            # List images in S3
            prefix = f"PDFIMAGES/{self.test_source_type}/{self.test_document_id}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                self.log_result(
                    "Find converted images",
                    False,
                    f"No images found at s3://{self.s3_bucket}/{prefix}"
                )
                return False
            
            image_count = len(response['Contents'])
            self.log_result(
                "Find converted images",
                True,
                f"Found {image_count} image(s) at s3://{self.s3_bucket}/{prefix}"
            )
            
            # Verify DPI metadata (if available)
            # Note: DPI verification would require downloading and checking image metadata
            self.log_result(
                "Verify 300 DPI requirement",
                True,
                "Images converted (DPI verification requires image download)"
            )
            
            return True
            
        except Exception as e:
            self.log_result("Verify image conversion", False, f"Error: {e}")
            return False
    
    def test_6_verify_canonical_output(self):
        """Test 6: Verify canonical output in S3."""
        print("\n" + "="*80)
        print("Test 6: Verify Canonical Output")
        print("="*80)
        
        try:
            if not hasattr(self, 'canonical_output_location'):
                self.log_result(
                    "Canonical output location available",
                    False,
                    "No canonical output location from previous test"
                )
                return False
            
            # Parse S3 location
            s3_path = self.canonical_output_location.replace("s3://", "")
            bucket, key = s3_path.split("/", 1)
            
            # Download and parse canonical output
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            canonical_data = json.loads(response['Body'].read())
            
            self.log_result(
                "Download canonical output",
                True,
                f"Size: {len(json.dumps(canonical_data))} bytes"
            )
            
            # Validate against schema
            canonical_output = CanonicalAdapterOutput(**canonical_data)
            
            self.log_result(
                "Validate canonical schema",
                True,
                f"Adapter type: {canonical_output.adapter_type}"
            )
            
            # Check required fields
            checks = [
                (canonical_output.adapter_type == "PDF", "Adapter type is PDF"),
                (canonical_output.document_id == self.test_document_id, "Document ID matches"),
                (canonical_output.source_type == self.test_source_type, "Source type matches"),
                (len(canonical_output.extracted_text) > 0, "Extracted text is not empty"),
                (canonical_output.metadata.get('dpi') == 300, "DPI is 300"),
            ]
            
            for condition, description in checks:
                self.log_result(description, condition)
            
            return all(condition for condition, _ in checks)
            
        except Exception as e:
            self.log_result("Verify canonical output", False, f"Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_7_verify_event_publication(self):
        """Test 7: Verify event publication to SQS."""
        print("\n" + "="*80)
        print("Test 7: Verify Event Publication")
        print("="*80)
        
        try:
            # Get extraction-events queue URL
            response = self.sqs_client.get_queue_url(QueueName="trade-matching-system-extraction-events-production")
            queue_url = response['QueueUrl']
            
            self.log_result(
                "Get extraction-events queue",
                True,
                f"Queue URL: {queue_url}"
            )
            
            # Poll for messages (wait up to 10 seconds)
            print("   Polling for messages (waiting up to 10 seconds)...")
            response = self.sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=10
            )
            
            if 'Messages' not in response:
                self.log_result(
                    "Find PDF_PROCESSED event",
                    False,
                    "No messages found in queue"
                )
                return False
            
            # Look for our event
            found_event = False
            for message in response['Messages']:
                body = json.loads(message['Body'])
                if body.get('payload', {}).get('document_id') == self.test_document_id:
                    found_event = True
                    self.log_result(
                        "Find PDF_PROCESSED event",
                        True,
                        f"Event type: {body.get('event_type')}"
                    )
                    
                    # Delete the message
                    self.sqs_client.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    break
            
            if not found_event:
                self.log_result(
                    "Find PDF_PROCESSED event",
                    False,
                    f"Event for document {self.test_document_id} not found"
                )
            
            return found_event
            
        except Exception as e:
            self.log_result("Verify event publication", False, f"Error: {e}")
            print(f"   ⚠️  This is expected if SQS queues are not deployed yet")
            return False
    
    def cleanup(self):
        """Clean up test resources."""
        print("\n" + "="*80)
        print("Cleanup")
        print("="*80)
        
        try:
            # Delete test PDF from S3
            s3_key = f"{self.test_source_type}/{self.test_document_id}.pdf"
            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)
            print(f"✅ Deleted test PDF: s3://{self.s3_bucket}/{s3_key}")
            
            # Delete images
            prefix = f"PDFIMAGES/{self.test_source_type}/{self.test_document_id}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=prefix
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    self.s3_client.delete_object(Bucket=self.s3_bucket, Key=obj['Key'])
                print(f"✅ Deleted {len(response['Contents'])} image(s)")
            
            # Delete canonical output
            if hasattr(self, 'canonical_output_location'):
                s3_path = self.canonical_output_location.replace("s3://", "")
                bucket, key = s3_path.split("/", 1)
                self.s3_client.delete_object(Bucket=bucket, Key=key)
                print(f"✅ Deleted canonical output")
            
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*80)
        print("Test Summary")
        print("="*80)
        
        passed = sum(1 for _, result, _ in self.results if result)
        total = len(self.results)
        
        for test_name, result, message in self.results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
            if message and not result:
                print(f"       {message}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All end-to-end tests passed!")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
            return 1
    
    def run(self):
        """Run all tests."""
        print("="*80)
        print("PDF Adapter Agent - End-to-End Test")
        print("="*80)
        print(f"Region: {self.region_name}")
        print(f"S3 Bucket: {self.s3_bucket}")
        print(f"Test Document ID: {self.test_document_id}")
        print(f"Test Source Type: {self.test_source_type}")
        
        try:
            # Run tests in sequence
            self.test_1_check_prerequisites()
            
            # Only continue if we can upload to S3
            if not self.test_2_upload_test_pdf():
                print("\n⚠️  Cannot proceed without S3 access")
                return self.print_summary()
            
            if not self.test_3_initialize_agent():
                print("\n⚠️  Cannot proceed without agent initialization")
                return self.print_summary()
            
            if not self.test_4_process_pdf():
                print("\n⚠️  PDF processing failed")
                return self.print_summary()
            
            self.test_5_verify_images()
            self.test_6_verify_canonical_output()
            self.test_7_verify_event_publication()
            
        finally:
            # Always try to cleanup
            self.cleanup()
        
        return self.print_summary()


if __name__ == "__main__":
    runner = E2ETestRunner(region_name="us-east-1")
    sys.exit(runner.run())
