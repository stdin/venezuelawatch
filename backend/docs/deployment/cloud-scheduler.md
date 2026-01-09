# GCP Cloud Scheduler Setup for Production Ingestion

This guide covers setting up GCP Cloud Scheduler to trigger periodic data ingestion tasks in production.

## Overview

Cloud Scheduler is Google Cloud's fully managed cron service. It triggers ingestion tasks via HTTP POST requests to your API, replacing Celery Beat in production.

**Why Cloud Scheduler over Celery Beat:**
- Fully managed (no Beat process to maintain)
- Integrated with Cloud Run (automatic authentication)
- Better observability (Cloud Logging, Cloud Monitoring)
- Automatic retry and failure handling
- Scales independently of workers

## Prerequisites

- GCP project with billing enabled (`venezuelawatch-staging` or `venezuelawatch-production`)
- Cloud Run API deployed at a public URL
- gcloud CLI installed and authenticated

## 1. Enable Cloud Scheduler API

```bash
gcloud services enable cloudscheduler.googleapis.com --project=venezuelawatch-staging
```

## 2. Create Service Account

Create a dedicated service account for Cloud Scheduler with limited permissions:

```bash
# Create service account
gcloud iam service-accounts create venezuelawatch-scheduler \
  --display-name="VenezuelaWatch Cloud Scheduler" \
  --description="Service account for Cloud Scheduler to invoke task triggers" \
  --project=venezuelawatch-staging

# Grant Cloud Run Invoker role (allows calling Cloud Run services)
gcloud projects add-iam-policy-binding venezuelawatch-staging \
  --member="serviceAccount:venezuelawatch-scheduler@venezuelawatch-staging.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

# Verify service account
gcloud iam service-accounts describe venezuelawatch-scheduler@venezuelawatch-staging.iam.gserviceaccount.com \
  --project=venezuelawatch-staging
```

## 3. Create Cloud Scheduler Jobs

### GDELT Ingestion (Every 15 Minutes)

```bash
gcloud scheduler jobs create http gdelt-ingestion \
  --location=us-central1 \
  --schedule="*/15 * * * *" \
  --uri="https://venezuelawatch-api.run.app/api/tasks/trigger/gdelt" \
  --http-method=POST \
  --oidc-service-account-email=venezuelawatch-scheduler@venezuelawatch-staging.iam.gserviceaccount.com \
  --headers="Content-Type=application/json" \
  --message-body='{"lookback_minutes": 15}' \
  --time-zone="America/New_York" \
  --project=venezuelawatch-staging
```

**Schedule Format**: `*/15 * * * *` = Every 15 minutes
**Timezone**: America/New_York (adjust as needed)

### ReliefWeb Ingestion (Daily at 9 AM UTC)

```bash
gcloud scheduler jobs create http reliefweb-ingestion \
  --location=us-central1 \
  --schedule="0 9 * * *" \
  --uri="https://venezuelawatch-api.run.app/api/tasks/trigger/reliefweb" \
  --http-method=POST \
  --oidc-service-account-email=venezuelawatch-scheduler@venezuelawatch-staging.iam.gserviceaccount.com \
  --headers="Content-Type=application/json" \
  --message-body='{"lookback_days": 1}' \
  --time-zone="UTC" \
  --project=venezuelawatch-staging
```

**Schedule Format**: `0 9 * * *` = Daily at 9:00 AM
**Timezone**: UTC

## 4. Verify Scheduler Jobs

List all Cloud Scheduler jobs:

```bash
gcloud scheduler jobs list --location=us-central1 --project=venezuelawatch-staging
```

Expected output:
```
ID                    LOCATION      SCHEDULE (TZ)              TARGET_TYPE  STATE
gdelt-ingestion       us-central1   */15 * * * * (Etc/UTC)     HTTP         ENABLED
reliefweb-ingestion   us-central1   0 9 * * * (Etc/UTC)        HTTP         ENABLED
```

Describe a specific job:

```bash
gcloud scheduler jobs describe gdelt-ingestion \
  --location=us-central1 \
  --project=venezuelawatch-staging
```

## 5. Test Scheduler Jobs Manually

Trigger a job manually to test:

```bash
# Test GDELT ingestion
gcloud scheduler jobs run gdelt-ingestion \
  --location=us-central1 \
  --project=venezuelawatch-staging

# Test ReliefWeb ingestion
gcloud scheduler jobs run reliefweb-ingestion \
  --location=us-central1 \
  --project=venezuelawatch-staging
```

Check the job execution logs:

```bash
gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_id=gdelt-ingestion" \
  --limit=10 \
  --format=json \
  --project=venezuelawatch-staging
```

