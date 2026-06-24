#!/bin/bash
# deploy.sh — builds and deploys the MCP server to Cloud Run
# Usage: bash deploy.sh

set -e  # stop on any error

PROJECT_ID="wohlig"
SERVICE_NAME="bootcamp-mcp-server"
REGION="us-central1"
IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "==> Building and pushing Docker image..."
gcloud builds submit --tag "$IMAGE" .

echo "==> Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --timeout 60 \
  --set-env-vars "PROJECT_ID=$PROJECT_ID,API_KEY=wohlig-mcp-key-2024"

echo ""
echo "==> Done! Service URL:"
gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" \
  --format "value(status.url)"
