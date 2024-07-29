#!/bin/bash

# Navigate to the InstructLab directory
cd ~/InstructLab-QA-Generator || { echo "Failed to navigate to InstructLab directory. Exiting..."; exit 1; }

# Activate the Python virtual environment
source venv/bin/activate || { echo "Failed to activate virtual environment. Exiting..."; exit 1; }

# Function to remove the tested model from the model_list in config.yaml
remove_tested_model() {
    local model_to_remove=$1
    python -c "
import yaml
config_path='config.yaml'
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)
if '$model_to_remove' in config['model_list']:
    config['model_list'].remove('$model_to_remove')
with open(config_path, 'w') as file:
    yaml.dump(config, file, default_flow_style=False)
" || { echo "Failed to remove tested model. Exiting..."; exit 1; }
}

# Run the generate_project_qa.py script with optimization and save the results to a CSV file
while true; do
    python generate_project_qa.py --config_path config.yaml --save_scores
    if [ $? -ne 0 ]; then
        echo "Error occurred during script execution. Exiting..."
        exit 1
    fi
    # Get the last model from the model_list in config.yaml
    tested_model=$(python -c "
import yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)
print(config['model_list'][-1] if config['model_list'] else '')
") || { echo "Failed to retrieve the last model. Exiting..."; exit 1; }

    if [ -z "$tested_model" ]; then
        echo "No more models to test. Exiting..."
        break
    fi

    # Check if qna.yml exists before removing the tested model
    yaml_file_path=$(python -c "
import os
import yaml
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)
taxonomy_path = os.path.join(config['taxonomy_dir'], 'knowledge', config['project_name'].lower(), 'overview')
yaml_path = config['yaml_path']
print(os.path.join(taxonomy_path, yaml_path))
") || { echo "Failed to construct yaml file path. Exiting..."; exit 1; }

    if [ -f "$yaml_file_path" ]; then
        remove_tested_model "$tested_model"
    else
        echo "Skipping model removal as $yaml_file_path does not exist."
        exit $?
    fi
done
