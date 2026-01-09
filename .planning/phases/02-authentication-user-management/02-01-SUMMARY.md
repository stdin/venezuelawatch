---
phase: 02-authentication-user-management
plan: 01
subsystem: api
tags: [django-allauth, authentication, user-model, jwt]

requires:
  - phase: 01-01
    provides: Django 5.2 backend with settings
  - phase: 01-03
    provides: PostgreSQL database

provides:
  - django-allauth with headless mode configured
  - Custom User model with team-ready fields (organization_name, role, subscription_tier, timezone)
  - JWT authentication backend configured
  - Sites framework integrated

affects: [02-02-auth-endpoints, 02-03-protected-routes, 02-04-react-ui, future-teams]

tech-stack:
  added: [django-allauth 65.12.1, djangorestframework-simplejwt 5.5.1, django.contrib.sites]
  patterns: [Custom User model with future-proof fields, allauth headless for SPA]

key-files:
  created:
    - backend/core/migrations/0003_user.py
    - backend/.env
  modified:
    - backend/requirements.txt
    - backend/venezuelawatch/settings.py
    - backend/core/models.py

key-decisions:
  - "django-allauth headless for SPA authentication (not dj-rest-auth)"
  - "Custom User model NOW to avoid migration pain for future teams"
  - "JWT in httpOnly cookies via djangorestframework-simplejwt"
  - "CORS_ALLOW_CREDENTIALS=True for cross-origin cookie authentication"
  - "Email verification set to optional for Phase 2 (can be enabled later)"
  - "PostgreSQL with TimescaleDB required for ArrayField in Event model"

---

# Plan 02-01 Summary: django-allauth Setup & User Model

Established authentication foundation with django-allauth headless mode and custom User model designed to support future team features without migration pain.

## Accomplishments

- Installed and configured django-allauth 65.12.1 with headless mode for SPA
- Created custom User model extending AbstractUser with team-ready fields
- Configured JWT authentication backend (djangorestframework-simplejwt 5.5.1)
- Applied migrations for User model, allauth, and sites framework
- Enabled CORS credentials for httpOnly cookie authentication
- Set up PostgreSQL database with TimescaleDB for development

## Files Created/Modified

### Created:
- `backend/core/migrations/0003_user.py` - User model migration
- `backend/.env` - Local development environment configuration (PostgreSQL)

### Modified:
- `backend/requirements.txt` - Added django-allauth>=0.63.0 and djangorestframework-simplejwt>=5.3
- `backend/venezuelawatch/settings.py` - AUTH_USER_MODEL, allauth config, sites framework, CORS credentials
- `backend/core/models.py` - Custom User model with organization_name, role, subscription_tier, timezone fields

## Decisions Made

1. **Custom User Model Design**: Added organization_name, role, subscription_tier, timezone fields now to avoid costly migrations when team features are added in future phases
2. **django-allauth Headless**: Selected over dj-rest-auth for cleaner django-ninja integration and better SPA support
3. **CORS Credentials**: Enabled CORS_ALLOW_CREDENTIALS for httpOnly cookie authentication with React frontend
4. **Email Verification**: Set to optional for Phase 2 (simpler development flow, can be enabled to mandatory later)
5. **PostgreSQL Required**: Used Docker TimescaleDB container for local development due to ArrayField in Event model

## Issues Encountered

### Issue 1: Email Verification Configuration Conflict
- **Problem**: Initial setting ACCOUNT_EMAIL_VERIFICATION='optional' with ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED=True caused Django check failure
- **Solution**: Removed ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED for Phase 2, set verification to 'optional'
- **Impact**: Simplified auth flow for development; can enable code-based verification in future phases

### Issue 2: Migration Order for Custom User Model
- **Problem**: django-allauth migrations attempted to run before core.0003_user, causing "Related model 'core.user' cannot be resolved" error
- **Solution**: Migrated apps in specific order (contenttypes, auth, core) before running allauth migrations
- **Impact**: Required careful migration sequencing; added contenttypes dependency to User migration

### Issue 3: TimescaleDB Hypertable Primary Key Constraint
- **Problem**: Migration 0002_create_hypertable failed with UUID primary key not including timestamp partition column
- **Solution**: Faked the hypertable migration for now (not critical for auth setup)
- **Impact**: Event model exists as regular PostgreSQL table; hypertable conversion deferred to data ingestion phase

### Issue 4: PostgreSQL Database Required
- **Problem**: Event model uses PostgreSQL-specific ArrayField, SQLite fallback failed
- **Solution**: Set up Docker TimescaleDB container for local development
- **Impact**: Created .env file with DATABASE_URL (not committed); documented in backend/README.md

## Task Commits

- Task 1: `2af91f4` - feat(02-01): install django-allauth and configure settings
- Task 2: `85b8f63` - feat(02-01): create custom User model with team-ready fields
- Task 3: `7317670` - chore(02-01): install dependencies, add sites framework, and run migrations

## Next Phase Readiness

Ready for Plan 02-02 (Authentication Endpoints).
- User model created and migrated to database
- django-allauth installed and configured with headless mode
- JWT backend (djangorestframework-simplejwt) ready for endpoint integration
- Sites framework configured (SITE_ID=1)
- CORS credentials enabled for cookie-based auth

**Prerequisites for next plan:**
- PostgreSQL database running (Docker container or Cloud SQL proxy)
- Environment variables set in backend/.env
- All migrations applied successfully

---
