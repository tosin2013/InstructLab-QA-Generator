#!/bin/bash
set -x 

if [ -f /tmp/config.yaml ]; then
    cp /tmp/config.yaml ~/InstructLab-QA-Generator/config.yaml || { echo "Failed to copy config.yaml. Exiting..."; exit 1; }
else
    echo "config.yaml not found. Exiting..."
    exit 1
fi

# Navigate to the InstructLab directory
cd ~/InstructLab-QA-Generator || { echo "Failed to navigate to InstructLab directory. Exiting..."; exit 1; }

# Activate the Python virtual environment
source venv/bin/activate || { echo "Failed to activate virtual environment. Exiting..."; exit 1; }

# Function to remove the tested model from the model_list in config.yaml using yq
remove_tested_model() {
    local model_to_remove=$1
    yq -i 'del(.model_list[] | select(. == "'"$model_to_remove"'"))' config.yaml || { echo "Failed to remove tested model. Exiting..."; exit 1; }
}

# Run the generate_project_qa.py script with optimization and save the results to a CSV file
while true; do
    python generate_project_qa.py --config_path config.yaml --save_scores
    if [ $? -ne 0 ]; then
        echo "Error occurred during script execution. Exiting..."
        exit 1
    fi

    # Get the last model from the model_list in config.yaml using yq
    tested_model=$(yq '.model_list[-1]' config.yaml) || { echo "Failed to retrieve the last model. Exiting..."; exit 1; }

    if [ -z "$tested_model" ]; then
        echo "No more models to test. Exiting..."
        break
    fi

    # Remove the tested model from the model_list
    remove_tested_model "$tested_model"
done
