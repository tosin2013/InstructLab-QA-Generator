#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Variables
GITHUB_OWNER="tosin2013"          # Replace with your GitHub username or organization name
GITHUB_REPO="InstructLab-QA-Generator" # Replace with your GitHub repository name
GITHUB_TOKEN="your-token"         # Replace with your GitHub Personal Access Token (should be set as an environment variable)
RUNNER_VERSION="2.317.0"          # Desired GitHub Runner version
RUNNER_NAME="rhel9-runner"        # Customize the runner name
RUNNER_DIR="$HOME/actions-runner" # Directory where the runner will be installed
TMUX_SESSION="github-runner"      # Name of the tmux session

# Install tmux if it is not installed
if ! command -v tmux &> /dev/null
then
    echo "tmux not found. Installing tmux..."
    sudo yum install -y tmux
fi

# Create the runner directory
mkdir -p $RUNNER_DIR
cd $RUNNER_DIR

# Download the specified version of the GitHub Runner package for Linux x64
echo "Downloading GitHub Runner..."
curl -o actions-runner-linux-x64-$RUNNER_VERSION.tar.gz -L https://github.com/actions/runner/releases/download/v$RUNNER_VERSION/actions-runner-linux-x64-$RUNNER_VERSION.tar.gz

# Optional: Validate the hash (update the hash if using a different version)
echo "Validating download..."
echo "9e883d210df8c6028aff475475a457d380353f9d01877d51cc01a17b2a91161d  actions-runner-linux-x64-$RUNNER_VERSION.tar.gz" | sha256sum -c

# Extract the runner package
echo "Extracting GitHub Runner..."
tar xzf ./actions-runner-linux-x64-$RUNNER_VERSION.tar.gz

# Install dependencies
echo "Installing dependencies..."
sudo yum install -y gcc libicu

# Configure the runner
echo "Configuring GitHub Runner..."
./config.sh --url https://github.com/$GITHUB_OWNER/$GITHUB_REPO --token $GITHUB_TOKEN --name $RUNNER_NAME --work _work

# Install systemd service
#echo "Installing systemd service..."
#sudo ./svc.sh install

# Start the runner service within tmux
echo "Starting GitHub Runner service in tmux session..."
tmux new-session -d -s $TMUX_SESSION "sudo ./svc.sh install && sudo  ./runsvc.sh"

echo "GitHub Runner has been successfully set up and started in tmux session '$TMUX_SESSION'."
echo "You can attach to the session using: tmux attach -t $TMUX_SESSION"


