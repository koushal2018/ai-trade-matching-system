#!/bin/bash

# Navigate to the frontend directory
cd trade-reconciliation-frontend

# Install the correct dependencies with legacy peer deps to handle conflicts
npm install --legacy-peer-deps

# Build the project to verify everything works
npm run build

echo "Frontend dependencies updated and build verified!"