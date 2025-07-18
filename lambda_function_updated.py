import json
import boto3
import os
import uuid
from decimal import Decimal
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr

# Initialize DynamoDB resources
dynamodb = boto3.resource('dynamodb')
bank_table = dynamodb.Table(os.environ.get('BANK_TABLE', 'BankTradeData'))
counterparty_table = dynamodb.Table(os.environ.get('COUNTERPARTY_TABLE', 'CounterpartyTradeData'))
matches_table = dynamodb.Table(os.environ.get('MATCHES_TABLE', 'TradeMatches'))

# Initialize S3 client
s3 = boto3.client('s3')
bucket_name = os.environ.get('BUCKET_NAME', 'fab-otc-reconciliation-deployment')

# Helper for DynamoDB JSON serialization
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    """
    Main handler for API Gateway requests
    """
    print(f"Event received: {json.dumps(event)}")
    
    # Extract request details
    http_method = event.get('httpMethod', '')
    resource = event.get('resource', '')
    path_parameters = event.get('pathParameters', {}) or {}
    query_parameters = event.get('queryStringParameters', {}) or {}
    body = event.get('body')
    
    # Handle OPTIONS requests for CORS
    if http_method == 'OPTIONS':
        return response(200, {})
    
    if body:
        try:
            body = json.loads(body)
        except:
            return response(400, {"message": "Invalid request body"})
    
    # Route the request based on path and method
    try:
        if resource == '/dashboard' and http_method == 'GET':
            return get_dashboard_data()
        
        elif resource == '/documents' and http_method == 'POST':
            return create_upload_url(body)
        
        elif resource == '/trades' and http_method == 'GET':
            return get_trades(query_parameters)
        
        elif resource == '/trades/{tradeId}' and http_method == 'GET':
            return get_trade(path_parameters.get('tradeId'))
        
        elif resource == '/matches' and http_method == 'GET':
            return get_matches(query_parameters)
        
        elif resource == '/matches/{matchId}' and http_method == 'GET':
            return get_match(path_parameters.get('matchId'))
        
        elif resource == '/matches/{matchId}/status' and http_method == 'PUT':
            return update_match_status(path_parameters.get('matchId'), body)
        
        elif resource == '/reconciliation/{matchId}' and http_method == 'GET':
            return get_reconciliation_details(path_parameters.get('matchId'))
        
        elif resource == '/reports' and http_method == 'GET':
            return get_reports(query_parameters)
        
        elif resource == '/reports/{reportId}' and http_method == 'GET':
            return get_report(path_parameters.get('reportId'))
        
        elif resource == '/reports' and http_method == 'POST':
            return generate_report(body)
        
        elif resource == '/settings' and http_method == 'GET':
            return get_settings()
        
        elif resource == '/settings' and http_method == 'PUT':
            return update_settings(body)
        
        else:
            return response(404, {"message": "Not Found"})
    
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return response(500, {"message": f"Internal Server Error: {str(e)}"})

def get_dashboard_data():
    """Get dashboard summary data"""
    try:
        # Query bank trades
        bank_matched = 0
        bank_unmatched = 0
        
        bank_response = bank_table.scan(
            FilterExpression=Attr('matched_status').exists()
        )
        
        for item in bank_response.get('Items', []):
            if item.get('matched_status') == 'MATCHED':
                bank_matched += 1
            elif item.get('matched_status') == 'UNMATCHED' or item.get('matched_status') == 'PENDING':
                bank_unmatched += 1
        
        # Query counterparty trades
        cpty_matched = 0
        cpty_unmatched = 0
        
        cpty_response = counterparty_table.scan(
            FilterExpression=Attr('matched_status').exists()
        )
        
        for item in cpty_response.get('Items', []):
            if item.get('matched_status') == 'MATCHED':
                cpty_matched += 1
            elif item.get('matched_status') == 'UNMATCHED' or item.get('matched_status') == 'PENDING':
                cpty_unmatched += 1
        
        # Query matches
        partially_matched = 0
        
        matches_response = matches_table.scan(
            FilterExpression=Attr('reconciliation_status').eq('PARTIALLY_MATCHED')
        )
        
        partially_matched = len(matches_response.get('Items', []))
        
        # Calculate totals
        matched = bank_matched  # We count only bank trades to avoid double counting
        unmatched = bank_unmatched + cpty_unmatched
        total = matched + partially_matched + unmatched
        
        return response(200, {
            "summary": {
                "matched": matched,
                "partiallyMatched": partially_matched,
                "unmatched": unmatched,
                "total": total
            },
            "timeSeriesData": [
                {"date": "2025-07-10", "processed": 25},
                {"date": "2025-07-11", "processed": 32},
                {"date": "2025-07-12", "processed": 18},
                {"date": "2025-07-13", "processed": 29},
                {"date": "2025-07-14", "processed": 15},
                {"date": "2025-07-15", "processed": 26},
                {"date": "2025-07-16", "processed": 35},
                {"date": "2025-07-17", "processed": 42},
                {"date": "2025-07-18", "processed": 38}
            ]
        })
    except Exception as e:
        print(f"Error getting dashboard data: {str(e)}")
        return response(500, {"message": f"Error getting dashboard data: {str(e)}"})

