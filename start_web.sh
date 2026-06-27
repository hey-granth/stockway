#!/bin/bash
# Django web server startup script using Gunicorn

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

mask_redis_url() {
  echo "$1" | sed -E 's#(redis[s]?://)([^:@/]+:)?([^@/]+)@#\1***:***@#'
}

if [[ -z "${REDIS_URL:-}" ]]; then
  echo "ERROR: REDIS_URL must be explicitly set before starting web."
  exit 2
fi

PYTHON_BIN="${PYTHON_BIN:-$PROJECT_ROOT/.venv/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3 || true)"
fi

if [[ -z "$PYTHON_BIN" ]]; then
  echo "ERROR: Python interpreter not found."
  exit 3
fi

CPU_COUNT="$(getconf _NPROCESSORS_ONLN 2>/dev/null || nproc 2>/dev/null || echo 2)"
WEB_WORKERS="${WEB_WORKERS:-$((CPU_COUNT * 2 + 1))}"
WEB_THREADS="${WEB_THREADS:-2}"

export DEBUG="${DEBUG:-False}"

echo "Starting Django application..."
echo "Resolved REDIS_URL: $(mask_redis_url "$REDIS_URL")"
echo "DEBUG=$DEBUG"
echo "Gunicorn workers=$WEB_WORKERS threads=$WEB_THREADS"

echo "Running migrations..."
"$PYTHON_BIN" manage.py migrate --noinput

echo "Starting Gunicorn..."
exec "$PYTHON_BIN" -m gunicorn backend.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers "$WEB_WORKERS" \
  --threads "$WEB_THREADS" \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
