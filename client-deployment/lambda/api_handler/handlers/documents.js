/**
 * Document API Handlers
 * 
 * These handlers manage document operations including uploading, listing,
 * and retrieving documents used for trade reconciliation.
 */

const AWS = require('aws-sdk');
const { v4: uuidv4 } = require('uuid');

// Environment variables
const DOCUMENT_TABLE = process.env.DOCUMENT_TABLE;
const SOURCE_TRADE_TABLE = process.env.SOURCE_TRADE_TABLE;
const TARGET_TRADE_TABLE = process.env.TARGET_TRADE_TABLE;
const DOCUMENT_BUCKET = process.env.DOCUMENT_BUCKET;
const DOCUMENT_PROCESSOR_FUNCTION = process.env.DOCUMENT_PROCESSOR_FUNCTION;

// AWS clients
const s3 = new AWS.S3();
const lambda = new AWS.Lambda();

/**
 * List documents with filtering and pagination support
 */
exports.listDocuments = async (pathParams, body, queryParams, context) => {
  const { dynamoDB } = context;
  
  // Extract query parameters for filtering
  const limit = queryParams?.limit ? parseInt(queryParams.limit, 10) : 50;
  const startKey = queryParams?.startKey ? JSON.parse(decodeURIComponent(queryParams.startKey)) : null;
  
  // Build filter expression
  let filterExpressions = [];
  let expressionAttributeValues = {};
  let expressionAttributeNames = {};
  
  // Filter by document type (source or target)
  if (queryParams?.type === 'source') {
    filterExpressions.push('isSource = :isSource');
    expressionAttributeValues[':isSource'] = true;
  } else if (queryParams?.type === 'target') {
    filterExpressions.push('isSource = :isSource');
    expressionAttributeValues[':isSource'] = false;
  }
  
  // Filter by status
  if (queryParams?.status) {
    filterExpressions.push('#status = :status');
    expressionAttributeValues[':status'] = queryParams.status;
    expressionAttributeNames['#status'] = 'status';
  }
  
  // Filter by name
  if (queryParams?.name) {
    filterExpressions.push('contains(#name, :name)');
    expressionAttributeValues[':name'] = queryParams.name;
    expressionAttributeNames['#name'] = 'name';
  }
  
  // Filter by date range (createdAt)
  if (queryParams?.fromDate && queryParams?.toDate) {
    filterExpressions.push('createdAt BETWEEN :fromDate AND :toDate');
    expressionAttributeValues[':fromDate'] = queryParams.fromDate;
    expressionAttributeValues[':toDate'] = queryParams.toDate;
  } else if (queryParams?.fromDate) {
    filterExpressions.push('createdAt >= :fromDate');
    expressionAttributeValues[':fromDate'] = queryParams.fromDate;
  } else if (queryParams?.toDate) {
    filterExpressions.push('createdAt <= :toDate');
    expressionAttributeValues[':toDate'] = queryParams.toDate;
  }
  
  // Combine filter expressions
  const combinedFilterExpression = filterExpressions.length > 0 
    ? filterExpressions.join(' AND ') 
    : undefined;
  
  // Prepare query params
  const params = {
    TableName: DOCUMENT_TABLE,
    Limit: limit,
  };
  
  // Add filter expression if present
  if (combinedFilterExpression) {
    params.FilterExpression = combinedFilterExpression;
    params.ExpressionAttributeValues = expressionAttributeValues;
    
    if (Object.keys(expressionAttributeNames).length > 0) {
      params.ExpressionAttributeNames = expressionAttributeNames;
    }
  }
  
  // Add pagination if start key provided
  if (startKey) {
    params.ExclusiveStartKey = startKey;
  }
  
  // Query DynamoDB
  const result = await dynamoDB.scan(params).promise();
  
  // Format response
  return {
    documents: result.Items,
    pagination: {
      count: result.Items.length,
      lastEvaluatedKey: result.LastEvaluatedKey 
        ? encodeURIComponent(JSON.stringify(result.LastEvaluatedKey))
        : null,
    },
  };
};

