#!/usr/bin/env bash
set -euo pipefail

echo "[swiggy-oauth-vps] Checking Python..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required. Install python3 first." >&2
  exit 1
fi

echo "[swiggy-oauth-vps] Creating virtualenv (.venv)..."
python3 -m venv .venv

source .venv/bin/activate

echo "[swiggy-oauth-vps] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[swiggy-oauth-vps] Done. Use:"
echo "  source .venv/bin/activate"
echo "  python3 scripts/swiggy_oauth_manual.py interactive --out ~/.swiggy-oauth/latest-token.json"
