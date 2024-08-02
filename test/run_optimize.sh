#!/bin/bash
set -e 

# Function to print colored messages
print_colored_message() {
    local color=$1
    local message=$2
    case $color in
        "red") echo -e "\e[31m$message\e[0m" ;;
        "green") echo -e "\e[32m$message\e[0m" ;;
        "yellow") echo -e "\e[33m$message\e[0m" ;;
        "blue") echo -e "\e[34m$message\e[0m" ;;
        "magenta") echo -e "\e[35m$message\e[0m" ;;
        "cyan") echo -e "\e[36m$message\e[0m" ;;
        *) echo "$message" ;;
    esac
}

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
    print_colored_message "cyan" "Running optimization with the following model:"
    tested_model=$(yq '.model_list[-1]' config.yaml) || { echo "Failed to retrieve the last model. Exiting..."; exit 1; }
    print_colored_message "green" "$tested_model"

    python generate_project_qa.py --config_path config.yaml --save_scores
    if [ $? -ne 0 ]; then
        print_colored_message "red" "Error occurred during script execution. Exiting..."
        exit 1
    fi

    if [ -z "$tested_model" ]; then
        print_colored_message "yellow" "No more models to test. Exiting..."
        break
    fi

    # Remove the tested model from the model_list
    remove_tested_model "$tested_model"
done
