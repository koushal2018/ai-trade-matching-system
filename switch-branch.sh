#!/bin/bash

# Branch switching helper script

case "$1" in
    "local"|"main")
        echo "🏠 Switching to local development (main branch)..."
        git checkout main
        ;;
    "dev"|"develop")
        echo "🔧 Switching to development branch..."
        git checkout develop
        ;;
    "aws"|"aws-native")
        echo "☁️ Switching to AWS native services..."
        git checkout aws-native
        ;;
    "ml"|"sagemaker")
        echo "🤖 Switching to SageMaker ML hosting..."
        git checkout sagemaker
        ;;
    "agents"|"aws-agentcore")
        echo "🎯 Switching to Bedrock Agents..."
        git checkout aws-agentcore
        ;;
    "list"|"ls")
        echo "📋 Available branches:"
        git branch
        ;;
    *)
        echo "Usage: ./switch-branch.sh [local|dev|aws|ml|agents|list]"
        echo ""
        echo "Branches:"
        echo "  local/main     - Local development with TinyDB"
        echo "  dev/develop    - Development/testing"
        echo "  aws/aws-native - Full AWS services"
        echo "  ml/sagemaker   - SageMaker ML hosting"
        echo "  agents/aws-agentcore - Bedrock Agents"
        echo "  list/ls        - Show all branches"
        ;;
esac