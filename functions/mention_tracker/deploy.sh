#!/bin/bash
# Deploy mention_tracker Cloud Function
# Run from this directory: ./deploy.sh

set -e  # Exit on error

PROJECT_ID="venezuelawatch-447923"
REGION="us-central1"
FUNCTION_NAME="mention-tracker"
ENTRY_POINT="mention_tracker"
SERVICE_ACCOUNT="ingestion-runner@${PROJECT_ID}.iam.gserviceaccount.com"

echo "======================================"
echo "Deploying Mention Tracker Cloud Function"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "======================================"
echo

gcloud functions deploy "$FUNCTION_NAME" \
    --gen2 \
    --runtime python311 \
    --region "$REGION" \
    --source . \
    --entry-point "$ENTRY_POINT" \
    --trigger-http \
    --no-allow-unauthenticated \
    --memory 512MB \
    --timeout 540s \
    --max-instances 10 \
    --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID}" \
    --set-secrets "DB_HOST=projects/${PROJECT_ID}/secrets/DB_HOST:latest,\
DB_PORT=projects/${PROJECT_ID}/secrets/DB_PORT:latest,\
DB_NAME=projects/${PROJECT_ID}/secrets/DB_NAME:latest,\
DB_USER=projects/${PROJECT_ID}/secrets/DB_USER:latest,\
DB_PASSWORD=projects/${PROJECT_ID}/secrets/DB_PASSWORD:latest" \
    --service-account "$SERVICE_ACCOUNT" \
    --quiet

echo
echo "======================================"
echo "✓ Mention Tracker deployed successfully!"
echo "======================================"
echo
echo "Function URL:"
echo "  https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}"
echo
echo "Next steps:"
echo "1. Update Cloud Scheduler jobs: Run updated create_scheduler_jobs.sh"
echo "2. Test function manually:"
echo "   gcloud functions call ${FUNCTION_NAME} --region ${REGION} --gen2"
echo "3. View logs:"
echo "   gcloud functions logs read ${FUNCTION_NAME} --region ${REGION} --gen2"
