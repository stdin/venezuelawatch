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
