/**
 * Match API Handlers
 * 
 * These handlers manage match operations including creating, listing,
 * and updating matches between source and target trades.
 */

const AWS = require('aws-sdk');
const { v4: uuidv4 } = require('uuid');

// Environment variables
const MATCH_TABLE = process.env.MATCH_TABLE;
const SOURCE_TRADE_TABLE = process.env.SOURCE_TRADE_TABLE;
const TARGET_TRADE_TABLE = process.env.TARGET_TRADE_TABLE;
const RECONCILIATION_TABLE = process.env.RECONCILIATION_TABLE;

/**
 * List matches with filtering and pagination support
 */
exports.listMatches = async (pathParams, body, queryParams, context) => {
  const { dynamoDB } = context;
  
  // Extract query parameters for filtering
  const limit = queryParams?.limit ? parseInt(queryParams.limit, 10) : 50;
  const startKey = queryParams?.startKey ? JSON.parse(decodeURIComponent(queryParams.startKey)) : null;
  
  // Build filter expression
  let filterExpressions = [];
  let expressionAttributeValues = {};
  let expressionAttributeNames = {};
  
  // Filter by reconciliation ID
  if (queryParams?.reconciliationId) {
    filterExpressions.push('reconciliationId = :reconciliationId');
    expressionAttributeValues[':reconciliationId'] = queryParams.reconciliationId;
  }
  
  // Filter by source trade ID
  if (queryParams?.sourceTradeId) {
    filterExpressions.push('sourceTradeId = :sourceTradeId');
    expressionAttributeValues[':sourceTradeId'] = queryParams.sourceTradeId;
  }
  
  // Filter by target trade ID
  if (queryParams?.targetTradeId) {
    filterExpressions.push('targetTradeId = :targetTradeId');
    expressionAttributeValues[':targetTradeId'] = queryParams.targetTradeId;
  }
  
  // Filter by status
  if (queryParams?.status) {
    filterExpressions.push('#status = :status');
    expressionAttributeValues[':status'] = queryParams.status;
    expressionAttributeNames['#status'] = 'status';
  }
  
  // Filter by match type
  if (queryParams?.matchType) {
    filterExpressions.push('matchType = :matchType');
    expressionAttributeValues[':matchType'] = queryParams.matchType;
  }
  
  // Filter by score range
  if (queryParams?.minScore || queryParams?.maxScore) {
    if (queryParams?.minScore && queryParams?.maxScore) {
      filterExpressions.push('score BETWEEN :minScore AND :maxScore');
      expressionAttributeValues[':minScore'] = parseFloat(queryParams.minScore);
      expressionAttributeValues[':maxScore'] = parseFloat(queryParams.maxScore);
    } else if (queryParams?.minScore) {
      filterExpressions.push('score >= :minScore');
      expressionAttributeValues[':minScore'] = parseFloat(queryParams.minScore);
    } else {
      filterExpressions.push('score <= :maxScore');
      expressionAttributeValues[':maxScore'] = parseFloat(queryParams.maxScore);
    }
  }
  
  // Combine filter expressions
  const combinedFilterExpression = filterExpressions.length > 0 
    ? filterExpressions.join(' AND ') 
    : undefined;
  
  // Prepare query params
  const params = {
    TableName: MATCH_TABLE,
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
    matches: result.Items,
    pagination: {
      count: result.Items.length,
      lastEvaluatedKey: result.LastEvaluatedKey 
        ? encodeURIComponent(JSON.stringify(result.LastEvaluatedKey))
        : null,
    },
  };
};

/**
 * Get match by ID
 */
