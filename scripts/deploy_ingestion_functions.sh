#!/bin/bash
# Deploy all Cloud Functions for data ingestion
# Run from project root: ./scripts/deploy_ingestion_functions.sh

set -e  # Exit on error

PROJECT_ID="venezuelawatch-447923"
REGION="us-central1"
DATASET="venezuelawatch_analytics"
SERVICE_ACCOUNT="ingestion-runner@${PROJECT_ID}.iam.gserviceaccount.com"

echo "======================================"
echo "Deploying VenezuelaWatch Cloud Functions"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "======================================"
echo

# Function to deploy with common settings
deploy_function() {
    local name=$1
    local source_dir=$2
    local entry_point=$3
    local timeout=$4
    local memory=$5

    echo "Deploying $name..."
    gcloud functions deploy "$name" \
        --gen2 \
        --runtime python311 \
        --region "$REGION" \
        --source "$source_dir" \
        --entry-point "$entry_point" \
        --trigger-http \
        --no-allow-unauthenticated \
        --timeout "${timeout}s" \
        --memory "$memory" \
        --max-instances 10 \
        --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},BIGQUERY_DATASET=${DATASET}" \
        --service-account "$SERVICE_ACCOUNT" \
        --quiet

    echo "✓ $name deployed successfully"
    echo
}

# Deploy GDELT sync (every 15 minutes)
deploy_function \
    "gdelt-sync" \
    "functions/gdelt_sync" \
    "sync_gdelt_events" \
    540 \
    "512MB"

# Deploy ReliefWeb sync (daily)
deploy_function \
    "reliefweb-sync" \
    "functions/reliefweb" \
    "sync_reliefweb" \
    540 \
    "512MB"

# Deploy FRED sync (daily)
deploy_function \
    "fred-sync" \
    "functions/fred" \
    "sync_fred" \
    540 \
    "512MB"

# Deploy Comtrade sync (monthly)
deploy_function \
    "comtrade-sync" \
    "functions/comtrade" \
    "sync_comtrade" \
    900 \
    "512MB"

# Deploy World Bank sync (quarterly)
deploy_function \
    "worldbank-sync" \
    "functions/worldbank" \
    "sync_worldbank" \
    900 \
    "512MB"

# Deploy Sanctions sync (daily)
deploy_function \
    "sanctions-sync" \
    "functions/sanctions" \
    "sync_sanctions" \
    540 \
    "512MB"

# Deploy Mention Tracker (daily)
deploy_function \
    "mention-tracker" \
    "functions/mention_tracker" \
    "mention_tracker" \
    540 \
    "512MB"

echo "======================================"
echo "All functions deployed successfully!"
echo "======================================"
echo
echo "Next steps:"
echo "1. Create Cloud Scheduler jobs: ./scripts/create_scheduler_jobs.sh"
echo "2. Verify functions: gcloud functions list --gen2 --region $REGION"
echo "3. Check logs: gcloud functions logs read <function-name> --gen2 --region $REGION"
