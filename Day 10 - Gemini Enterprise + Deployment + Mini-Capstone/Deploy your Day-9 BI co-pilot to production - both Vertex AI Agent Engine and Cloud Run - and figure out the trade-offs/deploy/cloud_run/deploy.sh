#!/bin/bash
# deploy/cloud_run/deploy.sh
# ----------------------------
# Builds the BI Co-Pilot Docker image and deploys to Cloud Run.
#
# Run from the deploy/cloud_run/ directory:
#   chmod +x deploy.sh
#   ./deploy.sh

set -e

PROJECT="wohlig"
REGION="us-central1"
SERVICE="bi-copilot"
IMAGE="gcr.io/${PROJECT}/${SERVICE}"

DAY9_PATH="../../../../Day 9 - ADK Multi-Agent (BI Co-Pilot , Doc Governance Pattern/Build a multi-agent BI co-pilot - the same pattern as the Jindal Leadership Co-Pilot"

echo "=== BI Co-Pilot — Cloud Run Deployment ==="
echo "Project : $PROJECT"
echo "Region  : $REGION"
echo "Image   : $IMAGE"
echo ""

# Step 1 — Copy bi_copilot package into the build context
echo "[1/4] Copying bi_copilot package..."
cp -r "${DAY9_PATH}/bi_copilot" ./bi_copilot
cp "${DAY9_PATH}/.env" ./.env

# Step 2 — Build and push Docker image
echo "[2/4] Building Docker image..."
gcloud builds submit \
    --tag "$IMAGE" \
    --project "$PROJECT" \
    .

# Step 3 — Deploy to Cloud Run
echo "[3/4] Deploying to Cloud Run..."
gcloud run deploy "$SERVICE" \
    --image "$IMAGE" \
    --platform managed \
    --region "$REGION" \
    --project "$PROJECT" \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT},GOOGLE_CLOUD_LOCATION=${REGION}"

# Step 4 — Print the live URL
echo "[4/4] Done."
SERVICE_URL=$(gcloud run services describe "$SERVICE" \
    --platform managed \
    --region "$REGION" \
    --project "$PROJECT" \
    --format "value(status.url)")

echo ""
echo "=== Deployment complete ==="
echo "Live URL: ${SERVICE_URL}"
echo ""
echo "Test with:"
echo "  curl -X POST ${SERVICE_URL}/query \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"question\": \"How many trips last month?\"}'"

# Cleanup copied files
rm -rf ./bi_copilot ./.env