/**
 * Get document by ID
 */
exports.getDocument = async (pathParams, body, queryParams, context) => {
  const { dynamoDB } = context;
  const { documentId } = pathParams;
  
  if (!documentId) {
    const error = new Error('Document ID is required');
    error.statusCode = 400;
    throw error;
  }
  
  // Get document from DynamoDB
  const result = await dynamoDB.get({
    TableName: DOCUMENT_TABLE,
    Key: { documentId },
  }).promise();
  
  if (!result.Item) {
    const error = new Error(`Document not found: ${documentId}`);
    error.statusCode = 404;
    throw error;
  }
  
  const document = result.Item;
  
  // If includeTrades=true, get trade counts and statistics
  if (queryParams?.includeTrades === 'true') {
    const tradeTable = document.isSource ? SOURCE_TRADE_TABLE : TARGET_TRADE_TABLE;
    
    // Count trades
    const tradeParams = {
      TableName: tradeTable,
      FilterExpression: 'documentId = :documentId',
      ExpressionAttributeValues: {
        ':documentId': documentId,
      },
    };
    
    try {
      // Get all trades to calculate statistics (could be optimized with a counter table for large documents)
      const tradeResult = await dynamoDB.scan(tradeParams).promise();
      const trades = tradeResult.Items;
      
      // Calculate total number of trades
      document.tradeCount = trades.length;
      
      // Group trades by status
      const tradesByStatus = trades.reduce((acc, trade) => {
        const status = trade.matchStatus || 'unmatched';
        acc[status] = (acc[status] || 0) + 1;
        return acc;
      }, {});
      
      document.tradeStatistics = {
        totalTrades: trades.length,
        matchedTrades: tradesByStatus.matched || 0,
        unmatchedTrades: tradesByStatus.unmatched || 0,
      };
    } catch (error) {
      console.error('Error getting trades:', error);
      document.tradeStatistics = {
        error: 'Failed to retrieve trade statistics',
      };
    }
  }
  
  return document;
};

/**
 * Create a pre-signed URL for document upload
 */
exports.createUploadUrl = async (pathParams, body, queryParams, context) => {
  const { dynamoDB } = context;
  
  // Validate request
  if (!body || !body.fileName || !body.contentType) {
    const error = new Error('File name and content type are required');
    error.statusCode = 400;
    throw error;
  }
  
  const { fileName, contentType, isSource = true, description } = body;
  
  // Generate document ID and key
  const documentId = `doc-${uuidv4()}`;
  const key = `documents/${documentId}/${fileName}`;
  const timestamp = new Date().toISOString();
  
  // Create document entry in DynamoDB
  const document = {
    documentId,
    name: fileName.split('.')[0], // Default name from filename
    originalFilename: fileName,
    description: description || '',
    contentType,
    isSource: isSource === true || isSource === 'true',
    status: 'pending',
    s3Key: key,
    createdAt: timestamp,
    updatedAt: timestamp,
  };
  
  await dynamoDB.put({
    TableName: DOCUMENT_TABLE,
    Item: document,
  }).promise();
  
  // Generate pre-signed URL for upload
  const presignedUrl = s3.getSignedUrl('putObject', {
    Bucket: DOCUMENT_BUCKET,
    Key: key,
    ContentType: contentType,
    Expires: 3600, // URL expires in 1 hour
  });
  
  return {
    documentId,
    presignedUrl,
    document,
  };
};

/**
 * Update document metadata
 */
