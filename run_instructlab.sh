#!/bin/bash

# Navigate to the InstructLab directory
cd ~/instructlab

# Activate the Python virtual environment
source venv/bin/activate

# Install the command line tool using pip
pip3 install git+https://github.com/instructlab/instructlab.git@v0.16.1

# Verify ilab is installed correctly
ilab

# Initialize ilab
ilab init

# Download the model
ilab download --repository instructlab/granite-7b-lab-GGUF --filename=granite-7b-lab-Q4_K_M.gguf

# Serve the model
ilab serve --model-path models/granite-7b-lab-Q4_K_M.gguf

# Open a new terminal window and activate the environment
# (This step cannot be automated in a script, so it needs to be done manually)

# Chat with the model
ilab chat -m models/granite-7b-lab-Q4_K_M.gguf

# Stop the server (manually with CTRL+C)
# (This step cannot be automated in a script, so it needs to be done manually)

# Serve the merlinite model for synthetic data generation
ilab serve --model-path models/merlinite-7b-lab-Q4_K_M.gguf

# Generate synthetic data
ilab generate --num-instructions 5

# Stop the server (manually with CTRL+C)
# (This step cannot be automated in a script, so it needs to be done manually)

# Serve the new model
ilab serve --model-path models/ggml-ilab-pretrained-Q4_K_M.gguf

# Chat with the new model
ilab chat -m models/ggml-ilab-pretrained-Q4_K_M.gguf
