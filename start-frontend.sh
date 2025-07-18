#!/bin/bash

# Navigate to the frontend directory and start the development server
cd trade-reconciliation-frontend

# Set environment variables for the API
export REACT_APP_API_ENDPOINT=https://mdj9ch24qg.execute-api.us-east-1.amazonaws.com/dev
export REACT_APP_REGION=us-east-1
export REACT_APP_DEBUG=true
export REACT_APP_S3_BUCKET=fab-otc-reconciliation-deployment

# Start the development server
BROWSER=none npm start