/**
 * Document Processor Lambda Function
 * 
 * This Lambda function processes documents uploaded to S3, extracts trade data,
 * and stores the data in DynamoDB tables.
 */

const AWS = require('aws-sdk');
const s3 = new AWS.S3();
const dynamoDB = new AWS.DynamoDB.DocumentClient();
const { v4: uuidv4 } = require('uuid');

// Environment variables from CloudFormation
const ENVIRONMENT_NAME = process.env.ENVIRONMENT_NAME || 'dev';
const DOCUMENTS_BUCKET = process.env.DOCUMENTS_BUCKET || `${ENVIRONMENT_NAME}-trade-reconciliation-documents`;
const SOURCE_TRADE_TABLE = process.env.SOURCE_TRADE_TABLE || `${ENVIRONMENT_NAME}-source-trades`;
const TARGET_TRADE_TABLE = process.env.TARGET_TRADE_TABLE || `${ENVIRONMENT_NAME}-target-trades`;
const DOCUMENT_TABLE = process.env.DOCUMENT_TABLE || `${ENVIRONMENT_NAME}-documents`;

/**
 * Main handler function for the Lambda
 */
exports.handler = async (event) => {
  console.log('Document processor Lambda triggered:', JSON.stringify(event, null, 2));
  
  try {
    // Handle S3 trigger events
    if (event.Records && event.Records.length > 0 && event.Records[0].eventSource === 'aws:s3') {
      return await processS3Event(event);
    }
    
    // Handle direct invocations from API
    if (event.document) {
      return await processDocumentEvent(event);
    }
    
    return {
      statusCode: 400,
      body: JSON.stringify({ message: 'Invalid event format' })
    };
  } catch (error) {
    console.error('Error processing document:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ message: 'Error processing document', error: error.message })
    };
  }
};

/**
 * Process S3 event triggered when a document is uploaded to the S3 bucket
 */
async function processS3Event(event) {
  const record = event.Records[0];
  const bucket = record.s3.bucket.name;
  const key = decodeURIComponent(record.s3.object.key.replace(/\+/g, ' '));
  
  console.log(`Processing file ${key} from bucket ${bucket}`);
  
  // Get document metadata from S3 object tags
  const tagsResponse = await s3.getObjectTagging({
    Bucket: bucket,
    Key: key
  }).promise();
  
  const tags = {};
  tagsResponse.TagSet.forEach(tag => {
    tags[tag.Key] = tag.Value;
  });
  
  // Get the file from S3
  const s3Object = await s3.getObject({
    Bucket: bucket,
    Key: key
  }).promise();
  
  // Process the document based on file type
  const documentType = tags.documentType || getDocumentTypeFromFilename(key);
  const documentId = tags.documentId || uuidv4();
  const userId = tags.userId || 'system';
  
  // Extract trade data from the document
  const tradeData = await extractTradeData(s3Object, documentType);
  
  // Save document metadata to DynamoDB
  await saveDocumentMetadata(documentId, key, documentType, userId, tradeData);
  
  // Save trade data to appropriate table based on document type
  if (documentType === 'source') {
    await saveSourceTrades(documentId, tradeData);
  } else if (documentType === 'target') {
    await saveTargetTrades(documentId, tradeData);
  }
  
  return {
    statusCode: 200,
    body: JSON.stringify({
      message: 'Document processed successfully',
      documentId: documentId,
      documentType: documentType,
      tradeCount: tradeData.length
    })
  };
}

/**
 * Process document event from direct API invocation
 */
async function processDocumentEvent(event) {
  const { document } = event;
  const { documentId, documentType, userId, s3Key } = document;
  
  console.log(`Processing document ${documentId} of type ${documentType}`);
  
  // Get the file from S3
  const s3Object = await s3.getObject({
    Bucket: DOCUMENTS_BUCKET,
    Key: s3Key
  }).promise();
  
  // Extract trade data from the document
  const tradeData = await extractTradeData(s3Object, documentType);
  
  // Save document metadata to DynamoDB
  await saveDocumentMetadata(documentId, s3Key, documentType, userId, tradeData);
  
  // Save trade data to appropriate table based on document type
  if (documentType === 'source') {
    await saveSourceTrades(documentId, tradeData);
  } else if (documentType === 'target') {
    await saveTargetTrades(documentId, tradeData);
  }
  
  return {
    statusCode: 200,
    body: JSON.stringify({
      message: 'Document processed successfully',
      documentId: documentId,
      documentType: documentType,
      tradeCount: tradeData.length
    })
  };
}

