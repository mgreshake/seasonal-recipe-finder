#!/usr/bin/env bash

PYTHON_BIN="python3"
VENV_DIR=".venv"
REQ_FILE="requirements.txt"
SCRIPT="src/main.py"

if ! command -v $PYTHON_BIN &> /dev/null; then
  echo "ERROR: No Python 3 instance found"
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  echo "Create new virtual environment in $VENV_DIR"
  if ! $PYTHON_BIN -m venv "$VENV_DIR" &> /dev/null; then
    echo "ERROR: Python venv module is missing"
    rm -rf "$VENV_DIR"
    exit 1
  fi
  source "$VENV_DIR/bin/activate"
  pip install --upgrade pip
  echo "Install package dependencies from $REQ_FILE"
  pip install -r "$REQ_FILE"
else
  echo "Existing virtual environment found"
  source "$VENV_DIR/bin/activate"
fi

echo "Run Seasonal Recipe Finder..."
$PYTHON_BIN "$SCRIPT"
echo "Exit Seasonal Recipe Finder"
