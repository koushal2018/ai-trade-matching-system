# Storage Directory

This directory contains TinyDB database files for local trade data storage.

## Database Files

The system creates the following TinyDB files:
- `bank_trade_data.db` - Bank trade confirmations
- `counterparty_trade_data.db` - Counterparty trade confirmations  
- `matching_results.db` - Trade matching results

## Notes

- Database files are created automatically when the system runs
- Files are excluded from version control via `.gitignore`
- For production use, consider migrating to AWS DynamoDB or other enterprise databases