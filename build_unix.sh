#!/bin/bash

echo "Creating virtual environment..."
python3 -m venv venv

echo
echo "Activating virtual environment..."
source venv/bin/activate

echo
echo "Installing requirements..."
pip install -r requirements.txt

echo
echo "Building application..."
python build.py

echo
echo "Build process complete!"
echo "Press Enter to exit..."
read

deactivate
