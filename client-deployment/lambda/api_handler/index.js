/**
 * API Handler Lambda
 * 
 * This Lambda function handles API Gateway requests for the Trade Reconciliation API.
 * It routes requests to the appropriate handlers based on the resource and HTTP method.
 */

const AWS = require('aws-sdk');
const documentHandlers = require('./handlers/documents');
const tradeHandlers = require('./handlers/trades');
const reconciliationHandlers = require('./handlers/reconciliations');
const matchHandlers = require('./handlers/matches');

// Create AWS SDK clients
const dynamoDB = new AWS.DynamoDB.DocumentClient();
const lambda = new AWS.Lambda();
const s3 = new AWS.S3();

/**
 * Main handler for API Gateway requests
 */
exports.handler = async (event) => {
  console.log('Received event:', JSON.stringify(event, null, 2));
  
  try {
    // Extract request details from event
    const { resource, httpMethod, pathParameters, body, queryStringParameters } = event;
    
    // Parse request body if present
    const requestBody = body ? JSON.parse(body) : {};
    
    // Create context object with common dependencies
    const context = {
      dynamoDB,
      lambda,
      s3,
      event,
    };
    
    // Route request to appropriate handler
    const response = await routeRequest(resource, httpMethod, pathParameters, requestBody, queryStringParameters, context);
    
    // Return response
    return formatResponse(200, response);
  } catch (error) {
    console.error('Error processing request:', error);
    
    // Return error response
    return formatResponse(
      error.statusCode || 500,
      {
        error: error.message || 'Internal Server Error',
        details: error.details || error.stack,
      }
    );
  }
};

/**
 * Route request to appropriate handler based on resource and HTTP method
 */
async function routeRequest(resource, httpMethod, pathParameters, requestBody, queryStringParameters, context) {
  // Define routes
  const routes = {
    '/documents': {
      GET: documentHandlers.listDocuments,
      POST: documentHandlers.createDocument,
    },
    '/documents/{documentId}': {
      GET: documentHandlers.getDocument,
      DELETE: documentHandlers.deleteDocument,
    },
    '/documents/{documentId}/trades': {
      GET: tradeHandlers.listDocumentTrades,
    },
    '/trades': {
      GET: tradeHandlers.listTrades,
    },
    '/trades/{tradeId}': {
      GET: tradeHandlers.getTrade,
      PUT: tradeHandlers.updateTrade,
    },
    '/reconciliations': {
      GET: reconciliationHandlers.listReconciliations,
      POST: reconciliationHandlers.createReconciliation,
    },
    '/reconciliations/{reconciliationId}': {
      GET: reconciliationHandlers.getReconciliation,
      DELETE: reconciliationHandlers.deleteReconciliation,
    },
    '/reconciliations/{reconciliationId}/start': {
      POST: reconciliationHandlers.startReconciliation,
    },
    '/reconciliations/{reconciliationId}/matches': {
      GET: matchHandlers.listReconciliationMatches,
    },
    '/matches': {
      GET: matchHandlers.listMatches,
    },
    '/matches/{matchId}': {
      GET: matchHandlers.getMatch,
      PUT: matchHandlers.updateMatch,
    },
  };
  
  // Find handler for route
  const route = routes[resource];
  if (!route) {
    const error = new Error(`Resource not found: ${resource}`);
    error.statusCode = 404;
    throw error;
  }
  
  // Find handler for HTTP method
  const handler = route[httpMethod];
  if (!handler) {
    const error = new Error(`Method not allowed: ${httpMethod}`);
    error.statusCode = 405;
    throw error;
  }
  
  // Call handler with request parameters
  return await handler(pathParameters, requestBody, queryStringParameters, context);
}

/**
 * Format API response with appropriate headers
 */
function formatResponse(statusCode, body) {
  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Credentials': true,
    },
    body: JSON.stringify(body),
  };
}
