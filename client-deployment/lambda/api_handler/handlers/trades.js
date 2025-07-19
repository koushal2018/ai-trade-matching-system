/**
 * Trades API Handlers
 * 
 * These handlers manage trade data operations including listing trades,
 * retrieving trade details, updating trade information, and handling 
 * trade matching operations.
 */

const AWS = require('aws-sdk');
const { v4: uuidv4 } = require('uuid');

// Environment variables
const SOURCE_TRADE_TABLE = process.env.SOURCE_TRADE_TABLE;
const TARGET_TRADE_TABLE = process.env.TARGET_TRADE_TABLE;
const MATCH_TABLE = process.env.MATCH_TABLE;

// AWS SDK clients
const dynamoDB = new AWS.DynamoDB.DocumentClient();

/**
 * List trades with filtering and pagination
 */
exports.listTrades = async (pathParams, body, queryParams, context) => {
  try {
    // Determine which table to query based on trade type
    const tradeType = queryParams?.tradeType || 'SOURCE';
    const tableName = tradeType === 'SOURCE' ? SOURCE_TRADE_TABLE : TARGET_TRADE_TABLE;
    
    // Extract pagination parameters
    const limit = queryParams?.limit ? parseInt(queryParams.limit, 10) : 50;
    const startKey = queryParams?.startKey ? JSON.parse(decodeURIComponent(queryParams.startKey)) : null;
    
    // Build filter expressions
    let filterExpressions = [];
    let expressionAttributeValues = {};
    let expressionAttributeNames = {};
    
    // Filter by document ID
    if (queryParams?.documentId) {
      filterExpressions.push('documentId = :documentId');
      expressionAttributeValues[':documentId'] = queryParams.documentId;
    }
    
    // Filter by match status
    if (queryParams?.matchStatus) {
      filterExpressions.push('#matchStatus = :matchStatus');
      expressionAttributeValues[':matchStatus'] = queryParams.matchStatus;
      expressionAttributeNames['#matchStatus'] = 'matchStatus';
    }
    
    // Filter by match ID
    if (queryParams?.matchId) {
      filterExpressions.push('matchId = :matchId');
      expressionAttributeValues[':matchId'] = queryParams.matchId;
    }
    
    // Filter by security ID
    if (queryParams?.securityId) {
      filterExpressions.push('securityId = :securityId');
      expressionAttributeValues[':securityId'] = queryParams.securityId;
    }
    
    // Filter by trade reference
    if (queryParams?.tradeReference) {
      filterExpressions.push('contains(tradeReference, :tradeReference)');
      expressionAttributeValues[':tradeReference'] = queryParams.tradeReference;
    }
    
    // Filter by date range
    if (queryParams?.startDate && queryParams?.endDate) {
      filterExpressions.push('tradeDate BETWEEN :startDate AND :endDate');
      expressionAttributeValues[':startDate'] = queryParams.startDate;
      expressionAttributeValues[':endDate'] = queryParams.endDate;
    } else if (queryParams?.startDate) {
      filterExpressions.push('tradeDate >= :startDate');
      expressionAttributeValues[':startDate'] = queryParams.startDate;
    } else if (queryParams?.endDate) {
      filterExpressions.push('tradeDate <= :endDate');
      expressionAttributeValues[':endDate'] = queryParams.endDate;
    }
    
    // Construct DynamoDB query parameters
    const params = {
      TableName: tableName,
      Limit: limit
    };
    
    // Add filter expression if any filters are applied
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
        trades: result.Items,
        lastEvaluatedKey: result.LastEvaluatedKey,
        count: result.Items.length
      })
    };
  } catch (error) {
    console.error('Error listing trades:', error);
    
    return {
      statusCode: 500,
      body: JSON.stringify({
        message: 'Error listing trades',
        error: error.message
      })
    };
  }
};

/**
 * Get trade details by ID
 */
