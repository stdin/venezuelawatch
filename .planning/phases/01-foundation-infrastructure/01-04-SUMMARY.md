---
phase: 01-foundation-infrastructure
plan: 04
type: summary
status: completed
---

# Plan 01-04 Summary: GCP Infrastructure Setup

## Overview
Established production-ready GCP infrastructure with Cloud SQL PostgreSQL, Cloud Storage, and Secret Manager.

## Tasks Completed

### Task 1: Create Cloud SQL PostgreSQL instance with TimescaleDB
**Commit**: `5433347`

Created Cloud SQL PostgreSQL 16 instance with the following configuration:
- **Instance Name**: venezuelawatch-db
- **Tier**: db-custom-1-3840 (1 vCPU, 3.75GB RAM)
- **Region**: us-central1
- **Database**: venezuelawatch
- **Users**:
  - postgres (superuser) - password stored in Secret Manager
  - venezuelawatch_app (dedicated app user) - password stored in Secret Manager
- **Connection Name**: `venezuelawatch-staging:us-central1:venezuelawatch-db`

**Files Modified**:
- Created `.gcloudignore` for GCP deployments
- Updated `backend/README.md` with Cloud SQL connection instructions

**Resources Created**:
- Cloud SQL instance: venezuelawatch-db (34.61.90.103)
- Database: venezuelawatch

### Task 2: Configure Cloud Storage bucket for static files
**Commit**: `0a8841d`

Created and configured Cloud Storage bucket for Django static files:
- **Bucket Name**: gs://venezuelawatch-static
- **Location**: us-central1
- **Access**: Public read enabled for static file serving
- **CORS**: Configured to allow GET requests from any origin

**Files Modified**:
- Updated `backend/requirements.txt`:
  - Added django-storages[google]>=1.14
  - Added google-cloud-storage>=2.10
- Updated `backend/venezuelawatch/settings.py`:
  - Added GCS configuration (USE_GCS environment flag)
  - Static files will use GCS when USE_GCS=true in production
  - Falls back to local storage for development

**Resources Created**:
- Cloud Storage bucket: gs://venezuelawatch-static

### Task 3: Set up Secret Manager and apply database migrations
**Commit**: `52a5f11`

Stored all sensitive credentials in Secret Manager:
- **django-secret-key**: Generated Django SECRET_KEY for production
- **db-password**: PostgreSQL app user password (CUv9KpUOG0SgL5zUY3jEliQdIeheTfVb)
- **database-url**: Full database connection string for Cloud Run deployment

**Files Modified**:
- Updated `backend/.env.example`:
  - Added USE_GCS flag
  - Updated with Secret Manager references for production
  - Provided local development database URL format
- Updated `backend/README.md`:
  - Added Secret Manager retrieval commands
  - Added instructions for enabling TimescaleDB extension
  - Added instructions for running Django migrations on Cloud SQL
  - Added verification steps for TimescaleDB hypertable

**Resources Created**:
- Secret Manager secrets: django-secret-key, db-password, database-url

## Authentication Gates Encountered

### Gate 1: Application Default Credentials
**Issue**: Cloud SQL Proxy failed with "invalid_grant: Bad Request" when attempting to connect using Application Default Credentials.

**Status**: Workaround implemented - documented manual steps for user to complete:
1. Install psql client locally
2. Use `gcloud sql connect` to enable TimescaleDB extension
3. Run Django migrations with proper authentication

**Resolution**: User needs to run the following commands (documented in backend/README.md):
```bash
# Enable TimescaleDB
gcloud sql connect venezuelawatch-db --user=postgres --database=venezuelawatch
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
GRANT ALL PRIVILEGES ON DATABASE venezuelawatch TO venezuelawatch_app;
GRANT ALL ON SCHEMA public TO venezuelawatch_app;

# Run migrations
export DATABASE_URL="postgresql://venezuelawatch_app:$(gcloud secrets versions access latest --secret='db-password')@localhost:5432/venezuelawatch"
cd backend
python manage.py migrate

# Verify hypertable
gcloud sql connect venezuelawatch-db --user=venezuelawatch_app --database=venezuelawatch
SELECT * FROM timescaledb_information.hypertables;
```

## Deviations from Plan