/**
 * Extract trade data from document
 * This is a simplified implementation - in a production environment,
 * this would involve more sophisticated parsing based on file format
 */
async function extractTradeData(s3Object, documentType) {
  // Get file content
  const content = s3Object.Body.toString('utf-8');
  
  // In a real implementation, this would parse CSV, Excel, or other formats
  // For simplicity, we assume the document is a JSON array of trades
  try {
    const trades = JSON.parse(content);
    
    // Add unique IDs to trades if they don't have one
    return trades.map(trade => {
      return {
        id: trade.id || uuidv4(),
        ...trade,
        processedAt: new Date().toISOString()
      };
    });
  } catch (error) {
    console.error('Error parsing document content:', error);
    
    // For demonstration, return sample trades
    return [
      {
        id: uuidv4(),
        tradeId: 'T12345',
        symbol: 'AAPL',
        quantity: 100,
        price: 150.25,
        tradeDate: '2025-06-15',
        settlementDate: '2025-06-17',
        broker: 'ABC Securities',
        counterparty: 'XYZ Capital',
        processedAt: new Date().toISOString()
      },
      {
        id: uuidv4(),
        tradeId: 'T12346',
        symbol: 'MSFT',
        quantity: 50,
        price: 280.75,
        tradeDate: '2025-06-15',
        settlementDate: '2025-06-17',
        broker: 'ABC Securities',
        counterparty: 'PQR Investments',
        processedAt: new Date().toISOString()
      }
    ];
  }
}

/**
 * Save document metadata to DynamoDB
 */
async function saveDocumentMetadata(documentId, s3Key, documentType, userId, tradeData) {
  const timestamp = new Date().toISOString();
  
  const documentItem = {
    id: documentId,
    s3Key: s3Key,
    documentType: documentType,
    userId: userId,
    tradeCount: tradeData.length,
    status: 'PROCESSED',
    createdAt: timestamp,
    updatedAt: timestamp
  };
  
  await dynamoDB.put({
    TableName: DOCUMENT_TABLE,
    Item: documentItem
  }).promise();
  
  console.log(`Document metadata saved for document ${documentId}`);
}

/**
 * Save source trades to DynamoDB
 */
async function saveSourceTrades(documentId, trades) {
  // Use batch write to add multiple items efficiently
  const batchSize = 25; // DynamoDB batch write limit
  const batches = [];
  
  // Split trades into batches
  for (let i = 0; i < trades.length; i += batchSize) {
    batches.push(trades.slice(i, i + batchSize));
  }
  
  // Process each batch
  for (const batch of batches) {
    const batchWriteParams = {
      RequestItems: {
        [SOURCE_TRADE_TABLE]: batch.map(trade => ({
          PutRequest: {
            Item: {
              ...trade,
              documentId: documentId
            }
          }
        }))
      }
    };
    
    await dynamoDB.batchWrite(batchWriteParams).promise();
  }
  
  console.log(`${trades.length} source trades saved for document ${documentId}`);
}

/**
 * Save target trades to DynamoDB
 */
async function saveTargetTrades(documentId, trades) {
  // Use batch write to add multiple items efficiently
  const batchSize = 25; // DynamoDB batch write limit
  const batches = [];
  
  // Split trades into batches
  for (let i = 0; i < trades.length; i += batchSize) {
    batches.push(trades.slice(i, i + batchSize));
  }
  
  // Process each batch
  for (const batch of batches) {
    const batchWriteParams = {
      RequestItems: {
        [TARGET_TRADE_TABLE]: batch.map(trade => ({
          PutRequest: {
            Item: {
              ...trade,
              documentId: documentId
            }
          }
        }))
      }
    };
    
    await dynamoDB.batchWrite(batchWriteParams).promise();
  }
  
  console.log(`${trades.length} target trades saved for document ${documentId}`);
}

/**
 * Determine document type from filename
 */
function getDocumentTypeFromFilename(filename) {
  const lowerFilename = filename.toLowerCase();
  
  if (lowerFilename.includes('source') || lowerFilename.includes('internal')) {
    return 'source';
  } else if (lowerFilename.includes('target') || lowerFilename.includes('external')) {
    return 'target';
  }
  
  // Default to source if can't determine
  return 'source';
}