def create_upload_url(body):
    """Generate pre-signed URL for document upload"""
    print(f"Creating upload URL with body: {json.dumps(body)}")
    
    if not body or 'fileName' not in body or 'source' not in body:
        return response(400, {"message": "Missing required parameters: fileName and source"})
    
    file_name = body['fileName']
    source = body['source']
    trade_date_range = body.get('tradeDateRange', 'unspecified')
    
    if source not in ['BANK', 'COUNTERPARTY']:
        return response(400, {"message": "Source must be either BANK or COUNTERPARTY"})
    
    # Generate a unique key for the file
    key = f"{source}/{str(uuid.uuid4())}-{file_name}"
    
    # Generate a pre-signed URL for uploading
    try:
        # Verify S3 permissions by checking if the bucket exists
        try:
            s3.head_bucket(Bucket=bucket_name)
        except Exception as bucket_error:
            print(f"Error accessing S3 bucket: {str(bucket_error)}")
            return response(500, {"message": f"Error accessing S3 bucket: {str(bucket_error)}"})
        
        # Generate the pre-signed URL
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name,
                'Key': key,
                'ContentType': 'application/pdf'
            },
            ExpiresIn=3600  # URL expires in 1 hour
        )
        
        print(f"Generated pre-signed URL for {key}: {presigned_url[:100]}...")
        
        return response(200, {
            "uploadUrl": presigned_url,
            "key": key,
            "source": source,
            "tradeDateRange": trade_date_range
        })
    except Exception as e:
        print(f"Error generating presigned URL: {str(e)}")
        return response(500, {"message": f"Failed to generate upload URL: {str(e)}"})

def get_trades(query_params):
    """Get trades with optional filtering"""
    # Extract filter parameters
    source = query_params.get('source')
    status = query_params.get('status')
    
    trades = []
    
    try:
        if source == 'BANK' or not source:
            # Query bank trades
            filter_expression = None
            expression_values = {}
            
            if status:
                filter_expression = Attr('matched_status').eq(status)
            
            scan_kwargs = {}
            if filter_expression:
                scan_kwargs['FilterExpression'] = filter_expression
            
            bank_response = bank_table.scan(**scan_kwargs)
            trades.extend(bank_response.get('Items', []))
            
            # Handle pagination if LastEvaluatedKey is present
            while 'LastEvaluatedKey' in bank_response:
                scan_kwargs['ExclusiveStartKey'] = bank_response['LastEvaluatedKey']
                bank_response = bank_table.scan(**scan_kwargs)
                trades.extend(bank_response.get('Items', []))
        
        if source == 'COUNTERPARTY' or not source:
            # Query counterparty trades
            filter_expression = None
            expression_values = {}
            
            if status:
                filter_expression = Attr('matched_status').eq(status)
            
            scan_kwargs = {}
            if filter_expression:
                scan_kwargs['FilterExpression'] = filter_expression
            
            cpty_response = counterparty_table.scan(**scan_kwargs)
            trades.extend(cpty_response.get('Items', []))
            
            # Handle pagination if LastEvaluatedKey is present
            while 'LastEvaluatedKey' in cpty_response:
                scan_kwargs['ExclusiveStartKey'] = cpty_response['LastEvaluatedKey']
                cpty_response = counterparty_table.scan(**scan_kwargs)
                trades.extend(cpty_response.get('Items', []))
        
        # Convert Decimal to float for JSON serialization
        trades_json = json.loads(json.dumps(trades, cls=DecimalEncoder))
        
        return response(200, {"trades": trades_json})
    except Exception as e:
        print(f"Error getting trades: {str(e)}")
        return response(500, {"message": f"Error getting trades: {str(e)}"})

