# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code
COPY . .

# Collect static files (skip for now, will do at runtime if needed)
# RUN python manage.py collectstatic --noinput || echo "No static files to collect"

# Start server (skip migrations for initial deployment)
CMD gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 0 venezuelawatch.wsgi:application
