/**
 * Reconciliations API Handlers
 * 
 * These handlers manage reconciliation operations including creating new
 * reconciliation processes, listing reconciliations, and retrieving reconciliation details.
 */

const AWS = require('aws-sdk');
const { v4: uuidv4 } = require('uuid');

// Environment variables
const RECONCILIATION_TABLE = process.env.RECONCILIATION_TABLE;
const MATCH_TABLE = process.env.MATCH_TABLE;
const RECONCILIATION_ENGINE_LAMBDA = process.env.RECONCILIATION_ENGINE_LAMBDA;

// AWS SDK clients
const dynamoDB = new AWS.DynamoDB.DocumentClient();
const lambda = new AWS.Lambda();

/**
 * Create a new reconciliation process
 */
exports.createReconciliation = async (pathParams, body, queryParams, context) => {
  try {
    console.log('Creating new reconciliation:', JSON.stringify(body));
    
    const { sourceDocumentId, targetDocumentId, matchingRules } = body;
    
    // Validate required parameters
    if (!sourceDocumentId || !targetDocumentId) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          message: 'Source and target document IDs are required'
        })
      };
    }
    
    // Create reconciliation record
    const reconciliationId = uuidv4();
    const timestamp = new Date().toISOString();
    
    const reconciliation = {
      id: reconciliationId,
      sourceDocumentId,
      targetDocumentId,
      status: 'CREATED',
      createdAt: timestamp,
      updatedAt: timestamp
    };
    
    // Store reconciliation record in DynamoDB
    await dynamoDB.put({
      TableName: RECONCILIATION_TABLE,
      Item: reconciliation
    }).promise();
    
    // Invoke reconciliation engine Lambda function asynchronously
    await lambda.invoke({
      FunctionName: RECONCILIATION_ENGINE_LAMBDA,
      InvocationType: 'Event',
      Payload: JSON.stringify({
        reconciliationId,
        sourceDocumentId,
        targetDocumentId,
        matchingRules: matchingRules || null
      })
    }).promise();
    
    return {
      statusCode: 201,
      body: JSON.stringify({
        message: 'Reconciliation process initiated',
        reconciliationId: reconciliationId,
        status: 'CREATED'
      })
    };
  } catch (error) {
    console.error('Error creating reconciliation:', error);
    
    return {
      statusCode: 500,
      body: JSON.stringify({
        message: 'Error creating reconciliation',
        error: error.message
      })
    };
  }
};

/**
 * List reconciliations with filtering and pagination support
 */
exports.listReconciliations = async (pathParams, body, queryParams, context) => {
  try {
    // Extract query parameters for filtering and pagination
    const limit = queryParams?.limit ? parseInt(queryParams.limit, 10) : 50;
    const startKey = queryParams?.startKey ? JSON.parse(decodeURIComponent(queryParams.startKey)) : null;
    
    // Build filter expression
    let filterExpressions = [];
    let expressionAttributeValues = {};
    let expressionAttributeNames = {};
    
    // Filter by status
    if (queryParams?.status) {
      filterExpressions.push('#status = :status');
      expressionAttributeValues[':status'] = queryParams.status;
      expressionAttributeNames['#status'] = 'status';
    }
    
    // Filter by sourceDocumentId
    if (queryParams?.sourceDocumentId) {
      filterExpressions.push('sourceDocumentId = :sourceDocumentId');
      expressionAttributeValues[':sourceDocumentId'] = queryParams.sourceDocumentId;
    }
    
    // Filter by targetDocumentId
    if (queryParams?.targetDocumentId) {
      filterExpressions.push('targetDocumentId = :targetDocumentId');
      expressionAttributeValues[':targetDocumentId'] = queryParams.targetDocumentId;
    }
    
    // Filter by date range
    if (queryParams?.startDate && queryParams?.endDate) {
      filterExpressions.push('createdAt BETWEEN :startDate AND :endDate');
      expressionAttributeValues[':startDate'] = queryParams.startDate;
      expressionAttributeValues[':endDate'] = queryParams.endDate;
    } else if (queryParams?.startDate) {
      filterExpressions.push('createdAt >= :startDate');
      expressionAttributeValues[':startDate'] = queryParams.startDate;
    } else if (queryParams?.endDate) {
      filterExpressions.push('createdAt <= :endDate');
      expressionAttributeValues[':endDate'] = queryParams.endDate;
    }
    
    // Construct DynamoDB params
    const params = {
      TableName: RECONCILIATION_TABLE,
      Limit: limit,
      ScanIndexForward: false // Sort in descending order (newest first)
    };
    
    // Add filter expression if filters are specified
    if (filterExpressions.length > 0) {
      params.FilterExpression = filterExpressions.join(' AND ');
      params.ExpressionAttributeValues = expressionAttributeValues;
      
      if (Object.keys(expressionAttributeNames).length > 0) {
        params.ExpressionAttributeNames = expressionAttributeNames;
      }
    }
    
    // Add pagination token if provided
    if (startKey) {
      params.ExclusiveStartKey = startKey;
    }
    
    // Query DynamoDB
    const result = await dynamoDB.scan(params).promise();
    
    return {
      statusCode: 200,
      body: JSON.stringify({
        reconciliations: result.Items,
        lastEvaluatedKey: result.LastEvaluatedKey
      })
    };
  } catch (error) {
    console.error('Error listing reconciliations:', error);
    
    return {
      statusCode: 500,
      body: JSON.stringify({
        message: 'Error listing reconciliations',
        error: error.message
      })
    };
  }
};

/**
 * Get reconciliation details by ID
 */