exports.getTrade = async (pathParams, body, queryParams, context) => {
  try {
    const tradeId = pathParams.id;
    const tradeType = queryParams?.tradeType || 'SOURCE';
    
    // Validate trade ID
    if (!tradeId) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          message: 'Trade ID is required'
        })
      };
    }
    
    // Determine which table to query
    const tableName = tradeType === 'SOURCE' ? SOURCE_TRADE_TABLE : TARGET_TRADE_TABLE;
    
    // Get trade from DynamoDB
    const params = {
      TableName: tableName,
      Key: { id: tradeId }
    };
    
    const result = await dynamoDB.get(params).promise();
    
    if (!result.Item) {
      return {
        statusCode: 404,
        body: JSON.stringify({
          message: `Trade with ID ${tradeId} not found in ${tradeType} trades`
        })
      };
    }
    
    // Get match details if trade is matched and includeMatch is requested
    let matchDetails = null;
    if (result.Item.matchId && queryParams?.includeMatch === 'true') {
      const matchParams = {
        TableName: MATCH_TABLE,
        Key: { id: result.Item.matchId }
      };
      
      const matchResult = await dynamoDB.get(matchParams).promise();
      if (matchResult.Item) {
        matchDetails = matchResult.Item;
      }
    }
    
    // Return trade with optional match details
    return {
      statusCode: 200,
      body: JSON.stringify({
        ...result.Item,
        match: matchDetails
      })
    };
  } catch (error) {
    console.error('Error getting trade:', error);
    
    return {
      statusCode: 500,
      body: JSON.stringify({
        message: 'Error getting trade',
        error: error.message
      })
    };
  }
};

/**
 * Update trade details
 */
exports.updateTrade = async (pathParams, body, queryParams, context) => {
  try {
    const tradeId = pathParams.id;
    const tradeType = queryParams?.tradeType || 'SOURCE';
    
    // Validate trade ID
    if (!tradeId) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          message: 'Trade ID is required'
        })
      };
    }
    
    // Determine which table to update
    const tableName = tradeType === 'SOURCE' ? SOURCE_TRADE_TABLE : TARGET_TRADE_TABLE;
    
    // Check if trade exists
    const checkParams = {
      TableName: tableName,
      Key: { id: tradeId }
    };
    
    const checkResult = await dynamoDB.get(checkParams).promise();
    
    if (!checkResult.Item) {
      return {
        statusCode: 404,
        body: JSON.stringify({
          message: `Trade with ID ${tradeId} not found in ${tradeType} trades`
        })
      };
    }
    
    // Build update expression
    let updateExpression = 'SET updatedAt = :updatedAt';
    let expressionAttributeValues = {
      ':updatedAt': new Date().toISOString()
    };
    let expressionAttributeNames = {};
    
    // Updatable fields
    const updatableFields = [
      'tradeReference', 'tradeDate', 'settlementDate', 'securityId', 
      'securityName', 'quantity', 'price', 'amount', 'currency', 'counterparty'
    ];
    
    // Add each provided field to the update expression
    for (const field of updatableFields) {
      if (body[field] !== undefined) {
        updateExpression += `, #${field} = :${field}`;
        expressionAttributeValues[`:${field}`] = body[field];
        expressionAttributeNames[`#${field}`] = field;
      }
    }
    
    // Perform update
    const updateParams = {
      TableName: tableName,
      Key: { id: tradeId },
      UpdateExpression: updateExpression,
      ExpressionAttributeValues: expressionAttributeValues,
      ExpressionAttributeNames: expressionAttributeNames,
      ReturnValues: 'ALL_NEW'
    };
    
    const updateResult = await dynamoDB.update(updateParams).promise();
    
    return {
      statusCode: 200,
      body: JSON.stringify({
        message: 'Trade updated successfully',
        trade: updateResult.Attributes
      })
    };
  } catch (error) {
    console.error('Error updating trade:', error);
    
    return {
      statusCode: 500,
      body: JSON.stringify({
        message: 'Error updating trade',
        error: error.message
      })
    };
  }
};

/**
 * Get trade match details
 */
