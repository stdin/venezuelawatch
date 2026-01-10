#!/bin/bash
#
# Setup GCP-Native Processing Infrastructure
# Creates Pub/Sub topics, subscriptions, Cloud Tasks queues, and IAM permissions
#
# Usage: ./scripts/setup_processing_infrastructure.sh
#
# Prerequisites:
# - gcloud CLI authenticated
# - Project: venezuelawatch-447923
# - Region: us-central1
#
# Note: This script creates GCP resources but does NOT execute automatically.
# Review and run manually when ready to deploy infrastructure.

set -e

PROJECT_ID="venezuelawatch-447923"
REGION="us-central1"

# Cloud Run service URL (will be filled in during actual deployment)
# TODO: Replace XXXXX with actual Cloud Run service URL after deployment
CLOUD_RUN_URL="https://venezuelawatch-api-XXXXX-uc.a.run.app"

echo "========================================="
echo "Setting up GCP-Native Processing Infrastructure"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "========================================="

# =====================================
# 1. Create Pub/Sub Topics
# =====================================

echo ""
echo "[1/6] Creating Pub/Sub topics..."

# Topic for event analysis triggers (published by ingestion functions)
gcloud pubsub topics create event-analysis \
  --project $PROJECT_ID \
  --quiet || echo "Topic 'event-analysis' already exists"

# Topic for entity extraction (published after intelligence analysis)
gcloud pubsub topics create entity-extraction \
  --project $PROJECT_ID \
  --quiet || echo "Topic 'entity-extraction' already exists"

echo "✓ Pub/Sub topics created"

# =====================================
# 2. Create Pub/Sub Push Subscriptions
# =====================================

echo ""
echo "[2/6] Creating Pub/Sub push subscriptions..."

# Push subscription to Cloud Run handler endpoint for event analysis
gcloud pubsub subscriptions create event-analysis-sub \
  --topic event-analysis \
  --push-endpoint ${CLOUD_RUN_URL}/api/internal/process-event \
  --push-auth-service-account pubsub-invoker@${PROJECT_ID}.iam.gserviceaccount.com \
  --ack-deadline 600 \
  --message-retention-duration 7d \
  --max-delivery-attempts 5 \
  --project $PROJECT_ID \
  --quiet || echo "Subscription 'event-analysis-sub' already exists"

# Push subscription for entity extraction
gcloud pubsub subscriptions create entity-extraction-sub \
  --topic entity-extraction \
  --push-endpoint ${CLOUD_RUN_URL}/api/internal/extract-entities \
  --push-auth-service-account pubsub-invoker@${PROJECT_ID}.iam.gserviceaccount.com \
  --ack-deadline 300 \
  --message-retention-duration 7d \
  --max-delivery-attempts 5 \
  --project $PROJECT_ID \
  --quiet || echo "Subscription 'entity-extraction-sub' already exists"

echo "✓ Pub/Sub subscriptions created"

# =====================================
# 3. Create Cloud Tasks Queues
# =====================================

echo ""
echo "[3/6] Creating Cloud Tasks queues..."

# Queue for LLM intelligence analysis (handles retries, rate limiting)
gcloud tasks queues create intelligence-analysis \
  --location $REGION \
  --max-concurrent-dispatches 10 \
  --max-dispatches-per-second 5 \
  --max-attempts 3 \
  --min-backoff 60s \
  --max-backoff 3600s \
  --project $PROJECT_ID \
  --quiet || echo "Queue 'intelligence-analysis' already exists"

# Queue for entity extraction
gcloud tasks queues create entity-extraction \
  --location $REGION \
  --max-concurrent-dispatches 20 \
  --max-dispatches-per-second 10 \
  --max-attempts 3 \
  --min-backoff 30s \
  --max-backoff 1800s \
  --project $PROJECT_ID \
  --quiet || echo "Queue 'entity-extraction' already exists"

echo "✓ Cloud Tasks queues created"

# =====================================
# 4. Grant IAM Permissions
# =====================================

echo ""
echo "[4/6] Granting IAM permissions..."

# Grant Pub/Sub publisher role to ingestion functions service account
gcloud pubsub topics add-iam-policy-binding event-analysis \
  --member serviceAccount:ingestion-runner@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/pubsub.publisher \
  --project $PROJECT_ID \
  --quiet || echo "IAM binding already exists"

# Grant Cloud Tasks enqueuer role to Cloud Run service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member serviceAccount:cloudrun-tasks@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/cloudtasks.enqueuer \
  --quiet || echo "IAM binding already exists"

# Grant Cloud Run invoker role to Pub/Sub service account
# Note: This requires the Cloud Run service to exist first
# This command will be run after Cloud Run deployment
echo "Note: Cloud Run invoker role must be granted after service deployment:"
echo "  gcloud run services add-iam-policy-binding venezuelawatch-api \\"
echo "    --region $REGION \\"
echo "    --member serviceAccount:pubsub-invoker@${PROJECT_ID}.iam.gserviceaccount.com \\"
echo "    --role roles/run.invoker"

echo "✓ IAM permissions granted"

# =====================================
# 5. Verify Infrastructure
# =====================================

echo ""
echo "[5/6] Verifying infrastructure..."

echo "Pub/Sub topics:"
gcloud pubsub topics list --project $PROJECT_ID | grep -E "(event-analysis|entity-extraction)" || echo "No topics found"

echo ""
echo "Pub/Sub subscriptions:"
gcloud pubsub subscriptions list --project $PROJECT_ID | grep -E "(event-analysis-sub|entity-extraction-sub)" || echo "No subscriptions found"

echo ""
echo "Cloud Tasks queues:"
gcloud tasks queues list --location $REGION --project $PROJECT_ID | grep -E "(intelligence-analysis|entity-extraction)" || echo "No queues found"

echo "✓ Verification complete"

# =====================================
# 6. Test Publishing (Optional)
# =====================================

echo ""
echo "[6/6] Infrastructure setup complete!"
echo ""
echo "========================================="
echo "NEXT STEPS:"
echo "========================================="
echo ""
echo "1. Deploy Cloud Run service with internal handlers (Plan 18-02 Task 2)"
echo "2. Update CLOUD_RUN_URL in this script with actual service URL"
echo "3. Re-run this script to create push subscriptions with correct endpoint"
echo "4. Grant Cloud Run invoker role to Pub/Sub service account:"
echo "     gcloud run services add-iam-policy-binding venezuelawatch-api \\"
echo "       --region $REGION \\"
echo "       --member serviceAccount:pubsub-invoker@${PROJECT_ID}.iam.gserviceaccount.com \\"
echo "       --role roles/run.invoker"
echo "5. Test publishing a message:"
echo "     gcloud pubsub topics publish event-analysis \\"
echo "       --message '{\"event_id\": \"test-123\"}' \\"
echo "       --project $PROJECT_ID"
echo ""
echo "========================================="