exports.getMatch = async (pathParams, body, queryParams, context) => {
  const { dynamoDB } = context;
  const { matchId } = pathParams;
  
  if (!matchId) {
    const error = new Error('Match ID is required');
    error.statusCode = 400;
    throw error;
  }
  
  // Get match from DynamoDB
  const result = await dynamoDB.get({
    TableName: MATCH_TABLE,
    Key: { matchId },
  }).promise();
  
  if (!result.Item) {
    const error = new Error(`Match not found: ${matchId}`);
    error.statusCode = 404;
    throw error;
  }
  
  const match = result.Item;
  
  // If includeTrades=true, get trade details
  if (queryParams?.includeTrades === 'true') {
    // Get source trade
    if (match.sourceTradeId) {
      const sourceTradeResult = await dynamoDB.get({
        TableName: SOURCE_TRADE_TABLE,
        Key: { tradeId: match.sourceTradeId },
      }).promise();
      
      if (sourceTradeResult.Item) {
        match.sourceTrade = sourceTradeResult.Item;
      }
    }
    
    // Get target trade
    if (match.targetTradeId) {
      const targetTradeResult = await dynamoDB.get({
        TableName: TARGET_TRADE_TABLE,
        Key: { tradeId: match.targetTradeId },
      }).promise();
      
      if (targetTradeResult.Item) {
        match.targetTrade = targetTradeResult.Item;
      }
    }
  }
  
  // If includeReconciliation=true, get reconciliation details
  if (queryParams?.includeReconciliation === 'true' && match.reconciliationId) {
    const reconciliationResult = await dynamoDB.get({
      TableName: RECONCILIATION_TABLE,
      Key: { reconciliationId: match.reconciliationId },
    }).promise();
    
    if (reconciliationResult.Item) {
      match.reconciliation = {
        reconciliationId: reconciliationResult.Item.reconciliationId,
        name: reconciliationResult.Item.name,
        status: reconciliationResult.Item.status,
        sourceDocumentId: reconciliationResult.Item.sourceDocumentId,
        targetDocumentId: reconciliationResult.Item.targetDocumentId,
      };
    }
  }
  
  return match;
};

/**
 * Create a new match
 */
exports.createMatch = async (pathParams, body, queryParams, context) => {
  const { dynamoDB } = context;
  
  // Validate request
  if (!body || !body.reconciliationId || !body.sourceTradeId || !body.targetTradeId) {
    const error = new Error('Reconciliation ID, source trade ID, and target trade ID are required');
    error.statusCode = 400;
    throw error;
  }
  
  const { 
    reconciliationId, sourceTradeId, targetTradeId,
    matchType, score, details
  } = body;
  
  // Check if reconciliation exists
  const reconciliationResult = await dynamoDB.get({
    TableName: RECONCILIATION_TABLE,
    Key: { reconciliationId },
  }).promise();
  
  if (!reconciliationResult.Item) {
    const error = new Error(`Reconciliation not found: ${reconciliationId}`);
    error.statusCode = 404;
    throw error;
  }
  
  // Check if source trade exists
  const sourceTradeResult = await dynamoDB.get({
    TableName: SOURCE_TRADE_TABLE,
    Key: { tradeId: sourceTradeId },
  }).promise();
  
  if (!sourceTradeResult.Item) {
    const error = new Error(`Source trade not found: ${sourceTradeId}`);
    error.statusCode = 404;
    throw error;
  }
  
  // Check if target trade exists
  const targetTradeResult = await dynamoDB.get({
    TableName: TARGET_TRADE_TABLE,
    Key: { tradeId: targetTradeId },
  }).promise();
  
  if (!targetTradeResult.Item) {
    const error = new Error(`Target trade not found: ${targetTradeId}`);
    error.statusCode = 404;
    throw error;
  }
  
  // Check if source trade is already matched
  const sourceTrade = sourceTradeResult.Item;
  
  if (sourceTrade.matchStatus === 'matched' && sourceTrade.matchId) {
    const error = new Error(`Source trade ${sourceTradeId} is already matched (matchId: ${sourceTrade.matchId})`);
    error.statusCode = 400;
    throw error;
  }
  
  // Check if target trade is already matched
  const targetTrade = targetTradeResult.Item;
  
  if (targetTrade.matchStatus === 'matched' && targetTrade.matchId) {
    const error = new Error(`Target trade ${targetTradeId} is already matched (matchId: ${targetTrade.matchId})`);
    error.statusCode = 400;
    throw error;
  }
  
  // Generate a unique match ID
  const matchId = `match-${uuidv4()}`;
  const timestamp = new Date().toISOString();
  
  // Determine match status based on score
  let status = 'pending';
  
  // Check if auto-confirm threshold is met
  const reconciliation = reconciliationResult.Item;
  const autoConfirmThreshold = reconciliation.config?.autoConfirmThreshold || 0.8;
  
  if (score && score >= autoConfirmThreshold) {
    status = 'confirmed';
  }
  
  // Create match record
  const match = {
    matchId,
    reconciliationId,
    sourceTradeId,
    targetTradeId,
    matchType: matchType || 'auto', // 'auto' or 'manual'
    status, // 'pending', 'confirmed', 'rejected'
    score: score || 0, // Match score between 0 and 1
    details: details || {}, // Additional matching details
    createdAt: timestamp,
    updatedAt: timestamp,
  };
  
  // Store match in DynamoDB
  await dynamoDB.put({
    TableName: MATCH_TABLE,
    Item: match,
  }).promise();
  
  // Update source and target trades if status is 'confirmed'
  if (status === 'confirmed') {
    // Update source trade
    await dynamoDB.update({
      TableName: SOURCE_TRADE_TABLE,
      Key: { tradeId: sourceTradeId },
      UpdateExpression: 'SET matchStatus = :matchStatus, matchId = :matchId, updatedAt = :updatedAt',
      ExpressionAttributeValues: {
        ':matchStatus': 'matched',
        ':matchId': matchId,
        ':updatedAt': timestamp,
      },
    }).promise();
    
    // Update target trade
    await dynamoDB.update({
      TableName: TARGET_TRADE_TABLE,
      Key: { tradeId: targetTradeId },
      UpdateExpression: 'SET matchStatus = :matchStatus, matchId = :matchId, updatedAt = :updatedAt',
      ExpressionAttributeValues: {
        ':matchStatus': 'matched',
        ':matchId': matchId,
        ':updatedAt': timestamp,
      },
    }).promise();
  }
  
  return match;
};

