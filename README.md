# VenezuelaWatch

Real-time intelligence platform for tracking political, economic, and trade events in Venezuela.

## Overview

VenezuelaWatch is a SaaS platform that aggregates data from multiple sources to provide actionable risk intelligence for investors and operators dealing with Venezuela. The platform helps track sanctions changes, political disruptions, trade opportunities, and competitive positioning.

### Target Users
- Oil & energy companies evaluating Venezuela operations
- Commodity traders dealing with Venezuela-related products
- Private equity and investment funds assessing Venezuela exposure

### Key Features
- Real-time event aggregation from 7+ data sources
- News and events feed with sentiment analysis
- Risk scoring system for sanctions, political changes, and supply chain disruptions
- Entity tracking (people, companies, governments)
- AI-powered chat interface for natural language queries
- Trade opportunity identification

## Project Structure

This is a monorepo containing:

```
venezuelawatch2/
├── backend/          # Django 5.2 REST API
│   └── README.md    # Backend setup instructions
├── frontend/         # React 18 web application (coming soon)
│   └── README.md    # Frontend setup instructions (coming soon)
└── README.md        # This file
```

## Technology Stack

### Backend
- Django 5.2
- django-ninja (API framework)
- PostgreSQL
- Python 3.10+

### Frontend (Coming Soon)
- React 18
- Vite
- TypeScript

### Infrastructure
- Google Cloud Platform (GCP)
  - Cloud Run (application hosting)
  - Cloud SQL (PostgreSQL database)
  - Cloud Storage (static assets)

## Getting Started

### Backend Setup

See [backend/README.md](backend/README.md) for detailed setup instructions.

Quick start:
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

### Frontend Setup (Coming Soon)

Frontend setup instructions will be available in `frontend/README.md`.

## Development

### API Documentation

Once the backend is running, visit:
- http://localhost:8000/api/docs - Interactive API documentation

### Health Check

Test the API is running:
```bash
curl http://localhost:8000/api/health/health
```

Expected response:
```json
{"status": "ok", "service": "venezuelawatch"}
```

## Deployment

The application is designed to deploy on Google Cloud Platform:
- **Backend**: Cloud Run (containerized Django application)
- **Database**: Cloud SQL (PostgreSQL)
- **Static Files**: Cloud Storage
- **Frontend**: Cloud Run or Cloud Storage + CDN

Detailed deployment instructions coming soon.

## License

Proprietary - All rights reserved.
