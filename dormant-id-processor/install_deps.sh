#!/bin/bash
# Install dependencies script

echo "Installing dependencies..."

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing requirements..."
pip install -r requirements.txt

echo ""
echo "✅ Installation complete!"
echo ""
echo "To run the processor:"
echo "  source venv/bin/activate"
echo "  python main.py"

# Made with Bob
