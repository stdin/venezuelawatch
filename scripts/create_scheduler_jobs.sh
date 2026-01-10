#!/bin/bash
# Create Cloud Scheduler jobs for all ingestion functions
# Run from project root: ./scripts/create_scheduler_jobs.sh

set -e  # Exit on error

PROJECT_ID="venezuelawatch-447923"
REGION="us-central1"
SCHEDULER_SA="scheduler@${PROJECT_ID}.iam.gserviceaccount.com"

echo "======================================"
echo "Creating Cloud Scheduler Jobs"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "======================================"
echo

# Function to create scheduler job
create_job() {
    local name=$1
    local schedule=$2
    local function_name=$3
    local body=$4

    echo "Creating scheduler job: $name"
    echo "  Schedule: $schedule"
    echo "  Target: $function_name"

    gcloud scheduler jobs create http "$name" \
        --location "$REGION" \
        --schedule "$schedule" \
        --uri "https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${function_name}" \
        --http-method POST \
        --headers "Content-Type=application/json" \
        --message-body "$body" \
        --oidc-service-account-email "$SCHEDULER_SA" \
        --oidc-token-audience "https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${function_name}" \
        --quiet || echo "  (Job may already exist - use 'gcloud scheduler jobs update http' to modify)"

    echo "✓ $name created"
    echo
}

# GDELT: Every 15 minutes
create_job \
    "gdelt-sync-job" \
    "*/15 * * * *" \
    "gdelt-sync" \
    '{"lookback_minutes": 15}'

# ReliefWeb: Daily at 00:00 UTC
create_job \
    "reliefweb-sync-job" \
    "0 0 * * *" \
    "reliefweb-sync" \
    '{"lookback_days": 1}'

# FRED: Daily at 01:00 UTC
create_job \
    "fred-sync-job" \
    "0 1 * * *" \
    "fred-sync" \
    '{"lookback_days": 7}'

# Comtrade: Monthly on 1st at 02:00 UTC
create_job \
    "comtrade-sync-job" \
    "0 2 1 * *" \
    "comtrade-sync" \
    '{"lookback_months": 3}'

# World Bank: Quarterly on 1st of Jan/Apr/Jul/Oct at 03:00 UTC
create_job \
    "worldbank-sync-job" \
    "0 3 1 1,4,7,10 *" \
    "worldbank-sync" \
    '{"lookback_years": 2}'

# Sanctions: Daily at 04:00 UTC (match current Celery schedule)
create_job \
    "sanctions-sync-job" \
    "0 4 * * *" \
    "sanctions-sync" \
    '{"lookback_days": 7}'

echo "======================================"
echo "All scheduler jobs created successfully!"
echo "======================================"
echo
echo "Verify jobs:"
echo "  gcloud scheduler jobs list --location $REGION"
echo
echo "Test a job manually:"
echo "  gcloud scheduler jobs run gdelt-sync-job --location $REGION"
echo
echo "View job logs:"
echo "  gcloud scheduler jobs describe gdelt-sync-job --location $REGION"