def get_trade(trade_id):
    """Get a specific trade by ID"""
    if not trade_id:
        return response(400, {"message": "Trade ID is required"})
    
    # Try to find the trade in both tables
    try:
        # Check bank table first
        bank_response = bank_table.get_item(Key={"trade_id": trade_id})
        if 'Item' in bank_response:
            trade_json = json.loads(json.dumps(bank_response['Item'], cls=DecimalEncoder))
            return response(200, {"trade": trade_json, "source": "BANK"})
        
        # Check counterparty table
        cpty_response = counterparty_table.get_item(Key={"trade_id": trade_id})
        if 'Item' in cpty_response:
            trade_json = json.loads(json.dumps(cpty_response['Item'], cls=DecimalEncoder))
            return response(200, {"trade": trade_json, "source": "COUNTERPARTY"})
        
        # Trade not found
        return response(404, {"message": f"Trade with ID {trade_id} not found"})
    except Exception as e:
        print(f"Error retrieving trade {trade_id}: {str(e)}")
        return response(500, {"message": f"Error retrieving trade: {str(e)}"})

def get_matches(query_params):
    """Get matches with optional filtering"""
    status = query_params.get('status')
    
    try:
        filter_expression = None
        
        if status:
            filter_expression = Attr('reconciliation_status').eq(status)
        
        scan_kwargs = {}
        if filter_expression:
            scan_kwargs['FilterExpression'] = filter_expression
        
        matches_response = matches_table.scan(**scan_kwargs)
        matches = matches_response.get('Items', [])
        
        # Handle pagination if LastEvaluatedKey is present
        while 'LastEvaluatedKey' in matches_response:
            scan_kwargs['ExclusiveStartKey'] = matches_response['LastEvaluatedKey']
            matches_response = matches_table.scan(**scan_kwargs)
            matches.extend(matches_response.get('Items', []))
        
        # Convert Decimal to float for JSON serialization
        matches_json = json.loads(json.dumps(matches, cls=DecimalEncoder))
        
        return response(200, {"matches": matches_json})
    except Exception as e:
        print(f"Error retrieving matches: {str(e)}")
        return response(500, {"message": f"Error retrieving matches: {str(e)}"})

def get_match(match_id):
    """Get a specific match by ID"""
    if not match_id:
        return response(400, {"message": "Match ID is required"})
    
    try:
        match_response = matches_table.get_item(Key={"match_id": match_id})
        
        if 'Item' not in match_response:
            return response(404, {"message": f"Match with ID {match_id} not found"})
        
        match = match_response['Item']
        
        # Get the associated trades
        bank_trade = None
        counterparty_trade = None
        
        if 'bank_trade_id' in match:
            bank_response = bank_table.get_item(Key={"trade_id": match['bank_trade_id']})
            if 'Item' in bank_response:
                bank_trade = bank_response['Item']
        
        if 'counterparty_trade_id' in match:
            cpty_response = counterparty_table.get_item(Key={"trade_id": match['counterparty_trade_id']})
            if 'Item' in cpty_response:
                counterparty_trade = cpty_response['Item']
        
        # Convert Decimal to float for JSON serialization
        result = {
            "match": match,
            "bankTrade": bank_trade,
            "counterpartyTrade": counterparty_trade
        }
        result_json = json.loads(json.dumps(result, cls=DecimalEncoder))
        
        return response(200, result_json)
    except Exception as e:
        print(f"Error retrieving match {match_id}: {str(e)}")
        return response(500, {"message": f"Error retrieving match: {str(e)}"})

def update_match_status(match_id, body):
    """Update the status of a match"""
    if not match_id:
        return response(400, {"message": "Match ID is required"})
    
    if not body or 'status' not in body:
        return response(400, {"message": "Status is required in request body"})
    
    status = body['status']
    
    try:
        # Update the match status
        update_response = matches_table.update_item(
            Key={"match_id": match_id},
            UpdateExpression="SET reconciliation_status = :status, last_updated = :timestamp",
            ExpressionAttributeValues={
                ":status": status,
                ":timestamp": datetime.now().isoformat()
            },
            ReturnValues="ALL_NEW"
        )
        
        if 'Attributes' not in update_response:
            return response(404, {"message": f"Match with ID {match_id} not found"})
        
        # Convert Decimal to float for JSON serialization
        result_json = json.loads(json.dumps(update_response['Attributes'], cls=DecimalEncoder))
        
        return response(200, {"match": result_json})
    except Exception as e:
        print(f"Error updating match {match_id}: {str(e)}")
        return response(500, {"message": f"Error updating match: {str(e)}"})

