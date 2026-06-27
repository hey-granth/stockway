#!/usr/bin/env bash
# run_load_test.sh
# Staged load test for Stockway. Three phases:
#   1. Warm-up   : 20 users, 2 min  — confirm zero errors before scaling
#   2. Ramp      : 100 users, 5 min — find the first bottleneck
#   3. Peak      : 200 users, 8 min — sustained stress, where resume numbers come from
#
# Prerequisites:
#   - Stockway running at $HOST (Docker Compose or deployed instance)
#   - uv installed, dependencies in pyproject.toml
#   - Pre-seeded test accounts (see load_tests/config.py)
#
# Usage:
#   chmod +x run_load_test.sh
#   HOST=http://localhost:8000 bash run_load_test.sh

set -euo pipefail

HOST="${HOST:-http://localhost:8000}"
RESULTS_DIR="load_tests/results/$(date +%Y%m%d_%H%M%S)"
LOCUSTFILE="load_tests/locustfile.py"

mkdir -p "$RESULTS_DIR"

echo "========================================"
echo " Stockway Load Test — $(date)"
echo " Host     : $HOST"
echo " Output   : $RESULTS_DIR"
echo "========================================"

run_phase() {
  local phase=$1
  local users=$2
  local spawn_rate=$3
  local duration=$4
  local tag="${RESULTS_DIR}/${phase}"

  echo ""
  echo "--- Phase: $phase | Users: $users | Duration: ${duration} ---"

  uv run locust \
    -f "$LOCUSTFILE" \
    --headless \
    --host="$HOST" \
    -u "$users" \
    -r "$spawn_rate" \
    --run-time "$duration" \
    --csv="$tag" \
    --html="${tag}_report.html" \
    --csv-full-history \
    --logfile="${tag}.log" \
    2>&1 | tee "${tag}_stdout.txt"

  echo "Phase $phase complete. Reports: ${tag}_report.html"
}

# Phase 1: Warm-up — 20 users, ramp 5/s, 2 minutes
# Purpose: Confirm auth, seeded data, and routing work before scaling.
# Abort the full test if error rate > 1% here.
run_phase "1_warmup" 20 5 2m

# Check warm-up error rate before proceeding
WARMUP_FAILURES=$(grep -oP '"num_failures":\s*\K\d+' "${RESULTS_DIR}/1_warmup_stats.csv" | tail -1 || echo "0")
if [ "${WARMUP_FAILURES:-0}" -gt 5 ]; then
  echo "ERROR: Warm-up phase had $WARMUP_FAILURES failures. Fix errors before scaling. Aborting."
  exit 1
fi

# Phase 2: Ramp — 100 users, ramp 10/s, 5 minutes
# Purpose: Find the first bottleneck (DB pool, Redis, Celery queue depth).
# Watch logs for: django.db.utils.OperationalError (pool exhaustion),
# slow PostGIS queries, Celery task queue backup.
run_phase "2_ramp" 100 10 5m

# Phase 3: Peak — 200 users, ramp 20/s, 8 minutes
# Purpose: Sustained stress. Resume numbers come from this phase.
# Target: p95 < 500ms, failure rate < 0.5%, RPS > 50.
run_phase "3_peak" 200 20 8m

echo ""
echo "========================================"
echo " All phases complete."
echo " Resume-worthy metrics to pull from:"
echo "   ${RESULTS_DIR}/3_peak_report.html"
echo ""
echo " Key numbers to check (phase 3 Aggregated row):"
echo "   - Total Requests"
echo "   - RPS (requests/sec)"
echo "   - p50, p95 response times"
echo "   - Failure rate (target: < 0.5%)"
echo "========================================"