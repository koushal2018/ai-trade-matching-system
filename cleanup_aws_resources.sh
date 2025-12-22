#!/bin/bash

# Clean up S3 bucket contents (keep folders)
echo "Cleaning S3 bucket contents..."

# Delete only files, not folders - exclude directories by filtering out keys ending with '/'
aws s3api list-objects-v2 --bucket trade-matching-system-agentcore-production --prefix "BANK/" --query "Contents[?!ends_with(Key, '/')].Key" --output text | tr '\t' '\n' | while read -r key; do
    [ -n "$key" ] && aws s3 rm "s3://trade-matching-system-agentcore-production/$key"
done

aws s3api list-objects-v2 --bucket trade-matching-system-agentcore-production --prefix "COUNTERPARTY/" --query "Contents[?!ends_with(Key, '/')].Key" --output text | tr '\t' '\n' | while read -r key; do
    [ -n "$key" ] && aws s3 rm "s3://trade-matching-system-agentcore-production/$key"
done

aws s3api list-objects-v2 --bucket trade-matching-system-agentcore-production --prefix "extracted/" --query "Contents[?!ends_with(Key, '/')].Key" --output text | tr '\t' '\n' | while read -r key; do
    [ -n "$key" ] && aws s3 rm "s3://trade-matching-system-agentcore-production/$key"
done

aws s3api list-objects-v2 --bucket trade-matching-system-agentcore-production --prefix "reports/" --query "Contents[?!ends_with(Key, '/')].Key" --output text | tr '\t' '\n' | while read -r key; do
    [ -n "$key" ] && aws s3 rm "s3://trade-matching-system-agentcore-production/$key"
done

echo "S3 cleanup complete."

# Clean up DynamoDB table contents (keep tables)
echo "Cleaning DynamoDB table contents..."

# Simple approach: Use AWS CLI to delete items one by one
# BankTradeData table
echo "Deleting items from BankTradeData..."
aws dynamodb scan --table-name BankTradeData --select "ALL_ATTRIBUTES" --output json > /tmp/bank_items.json
if [ -s /tmp/bank_items.json ]; then
    grep -o '"trade_id":{"S":"[^"]*"}' /tmp/bank_items.json | sed 's/"trade_id":{"S":"//' | sed 's/"}//' > /tmp/bank_trade_ids.txt
    grep -o '"internal_reference":{"S":"[^"]*"}' /tmp/bank_items.json | sed 's/"internal_reference":{"S":"//' | sed 's/"}//' > /tmp/bank_refs.txt
    paste /tmp/bank_trade_ids.txt /tmp/bank_refs.txt | while IFS=$'\t' read -r trade_id internal_ref; do
        if [ ! -z "$trade_id" ] && [ ! -z "$internal_ref" ]; then
            aws dynamodb delete-item --table-name BankTradeData --key '{"trade_id":{"S":"'$trade_id'"},"internal_reference":{"S":"'$internal_ref'"}}' >/dev/null 2>&1
            echo "Deleted: $trade_id"
        fi
    done
fi

# CounterpartyTradeData table
echo "Deleting items from CounterpartyTradeData..."
aws dynamodb scan --table-name CounterpartyTradeData --select "ALL_ATTRIBUTES" --output json > /tmp/cp_items.json
if [ -s /tmp/cp_items.json ]; then
    grep -o '"trade_id":{"S":"[^"]*"}' /tmp/cp_items.json | sed 's/"trade_id":{"S":"//' | sed 's/"}//' > /tmp/cp_trade_ids.txt
    grep -o '"internal_reference":{"S":"[^"]*"}' /tmp/cp_items.json | sed 's/"internal_reference":{"S":"//' | sed 's/"}//' > /tmp/cp_refs.txt
    paste /tmp/cp_trade_ids.txt /tmp/cp_refs.txt | while IFS=$'\t' read -r trade_id internal_ref; do
        if [ ! -z "$trade_id" ] && [ ! -z "$internal_ref" ]; then
            aws dynamodb delete-item --table-name CounterpartyTradeData --key '{"trade_id":{"S":"'$trade_id'"},"internal_reference":{"S":"'$internal_ref'"}}' >/dev/null 2>&1
            echo "Deleted: $trade_id"
        fi
    done
fi

# Exceptions table
echo "Deleting items from trade-matching-system-exceptions-production..."
aws dynamodb scan --table-name trade-matching-system-exceptions-production --select "ALL_ATTRIBUTES" --output json > /tmp/exc_items.json
if [ -s /tmp/exc_items.json ]; then
    grep -o '"exception_id":{"S":"[^"]*"}' /tmp/exc_items.json | sed 's/"exception_id":{"S":"//' | sed 's/"}//' > /tmp/exc_ids.txt
    grep -o '"timestamp":{"S":"[^"]*"}' /tmp/exc_items.json | sed 's/"timestamp":{"S":"//' | sed 's/"}//' > /tmp/exc_timestamps.txt
    paste /tmp/exc_ids.txt /tmp/exc_timestamps.txt | while IFS=$'\t' read -r exc_id timestamp; do
        if [ ! -z "$exc_id" ] && [ ! -z "$timestamp" ]; then
            aws dynamodb delete-item --table-name trade-matching-system-exceptions-production --key '{"exception_id":{"S":"'$exc_id'"},"timestamp":{"S":"'$timestamp'"}}' >/dev/null 2>&1
            echo "Deleted: $exc_id"
        fi
    done
fi

# Clean up temp files
rm -f /tmp/bank_items.json /tmp/bank_trade_ids.txt /tmp/bank_refs.txt
rm -f /tmp/cp_items.json /tmp/cp_trade_ids.txt /tmp/cp_refs.txt
rm -f /tmp/exc_items.json /tmp/exc_ids.txt /tmp/exc_timestamps.txt

echo "DynamoDB cleanup complete."
echo "All resources cleaned successfully!"