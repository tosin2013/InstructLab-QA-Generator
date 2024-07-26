#!/bin/bash

# Run the generate_project_qa.py script with optimization and save the results to a CSV file
#!/bin/bash

# Function to remove the tested model from the model_list in config.yaml
remove_tested_model() {
    local model_to_remove=$1
    python -c "import yaml; config_path='config.yaml'; config=yaml.safe_load(open(config_path)); config['model_list'].remove('$model_to_remove'); yaml.dump(config, open(config_path, 'w'))"
}

# Run the generate_project_qa.py script with optimization and save the results to a CSV file
while true; do
    python generate_project_qa.py --config_path config.yaml --save_scores
    if [ $? -ne 0 ]; then
        echo "Error occurred during script execution. Exiting..."
        exit 1
    fi
    tested_model=$(python -c "import yaml; config=yaml.safe_load(open('config.yaml')); print(config['model_list'][-1] if config['model_list'] else '')")
    if [ -z "$tested_model" ]; then
        echo "No more models to test. Exiting..."
        break
    fi
    remove_tested_model "$tested_model"
done