exports.getReconciliation = async (pathParams, body, queryParams, context) => {
  try {
    const reconciliationId = pathParams.id;
    
    // Validate reconciliation ID
    if (!reconciliationId) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          message: 'Reconciliation ID is required'
        })
      };
    }
    
    // Get reconciliation record from DynamoDB
    const reconciliationResult = await dynamoDB.get({
      TableName: RECONCILIATION_TABLE,
      Key: { id: reconciliationId }
    }).promise();
    
    if (!reconciliationResult.Item) {
      return {
        statusCode: 404,
        body: JSON.stringify({
          message: `Reconciliation with ID ${reconciliationId} not found`
        })
      };
    }
    
    // Get matches for this reconciliation
    const matchParams = {
      TableName: MATCH_TABLE,
      FilterExpression: 'reconciliationId = :reconciliationId',
      ExpressionAttributeValues: {
        ':reconciliationId': reconciliationId
      }
    };
    
    // Include match details if requested
    let matches = [];
    if (queryParams?.includeMatches === 'true') {
      const matchResult = await dynamoDB.scan(matchParams).promise();
      matches = matchResult.Items;
    }
    
    // Return reconciliation details with optional match data
    return {
      statusCode: 200,
      body: JSON.stringify({
        ...reconciliationResult.Item,
        matches: queryParams?.includeMatches === 'true' ? matches : undefined,
        matchCount: queryParams?.includeMatches === 'true' ? matches.length : undefined
      })
    };
  } catch (error) {
    console.error('Error getting reconciliation:', error);
    
    return {
      statusCode: 500,
      body: JSON.stringify({
        message: 'Error getting reconciliation',
        error: error.message
      })
    };
  }
};

/**
 * Update reconciliation status
 */
exports.updateReconciliationStatus = async (pathParams, body, queryParams, context) => {
  try {
    const reconciliationId = pathParams.id;
    const { status } = body;
    
    // Validate required parameters
    if (!reconciliationId) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          message: 'Reconciliation ID is required'
        })
      };
    }
    
    if (!status) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          message: 'Status is required'
        })
      };
    }
    
    // Valid status values
    const validStatuses = ['IN_PROGRESS', 'COMPLETED', 'ERROR', 'CANCELLED'];
    if (!validStatuses.includes(status)) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          message: `Invalid status. Must be one of: ${validStatuses.join(', ')}`
        })
      };
    }
    
    // Check if reconciliation exists
    const reconciliationResult = await dynamoDB.get({
      TableName: RECONCILIATION_TABLE,
      Key: { id: reconciliationId }
    }).promise();
    
    if (!reconciliationResult.Item) {
      return {
        statusCode: 404,
        body: JSON.stringify({
          message: `Reconciliation with ID ${reconciliationId} not found`
        })
      };
    }
    
    // Update reconciliation status
    await dynamoDB.update({
      TableName: RECONCILIATION_TABLE,
      Key: { id: reconciliationId },
      UpdateExpression: 'SET #status = :status, updatedAt = :updatedAt',
      ExpressionAttributeNames: {
        '#status': 'status'
      },
      ExpressionAttributeValues: {
        ':status': status,
        ':updatedAt': new Date().toISOString()
      }
    }).promise();
    
    return {
      statusCode: 200,
      body: JSON.stringify({
        message: 'Reconciliation status updated',
        reconciliationId,
        status
      })
    };
  } catch (error) {
    console.error('Error updating reconciliation status:', error);
    
    return {
      statusCode: 500,
      body: JSON.stringify({
        message: 'Error updating reconciliation status',
        error: error.message
      })
    };
  }
};

/**
 * Delete reconciliation
 */
exports.deleteReconciliation = async (pathParams, body, queryParams, context) => {
  try {
    const reconciliationId = pathParams.id;
    
    // Validate reconciliation ID
    if (!reconciliationId) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          message: 'Reconciliation ID is required'
        })
      };
    }
    
    // Check if reconciliation exists
    const reconciliationResult = await dynamoDB.get({
      TableName: RECONCILIATION_TABLE,
      Key: { id: reconciliationId }
    }).promise();
    
    if (!reconciliationResult.Item) {
      return {
        statusCode: 404,
        body: JSON.stringify({
          message: `Reconciliation with ID ${reconciliationId} not found`
        })
      };
    }
    
    // Get associated matches to delete
    const matchParams = {
      TableName: MATCH_TABLE,
      FilterExpression: 'reconciliationId = :reconciliationId',
      ExpressionAttributeValues: {
        ':reconciliationId': reconciliationId
      }
    };
    
    const matchResult = await dynamoDB.scan(matchParams).promise();
    const matches = matchResult.Items;
    
    // Delete matches in batches (DynamoDB batch delete limit is 25 items)
    if (matches.length > 0) {
      const batchSize = 25;
      for (let i = 0; i < matches.length; i += batchSize) {
        const batch = matches.slice(i, i + batchSize);
        await dynamoDB.batchWrite({
          RequestItems: {
            [MATCH_TABLE]: batch.map(match => ({
              DeleteRequest: {
                Key: { id: match.id }
              }
            }))
          }
        }).promise();
      }
    }
    
    // Delete reconciliation record
    await dynamoDB.delete({
      TableName: RECONCILIATION_TABLE,
      Key: { id: reconciliationId }
    }).promise();
    
    return {
      statusCode: 200,
      body: JSON.stringify({
        message: 'Reconciliation deleted successfully',
        reconciliationId,
        matchesDeleted: matches.length
      })
    };
  } catch (error) {
    console.error('Error deleting reconciliation:', error);
    
    return {
      statusCode: 500,
      body: JSON.stringify({
        message: 'Error deleting reconciliation',
        error: error.message
      })
    };
  }
};