/**
 * Update match status
 */
exports.updateMatch = async (pathParams, body, queryParams, context) => {
  const { dynamoDB } = context;
  const { matchId } = pathParams;
  
  if (!matchId) {
    const error = new Error('Match ID is required');
    error.statusCode = 400;
    throw error;
  }
  
  if (!body) {
    const error = new Error('Update data is required');
    error.statusCode = 400;
    throw error;
  }
  
  // Get match from DynamoDB to make sure it exists
  const result = await dynamoDB.get({
    TableName: MATCH_TABLE,
    Key: { matchId },
  }).promise();
  
  if (!result.Item) {
    const error = new Error(`Match not found: ${matchId}`);
    error.statusCode = 404;
    throw error;
  }
  
  const match = result.Item;
  
  // Fields that can be updated
  const updatableFields = [
    'status',
    'score',
    'details',
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
  
  // Check if status is being updated
  const isStatusUpdate = updates.hasOwnProperty('status');
  const newStatus = isStatusUpdate ? updates.status : match.status;
  const oldStatus = match.status;
  
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
    TableName: MATCH_TABLE,
    Key: { matchId },
    UpdateExpression: updateExpression,
    ExpressionAttributeValues: expressionAttributeValues,
    ReturnValues: 'ALL_NEW',
  }).promise();
  
  const updatedMatch = updateResult.Attributes;
  
  // Handle status changes and update trades accordingly
  if (isStatusUpdate && newStatus !== oldStatus) {
    // If status changed to 'confirmed', update trades to matched
    if (newStatus === 'confirmed') {
      // Update source trade
      if (updatedMatch.sourceTradeId) {
        await dynamoDB.update({
          TableName: SOURCE_TRADE_TABLE,
          Key: { tradeId: updatedMatch.sourceTradeId },
          UpdateExpression: 'SET matchStatus = :matchStatus, matchId = :matchId, updatedAt = :updatedAt',
          ExpressionAttributeValues: {
            ':matchStatus': 'matched',
            ':matchId': matchId,
            ':updatedAt': updatedMatch.updatedAt,
          },
        }).promise();
      }
      
      // Update target trade
      if (updatedMatch.targetTradeId) {
        await dynamoDB.update({
          TableName: TARGET_TRADE_TABLE,
          Key: { tradeId: updatedMatch.targetTradeId },
          UpdateExpression: 'SET matchStatus = :matchStatus, matchId = :matchId, updatedAt = :updatedAt',
          ExpressionAttributeValues: {
            ':matchStatus': 'matched',
            ':matchId': matchId,
            ':updatedAt': updatedMatch.updatedAt,
          },
        }).promise();
      }
    }
    // If status changed from 'confirmed' to anything else, update trades to unmatched
    else if (oldStatus === 'confirmed') {
      // Update source trade
      if (updatedMatch.sourceTradeId) {
        await dynamoDB.update({
          TableName: SOURCE_TRADE_TABLE,
          Key: { tradeId: updatedMatch.sourceTradeId },
          UpdateExpression: 'SET matchStatus = :matchStatus, updatedAt = :updatedAt REMOVE matchId',
          ExpressionAttributeValues: {
            ':matchStatus': 'unmatched',
            ':updatedAt': updatedMatch.updatedAt,
          },
        }).promise();
      }
      
      // Update target trade
      if (updatedMatch.targetTradeId) {
        await dynamoDB.update({
          TableName: TARGET_TRADE_TABLE,
          Key: { tradeId: updatedMatch.targetTradeId },
          UpdateExpression: 'SET matchStatus = :matchStatus, updatedAt = :updatedAt REMOVE matchId',
          ExpressionAttributeValues: {
            ':matchStatus': 'unmatched',
            ':updatedAt': updatedMatch.updatedAt,
          },
        }).promise();
      }
    }
  }
  
  return updatedMatch;
};