## 6. Monitor Scheduler Jobs

### View Job History

```bash
# View recent executions
gcloud scheduler jobs list --location=us-central1 --project=venezuelawatch-staging

# View logs for specific job
gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_id=gdelt-ingestion" \
  --limit=50 \
  --project=venezuelawatch-staging
```

### Set Up Alerts

Create alerting policies for job failures:

```bash
# Example: Alert if scheduler job fails 3 times in 1 hour
gcloud alpha monitoring policies create \
  --notification-channels=<CHANNEL_ID> \
  --display-name="Cloud Scheduler Failures" \
  --condition-display-name="Scheduler job failed" \
  --condition-threshold-value=3 \
  --condition-threshold-duration=3600s \
  --condition-filter='metric.type="cloudscheduler.googleapis.com/job/attempt_count" AND metric.label.response_code!="200"' \
  --project=venezuelawatch-staging
```

## 7. Update Scheduler Jobs

### Change Schedule

```bash
gcloud scheduler jobs update http gdelt-ingestion \
  --location=us-central1 \
  --schedule="*/30 * * * *" \
  --project=venezuelawatch-staging
```

### Change Message Body

```bash
gcloud scheduler jobs update http gdelt-ingestion \
  --location=us-central1 \
  --message-body='{"lookback_minutes": 30}' \
  --project=venezuelawatch-staging
```

### Pause/Resume Job

```bash
# Pause job
gcloud scheduler jobs pause gdelt-ingestion \
  --location=us-central1 \
  --project=venezuelawatch-staging

# Resume job
gcloud scheduler jobs resume gdelt-ingestion \
  --location=us-central1 \
  --project=venezuelawatch-staging
```

## 8. Delete Scheduler Jobs

```bash
gcloud scheduler jobs delete gdelt-ingestion \
  --location=us-central1 \
  --project=venezuelawatch-staging \
  --quiet
```

## Task Trigger API Endpoint

Cloud Scheduler calls the `/api/tasks/trigger/{task_name}` endpoint.

**Implementation**: See `backend/data_pipeline/api.py`

**Authentication**: OIDC token from Cloud Scheduler service account is verified by Cloud Run.

**Example Request**:
```bash
curl -X POST https://venezuelawatch-api.run.app/api/tasks/trigger/gdelt \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -d '{"lookback_minutes": 15}'
```

**Response**:
```json
{
  "status": "dispatched",
  "task_id": "abc-123-def",
  "task_name": "gdelt"
}
```

## Troubleshooting

### Job Returns 403 Forbidden

- Verify service account has `roles/run.invoker` permission
- Check Cloud Run service allows unauthenticated or service account invocations

```bash
gcloud run services add-iam-policy-binding venezuelawatch-api \
  --region=us-central1 \
  --member="serviceAccount:venezuelawatch-scheduler@venezuelawatch-staging.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --project=venezuelawatch-staging
```

### Job Returns 404 Not Found

- Verify API endpoint URL is correct
- Check Cloud Run service is deployed and accessible
- Test endpoint manually with curl

### Job Returns 500 Internal Server Error

- Check Cloud Run logs for application errors
- Verify Celery workers are running
- Check Redis broker is accessible from Cloud Run

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=venezuelawatch-api" \
  --limit=50 \
  --project=venezuelawatch-staging
```

### Job Not Executing on Schedule

- Verify job is in ENABLED state: `gcloud scheduler jobs list`
- Check job schedule is correct: `gcloud scheduler jobs describe <JOB_NAME>`
- Review Cloud Scheduler logs for errors

## Cost Optimization

**Cloud Scheduler Pricing** (as of 2024):
- First 3 jobs per month: Free
- Additional jobs: $0.10 per job per month

**Estimated Cost**:
- 2 jobs (GDELT + ReliefWeb): **Free**
- Future jobs (FRED, Comtrade, World Bank): $0.30/month

**Tips**:
- Use Cloud Scheduler for production cron
- Use Celery Beat for local development
- Combine multiple tasks into a single scheduled job if possible

## Production Checklist

- [ ] Cloud Scheduler API enabled
- [ ] Service account created with `roles/run.invoker` permission
- [ ] GDELT ingestion job created (every 15 minutes)
- [ ] ReliefWeb ingestion job created (daily at 9 AM)
- [ ] Jobs tested manually with `gcloud scheduler jobs run`
- [ ] Task trigger API endpoint deployed and accessible
- [ ] Cloud Run service allows service account invocations
- [ ] Alerting policies configured for job failures
- [ ] Monitoring dashboard created for job execution metrics
- [ ] Documentation updated with production URLs and schedules
