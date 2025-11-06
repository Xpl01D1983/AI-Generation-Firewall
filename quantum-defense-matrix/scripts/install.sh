#!/usr/bin/env bash
set -euo pipefail

echo "[Quantum Defense] Installing dependencies..."

if ! command -v python3 >/dev/null 2>&1; then
    sudo dnf install -y python3 python3-virtualenv
fi

python3 -m venv /opt/quantum-defense
/opt/quantum-defense/bin/pip install --upgrade pip
/opt/quantum-defense/bin/pip install quantum-defense-matrix

echo "[Quantum Defense] Installation complete."
