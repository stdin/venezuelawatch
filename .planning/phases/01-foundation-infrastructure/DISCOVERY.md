# Phase 1 Discovery: Foundation & Infrastructure

## Research Summary

Investigated Django 5.2 + React 18 + GCP deployment patterns for a time-series event data platform.

## Technology Stack Decisions

### Backend: Django 5.2 + django-ninja

**Django 5.2:**
- Requires Python 3.10+
- Project initialization: `django-admin startproject`
- Settings structure supports environment-based configuration
- Built-in admin interface for data management

**django-ninja:**
- FastAPI-like API framework for Django
- Automatic OpenAPI documentation
- Type hints for validation
- Setup pattern:
  ```python
  from ninja import NinjaAPI
  api = NinjaAPI()

  # In urls.py
  path("api/", api.urls)
  ```

### Frontend: React 18 + Vite

**React 18:**
- New `createRoot` API (replaces ReactDOM.render)
- Concurrent features enabled by default
- Better TypeScript support

**Vite:**
- Fast development server with HMR
- TypeScript template available
- Setup: `npm create vite@latest venezuelawatch-frontend -- --template react-ts`
- Proxy configuration for Django backend during development

### Database: PostgreSQL + TimescaleDB

**PostgreSQL:**
- Cloud SQL for production (managed by GCP)
- Local PostgreSQL for development
- Configuration in Django settings:
  ```python
  DATABASES = {
      "default": {
          "ENGINE": "django.db.backends.postgresql",
          "NAME": "venezuelawatch",
          ...
      }
  }
  ```

**TimescaleDB Extension:**
- PostgreSQL extension optimized for time-series data
- **Hypertables**: Automatic time-based partitioning
- **Compression**: Native compression for historical data (7+ days old)
- **Retention policies**: Automated cleanup of old data
- **Continuous aggregates**: Materialized views for common queries
- Ideal for event data with timestamps (news, price changes, sanctions updates)

### GCP Infrastructure

**Cloud Run:**
- Serverless container deployment for Django
- Auto-scaling based on traffic
- Listens on PORT environment variable
- Requires: Dockerfile, .dockerignore, requirements.txt

**Cloud SQL (PostgreSQL):**
- Managed PostgreSQL with TimescaleDB support
- Same region as Cloud Run for low latency
- Cloud SQL Proxy for secure connections
- Backup and high availability built-in

**Cloud Storage:**
- Static file hosting (CSS, JS, media uploads)
- django-storages integration
- Public bucket for static assets

**Secret Manager:**
- Secure storage for:
  - Database credentials
  - Django SECRET_KEY
  - API keys for data sources
- Never commit secrets to git

### Development vs Production

**Local Development:**
- Django dev server: `python manage.py runserver`
- Vite dev server: `npm run dev` (with proxy to Django)
- Local PostgreSQL with TimescaleDB extension
- `.env` file for local secrets (gitignored)

**Production (GCP):**
- Cloud Run (Django + gunicorn)
- Cloud SQL (PostgreSQL + TimescaleDB)
- Cloud Storage (static files)
- Secret Manager (credentials)
- Cloud Build for CI/CD (future phase)

## Architecture Decisions

### Monorepo vs Separate Repos
**Decision: Monorepo** (single repo with frontend/ and backend/ directories)
- Easier coordination between frontend and backend changes
- Single deployment pipeline
- Shared documentation and planning
- Common for small teams

### Project Structure
```
venezuelawatch2/
├── backend/
│   ├── manage.py
│   ├── venezuelawatch/        # Django project
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── api.py             # django-ninja API root
│   ├── core/                  # Core Django app
│   │   ├── models.py          # Event model, etc.
│   │   └── api.py             # API endpoints
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── .planning/
└── README.md
```

### Database Schema Foundation

**Event Model** (for Phase 3 data pipeline):
- `id`: UUID primary key
- `source`: Data source (GDELT, FRED, etc.)
- `event_type`: Category (political, economic, trade, etc.)
- `timestamp`: Event time (indexed, hypertable partition key)
- `title`: Event headline
- `content`: Event details (JSONB for flexibility)
- `entities`: Extracted entities (people, orgs, locations)
- `sentiment`: Sentiment score (-1 to 1)
- `risk_score`: Computed risk level (Phase 4)
- `created_at`, `updated_at`: Record metadata

**TimescaleDB Hypertable:**
- Convert Event table to hypertable partitioned by `timestamp`
- Enables efficient time-range queries
- Automatic chunk management (7-day chunks recommended)

## Security Considerations

### Django Settings
- **DEBUG = False** in production
- **ALLOWED_HOSTS** restricted to actual domains
- **CSRF_TRUSTED_ORIGINS** for Cloud Run URLs
- **SECRET_KEY** from Secret Manager (never hardcode)

### Database Security
- Cloud SQL uses private IP (no public exposure)
- Database user has minimal permissions (not cloudsqlsuperuser)
- SSL/TLS for all connections
- Cloud SQL Proxy for local development connections

### Static Files
- Cloud Storage bucket with public read access only
- CORS configured for frontend domain
- django-storages handles signed URLs for private files (future)

## Don't Hand-Roll

**DO NOT custom-build these - use established solutions:**

1. **API Framework**: Use django-ninja (not DRF, not custom JSON views)
2. **Static File Storage**: Use django-storages + GCS (not custom S3 code)
3. **Database Connection Pooling**: Use django-db-connection-pool or Cloud SQL Proxy
4. **Secret Management**: Use GCP Secret Manager (not .env in production)
5. **CORS**: Use django-cors-headers (not custom middleware)
6. **Time-series Optimization**: Use TimescaleDB (not custom partitioning)

## Common Pitfalls

1. **Cloud Run PORT**: Django must listen on `os.environ.get("PORT", 8000)` - Cloud Run won't work otherwise
2. **Static Files**: Django's `collectstatic` must run before deployment, files go to GCS
3. **Database Migrations**: Run migrations during Cloud Run deployment (not manually)
4. **TimescaleDB Extension**: Must be enabled in Cloud SQL BEFORE creating hypertables
5. **CORS**: Frontend and backend on different origins requires django-cors-headers
6. **Secret Access**: Cloud Run service account needs Secret Manager permissions

## Phase 1 Scope

**In scope:**
- Django project structure
- React project structure
- PostgreSQL database configuration (local + Cloud SQL connection)
- TimescaleDB extension setup
- Basic Event model and migrations
- django-ninja API framework setup
- GCP infrastructure (Cloud SQL, Cloud Storage, Secret Manager)
- Development environment working end-to-end

**Out of scope (later phases):**
- Authentication (Phase 2)
- Data ingestion pipelines (Phase 3)
- Risk scoring logic (Phase 4)
- Dashboard UI (Phase 5)
- Actual deployment to Cloud Run (after auth is ready)

## Next Steps

Phase 1 will be split into 4 plans:
1. **01-01**: Django backend setup with django-ninja
2. **01-02**: React frontend setup with Vite
3. **01-03**: Database schema foundation with TimescaleDB
4. **01-04**: GCP infrastructure setup

Each plan: 2-3 tasks, ~50% context target, atomic commits.
