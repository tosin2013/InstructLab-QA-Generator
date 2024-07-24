# generate_project_qa.py Script

## Purpose and Goals

The `generate_project_qa.py` script is designed to automate the generation of question-answer pairs from a Git repository. It leverages the power of NLP models to extract relevant information from the repository's content and generate meaningful Q&A pairs. The script can also be used to optimize different models to determine the best one for sentence transformation tasks.

## Use Cases

1. **Automated Documentation**: Generate Q&A pairs to create documentation for a project.
2. **Model Optimization**: Evaluate different NLP models to find the best one for specific tasks.
3. **Knowledge Extraction**: Extract relevant information from a repository for further analysis.

## How to Use the Script

### Prerequisites

- Python 3.6 or higher
- Required Python packages (listed in `requirements.txt`)

### Installation

1. Clone the repository:
    ```sh
    git clone <repository_url>
    cd <repository_directory>
    ```

2. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

### Configuration

Create a `config.yaml` file in the root directory of the project. This file should contain the necessary configuration parameters. Below is an example configuration:

```yaml
project_name: "ExampleProject"
repo_url: "https://github.com/example/repo.git"
commit_id: "main"
patterns:
  - "**/*.py"
yaml_path: "output.yaml"
max_files: 10
max_lines: 1000
keywords:
  - "def"
  - "class"
min_sentence_length: 5
min_answers: 3
questions:
  - "What does the {project_name} project do?"
  - "How does {project_name} handle errors?"
taxonomy_dir: "/path/to/taxonomy"
model_name: "distilbert-base-uncased"
optimize: false
model_list:
  - "distilbert-base-uncased"
  - "bert-base-uncased"
```

### Running the Script as a Single User

To run the script against a repository and generate Q&A pairs, use the following command:

```sh
python generate_project_qa.py --config_path config.yaml
```

### Optimizing Models

To optimize different models for sentence transformation, set the `optimize` flag to `true` in the `config.yaml` file and provide a list of models in the `model_list` parameter. Then run the script:

```sh
python generate_project_qa.py --config_path config.yaml
```

The script will iterate through the list of models and generate Q&A pairs for each model, logging the results for comparison.

### Saving Model Scores

To save the scores of the models during optimization, use the `--save_scores` flag:

```sh
python generate_project_qa.py --config_path config.yaml --save_scores
```

## Example

Here is an example of how to use the script:

1. Create a `config.yaml` file with the desired configuration.
2. Run the script to generate Q&A pairs:
    ```sh
    python generate_project_qa.py --config_path config.yaml
    ```
3. If optimizing models, set the `optimize` flag to `true` and run the script:
    ```sh
    python generate_project_qa.py --config_path config.yaml
    ```

The generated Q&A pairs will be saved in the specified YAML file, and the script will log the process and results.

## Conclusion

The `generate_project_qa.py` script is a powerful tool for automating the generation of Q&A pairs and optimizing NLP models. By following the steps outlined in this README, you can easily configure and run the script to meet your specific needs.
