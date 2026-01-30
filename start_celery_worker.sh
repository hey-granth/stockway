#!/bin/bash
# Celery worker startup script for Render
# This script starts the Celery worker process independently from the Django web server

set -e

echo "Starting Celery worker..."

# Wait a moment for Django to be ready (optional, helps with startup coordination)
sleep 5

# Start Celery worker with production-ready settings
exec celery -A backend worker \
  --loglevel=info \
  --concurrency=2 \
  --max-tasks-per-child=1000 \
  --time-limit=1800 \
  --soft-time-limit=1500 \
  -Q celery,notifications,payments