/**
 * Confirm match
 */
exports.confirmMatch = async (pathParams, body, queryParams, context) => {
  const { matchId } = pathParams;
  
  if (!matchId) {
    const error = new Error('Match ID is required');
    error.statusCode = 400;
    throw error;
  }
  
  // Call updateMatch with status=confirmed
  return exports.updateMatch(
    pathParams,
    { status: 'confirmed' },
    queryParams,
    context
  );
};

/**
 * Reject match
 */
exports.rejectMatch = async (pathParams, body, queryParams, context) => {
  const { matchId } = pathParams;
  
  if (!matchId) {
    const error = new Error('Match ID is required');
    error.statusCode = 400;
    throw error;
  }
  
  // Call updateMatch with status=rejected
  return exports.updateMatch(
    pathParams,
    { status: 'rejected' },
    queryParams,
    context
  );
};

/**
 * Delete match
 */
exports.deleteMatch = async (pathParams, body, queryParams, context) => {
  const { dynamoDB } = context;
  const { matchId } = pathParams;
  
  if (!matchId) {
    const error = new Error('Match ID is required');
    error.statusCode = 400;
    throw error;
  }
  
  // Get match from DynamoDB to make sure it exists
  const result = await dynamoDB.get({
    TableName: MATCH_TABLE,
    Key: { matchId },
  }).promise();
  
  if (!result.Item) {
    const error = new Error(`Match not found: ${matchId}`);
    error.statusCode = 404;
    throw error;
  }
  
  const match = result.Item;
  
  // If match is confirmed, update trades to unmatched
  if (match.status === 'confirmed') {
    // Update source trade
    if (match.sourceTradeId) {
      await dynamoDB.update({
        TableName: SOURCE_TRADE_TABLE,
        Key: { tradeId: match.sourceTradeId },
        UpdateExpression: 'SET matchStatus = :matchStatus, updatedAt = :updatedAt REMOVE matchId',
        ExpressionAttributeValues: {
          ':matchStatus': 'unmatched',
          ':updatedAt': new Date().toISOString(),
        },
      }).promise();
    }
    
    // Update target trade
    if (match.targetTradeId) {
      await dynamoDB.update({
        TableName: TARGET_TRADE_TABLE,
        Key: { tradeId: match.targetTradeId },
        UpdateExpression: 'SET matchStatus = :matchStatus, updatedAt = :updatedAt REMOVE matchId',
        ExpressionAttributeValues: {
          ':matchStatus': 'unmatched',
          ':updatedAt': new Date().toISOString(),
        },
      }).promise();
    }
  }
  
  // Delete the match
  await dynamoDB.delete({
    TableName: MATCH_TABLE,
    Key: { matchId },
  }).promise();
  
  return {
    matchId,
    message: 'Match deleted successfully',
  };
};

/**
 * Get match statistics for a reconciliation
 */
