#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

cd "$PROJECT_DIR"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
echo "Using Python: $(python -c 'import sys; print(sys.executable)')"

echo "Installing requirements..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Starting Flask server..."
python server/main.py
