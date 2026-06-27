#!/bin/bash
# Celery worker startup script

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

mask_redis_url() {
  echo "$1" | sed -E 's#(redis[s]?://)([^:@/]+:)?([^@/]+)@#\1***:***@#'
}

if [[ -z "${REDIS_URL:-}" ]]; then
  echo "ERROR: REDIS_URL must be explicitly set before starting Celery."
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

CELERY_CONCURRENCY="${CELERY_CONCURRENCY:-2}"
CELERY_QUEUES="${CELERY_QUEUES:-celery,notifications,payments}"

echo "Starting Celery worker..."
echo "Resolved REDIS_URL: $(mask_redis_url "$REDIS_URL")"
echo "Queues: $CELERY_QUEUES"

exec "$PYTHON_BIN" -m celery -A backend worker \
  --loglevel=info \
  --concurrency="$CELERY_CONCURRENCY" \
  --max-tasks-per-child=1000 \
  --time-limit=1800 \
  --soft-time-limit=1500 \
  -Q "$CELERY_QUEUES"
