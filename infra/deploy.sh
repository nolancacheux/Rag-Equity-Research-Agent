#!/bin/bash
set -e

# Azure deployment script for Equity Research Agent

RESOURCE_GROUP="${RESOURCE_GROUP:-equity-research-rg}"
LOCATION="${LOCATION:-westeurope}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo "🚀 Deploying Equity Research Agent to Azure..."
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Location: $LOCATION"
echo "   Environment: $ENVIRONMENT"

# Check required env vars
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY is required"
    exit 1
fi

# Login check
az account show > /dev/null 2>&1 || {
    echo "Please login to Azure: az login"
    exit 1
}

# Create resource group
echo "📦 Creating resource group..."
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output none

# Deploy Bicep
echo "🏗️  Deploying infrastructure..."
az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file infra/main.bicep \
    --parameters \
        environmentName="$ENVIRONMENT" \
        imageTag="$IMAGE_TAG" \
        openaiApiKey="$OPENAI_API_KEY" \
        langsmithApiKey="${LANGSMITH_API_KEY:-}" \
    --output none

# Get outputs
APP_URL=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name main \
    --query properties.outputs.appUrl.value \
    --output tsv)

REGISTRY=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name main \
    --query properties.outputs.containerRegistryLoginServer.value \
    --output tsv)

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Build and push Docker image:"
echo "      az acr login --name ${REGISTRY%%.*}"
echo "      docker build -t $REGISTRY/equity-research-agent:$IMAGE_TAG ."
echo "      docker push $REGISTRY/equity-research-agent:$IMAGE_TAG"
echo ""
echo "   2. Access your app at: $APP_URL"
echo ""