exports.getMatchStatistics = async (pathParams, body, queryParams, context) => {
  const { dynamoDB } = context;
  const { reconciliationId } = queryParams;
  
  if (!reconciliationId) {
    const error = new Error('Reconciliation ID is required');
    error.statusCode = 400;
    throw error;
  }
  
  // Check if reconciliation exists
  const reconciliationResult = await dynamoDB.get({
    TableName: RECONCILIATION_TABLE,
    Key: { reconciliationId },
  }).promise();
  
  if (!reconciliationResult.Item) {
    const error = new Error(`Reconciliation not found: ${reconciliationId}`);
    error.statusCode = 404;
    throw error;
  }
  
  // Get all matches for reconciliation
  const matchParams = {
    TableName: MATCH_TABLE,
    FilterExpression: 'reconciliationId = :reconciliationId',
    ExpressionAttributeValues: {
      ':reconciliationId': reconciliationId,
    },
  };
  
  const matchResults = await dynamoDB.scan(matchParams).promise();
  const matches = matchResults.Items;
  
  // Count matches by status
  const matchesByStatus = matches.reduce((acc, match) => {
    const status = match.status || 'unknown';
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {});
  
  // Count matches by type
  const matchesByType = matches.reduce((acc, match) => {
    const type = match.matchType || 'unknown';
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {});
  
  // Get score distribution
  const scoreDistribution = {};
  const scoreRanges = {
    '0.0-0.2': 0,
    '0.2-0.4': 0,
    '0.4-0.6': 0,
    '0.6-0.8': 0,
    '0.8-1.0': 0,
  };
  
  matches.forEach(match => {
    const score = match.score || 0;
    
    if (score < 0.2) {
      scoreRanges['0.0-0.2']++;
    } else if (score < 0.4) {
      scoreRanges['0.2-0.4']++;
    } else if (score < 0.6) {
      scoreRanges['0.4-0.6']++;
    } else if (score < 0.8) {
      scoreRanges['0.6-0.8']++;
    } else {
      scoreRanges['0.8-1.0']++;
    }
  });
  
  // Calculate match rate
  let matchRate = 0;
  
  // Get source and target trade counts
  const reconciliation = reconciliationResult.Item;
  
  if (reconciliation.sourceDocumentId && reconciliation.targetDocumentId) {
    const [sourceDocResult, targetDocResult] = await Promise.all([
      dynamoDB.get({
        TableName: 'Documents',
        Key: { documentId: reconciliation.sourceDocumentId },
      }).promise(),
      dynamoDB.get({
        TableName: 'Documents',
        Key: { documentId: reconciliation.targetDocumentId },
      }).promise(),
    ]);
    
    const sourceTradeCount = sourceDocResult.Item?.tradeCount || 0;
    const targetTradeCount = targetDocResult.Item?.tradeCount || 0;
    
    if (sourceTradeCount > 0 && targetTradeCount > 0) {
      const confirmedMatches = matchesByStatus.confirmed || 0;
      const minTradeCount = Math.min(sourceTradeCount, targetTradeCount);
      
      if (minTradeCount > 0) {
        matchRate = confirmedMatches / minTradeCount;
      }
    }
  }
  
  return {
    reconciliationId,
    totalMatches: matches.length,
    matchesByStatus,
    matchesByType,
    scoreDistribution: scoreRanges,
    matchRate,
  };
};

/**
 * Create potential matches for a reconciliation
 */
exports.suggestMatches = async (pathParams, body, queryParams, context) => {
  const { dynamoDB } = context;
  const { reconciliationId } = pathParams;
  
  if (!reconciliationId) {
    const error = new Error('Reconciliation ID is required');
    error.statusCode = 400;
    throw error;
  }
  
  // Get reconciliation
  const reconciliationResult = await dynamoDB.get({
    TableName: RECONCILIATION_TABLE,
    Key: { reconciliationId },
  }).promise();
  
  if (!reconciliationResult.Item) {
    const error = new Error(`Reconciliation not found: ${reconciliationId}`);
    error.statusCode = 404;
    throw error;
  }
  
  const reconciliation = reconciliationResult.Item;
  
  // Get all unmatched source trades
  const sourceTradeParams = {
    TableName: SOURCE_TRADE_TABLE,
    FilterExpression: 'documentId = :documentId AND (attribute_not_exists(matchStatus) OR matchStatus = :unmatchedStatus)',
    ExpressionAttributeValues: {
      ':documentId': reconciliation.sourceDocumentId,
      ':unmatchedStatus': 'unmatched',
    },
  };
  
  // Get all unmatched target trades
  const targetTradeParams = {
    TableName: TARGET_TRADE_TABLE,
    FilterExpression: 'documentId = :documentId AND (attribute_not_exists(matchStatus) OR matchStatus = :unmatchedStatus)',
    ExpressionAttributeValues: {
      ':documentId': reconciliation.targetDocumentId,
      ':unmatchedStatus': 'unmatched',
    },
  };
  
  const [sourceTradeResult, targetTradeResult] = await Promise.all([
    dynamoDB.scan(sourceTradeParams).promise(),
    dynamoDB.scan(targetTradeParams).promise(),
  ]);
  
  const sourceTrades = sourceTradeResult.Items;
  const targetTrades = targetTradeResult.Items;
  
  // Extract matching criteria from reconciliation config
  const matchingCriteria = reconciliation.config?.matchingCriteria || {
    tradeReference: { enabled: true, weight: 0.3 },
    securityId: { enabled: true, weight: 0.2 },
    amount: { enabled: true, weight: 0.3, tolerance: 0.01 },
    tradeDate: { enabled: true, weight: 0.2 },
  };
  
  const autoConfirmThreshold = reconciliation.config?.autoConfirmThreshold || 0.8;
  
  // Compute matches
  const computeMatchScore = (sourceTrade, targetTrade) => {
    let totalScore = 0;
    let totalWeight = 0;
    
    // Match by trade reference
    if (matchingCriteria.tradeReference?.enabled) {
      const weight = matchingCriteria.tradeReference.weight || 0;
      totalWeight += weight;
      
      if (sourceTrade.tradeReference === targetTrade.tradeReference) {
        totalScore += weight;
      }
    }
    
    // Match by security ID
    if (matchingCriteria.securityId?.enabled) {
      const weight = matchingCriteria.securityId.weight || 0;
      totalWeight += weight;
      
      if (sourceTrade.securityId === targetTrade.securityId) {
        totalScore += weight;
      }
    }
    
    // Match by amount with tolerance
    if (matchingCriteria.amount?.enabled) {
      const weight = matchingCriteria.amount.weight || 0;
      totalWeight += weight;
      
      const tolerance = matchingCriteria.amount.tolerance || 0.01;
      const sourceAmount = parseFloat(sourceTrade.amount);
      const targetAmount = parseFloat(targetTrade.amount);
      
      if (!isNaN(sourceAmount) && !isNaN(targetAmount)) {
        const diff = Math.abs(sourceAmount - targetAmount);
        const relDiff = sourceAmount !== 0 ? diff / Math.abs(sourceAmount) : diff;
        
        if (relDiff <= tolerance) {
          totalScore += weight;
        }
      }
    }
    
    // Match by trade date
    if (matchingCriteria.tradeDate?.enabled) {
      const weight = matchingCriteria.tradeDate.weight || 0;
      totalWeight += weight;
      
      if (sourceTrade.tradeDate === targetTrade.tradeDate) {
        totalScore += weight;
      }
    }
    
    // Normalize score
    return totalWeight > 0 ? totalScore / totalWeight : 0;
  };
  
  // Find potential matches
  const potentialMatches = [];
  
  // For each source trade, find the best matching target trade
  for (const sourceTrade of sourceTrades) {
    let bestMatch = null;
    let bestScore = 0;
    
    for (const targetTrade of targetTrades) {
      const score = computeMatchScore(sourceTrade, targetTrade);
      
      if (score > bestScore) {
        bestScore = score;
        bestMatch = {
          sourceTradeId: sourceTrade.tradeId,
          targetTradeId: targetTrade.tradeId,
          score,
        };
      }
    }
    
    // Only suggest matches with score above minimum threshold
    const minScoreThreshold = 0.1;
    if (bestMatch && bestMatch.score >= minScoreThreshold) {
      potentialMatches.push({
        ...bestMatch,
        autoConfirm: bestMatch.score >= autoConfirmThreshold,
      });
      
      // Remove matched target trade to avoid duplicate matches
      const targetTradeIndex = targetTrades.findIndex(t => t.tradeId === bestMatch.targetTradeId);
      if (targetTradeIndex >= 0) {
        targetTrades.splice(targetTradeIndex, 1);
      }
    }
  }
  
  // Sort matches by score (highest first)
  potentialMatches.sort((a, b) => b.score - a.score);
  
  // Return results
  return {
    reconciliationId,
    potentialMatches,
    unmatchedSourceTrades: sourceTrades.length - potentialMatches.length,
    unmatchedTargetTrades: targetTrades.length,
  };
};

/**
 * Create matches in bulk for a reconciliation
 */
exports.createMatches = async (pathParams, body, queryParams, context) => {
  const { dynamoDB } = context;
  
  // Validate request
  if (!body || !body.reconciliationId || !body.matches || !Array.isArray(body.matches) || body.matches.length === 0) {
    const error = new Error('Reconciliation ID and matches array are required');
    error.statusCode = 400;
    throw error;
  }
  
  const { reconciliationId, matches } = body;
  
  // Check if reconciliation exists
  const reconciliationResult = await dynamoDB.get({
    TableName: RECONCILIATION_TABLE,
    Key: { reconciliationId },
  }).promise();
  
  if (!reconciliationResult.Item) {
    const error = new Error(`Reconciliation not found: ${reconciliationId}`);
    error.statusCode = 404;
    throw error;
  }
  
  // Create matches in sequence
  const results = [];
  const timestamp = new Date().toISOString();
  const reconciliation = reconciliationResult.Item;
  const autoConfirmThreshold = reconciliation.config?.autoConfirmThreshold || 0.8;
  
  for (const matchData of matches) {
    const { sourceTradeId, targetTradeId, score, matchType, details } = matchData;
    
    try {
      // Check if source trade exists
      const sourceTradeResult = await dynamoDB.get({
        TableName: SOURCE_TRADE_TABLE,
        Key: { tradeId: sourceTradeId },
      }).promise();
      
      if (!sourceTradeResult.Item) {
        results.push({
          sourceTradeId,
          targetTradeId,
          success: false,
          error: `Source trade not found: ${sourceTradeId}`,
        });
        continue;
      }
      
      // Check if target trade exists
      const targetTradeResult = await dynamoDB.get({
        TableName: TARGET_TRADE_TABLE,
        Key: { tradeId: targetTradeId },
      }).promise();
      
      if (!targetTradeResult.Item) {
        results.push({
          sourceTradeId,
          targetTradeId,
          success: false,
          error: `Target trade not found: ${targetTradeId}`,
        });
        continue;
      }
      
      // Check if source trade is already matched
      const sourceTrade = sourceTradeResult.Item;
      
      if (sourceTrade.matchStatus === 'matched' && sourceTrade.matchId) {
        results.push({
          sourceTradeId,
          targetTradeId,
          success: false,
          error: `Source trade ${sourceTradeId} is already matched (matchId: ${sourceTrade.matchId})`,
        });
        continue;
      }
      
      // Check if target trade is already matched
      const targetTrade = targetTradeResult.Item;
      
      if (targetTrade.matchStatus === 'matched' && targetTrade.matchId) {
        results.push({
          sourceTradeId,
          targetTradeId,
          success: false,
          error: `Target trade ${targetTradeId} is already matched (matchId: ${targetTrade.matchId})`,
        });
        continue;
      }
      
      // Generate a unique match ID
      const matchId = `match-${uuidv4()}`;
      
      // Determine match status based on score
      let status = 'pending';
      
      if (score && score >= autoConfirmThreshold) {
        status = 'confirmed';
      }
      
      // Create match record
      const match = {
        matchId,
        reconciliationId,
        sourceTradeId,
        targetTradeId,
        matchType: matchType || 'auto',
        status,
        score: score || 0,
        details: details || {},
        createdAt: timestamp,
        updatedAt: timestamp,
      };
      
      // Store match in DynamoDB
      await dynamoDB.put({
        TableName: MATCH_TABLE,
        Item: match,
      }).promise();
      
      // Update source and target trades if status is 'confirmed'
      if (status === 'confirmed') {
        // Update source trade
        await dynamoDB.update({
          TableName: SOURCE_TRADE_TABLE,
          Key: { tradeId: sourceTradeId },
          UpdateExpression: 'SET matchStatus = :matchStatus, matchId = :matchId, updatedAt = :updatedAt',
          ExpressionAttributeValues: {
            ':matchStatus': 'matched',
            ':matchId': matchId,
            ':updatedAt': timestamp,
          },
        }).promise();
        
        // Update target trade
        await dynamoDB.update({
          TableName: TARGET_TRADE_TABLE,
          Key: { tradeId: targetTradeId },
          UpdateExpression: 'SET matchStatus = :matchStatus, matchId = :matchId, updatedAt = :updatedAt',
          ExpressionAttributeValues: {
            ':matchStatus': 'matched',
            ':matchId': matchId,
            ':updatedAt': timestamp,
          },
        }).promise();
      }
      
      results.push({
        matchId,
        sourceTradeId,
        targetTradeId,
        status,
        score: score || 0,
        success: true,
      });
    } catch (error) {
      console.error('Error creating match:', error);
      
      results.push({
        sourceTradeId,
        targetTradeId,
        success: false,
        error: error.message,
      });
    }
  }
  
  return {
    reconciliationId,
    results,
    summary: {
      total: matches.length,
      successful: results.filter(r => r.success).length,
      failed: results.filter(r => !r.success).length,
    },
  };
};
