#!/bin/bash
# Django web server startup script for Render
# This script starts the Django application using gunicorn

set -e

echo "Starting Django application..."

# Run database migrations (safe to run on every startup)
echo "Running migrations..."
python manage.py migrate --noinput

# Start gunicorn web server
echo "Starting gunicorn..."
exec gunicorn backend.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 2 \
  --threads 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