exports.updateDocument = async (pathParams, body, queryParams, context) => {
  const { dynamoDB } = context;
  const { documentId } = pathParams;
  
  if (!documentId) {
    const error = new Error('Document ID is required');
    error.statusCode = 400;
    throw error;
  }
  
  if (!body) {
    const error = new Error('Update data is required');
    error.statusCode = 400;
    throw error;
  }
  
  // Get document from DynamoDB to make sure it exists
  const result = await dynamoDB.get({
    TableName: DOCUMENT_TABLE,
    Key: { documentId },
  }).promise();
  
  if (!result.Item) {
    const error = new Error(`Document not found: ${documentId}`);
    error.statusCode = 404;
    throw error;
  }
  
  const document = result.Item;
  
  // Prevent updates to certain statuses
  const nonUpdatableStatuses = ['processing', 'deleting'];
  if (nonUpdatableStatuses.includes(document.status)) {
    const error = new Error(`Cannot update document with status: ${document.status}`);
    error.statusCode = 400;
    throw error;
  }
  
  // Fields that can be updated
  const updatableFields = [
    'name',
    'description',
    'metadata',
  ];
  
  // Filter out non-updatable fields
  const updates = Object.entries(body)
    .filter(([key]) => updatableFields.includes(key))
    .reduce((acc, [key, value]) => ({ ...acc, [key]: value }), {});
  
  // Ensure at least one valid field is being updated
  if (Object.keys(updates).length === 0) {
    const error = new Error('No valid fields to update');
    error.statusCode = 400;
    throw error;
  }
  
  // Build update expression
  let updateExpression = 'SET updatedAt = :updatedAt';
  let expressionAttributeValues = {
    ':updatedAt': new Date().toISOString(),
  };
  
  // Add each field to update expression
  Object.entries(updates).forEach(([key, value]) => {
    updateExpression += `, ${key} = :${key}`;
    expressionAttributeValues[`:${key}`] = value;
  });
  
  // Perform the update
  const updateResult = await dynamoDB.update({
    TableName: DOCUMENT_TABLE,
    Key: { documentId },
    UpdateExpression: updateExpression,
    ExpressionAttributeValues: expressionAttributeValues,
    ReturnValues: 'ALL_NEW',
  }).promise();
  
  return updateResult.Attributes;
};

/**
 * Delete document and related trades
 */
exports.deleteDocument = async (pathParams, body, queryParams, context) => {
  const { dynamoDB } = context;
  const { documentId } = pathParams;
  
  if (!documentId) {
    const error = new Error('Document ID is required');
    error.statusCode = 400;
    throw error;
  }
  
  // Get document from DynamoDB to make sure it exists
  const result = await dynamoDB.get({
    TableName: DOCUMENT_TABLE,
    Key: { documentId },
  }).promise();
  
  if (!result.Item) {
    const error = new Error(`Document not found: ${documentId}`);
    error.statusCode = 404;
    throw error;
  }
  
  const document = result.Item;
  
  // Prevent deletion of documents in certain statuses
  const nonDeletableStatuses = ['processing'];
  if (nonDeletableStatuses.includes(document.status)) {
    const error = new Error(`Cannot delete document with status: ${document.status}`);
    error.statusCode = 400;
    throw error;
  }
  
  // Update document status to deleting
  await dynamoDB.update({
    TableName: DOCUMENT_TABLE,
    Key: { documentId },
    UpdateExpression: 'SET #status = :status, updatedAt = :updatedAt',
    ExpressionAttributeNames: {
      '#status': 'status',
    },
    ExpressionAttributeValues: {
      ':status': 'deleting',
      ':updatedAt': new Date().toISOString(),
    },
  }).promise();
  
  // Determine which trade table to use
  const tradeTable = document.isSource ? SOURCE_TRADE_TABLE : TARGET_TRADE_TABLE;
  
  // Get all trades for this document
  const tradeParams = {
    TableName: tradeTable,
    FilterExpression: 'documentId = :documentId',
    ExpressionAttributeValues: {
      ':documentId': documentId,
    },
  };
  
  const tradeResult = await dynamoDB.scan(tradeParams).promise();
  const trades = tradeResult.Items;
  
  // Delete all trades in batches
  const BATCH_SIZE = 25; // DynamoDB batch size limit
  
  for (let i = 0; i < trades.length; i += BATCH_SIZE) {
    const batchTrades = trades.slice(i, i + BATCH_SIZE);
    
    if (batchTrades.length > 0) {
      const deleteRequests = batchTrades.map(trade => ({
        DeleteRequest: {
          Key: { tradeId: trade.tradeId },
        },
      }));
      
      await dynamoDB.batchWrite({
        RequestItems: {
          [tradeTable]: deleteRequests,
        },
      }).promise();
    }
  }
  
  // Delete the S3 object
  if (document.s3Key) {
    await s3.deleteObject({
      Bucket: DOCUMENT_BUCKET,
      Key: document.s3Key,
    }).promise();
  }
  
  // Delete the document
  await dynamoDB.delete({
    TableName: DOCUMENT_TABLE,
    Key: { documentId },
  }).promise();
  
  return {
    documentId,
    message: `Document deleted successfully along with ${trades.length} trades`,
  };
};

