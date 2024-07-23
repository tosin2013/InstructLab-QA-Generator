#!/bin/bash

# Update the system
sudo yum update -y

# Install necessary dependencies
sudo yum install -y python3 python3-venv python3-pip git gcc

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install the required Python packages
pip install -r requirements.txt

echo "Setup complete. To activate the virtual environment, run 'source venv/bin/activate'."
