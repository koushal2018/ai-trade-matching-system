"""
Lambda function to process S3 events and trigger EKS processing.
Handles S3 PUT events and forwards them to the EKS API.
"""

import json
import boto3
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import urllib3
from urllib.parse import unquote_plus
import re

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
http = urllib3.PoolManager()
ssm = boto3.client('ssm')

# Cache for EKS API endpoint
_eks_api_endpoint = None


def get_eks_api_endpoint() -> str:
    """
    Get EKS API endpoint from SSM Parameter Store.
    Caches the result for subsequent invocations.
    """
    global _eks_api_endpoint

    if _eks_api_endpoint:
        return _eks_api_endpoint

    try:
        parameter_name = os.environ.get('EKS_API_ENDPOINT_PARAM', '/trade-matching/eks-api-endpoint')
        response = ssm.get_parameter(Name=parameter_name)
        _eks_api_endpoint = response['Parameter']['Value']
        logger.info(f"Retrieved EKS API endpoint: {_eks_api_endpoint}")
        return _eks_api_endpoint
    except Exception as e:
        logger.error(f"Failed to get EKS API endpoint: {str(e)}")
        raise


def extract_source_type(s3_key: str) -> Optional[str]:
    """
    Extract source type (BANK or COUNTERPARTY) from S3 key.

    Args:
        s3_key: The S3 object key

    Returns:
        'BANK', 'COUNTERPARTY', or None if not found
    """
    # Pattern to match BANK or COUNTERPARTY in the path
    if '/BANK/' in s3_key.upper():
        return 'BANK'
    elif '/COUNTERPARTY/' in s3_key.upper():
        return 'COUNTERPARTY'

    # Alternative pattern matching
    pattern = r'/(BANK|COUNTERPARTY)/'
    match = re.search(pattern, s3_key, re.IGNORECASE)
    if match:
        return match.group(1).upper()

    return None


def extract_unique_identifier(s3_key: str) -> str:
    """
    Extract unique identifier from S3 key.

    Args:
        s3_key: The S3 object key

    Returns:
        Unique identifier extracted from filename
    """
    # Get filename without extension
    filename = os.path.basename(s3_key)
    name_without_ext = os.path.splitext(filename)[0]

    # Common patterns for trade IDs
    # Pattern 1: GCS382857_V1 -> GCS382857
    if '_V' in name_without_ext:
        return name_without_ext.split('_V')[0]

    # Pattern 2: trade_12345_20240101 -> 12345
    if name_without_ext.startswith('trade_'):
        parts = name_without_ext.split('_')
        if len(parts) >= 2:
            return parts[1]

    # Default: use the whole name without extension
    return name_without_ext


def validate_s3_event(event: Dict[str, Any]) -> bool:
    """
    Validate that the event is a valid S3 PUT event.

    Args:
        event: Lambda event object

    Returns:
        True if valid, False otherwise
    """
    try:
        # Check for S3 records
        if 'Records' not in event:
            return False

        for record in event['Records']:
            # Check event source and type
            if record.get('eventSource') != 'aws:s3':
                return False

            event_name = record.get('eventName', '')
            if not event_name.startswith('ObjectCreated:'):
                return False

            # Check for required S3 structure
            if 's3' not in record or 'bucket' not in record['s3'] or 'object' not in record['s3']:
                return False

        return True
    except Exception as e:
        logger.error(f"Event validation error: {str(e)}")
        return False


