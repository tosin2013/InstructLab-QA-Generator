#!/bin/bash

# curl -OL https://gist.githubusercontent.com/tosin2013/695835751174d725ac196582f3822137/raw/d12cd0fb7960d9928f6c83d9364973e1cd7572ce/configure-rhel9.x.sh
# chmod +x configure-rhel9.x.sh
# ./configure-rhel9.x.sh

# Update the system
sudo yum update -y

# Install necessary dependencies
sudo yum install -y python3 python3-venv python3-pip git gcc g++ gcc-c++


# Set the CXX environment variable to the path of the C++ compiler
export CXX=g++

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install the required Python packages
pip install -r requirements.txt

echo "Setup complete. To activate the virtual environment, run 'source venv/bin/activate'."