exports.getTradeMatch = async (pathParams, body, queryParams, context) => {
  try {
    const tradeId = pathParams.id;
    const tradeType = queryParams?.tradeType || 'SOURCE';
    
    // Validate trade ID
    if (!tradeId) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          message: 'Trade ID is required'
        })
      };
    }
    
    // Determine which table to query
    const tableName = tradeType === 'SOURCE' ? SOURCE_TRADE_TABLE : TARGET_TRADE_TABLE;
    
    // Get trade from DynamoDB
    const tradeParams = {
      TableName: tableName,
      Key: { id: tradeId }
    };
    
    const tradeResult = await dynamoDB.get(tradeParams).promise();
    
    if (!tradeResult.Item) {
      return {
        statusCode: 404,
        body: JSON.stringify({
          message: `Trade with ID ${tradeId} not found in ${tradeType} trades`
        })
      };
    }
    
    // Check if trade has a match
    if (!tradeResult.Item.matchId) {
      return {
        statusCode: 404,
        body: JSON.stringify({
          message: `Trade with ID ${tradeId} has no match`
        })
      };
    }
    
    // Get match details
    const matchParams = {
      TableName: MATCH_TABLE,
      Key: { id: tradeResult.Item.matchId }
    };
    
    const matchResult = await dynamoDB.get(matchParams).promise();
    
    if (!matchResult.Item) {
      return {
        statusCode: 404,
        body: JSON.stringify({
          message: `Match with ID ${tradeResult.Item.matchId} not found`
        })
      };
    }
    
    // Get the matching trade (counterparty trade)
    const counterpartyTradeId = tradeType === 'SOURCE' 
      ? matchResult.Item.targetTrade
      : matchResult.Item.sourceTrade;
    
    const counterpartyTable = tradeType === 'SOURCE' 
      ? TARGET_TRADE_TABLE 
      : SOURCE_TRADE_TABLE;
    
    const counterpartyParams = {
      TableName: counterpartyTable,
      Key: { id: counterpartyTradeId }
    };
    
    const counterpartyResult = await dynamoDB.get(counterpartyParams).promise();
    
    // Return match details with both trades
    return {
      statusCode: 200,
      body: JSON.stringify({
        match: matchResult.Item,
        trade: tradeResult.Item,
        counterpartyTrade: counterpartyResult.Item || null
      })
    };
  } catch (error) {
    console.error('Error getting trade match:', error);
    
    return {
      statusCode: 500,
      body: JSON.stringify({
        message: 'Error getting trade match',
        error: error.message
      })
    };
  }
};

/**
 * Manual match or unmatch trades
 */
exports.matchTrades = async (pathParams, body, queryParams, context) => {
  try {
    const { sourceTradeId, targetTradeId, action } = body;
    
    // Validate required parameters
    if (!sourceTradeId || !targetTradeId) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          message: 'Source and target trade IDs are required'
        })
      };
    }
    
    // Valid actions: 'match' or 'unmatch'
    if (!['match', 'unmatch'].includes(action)) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          message: 'Action must be either "match" or "unmatch"'
        })
      };
    }
    
    // Get source trade
    const sourceTradeParams = {
      TableName: SOURCE_TRADE_TABLE,
      Key: { id: sourceTradeId }
    };
    
    const sourceTradeResult = await dynamoDB.get(sourceTradeParams).promise();
    
    if (!sourceTradeResult.Item) {
      return {
        statusCode: 404,
        body: JSON.stringify({
          message: `Source trade with ID ${sourceTradeId} not found`
        })
      };
    }
    
    // Get target trade
    const targetTradeParams = {
      TableName: TARGET_TRADE_TABLE,
      Key: { id: targetTradeId }
    };
    
    const targetTradeResult = await dynamoDB.get(targetTradeParams).promise();
    
    if (!targetTradeResult.Item) {
      return {
        statusCode: 404,
        body: JSON.stringify({
          message: `Target trade with ID ${targetTradeId} not found`
        })
      };
    }
    
    if (action === 'match') {
      // Check if either trade is already matched
      if (
        sourceTradeResult.Item.matchStatus === 'EXACT_MATCH' || 
        sourceTradeResult.Item.matchStatus === 'POTENTIAL_MATCH'
      ) {
        return {
          statusCode: 400,
          body: JSON.stringify({
            message: `Source trade with ID ${sourceTradeId} is already matched`
          })
        };
      }
      
      if (
        targetTradeResult.Item.matchStatus === 'EXACT_MATCH' || 
        targetTradeResult.Item.matchStatus === 'POTENTIAL_MATCH'
      ) {
        return {
          statusCode: 400,
          body: JSON.stringify({
            message: `Target trade with ID ${targetTradeId} is already matched`
          })
        };
      }
      
      // Create a new match
      const matchId = uuidv4();
      const timestamp = new Date().toISOString();
      
      // Find discrepancies between source and target trades
      const discrepancies = findDiscrepancies(sourceTradeResult.Item, targetTradeResult.Item);
      
      const matchStatus = discrepancies.length === 0 ? 'EXACT_MATCH' : 'POTENTIAL_MATCH';
      
      // Create match record
      const matchParams = {
        TableName: MATCH_TABLE,
        Item: {
          id: matchId,
          sourceTrade: sourceTradeId,
          targetTrade: targetTradeId,
          status: matchStatus,
          matchScore: 1.0, // Manual match always gets perfect score
          discrepancies: discrepancies,
          manualMatch: true,
          createdAt: timestamp,
          updatedAt: timestamp
        }
      };
      
      await dynamoDB.put(matchParams).promise();
      
      // Update source trade
      await updateTradeMatchStatus(sourceTradeId, matchStatus, matchId, SOURCE_TRADE_TABLE);
      
      // Update target trade
      await updateTradeMatchStatus(targetTradeId, matchStatus, matchId, TARGET_TRADE_TABLE);
      
      return {
        statusCode: 200,
        body: JSON.stringify({
          message: 'Trades matched successfully',
          matchId: matchId,
          status: matchStatus,
          discrepancies: discrepancies
        })
      };
    } else if (action === 'unmatch') {
      // Check if trades are matched to each other
      if (!sourceTradeResult.Item.matchId || !targetTradeResult.Item.matchId) {
        return {
          statusCode: 400,
          body: JSON.stringify({
            message: 'One or both trades are not matched'
          })
        };
      }
      
      if (sourceTradeResult.Item.matchId !== targetTradeResult.Item.matchId) {
        return {
          statusCode: 400,
          body: JSON.stringify({
            message: 'Trades are not matched to each other'
          })
        };
      }
      
      const matchId = sourceTradeResult.Item.matchId;
      
      // Delete match record
      await dynamoDB.delete({
        TableName: MATCH_TABLE,
        Key: { id: matchId }
      }).promise();
      
      // Update source trade
      await updateTradeMatchStatus(sourceTradeId, 'UNMATCHED', null, SOURCE_TRADE_TABLE);
      
      // Update target trade
      await updateTradeMatchStatus(targetTradeId, 'UNMATCHED', null, TARGET_TRADE_TABLE);
      
      return {
        statusCode: 200,
        body: JSON.stringify({
          message: 'Trades unmatched successfully'
        })
      };
    }
  } catch (error) {
    console.error('Error matching/unmatching trades:', error);
    
    return {
      statusCode: 500,
      body: JSON.stringify({
        message: 'Error matching/unmatching trades',
        error: error.message
      })
    };
  }
};