def process_s3_event(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single S3 event record.

    Args:
        record: S3 event record

    Returns:
        Processing request for EKS API
    """
    try:
        # Extract S3 details
        s3_bucket = record['s3']['bucket']['name']
        s3_key = unquote_plus(record['s3']['object']['key'])
        object_size = record['s3']['object'].get('size', 0)
        event_time = record['eventTime']

        logger.info(f"Processing S3 event: bucket={s3_bucket}, key={s3_key}, size={object_size}")

        # Skip non-PDF files
        if not s3_key.lower().endswith('.pdf'):
            logger.info(f"Skipping non-PDF file: {s3_key}")
            return None

        # Skip if file is too large (>100MB)
        max_size = int(os.environ.get('MAX_FILE_SIZE', '104857600'))  # 100MB default
        if object_size > max_size:
            logger.warning(f"File too large ({object_size} bytes): {s3_key}")
            return None

        # Extract source type
        source_type = extract_source_type(s3_key)
        if not source_type:
            logger.error(f"Could not determine source type for: {s3_key}")
            # Try to infer from bucket name or prefix
            if 'bank' in s3_bucket.lower() or 'bank' in s3_key.lower():
                source_type = 'BANK'
            elif 'counterparty' in s3_bucket.lower() or 'counterparty' in s3_key.lower():
                source_type = 'COUNTERPARTY'
            else:
                return None

        # Extract unique identifier
        unique_identifier = extract_unique_identifier(s3_key)

        # Build processing request
        processing_request = {
            's3_bucket': s3_bucket,
            's3_key': s3_key,
            'source_type': source_type,
            'event_time': event_time,
            'unique_identifier': unique_identifier,
            'metadata': {
                'object_size': object_size,
                'lambda_request_id': logger.handlers[0].formatter.context.get('aws_request_id', 'unknown'),
                'processing_timestamp': datetime.utcnow().isoformat()
            }
        }

        logger.info(f"Built processing request: {json.dumps(processing_request)}")
        return processing_request

    except Exception as e:
        logger.error(f"Failed to process S3 event record: {str(e)}", exc_info=True)
        return None


def call_eks_api(processing_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call EKS API to process the document.

    Args:
        processing_request: Processing request payload

    Returns:
        API response
    """
    try:
        eks_endpoint = get_eks_api_endpoint()
        url = f"{eks_endpoint}/process"

        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'X-Lambda-Request-Id': processing_request['metadata'].get('lambda_request_id', 'unknown')
        }

        # Make HTTP request
        logger.info(f"Calling EKS API: {url}")
        response = http.request(
            'POST',
            url,
            body=json.dumps(processing_request),
            headers=headers,
            timeout=30.0
        )

        # Parse response
        response_data = json.loads(response.data.decode('utf-8'))

        if response.status == 200:
            logger.info(f"EKS API call successful: {response_data}")
            return {
                'success': True,
                'processing_id': response_data.get('processing_id'),
                'message': response_data.get('message')
            }
        else:
            logger.error(f"EKS API error: status={response.status}, body={response_data}")
            return {
                'success': False,
                'error': f"EKS API returned status {response.status}",
                'details': response_data
            }

    except Exception as e:
        logger.error(f"Failed to call EKS API: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def send_to_dlq(event: Dict[str, Any], error: str):
    """
    Send failed event to Dead Letter Queue.

    Args:
        event: Original event that failed
        error: Error message
    """
    try:
        dlq_name = os.environ.get('DLQ_NAME')
        if not dlq_name:
            logger.warning("DLQ_NAME not configured, skipping DLQ")
            return

        sqs = boto3.client('sqs')
        queue_url = sqs.get_queue_url(QueueName=dlq_name)['QueueUrl']

        message = {
            'original_event': event,
            'error': error,
            'timestamp': datetime.utcnow().isoformat(),
            'lambda_request_id': logger.handlers[0].formatter.context.get('aws_request_id', 'unknown')
        }

        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )

        logger.info(f"Sent failed event to DLQ: {dlq_name}")

    except Exception as e:
        logger.error(f"Failed to send to DLQ: {str(e)}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler function.

    Args:
        event: S3 event from EventBridge or S3 notifications
        context: Lambda context object

    Returns:
        Processing result
    """
    logger.info(f"Lambda invoked with event: {json.dumps(event)}")

    # Validate event
    if not validate_s3_event(event):
        error_msg = "Invalid S3 event format"
        logger.error(error_msg)
        send_to_dlq(event, error_msg)
        return {
            'statusCode': 400,
            'body': json.dumps({'error': error_msg})
        }

    results = []
    failures = []

    # Process each S3 record
    for record in event['Records']:
        try:
            # Process the S3 event
            processing_request = process_s3_event(record)

            if not processing_request:
                logger.info("Skipping record (non-PDF or invalid)")
                continue

            # Call EKS API
            api_result = call_eks_api(processing_request)

            if api_result['success']:
                results.append({
                    's3_key': processing_request['s3_key'],
                    'processing_id': api_result.get('processing_id'),
                    'status': 'initiated'
                })
            else:
                failures.append({
                    's3_key': processing_request['s3_key'],
                    'error': api_result.get('error')
                })
                # Send to DLQ if API call failed
                send_to_dlq(record, api_result.get('error'))

        except Exception as e:
            error_msg = f"Failed to process record: {str(e)}"
            logger.error(error_msg, exc_info=True)
            failures.append({
                'record': str(record),
                'error': error_msg
            })
            send_to_dlq(record, error_msg)

    # Build response
    response = {
        'processed': len(results),
        'failed': len(failures),
        'results': results
    }

    if failures:
        response['failures'] = failures
        logger.warning(f"Processing completed with {len(failures)} failures")
    else:
        logger.info(f"Successfully processed {len(results)} documents")

    return {
        'statusCode': 200 if not failures else 207,  # 207 Multi-Status
        'body': json.dumps(response)
    }


# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "eventName": "ObjectCreated:Put",
                "eventTime": "2024-01-01T00:00:00.000Z",
                "s3": {
                    "bucket": {
                        "name": "trade-documents-production"
                    },
                    "object": {
                        "key": "BANK/GCS382857_V1.pdf",
                        "size": 1024000
                    }
                }
            }
        ]
    }

    # Mock context
    class MockContext:
        aws_request_id = "test-request-id"
        function_name = "s3-event-processor"

    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))