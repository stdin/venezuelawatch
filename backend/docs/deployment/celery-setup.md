# Celery and Redis Deployment Guide

This guide covers deploying the Celery task queue infrastructure for VenezuelaWatch on Google Cloud Platform.

## Prerequisites

- GCP project with billing enabled
- Google Cloud SDK (gcloud) installed and configured
- Terraform or gcloud CLI access
- PostgreSQL database already deployed (from Phase 1)

## 1. Enable Required GCP APIs

```bash
# Enable Redis API
gcloud services enable redis.googleapis.com --project=venezuelawatch-staging

# Verify API is enabled
gcloud services list --enabled --project=venezuelawatch-staging | grep redis
```

## 2. Create GCP Memorystore Redis Instance

### Development/Staging Environment

```bash
gcloud redis instances create venezuelawatch-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0 \
  --tier=basic \
  --project=venezuelawatch-staging
```

**Configuration Details:**
- **Size**: 1GB (sufficient for task queue)
- **Tier**: Basic (no replication, suitable for staging)
- **Region**: us-central1 (match Cloud SQL region)
- **Version**: Redis 7.0 (latest stable)

### Production Environment

```bash
gcloud redis instances create venezuelawatch-redis-prod \
  --size=5 \
  --region=us-central1 \
  --redis-version=redis_7_0 \
  --tier=standard \
  --replica-count=1 \
  --project=venezuelawatch-production
```

**Production Configuration:**
- **Size**: 5GB (handles higher throughput)
- **Tier**: Standard (automatic failover)
- **Replica Count**: 1 (high availability)

### Get Redis Connection Details

```bash
# Get host IP and port
gcloud redis instances describe venezuelawatch-redis \
  --region=us-central1 \
  --project=venezuelawatch-staging \
  --format="value(host,port)"
```

The output will be in format: `10.x.x.x 6379`

## 3. Configure VPC Peering

Memorystore Redis requires VPC peering to connect from Cloud Run or Compute Engine.

```bash
# Create VPC connector for Cloud Run
gcloud compute networks vpc-access connectors create venezuelawatch-connector \
  --region=us-central1 \
  --network=default \
  --range=10.8.0.0/28 \
  --project=venezuelawatch-staging
```

## 4. Update Application Settings

### Environment Variables

Set these in your deployment environment (Cloud Run, App Engine, or .env file):

```bash
# Redis connection (use internal IP from step 2)
REDIS_URL=redis://10.x.x.x:6379/0

# GCP Secret Manager
GCP_PROJECT_ID=venezuelawatch-staging
SECRET_MANAGER_ENABLED=true

# Celery configuration (optional overrides)
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_TIME_LIMIT=300
```

### Production Settings File

Create `backend/config/settings_prod.py` (see settings section below).

## 5. Deploy Celery Workers

### Option A: Cloud Run (Serverless Workers)

**Dockerfile for Celery Worker:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run Celery worker
CMD celery -A config.celery worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=1000
```

**Deploy:**
```bash
gcloud run deploy venezuelawatch-celery-worker \
  --source=backend \
  --region=us-central1 \
  --vpc-connector=venezuelawatch-connector \
  --set-env-vars="REDIS_URL=redis://10.x.x.x:6379/0,GCP_PROJECT_ID=venezuelawatch-staging" \
  --no-allow-unauthenticated \
  --project=venezuelawatch-staging
```

### Option B: Compute Engine (Traditional Workers)

**Create worker instance:**
```bash
gcloud compute instances create celery-worker-1 \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=debian-11 \
  --scopes=cloud-platform \
  --project=venezuelawatch-staging
```

**SSH and setup:**
```bash
gcloud compute ssh celery-worker-1 --zone=us-central1-a

# Install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip git
git clone <your-repo>
cd venezuelawatch/backend
pip3 install -r requirements.txt

