# VenezuelaWatch Backend

Django 5.2 backend API for the VenezuelaWatch intelligence platform.

## Requirements

- Python 3.10+
- PostgreSQL (for production; SQLite for development)

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set:
   - `SECRET_KEY`: Django secret key (generate a new one for production)
   - `DEBUG`: Set to `True` for development, `False` for production
   - `DATABASE_URL`: PostgreSQL connection string (optional, uses SQLite by default)

3. **Setup database** (optional for full features)

   The application can run with SQLite for basic development, but PostgreSQL with TimescaleDB is required for production time-series features.

   ### Option 1: Cloud SQL (Production)

   VenezuelaWatch uses Google Cloud SQL PostgreSQL 16 for production.

   **Connection Name**: `venezuelawatch-staging:us-central1:venezuelawatch-db`

   **Connect locally via Cloud SQL Proxy**:
   ```bash
   # Install Cloud SQL Proxy
   # macOS: brew install cloud-sql-proxy
   # Or download from: https://cloud.google.com/sql/docs/postgres/sql-proxy

   # Start proxy (runs in foreground)
   cloud-sql-proxy venezuelawatch-staging:us-central1:venezuelawatch-db

   # Or start in background
   cloud-sql-proxy venezuelawatch-staging:us-central1:venezuelawatch-db &

   # Set DATABASE_URL in .env
   DATABASE_URL=postgresql://venezuelawatch_app:PASSWORD@localhost:5432/venezuelawatch
   ```

   **Retrieve passwords from Secret Manager**:
   ```bash
   # Database password
   gcloud secrets versions access latest --secret="db-password"

   # Full database URL
   gcloud secrets versions access latest --secret="database-url"

   # Django secret key
   gcloud secrets versions access latest --secret="django-secret-key"
   ```

   **Enable TimescaleDB and run migrations**:
   ```bash
   # Install psql client (if not installed)
   # macOS: brew install postgresql

   # Connect to database as postgres user
   gcloud sql connect venezuelawatch-db --user=postgres --database=venezuelawatch

   # In psql, enable TimescaleDB extension
   CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
   GRANT ALL PRIVILEGES ON DATABASE venezuelawatch TO venezuelawatch_app;
   GRANT ALL ON SCHEMA public TO venezuelawatch_app;
   \q

   # Back in your shell, run Django migrations
   cd backend
   export DATABASE_URL="postgresql://venezuelawatch_app:$(gcloud secrets versions access latest --secret='db-password')@localhost:5432/venezuelawatch"
   python manage.py migrate

   # Verify TimescaleDB hypertable
   gcloud sql connect venezuelawatch-db --user=venezuelawatch_app --database=venezuelawatch
   SELECT * FROM timescaledb_information.hypertables;
   \q
   ```

   ### Option 2: Docker (Local Development)
   ```bash
   docker run -d --name timescaledb -p 5432:5432 \
     -e POSTGRES_PASSWORD=password \
     -e POSTGRES_DB=venezuelawatch \
     timescale/timescaledb-ha:pg16
   ```

   ### Option 3: Local PostgreSQL + TimescaleDB
   - Install PostgreSQL 16
   - Install TimescaleDB extension: https://docs.timescale.com/install/
   - Create database: `createdb venezuelawatch`
   - Enable extension: `psql venezuelawatch -c "CREATE EXTENSION IF NOT EXISTS timescaledb"`

   **Note**: Migration 0002 requires TimescaleDB extension. For testing without TimescaleDB, you can skip it temporarily and use regular PostgreSQL table (not recommended for production).

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Start development server**
   ```bash
   python manage.py runserver
   ```

   The API will be available at http://localhost:8000

## Authentication

VenezuelaWatch uses django-allauth with headless mode for JWT authentication.

### Endpoints

Available at `/_allauth/browser/v1/auth/`:
- `POST /signup` - Create new user account
- `POST /login` - Authenticate and receive JWT tokens
- `DELETE /session` - Invalidate tokens (logout)
- `GET /session` - Get current user details
- `POST /password/request` - Request password reset

### JWT Tokens

- **Access Token**: 15-minute expiry, sent in httpOnly cookie
- **Refresh Token**: 7-day expiry, sent in httpOnly cookie
- **CSRF Protection**: Enabled for state-changing operations

### Testing Authentication

Register a user:
```bash
curl -X POST http://localhost:8000/_allauth/browser/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"securepass123"}' \
  -c cookies.txt
```

Login:
```bash
curl -X POST http://localhost:8000/_allauth/browser/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"securepass123"}' \
  -c cookies.txt
```

Access protected endpoints (will be configured in next plan):
```bash
curl http://localhost:8000/api/protected/ -b cookies.txt
```

### Email Configuration

Development: Emails print to console (EMAIL_BACKEND=console)
Production: Configure SMTP settings in .env (see .env.example)

## API Documentation

Interactive API documentation is automatically generated and available at:
- **Swagger UI**: http://localhost:8000/api/docs
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## Endpoints

### Health Check
- **GET** `/api/health/health` - Returns service health status

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Django Admin
Create a superuser to access the Django admin at http://localhost:8000/admin:
```bash
python manage.py createsuperuser
```

## Project Structure

```
backend/
├── core/              # Core app with base models and API endpoints
├── venezuelawatch/    # Django project settings and main API configuration
├── manage.py          # Django management script
└── requirements.txt   # Python dependencies
```