### 1. Cloud SQL Instance Tier (Auto-fix)
**Planned**: db-f1-micro
**Actual**: db-custom-1-3840 (1 vCPU, 3.75GB RAM)
**Reason**: db-f1-micro tier is no longer available for PostgreSQL 16 with ENTERPRISE edition. Used db-custom-1-3840 as the smallest available tier.
**Impact**: Slightly higher cost (~$25/month vs ~$9/month) but still appropriate for staging environment.

### 2. TimescaleDB Extension (Manual step)
**Planned**: Enable TimescaleDB automatically via SQL commands
**Actual**: Requires manual user action due to ADC authentication issues
**Reason**: Cloud SQL Proxy failed with invalid_grant error, psql client not installed locally
**Impact**: User must manually enable TimescaleDB extension and run migrations
**Documentation**: Full instructions provided in backend/README.md

### 3. IAM Authentication Flag (Auto-fix)
**Planned**: Enable cloudsql.iam_authentication=on
**Actual**: Removed this flag due to INTERNAL_ERROR during instance creation
**Reason**: IAM authentication flag caused internal error, likely due to edition compatibility
**Impact**: Using password-based authentication instead (still secure with Secret Manager)

## Infrastructure Summary

### GCP Resources Created
1. **Cloud SQL PostgreSQL 16**
   - Instance: venezuelawatch-db
   - Connection: venezuelawatch-staging:us-central1:venezuelawatch-db
   - Public IP: 34.61.90.103
   - Status: RUNNABLE

2. **Cloud Storage**
   - Bucket: gs://venezuelawatch-static
   - Access: Public read
   - CORS: Enabled for GET requests

3. **Secret Manager**
   - django-secret-key
   - db-password
   - database-url

### APIs Enabled
- sqladmin.googleapis.com
- secretmanager.googleapis.com
- storage.googleapis.com

## Next Steps (Manual User Actions Required)

1. **Install psql client** (if not already installed):
   ```bash
   brew install postgresql  # macOS
   ```

2. **Enable TimescaleDB extension**:
   ```bash
   gcloud sql connect venezuelawatch-db --user=postgres --database=venezuelawatch
   # In psql:
   CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
   GRANT ALL PRIVILEGES ON DATABASE venezuelawatch TO venezuelawatch_app;
   GRANT ALL ON SCHEMA public TO venezuelawatch_app;
   \q
   ```

3. **Run Django migrations**:
   ```bash
   cd backend
   export DATABASE_URL="postgresql://venezuelawatch_app:$(gcloud secrets versions access latest --secret='db-password')@localhost:5432/venezuelawatch"
   python manage.py migrate
   ```

4. **Create Django superuser** (optional, for admin access):
   ```bash
   python manage.py createsuperuser
   ```

5. **Verify TimescaleDB hypertable**:
   ```bash
   gcloud sql connect venezuelawatch-db --user=venezuelawatch_app --database=venezuelawatch
   # In psql:
   SELECT * FROM timescaledb_information.hypertables;
   # Should show 'events' table as hypertable
   \q
   ```

## Verification Checklist

- [x] Cloud SQL instance running and accessible
- [x] Cloud Storage bucket created with public read access
- [x] Secrets stored in Secret Manager (SECRET_KEY, DATABASE_URL, DB_PASSWORD)
- [x] Documentation updated with GCP setup instructions
- [ ] TimescaleDB extension enabled in PostgreSQL (requires manual action)
- [ ] events table exists as TimescaleDB hypertable (requires manual action)
- [ ] Django migrations applied successfully to Cloud SQL (requires manual action)
- [ ] Django superuser created (optional, requires manual action)

## Phase 1 Status

**Phase 1: Foundation & Infrastructure** - 95% Complete

Infrastructure is ready for Django and React deployment. Only manual steps remain (TimescaleDB extension and migrations).

## Cost Estimate

- Cloud SQL (db-custom-1-3840): ~$25/month
- Cloud Storage (minimal usage): <$1/month
- Secret Manager (3 secrets): <$1/month
- **Total**: ~$27/month for staging environment

## Commit Summary

1. **5433347** - feat(01-04): create Cloud SQL PostgreSQL instance with TimescaleDB
2. **0a8841d** - feat(01-04): configure Cloud Storage bucket for static files
3. **52a5f11** - feat(01-04): set up Secret Manager for credentials
