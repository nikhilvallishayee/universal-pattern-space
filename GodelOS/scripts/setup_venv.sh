#!/bin/bash

# This script sets up a Python virtual environment for the GödelOS project.

VENV_DIR="godelos_venv"
PYTHON_EXE="python3"

# Check if python3 is available
if ! command -v $PYTHON_EXE &> /dev/null
then
    echo "$PYTHON_EXE could not be found. Please install Python 3."
    exit 1
fi

echo "Creating virtual environment in '$VENV_DIR'..."

# Create the virtual environment
$PYTHON_EXE -m venv $VENV_DIR

# Check if the virtual environment was created successfully
if [ ! -d "$VENV_DIR" ]; then
    echo "Failed to create virtual environment."
    exit 1
fi

echo "Virtual environment created."
echo "To activate it, run: source $VENV_DIR/bin/activate"

# Activate the environment for the rest of the script
source $VENV_DIR/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "Installing dependencies from backend/requirements.txt..."
pip install -r backend/requirements.txt

echo "Verifying core imports..."
python - <<'PY'
import importlib, sys
packages = ['fastapi', 'pydantic', 'spacy']
missing = [p for p in packages if importlib.util.find_spec(p) is None]
if missing:
    print(f"❌ Missing packages: {', '.join(missing)}")
    sys.exit(1)
print("✅ All required packages are available")
PY

echo ""
echo "Setup complete! The virtual environment '$VENV_DIR' is ready."
echo "Remember to activate it in your shell by running: source $VENV_DIR/bin/activate"
