#!/bin/bash
# Set up Pub/Sub topics and subscriptions for VenezuelaWatch
# Run from project root: ./scripts/setup_pubsub.sh

set -e  # Exit on error

PROJECT_ID="venezuelawatch-staging"
REGION="us-central1"

echo "======================================"
echo "Setting up Pub/Sub Topics and Subscriptions"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "======================================"
echo

# Function to create topic
create_topic() {
    local topic_name=$1

    echo "Creating topic: $topic_name"
    gcloud pubsub topics create "$topic_name" \
        --project="$PROJECT_ID" \
        --quiet || echo "  (Topic may already exist)"

    echo "✓ Topic $topic_name created/verified"
    echo
}

# Function to create push subscription to Cloud Run
create_push_subscription() {
    local subscription_name=$1
    local topic_name=$2
    local push_endpoint=$3
    local service_account=$4

    echo "Creating push subscription: $subscription_name"
    echo "  Topic: $topic_name"
    echo "  Endpoint: $push_endpoint"

    gcloud pubsub subscriptions create "$subscription_name" \
        --topic="$topic_name" \
        --push-endpoint="$push_endpoint" \
        --push-auth-service-account="$service_account" \
        --project="$PROJECT_ID" \
        --quiet || echo "  (Subscription may already exist)"

    echo "✓ Subscription $subscription_name created/verified"
    echo
}

# Create topics for event-driven processing
create_topic "event-created"
create_topic "analyze-intelligence"
create_topic "extract-entities"
create_topic "calculate-risk"

echo "======================================"
echo "All Pub/Sub topics created successfully!"
echo "======================================"
echo
echo "Note: Push subscriptions will be created once Cloud Run API is deployed."
echo "For now, topics are ready to receive messages from Cloud Functions."
echo
echo "Verify topics:"
echo "  gcloud pubsub topics list --project=$PROJECT_ID"
echo