# Create systemd service
sudo nano /etc/systemd/system/celery.service
```

**Celery systemd service file:**
```ini
[Unit]
Description=Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/opt/venezuelawatch/backend
Environment="REDIS_URL=redis://10.x.x.x:6379/0"
Environment="GCP_PROJECT_ID=venezuelawatch-staging"
Environment="SECRET_MANAGER_ENABLED=true"
ExecStart=/usr/local/bin/celery -A config.celery worker \
  --loglevel=info \
  --concurrency=4 \
  --pidfile=/var/run/celery/celery.pid \
  --logfile=/var/log/celery/celery.log
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable celery
sudo systemctl start celery
sudo systemctl status celery
```

## 6. Deploy Celery Beat (Scheduler)

For periodic tasks, deploy Celery Beat alongside your workers.

**Cloud Run deployment:**
```bash
gcloud run deploy venezuelawatch-celery-beat \
  --source=backend \
  --region=us-central1 \
  --vpc-connector=venezuelawatch-connector \
  --set-env-vars="REDIS_URL=redis://10.x.x.x:6379/0" \
  --command="celery,-A,config.celery,beat,--loglevel=info" \
  --no-allow-unauthenticated \
  --project=venezuelawatch-staging
```

## 7. Provision API Secrets

Store API credentials in Secret Manager:

```bash
# FRED API Key
python manage.py set_secret fred-key "your-fred-api-key"

# GDELT (if required)
python manage.py set_secret gdelt-key "your-gdelt-api-key"

# ReliefWeb
python manage.py set_secret reliefweb-key "your-reliefweb-api-key"

# UN Comtrade
python manage.py set_secret comtrade-key "your-comtrade-api-key"
```

## 8. Verify Deployment

### Check Redis Connection

```bash
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value', 30)
>>> cache.get('test')
'value'
```

### Test Celery Worker

```bash
# Submit test task
python manage.py shell
>>> from data_pipeline.tasks.test_tasks import hello_world
>>> result = hello_world.delay()
>>> result.get(timeout=10)
'Hello World'
```

### Monitor Celery Workers

```bash
# View active workers
celery -A config.celery inspect active

# View registered tasks
celery -A config.celery inspect registered

# Monitor in real-time
celery -A config.celery events
```

## 9. Monitoring and Logging

### Cloud Logging

```bash
# View Celery worker logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=venezuelawatch-celery-worker" \
  --limit=50 \
  --project=venezuelawatch-staging
```

### Cloud Monitoring

Create alerting policies for:
- Redis memory usage > 80%
- Celery task failure rate > 5%
- Worker instance health checks
- Task queue depth > 1000

## 10. Scaling Considerations

### Horizontal Scaling (More Workers)

```bash
# Scale Cloud Run workers
gcloud run services update venezuelawatch-celery-worker \
  --min-instances=2 \
  --max-instances=10 \
  --project=venezuelawatch-staging
```

### Vertical Scaling (Bigger Redis)

```bash
# Upgrade Memorystore size
gcloud redis instances update venezuelawatch-redis \
  --size=5 \
  --region=us-central1 \
  --project=venezuelawatch-staging
```

## Troubleshooting

### Worker Can't Connect to Redis

- Verify VPC connector is attached to Cloud Run service
- Check Redis instance is in same region
- Confirm firewall rules allow internal traffic

### Tasks Stuck in Queue

- Check worker logs for errors
- Verify workers are running: `celery -A config.celery inspect active`
- Check Redis memory usage

### Secret Manager Errors

- Verify Secret Manager API is enabled
- Check service account has `secretmanager.secretAccessor` role
- Ensure secrets exist: `gcloud secrets list --project=venezuelawatch-staging`

## Production Checklist

- [ ] Redis API enabled in GCP project
- [ ] Memorystore instance created with Standard tier
- [ ] VPC connector created and configured
- [ ] Celery workers deployed with proper scaling
- [ ] Celery Beat deployed for scheduled tasks
- [ ] API secrets provisioned in Secret Manager
- [ ] Monitoring and alerting configured
- [ ] Backup strategy for Redis data (if needed)
- [ ] SSL/TLS enabled for Redis connections (production)
- [ ] Worker auto-scaling policies configured
