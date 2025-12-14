# Trade Reconciliation System - API Documentation

This document provides detailed information about the Trade Reconciliation API endpoints, request/response formats, and usage examples.

## API Base URL

The base URL for the API is:

```
https://[API_ID].execute-api.[REGION].amazonaws.com/v1
```

Replace `[API_ID]` and `[REGION]` with your specific API Gateway ID and AWS region.

## Authentication

Currently, the API does not require authentication. Future versions may implement authentication mechanisms such as API keys, IAM, or Cognito.

## Endpoints

### Root Endpoint

**GET /**

Returns basic information about the API.

**Example Request:**
```bash
curl -X GET https://[API_ID].execute-api.[REGION].amazonaws.com/v1
```

**Example Response:**
```json
{
  "message": "Welcome to Trade Reconciliation API",
  "version": "1.0.0",
  "timestamp": "2025-07-19T17:38:35.296Z",
  "environment": "AWS_Lambda_nodejs18.x"
}
```

### Health Check

**GET /health**

Returns the health status of the API.

**Example Request:**
```bash
curl -X GET https://[API_ID].execute-api.[REGION].amazonaws.com/v1/health
```

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-19T17:40:12.123Z"
}
```

### Trades

**GET /trades**

Returns a list of trades.

**Example Request:**
```bash
curl -X GET https://[API_ID].execute-api.[REGION].amazonaws.com/v1/trades
```

**Example Response:**
```json
{
  "message": "Trades endpoint",
  "method": "GET",
  "mockData": [
    {
      "tradeId": "T001",
      "amount": 10000,
      "currency": "USD",
      "status": "MATCHED"
    },
    {
      "tradeId": "T002",
      "amount": 15000,
      "currency": "EUR",
      "status": "UNMATCHED"
    }
  ]
}
```

## Error Handling

The API returns standard HTTP status codes to indicate the success or failure of a request:

- **200 OK**: The request was successful
- **400 Bad Request**: The request was invalid or cannot be served
- **401 Unauthorized**: Authentication is required and has failed or has not been provided
- **403 Forbidden**: The request is understood but refused due to permissions
- **404 Not Found**: The requested resource does not exist
- **500 Internal Server Error**: An error occurred on the server

Error responses follow this format:

```json
{
  "error": "Error message describing what went wrong"
}
```

## CORS Support

The API supports Cross-Origin Resource Sharing (CORS) and allows requests from any origin. The following headers are included in responses:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS
Access-Control-Allow-Headers: Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token
```

## Rate Limiting

Currently, there are no specific rate limits applied to the API. However, AWS services have their own service quotas that may apply.

## Future Endpoints

The following endpoints are planned for future releases:

### Reconciliation

**POST /reconciliations**

Initiates a new reconciliation process.

**GET /reconciliations/{id}**

Retrieves the status and results of a specific reconciliation.

### Documents

**GET /documents**

Lists all documents available for reconciliation.

**POST /documents/upload**

Uploads a new document for processing.

## API Integration

### Frontend Integration

To integrate with the frontend application, update the API endpoint configuration in your frontend code:

```javascript
// Example for React application
// src/config.js
export const API_ENDPOINT = 'https://[API_ID].execute-api.[REGION].amazonaws.com/v1';
```

### Postman Collection

A Postman collection for testing the API is available in the `postman` directory of this repository.

## Troubleshooting

If you encounter issues with the API, check the following:

1. Verify that the API endpoint URL is correct
2. Check that the API Gateway deployment was successful
3. Review CloudWatch Logs for the Lambda function
4. Ensure that CORS is properly configured if accessing from a browser

For more detailed troubleshooting, refer to the Troubleshooting Guide.