/**
 * Find discrepancies between source and target trades
 */
function findDiscrepancies(sourceTrade, targetTrade) {
  const discrepancies = [];
  
  // Fields to compare
  const fieldsToCompare = [
    { name: 'tradeReference', label: 'Trade Reference' },
    { name: 'tradeDate', label: 'Trade Date' },
    { name: 'settlementDate', label: 'Settlement Date' },
    { name: 'securityId', label: 'Security ID' },
    { name: 'securityName', label: 'Security Name' },
    { name: 'quantity', label: 'Quantity', type: 'number' },
    { name: 'price', label: 'Price', type: 'number' },
    { name: 'amount', label: 'Amount', type: 'number' },
    { name: 'currency', label: 'Currency' },
    { name: 'counterparty', label: 'Counterparty' }
  ];
  
  for (const field of fieldsToCompare) {
    // Compare values based on type
    if (field.type === 'number') {
      // For numeric fields, check if the difference exceeds a small threshold
      const sourceValue = parseFloat(sourceTrade[field.name] || 0);
      const targetValue = parseFloat(targetTrade[field.name] || 0);
      const tolerance = 0.01; // 1 cent tolerance for currency values
      
      if (Math.abs(sourceValue - targetValue) > tolerance) {
        discrepancies.push({
          field: field.label,
          sourceValue: sourceValue,
          targetValue: targetValue,
          difference: sourceValue - targetValue
        });
      }
    } else {
      // For string fields, check for exact match
      const sourceValue = sourceTrade[field.name] || '';
      const targetValue = targetTrade[field.name] || '';
      
      if (sourceValue !== targetValue) {
        discrepancies.push({
          field: field.label,
          sourceValue: sourceValue,
          targetValue: targetValue
        });
      }
    }
  }
  
  return discrepancies;
}

/**
 * Update trade match status
 */
async function updateTradeMatchStatus(tradeId, status, matchId, tableName) {
  const params = {
    TableName: tableName,
    Key: { id: tradeId },
    UpdateExpression: 'SET matchStatus = :status, matchId = :matchId, updatedAt = :updatedAt',
    ExpressionAttributeValues: {
      ':status': status,
      ':matchId': matchId,
      ':updatedAt': new Date().toISOString()
    }
  };
  
  await dynamoDB.update(params).promise();
}
