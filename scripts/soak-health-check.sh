#!/usr/bin/env bash
set -euo pipefail

# Lightweight soak smoke for self-hosted runners: repeated health/doctor checks.
# Usage: ./scripts/soak-health-check.sh [iterations] [sleep_seconds]

ITERATIONS="${1:-12}"
SLEEP_SECONDS="${2:-30}"
CONFIG_DIR="${EXPANDO_CONFIG_DIR:-$HOME/Library/Application Support/expando}"

echo "Soak health check: ${ITERATIONS} iterations, ${SLEEP_SECONDS}s interval"
echo "Config dir: ${CONFIG_DIR}"

for ((i = 1; i <= ITERATIONS; i++)); do
  echo "[$i/$ITERATIONS] expando health"
  expando --config-dir "$CONFIG_DIR" health
  echo "[$i/$ITERATIONS] expando doctor (summary)"
  expando --config-dir "$CONFIG_DIR" doctor | head -n 20
  if (( i < ITERATIONS )); then
    sleep "$SLEEP_SECONDS"
  fi
done

echo "Soak health check completed."