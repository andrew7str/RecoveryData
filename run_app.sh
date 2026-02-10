#!/usr/bin/env bash
set -euo pipefail

# Simple runner for the recovery helper on Linux/Debian
# - creates a Python venv (optional)
# - installs Python requirements from requirements.txt
# - optionally installs recommended system packages on Debian-based systems
# - runs recover.py

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

echo "Working dir: $ROOT_DIR"

if [ -f /etc/debian_version ]; then
  echo "Detected Debian-based system." 
  read -rp "Install recommended system packages (gddrescue testdisk foremost scalpel)? [y/N]: " INSTALL_SYS
  if [[ "$INSTALL_SYS" =~ ^[Yy]$ ]]; then
    if [ "$EUID" -ne 0 ]; then
      echo "Will attempt to install via sudo (you may be prompted for password)."
      sudo apt update
      sudo apt install -y gddrescue testdisk foremost scalpel
    else
      apt update
      apt install -y gddrescue testdisk foremost scalpel
    fi
  fi
fi

echo "Creating virtualenv (if missing) at $VENV_DIR"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
if [ -f "$ROOT_DIR/requirements.txt" ]; then
  "$VENV_DIR/bin/pip" install -r "$ROOT_DIR/requirements.txt"
fi

echo "Starting recover.py (use sudo if you need raw device access)."
exec "$VENV_DIR/bin/python" "$ROOT_DIR/recover.py"
