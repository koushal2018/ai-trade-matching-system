# Trade Reconciliation System - User Guide

This guide provides instructions for using the Trade Reconciliation System after it has been deployed and configured.

## Overview

The Trade Reconciliation System automates the process of comparing and matching trades between bank records and counterparty records. It helps identify discrepancies and ensures that all trades are properly reconciled.

## Accessing the System

Access the Trade Reconciliation System through your web browser:

```
http://your-frontend-bucket.s3-website-us-west-2.amazonaws.com
```

Or if using CloudFront:

```
https://your-cloudfront-distribution.cloudfront.net
```

## User Interface

The user interface consists of the following main sections:

1. **Dashboard**: Overview of reconciliation status and metrics
2. **Trades**: View and manage bank and counterparty trades
3. **Documents**: Upload and manage trade documents
4. **Reconciliations**: View and initiate reconciliation processes
5. **Reports**: Generate and download reconciliation reports
6. **Settings**: Configure system settings

## Working with Trades

### Viewing Trades

1. Navigate to the **Trades** section
2. Select either **Bank Trades** or **Counterparty Trades**
3. Use the filters to narrow down the list of trades
4. Click on a trade to view its details

### Uploading Trade Documents

1. Navigate to the **Documents** section
2. Click **Upload Document**
3. Select the document type (Bank or Counterparty)
4. Choose the file to upload (CSV or Excel format)
5. Click **Upload**

The system will automatically process the document and extract trade data.

### Document Format Requirements

Bank and counterparty documents should be in CSV or Excel format with the following columns:

- **tradeId**: Unique identifier for the trade
- **amount**: Trade amount
- **currency**: Currency code (USD, EUR, etc.)
- **valueDate**: Settlement date (YYYY-MM-DD)
- **counterparty**: Name of the counterparty

Example CSV format:
```csv
tradeId,amount,currency,valueDate,counterparty
T001,10000,USD,2025-07-20,ACME Corp
T002,15000,EUR,2025-07-21,XYZ Ltd
```

## Reconciliation Process

### Initiating a Reconciliation

1. Navigate to the **Reconciliations** section
2. Click **New Reconciliation**
3. Select the date range for the reconciliation
4. Choose the reconciliation criteria (e.g., match by tradeId, amount, and currency)
5. Click **Start Reconciliation**

### Viewing Reconciliation Results

1. Navigate to the **Reconciliations** section
2. Select a reconciliation from the list
3. View the summary of matched and unmatched trades
4. Click on **Matched Trades** or **Unmatched Trades** to see details

### Resolving Discrepancies

For unmatched trades:

1. Review the details of the unmatched trade
2. Compare with potential matches
3. Select a trade to match manually if appropriate
4. Add comments to explain the manual match
5. Click **Save** to update the reconciliation

## Generating Reports

1. Navigate to the **Reports** section
2. Select the report type:
   - Reconciliation Summary
   - Matched Trades
   - Unmatched Trades
   - Exceptions Report
3. Choose the date range and other filters
4. Click **Generate Report**
5. Download the report in CSV or PDF format

## System Administration

### Managing Users

Administrators can manage users through the AWS Cognito console:

1. Log in to the AWS Management Console
2. Navigate to Amazon Cognito
3. Select the user pool for the Trade Reconciliation System
4. Add, edit, or remove users as needed

### Configuring System Settings

1. Navigate to the **Settings** section
2. Configure the following settings:
   - Matching criteria
   - Notification preferences
   - Report formats
   - Default filters
3. Click **Save Changes**

## Best Practices

1. **Regular Reconciliations**: Perform reconciliations daily to identify discrepancies early
2. **Consistent Document Formats**: Ensure that all trade documents follow the required format
3. **Review Unmatched Trades**: Regularly review and resolve unmatched trades
4. **Document Resolutions**: Add comments when manually matching trades to explain the decision
5. **Generate Reports**: Create and archive reconciliation reports for audit purposes

## Troubleshooting

### Common Issues

1. **Document Upload Fails**:
   - Verify that the document is in the correct format (CSV or Excel)
   - Check that the document contains all required columns
   - Ensure the file size is within limits

2. **Trades Not Appearing**:
   - Check that the document was successfully processed
   - Verify that the trades are within the selected date range
   - Clear filters that might be hiding the trades

3. **Reconciliation Process Slow**:
   - Large volumes of trades may take longer to process
   - Consider narrowing the date range for faster processing
   - Check system metrics for any performance issues

### Getting Help

If you encounter issues that you cannot resolve:

1. Check the **Troubleshooting Guide** for common solutions
2. Contact your system administrator for assistance
3. Refer to the API documentation for advanced integrations

## Security Considerations

1. **Access Control**: Only share access with authorized personnel
2. **Data Protection**: Treat trade data as confidential information
3. **Audit Trail**: All actions in the system are logged for audit purposes
4. **Secure Connections**: Always use HTTPS when accessing the system

## Glossary

- **Trade**: A financial transaction between two parties
- **Reconciliation**: The process of comparing and matching trades
- **Match**: A pair of bank and counterparty trades that correspond to the same transaction
- **Discrepancy**: A difference between bank and counterparty records for the same trade
- **Exception**: A trade that requires manual review due to discrepancies