def get_reconciliation_details(match_id):
    """Get reconciliation details for a match"""
    if not match_id:
        return response(400, {"message": "Match ID is required"})
    
    try:
        # Get the match
        match_response = matches_table.get_item(Key={"match_id": match_id})
        
        if 'Item' not in match_response:
            return response(404, {"message": f"Match with ID {match_id} not found"})
        
        match = match_response['Item']
        
        # Get the associated trades
        bank_trade = None
        counterparty_trade = None
        
        if 'bank_trade_id' in match:
            bank_response = bank_table.get_item(Key={"trade_id": match['bank_trade_id']})
            if 'Item' in bank_response:
                bank_trade = bank_response['Item']
        
        if 'counterparty_trade_id' in match:
            cpty_response = counterparty_table.get_item(Key={"trade_id": match['counterparty_trade_id']})
            if 'Item' in cpty_response:
                counterparty_trade = cpty_response['Item']
        
        # Get field-level comparison results
        field_results = match.get('field_results', {})
        
        # Convert Decimal to float for JSON serialization
        result = {
            "match": match,
            "bankTrade": bank_trade,
            "counterpartyTrade": counterparty_trade,
            "fieldResults": field_results
        }
        result_json = json.loads(json.dumps(result, cls=DecimalEncoder))
        
        return response(200, result_json)
    except Exception as e:
        print(f"Error retrieving reconciliation details for match {match_id}: {str(e)}")
        return response(500, {"message": f"Error retrieving reconciliation details: {str(e)}"})

def get_reports(query_params):
    """Get list of reports"""
    # Mock data for now
    reports = [
        {
            "report_id": "recon-report-20250718-090000",
            "timestamp": "2025-07-18T09:00:00Z",
            "summary": {
                "total_matches": 145,
                "fully_matched": 120,
                "partially_matched": 18,
                "critical_mismatch": 7
            }
        },
        {
            "report_id": "recon-report-20250717-090000",
            "timestamp": "2025-07-17T09:00:00Z",
            "summary": {
                "total_matches": 132,
                "fully_matched": 110,
                "partially_matched": 15,
                "critical_mismatch": 7
            }
        }
    ]
    
    return response(200, {"reports": reports})

def get_report(report_id):
    """Get a specific report"""
    if not report_id:
        return response(400, {"message": "Report ID is required"})
    
    # Mock data for now
    report = {
        "report_id": report_id,
        "timestamp": "2025-07-18T09:00:00Z",
        "summary": {
            "total_matches": 145,
            "fully_matched": 120,
            "partially_matched": 18,
            "critical_mismatch": 7,
            "match_confidence_avg": 0.92
        },
        "detailed_results": [
            {
                "trade_pair_id": "match-001",
                "bank_trade_id": "BT-12345",
                "counterparty_trade_id": "CT-67890",
                "match_confidence": 0.95,
                "overall_status": "FULLY_MATCHED",
                "last_updated": "2025-07-18T08:30:00Z"
            },
            {
                "trade_pair_id": "match-002",
                "bank_trade_id": "BT-12346",
                "counterparty_trade_id": "CT-67891",
                "match_confidence": 0.85,
                "overall_status": "PARTIALLY_MATCHED",
                "last_updated": "2025-07-18T08:35:00Z",
                "field_results": {
                    "notional": {
                        "field_name": "notional",
                        "bank_value": 10000000,
                        "counterparty_value": 9995000,
                        "status": "MISMATCHED",
                        "reason": "Difference of 0.05% exceeds tolerance of 0.001%"
                    }
                }
            }
        ]
    }
    
    return response(200, {"report": report})

def generate_report(body):
    """Generate a new report"""
    # Mock data for now
    report_id = f"recon-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    return response(200, {
        "report_id": report_id,
        "status": "GENERATED",
        "message": "Report generated successfully"
    })

def get_settings():
    """Get system settings"""
    # Mock data for now
    settings = {
        "thresholds": {
            "matchScoreThreshold": 0.9,
            "notionalTolerance": 0.01
        },
        "criticalFields": [
            "trade_date",
            "currency",
            "total_notional_quantity"
        ]
    }
    
    return response(200, {"settings": settings})

def update_settings(body):
    """Update system settings"""
    if not body:
        return response(400, {"message": "Settings are required in request body"})
    
    # Mock update for now
    return response(200, {
        "settings": body,
        "message": "Settings updated successfully"
    })

def response(status_code, body):
    """Helper function to create API Gateway response"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            "Access-Control-Allow-Credentials": "true"
        },
        "body": json.dumps(body)
    }