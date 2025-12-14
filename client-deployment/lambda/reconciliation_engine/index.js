/**
 * Reconciliation Engine Lambda
 * 
 * This Lambda function performs trade reconciliation between source and target trade data.
 * It compares trades based on configurable matching rules and generates match results.
 */

// AWS SDK
const AWS = require('aws-sdk');
const dynamoDB = new AWS.DynamoDB.DocumentClient();

// Configuration
const SOURCE_TRADE_TABLE = process.env.SOURCE_TRADE_TABLE;
const TARGET_TRADE_TABLE = process.env.TARGET_TRADE_TABLE;
const MATCH_TABLE = process.env.MATCH_TABLE;
const RECONCILIATION_TABLE = process.env.RECONCILIATION_TABLE;

/**
 * Main handler function
 */
exports.handler = async (event) => {
    console.log('Starting reconciliation:', JSON.stringify(event, null, 2));

    try {
        // Extract reconciliation parameters from the event
        const {
            reconciliationId,
            userId,
            sourceDocumentId,
            targetDocumentId,
            matchingRules = ['tradeId', 'amount', 'currency'],
            fuzzyMatch = false,
            fuzzyMatchThreshold = 0.8
        } = event;

        if (!reconciliationId || !sourceDocumentId || !targetDocumentId) {
            throw new Error('Missing required parameters');
        }

        // Create reconciliation record with PROCESSING status
        await createReconciliationRecord(reconciliationId, userId, sourceDocumentId, targetDocumentId, 'PROCESSING');

        // Get trades from source and target documents
        const sourceTrades = await getTradesByDocumentId(SOURCE_TRADE_TABLE, sourceDocumentId);
        const targetTrades = await getTradesByDocumentId(TARGET_TRADE_TABLE, targetDocumentId);

        console.log(`Retrieved ${sourceTrades.length} source trades and ${targetTrades.length} target trades`);

        // Perform reconciliation
        const matchResults = await performReconciliation(
            reconciliationId,
            sourceTrades,
            targetTrades,
            matchingRules,
            fuzzyMatch,
            fuzzyMatchThreshold
        );

        // Update reconciliation record with results
        await updateReconciliationRecord(
            reconciliationId,
            'COMPLETED',
            matchResults.stats
        );

        return {
            statusCode: 200,
            body: JSON.stringify({
                message: 'Reconciliation completed successfully',
                reconciliationId,
                stats: matchResults.stats
            })
        };
    } catch (error) {
        console.error('Error during reconciliation:', error);

        // If we have a reconciliation ID, update its status to ERROR
        if (event.reconciliationId) {
            await updateReconciliationRecord(
                event.reconciliationId,
                'ERROR',
                null,
                error.message
            );
        }

        return {
            statusCode: 500,
            body: JSON.stringify({
                message: 'Error during reconciliation',
                error: error.message
            })
        };
    }
};

/**
 * Get trades by document ID
 */
async function getTradesByDocumentId(tableName, documentId) {
    const params = {
        TableName: tableName,
        IndexName: 'DocumentIdIndex',
        KeyConditionExpression: 'documentId = :documentId',
        ExpressionAttributeValues: {
            ':documentId': documentId
        }
    };

    const result = await dynamoDB.query(params).promise();
    return result.Items;
}

/**
 * Create reconciliation record
 */
async function createReconciliationRecord(reconciliationId, userId, sourceDocumentId, targetDocumentId, status) {
    const timestamp = new Date().toISOString();
    
    const params = {
        TableName: RECONCILIATION_TABLE,
        Item: {
            id: reconciliationId,
            userId: userId || 'anonymous',
            sourceDocumentId,
            targetDocumentId,
            status,
            createdAt: timestamp,
            updatedAt: timestamp,
            stats: {
                sourceTradeCount: 0,
                targetTradeCount: 0,
                matchedCount: 0,
                unmatchedSourceCount: 0,
                unmatchedTargetCount: 0
            }
        }
    };

    await dynamoDB.put(params).promise();
}

/**
 * Update reconciliation record
 */
async function updateReconciliationRecord(reconciliationId, status, stats = null, errorMessage = null) {
    let updateExpression = 'SET #status = :status, updatedAt = :updatedAt';
    let expressionAttributeNames = {
        '#status': 'status'
    };
    let expressionAttributeValues = {
        ':status': status,
        ':updatedAt': new Date().toISOString()
    };

    // Add stats if provided
    if (stats) {
        updateExpression += ', stats = :stats';
        expressionAttributeValues[':stats'] = stats;
    }

    // Add error message if present
    if (errorMessage) {
        updateExpression += ', errorMessage = :errorMessage';
        expressionAttributeValues[':errorMessage'] = errorMessage;
    }

    const params = {
        TableName: RECONCILIATION_TABLE,
        Key: {
            id: reconciliationId
        },
        UpdateExpression: updateExpression,
        ExpressionAttributeNames: expressionAttributeNames,
        ExpressionAttributeValues: expressionAttributeValues
    };

    await dynamoDB.update(params).promise();
}

/**
 * Perform reconciliation between source and target trades
 */