/**
 * Process document after upload
 */
exports.processDocument = async (pathParams, body, queryParams, context) => {
  const { dynamoDB } = context;
  const { documentId } = pathParams;
  
  if (!documentId) {
    const error = new Error('Document ID is required');
    error.statusCode = 400;
    throw error;
  }
  
  // Get document from DynamoDB
  const result = await dynamoDB.get({
    TableName: DOCUMENT_TABLE,
    Key: { documentId },
  }).promise();
  
  if (!result.Item) {
    const error = new Error(`Document not found: ${documentId}`);
    error.statusCode = 404;
    throw error;
  }
  
  const document = result.Item;
  
  // Check if document can be processed
  const processableStatuses = ['pending', 'failed'];
  if (!processableStatuses.includes(document.status)) {
    const error = new Error(`Cannot process document with status: ${document.status}`);
    error.statusCode = 400;
    throw error;
  }
  
  // Update document status to processing
  await dynamoDB.update({
    TableName: DOCUMENT_TABLE,
    Key: { documentId },
    UpdateExpression: 'SET #status = :status, updatedAt = :updatedAt',
    ExpressionAttributeNames: {
      '#status': 'status',
    },
    ExpressionAttributeValues: {
      ':status': 'processing',
      ':updatedAt': new Date().toISOString(),
    },
  }).promise();
  
  // Invoke document processor
  try {
    await lambda.invoke({
      FunctionName: DOCUMENT_PROCESSOR_FUNCTION,
      InvocationType: 'Event', // Async invocation
      Payload: JSON.stringify({
        documentId,
        operation: 'process',
      }),
    }).promise();
  } catch (error) {
    console.error('Error invoking document processor:', error);
    
    // Revert status to previous if processing fails to start
    await dynamoDB.update({
      TableName: DOCUMENT_TABLE,
      Key: { documentId },
      UpdateExpression: 'SET #status = :status, updatedAt = :updatedAt, errorDetails = :errorDetails',
      ExpressionAttributeNames: {
        '#status': 'status',
      },
      ExpressionAttributeValues: {
        ':status': 'failed',
        ':updatedAt': new Date().toISOString(),
        ':errorDetails': {
          message: `Failed to start processing: ${error.message}`,
          stack: error.stack,
        },
      },
    }).promise();
    
    throw error;
  }
  
  return {
    documentId,
    status: 'processing',
    message: 'Document processing started',
  };
};

/**
 * Get document download URL
 */
exports.getDownloadUrl = async (pathParams, body, queryParams, context) => {
  const { dynamoDB } = context;
  const { documentId } = pathParams;
  
  if (!documentId) {
    const error = new Error('Document ID is required');
    error.statusCode = 400;
    throw error;
  }
  
  // Get document from DynamoDB
  const result = await dynamoDB.get({
    TableName: DOCUMENT_TABLE,
    Key: { documentId },
  }).promise();
  
  if (!result.Item) {
    const error = new Error(`Document not found: ${documentId}`);
    error.statusCode = 404;
    throw error;
  }
  
  const document = result.Item;
  
  if (!document.s3Key) {
    const error = new Error(`Document ${documentId} has no associated file`);
    error.statusCode = 400;
    throw error;
  }
  
  // Generate pre-signed URL for download
  const presignedUrl = s3.getSignedUrl('getObject', {
    Bucket: DOCUMENT_BUCKET,
    Key: document.s3Key,
    Expires: 3600, // URL expires in 1 hour
  });
  
  return {
    documentId,
    presignedUrl,
    originalFilename: document.originalFilename,
    contentType: document.contentType,
  };
};

