#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

echo ""
echo "Expando installato. Per usarlo:"
echo "  source $(pwd)/.venv/bin/activate"
echo "  expando start"
echo ""
echo "Avvio automatico al login:"
echo "  ./scripts/install-launch-agent.sh"
echo ""
echo "Config: ~/Library/Application Support/expando"