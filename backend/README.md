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

3. **Run migrations**
   ```bash
   python manage.py migrate
   ```

4. **Start development server**
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