async function performReconciliation(
    reconciliationId,
    sourceTrades,
    targetTrades,
    matchingRules,
    fuzzyMatch,
    fuzzyMatchThreshold
) {
    // Create a copy of target trades to track which ones are matched
    const remainingTargetTrades = [...targetTrades];
    const matches = [];
    const unmatchedSourceTrades = [];

    // For each source trade, find a matching target trade
    for (const sourceTrade of sourceTrades) {
        let matched = false;
        
        // Compare source trade against all remaining target trades
        for (let i = 0; i < remainingTargetTrades.length; i++) {
            const targetTrade = remainingTargetTrades[i];
            
            // Check if trades match based on matching rules
            if (tradesMatch(sourceTrade, targetTrade, matchingRules, fuzzyMatch, fuzzyMatchThreshold)) {
                // Create a match record
                const matchId = `${reconciliationId}-${sourceTrade.id}-${targetTrade.id}`;
                const match = {
                    id: matchId,
                    reconciliationId,
                    sourceTradeId: sourceTrade.id,
                    targetTradeId: targetTrade.id,
                    matchedFields: getMatchedFields(sourceTrade, targetTrade, matchingRules),
                    unmatchedFields: getUnmatchedFields(sourceTrade, targetTrade, matchingRules),
                    status: 'MATCHED',
                    createdAt: new Date().toISOString()
                };
                
                matches.push(match);
                
                // Remove the matched target trade from remaining trades
                remainingTargetTrades.splice(i, 1);
                matched = true;
                break;
            }
        }
        
        // If source trade didn't match any target trade
        if (!matched) {
            unmatchedSourceTrades.push(sourceTrade);
        }
    }

    // Save matches to DynamoDB
    await saveMatches(matches);

    // Create records for unmatched trades
    const unmatchedRecords = [
        ...unmatchedSourceTrades.map(trade => ({
            id: `${reconciliationId}-${trade.id}-unmatched`,
            reconciliationId,
            sourceTradeId: trade.id,
            targetTradeId: null,
            status: 'UNMATCHED_SOURCE',
            createdAt: new Date().toISOString()
        })),
        ...remainingTargetTrades.map(trade => ({
            id: `${reconciliationId}-unmatched-${trade.id}`,
            reconciliationId,
            sourceTradeId: null,
            targetTradeId: trade.id,
            status: 'UNMATCHED_TARGET',
            createdAt: new Date().toISOString()
        }))
    ];

    // Save unmatched records to DynamoDB
    await saveMatches(unmatchedRecords);

    // Calculate statistics
    const stats = {
        sourceTradeCount: sourceTrades.length,
        targetTradeCount: targetTrades.length,
        matchedCount: matches.length,
        unmatchedSourceCount: unmatchedSourceTrades.length,
        unmatchedTargetCount: remainingTargetTrades.length
    };

    return {
        matches,
        unmatchedSourceTrades,
        unmatchedTargetTrades: remainingTargetTrades,
        stats
    };
}

/**
 * Check if trades match based on matching rules
 */
function tradesMatch(sourceTrade, targetTrade, matchingRules, fuzzyMatch, fuzzyMatchThreshold) {
    return matchingRules.every(field => {
        if (!sourceTrade[field] || !targetTrade[field]) {
            return false;
        }

        if (fuzzyMatch && typeof sourceTrade[field] === 'string' && typeof targetTrade[field] === 'string') {
            return calculateSimilarity(sourceTrade[field], targetTrade[field]) >= fuzzyMatchThreshold;
        }

        return sourceTrade[field] === targetTrade[field];
    });
}

/**
 * Get fields that match between source and target trades
 */
function getMatchedFields(sourceTrade, targetTrade, matchingRules) {
    return matchingRules.filter(field => 
        sourceTrade[field] && targetTrade[field] && sourceTrade[field] === targetTrade[field]
    );
}

/**
 * Get fields that don't match between source and target trades
 */
function getUnmatchedFields(sourceTrade, targetTrade, matchingRules) {
    return matchingRules.filter(field => 
        !sourceTrade[field] || !targetTrade[field] || sourceTrade[field] !== targetTrade[field]
    );
}

/**
 * Calculate string similarity using Levenshtein distance
 */
function calculateSimilarity(str1, str2) {
    const track = Array(str2.length + 1).fill(null).map(() => 
        Array(str1.length + 1).fill(null));
    
    for (let i = 0; i <= str1.length; i += 1) {
        track[0][i] = i;
    }
    
    for (let j = 0; j <= str2.length; j += 1) {
        track[j][0] = j;
    }
    
    for (let j = 1; j <= str2.length; j += 1) {
        for (let i = 1; i <= str1.length; i += 1) {
            const indicator = str1[i - 1] === str2[j - 1] ? 0 : 1;
            track[j][i] = Math.min(
                track[j][i - 1] + 1, // deletion
                track[j - 1][i] + 1, // insertion
                track[j - 1][i - 1] + indicator, // substitution
            );
        }
    }
    
    const distance = track[str2.length][str1.length];
    const maxLength = Math.max(str1.length, str2.length);
    return maxLength > 0 ? 1 - distance / maxLength : 1;
}

/**
 * Save matches to DynamoDB
 */
async function saveMatches(matches) {
    if (!matches || matches.length === 0) {
        return;
    }

    // Process in batches of 25 (DynamoDB batch write limit)
    const batchSize = 25;
    const batches = [];

    for (let i = 0; i < matches.length; i += batchSize) {
        const batch = matches.slice(i, i + batchSize);
        
        // Create batch request
        const batchRequest = {
            RequestItems: {
                [MATCH_TABLE]: batch.map(match => ({
                    PutRequest: {
                        Item: match
                    }
                }))
            }
        };

        batches.push(dynamoDB.batchWrite(batchRequest).promise());
    }

    // Execute all batches in parallel
    await Promise.all(batches);
}