/**
 * Get document statistics
 */
exports.getDocumentStatistics = async (pathParams, body, queryParams, context) => {
  const { dynamoDB } = context;
  
  // Get all documents
  const result = await dynamoDB.scan({ TableName: DOCUMENT_TABLE }).promise();
  const documents = result.Items;
  
  // Count documents by type
  const documentsByType = {
    source: documents.filter(doc => doc.isSource).length,
    target: documents.filter(doc => !doc.isSource).length,
  };
  
  // Count documents by status
  const documentsByStatus = documents.reduce((acc, doc) => {
    const status = doc.status || 'unknown';
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {});
  
  // Get recently updated documents
  const recentDocuments = [...documents]
    .sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt))
    .slice(0, 5)
    .map(doc => ({
      documentId: doc.documentId,
      name: doc.name,
      originalFilename: doc.originalFilename,
      isSource: doc.isSource,
      status: doc.status,
      updatedAt: doc.updatedAt,
    }));
  
  return {
    totalDocuments: documents.length,
    documentsByType,
    documentsByStatus,
    recentDocuments,
  };
};

/**
 * Get document trades (paginated)
 */
exports.getDocumentTrades = async (pathParams, body, queryParams, context) => {
  const { dynamoDB } = context;
  const { documentId } = pathParams;
  
  if (!documentId) {
    const error = new Error('Document ID is required');
    error.statusCode = 400;
    throw error;
  }
  
  // Get document from DynamoDB
  const docResult = await dynamoDB.get({
    TableName: DOCUMENT_TABLE,
    Key: { documentId },
  }).promise();
  
  if (!docResult.Item) {
    const error = new Error(`Document not found: ${documentId}`);
    error.statusCode = 404;
    throw error;
  }
  
  const document = docResult.Item;
  
  // Determine which trade table to use
  const tradeTable = document.isSource ? SOURCE_TRADE_TABLE : TARGET_TRADE_TABLE;
  
  // Extract query parameters for filtering
  const limit = queryParams?.limit ? parseInt(queryParams.limit, 10) : 50;
  const startKey = queryParams?.startKey ? JSON.parse(decodeURIComponent(queryParams.startKey)) : null;
  
  // Build filter expression
  let filterExpressions = ['documentId = :documentId'];
  let expressionAttributeValues = { ':documentId': documentId };
  
  // Filter by match status
  if (queryParams?.matchStatus) {
    filterExpressions.push('matchStatus = :matchStatus');
    expressionAttributeValues[':matchStatus'] = queryParams.matchStatus;
  }
  
  // Combine filter expressions
  const filterExpression = filterExpressions.join(' AND ');
  
  // Prepare query params
  const params = {
    TableName: tradeTable,
    FilterExpression: filterExpression,
    ExpressionAttributeValues: expressionAttributeValues,
    Limit: limit,
  };
  
  // Add pagination if start key provided
  if (startKey) {
    params.ExclusiveStartKey = startKey;
  }
  
  // Query DynamoDB
  const result = await dynamoDB.scan(params).promise();
  
  // Format response
  return {
    documentId,
    isSource: document.isSource,
    trades: result.Items,
    pagination: {
      count: result.Items.length,
      lastEvaluatedKey: result.LastEvaluatedKey 
        ? encodeURIComponent(JSON.stringify(result.LastEvaluatedKey))
        : null,
    },
  };
};
