import os
import git
import yaml
import argparse
import nltk
from nltk.corpus import stopwords
from collections import Counter
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Download necessary NLTK data if not already downloaded
nltk.download('stopwords')
nltk.download('punkt')

# CLI for asking repo_url, clone_dir, project_name, and commit_id
parser = argparse.ArgumentParser(description="Clone a GitHub repo and generate a configuration YAML file.")
parser.add_argument('repo_url', type=str, help='The URL of the GitHub repository to clone')
parser.add_argument('clone_dir', type=str, help='The directory where the repository will be cloned')
parser.add_argument('--project_name', type=str, default="InstructLab", help='The name of the project')
parser.add_argument('--commit_id', type=str, default="83d9852ad97c6b27d4b24508f7cfe7ff5dd04d0d", help='The commit ID of the repository')

args = parser.parse_args()
repo_url = args.repo_url
clone_dir = args.clone_dir
project_name = args.project_name
commit_id = args.commit_id

# Clone the repository
if not os.path.exists(clone_dir):
    git.Repo.clone_from(repo_url, clone_dir)

# Function to find files and create patterns
def find_files_and_patterns(base_dir):
    file_extensions = set()
    max_depth = 0

    for root, _, filenames in os.walk(base_dir):
        # Calculate the depth of the current directory
        depth = root[len(base_dir):].count(os.sep)
        max_depth = max(max_depth, depth)

        for filename in filenames:
            file_extension = os.path.splitext(filename)[1]
            file_extensions.add(file_extension)
            
            # Special case for README.md
            if filename == 'README.md':
                file_extensions.add('README.md')

    patterns = set()

    # Generate patterns for each file extension
    for extension in file_extensions:
        if extension == 'README.md':
            patterns.add('README.md')
        else:
            patterns.add(f'*{extension}')
            for depth in range(1, max_depth + 1):
                patterns.add(f'{"**/" * depth}*{extension}')

    return sorted(patterns)

# Function to extract keywords from README.md
def extract_keywords_from_readme(readme_path, num_keywords=10):
    stop_words = set(stopwords.words('english'))
    word_counter = Counter()

    try:
        with open(readme_path, 'r', errors='ignore') as file:
            content = file.read().lower()
            words = nltk.word_tokenize(content)
            filtered_words = [word for word in words if word.isalnum() and word not in stop_words]
            word_counter.update(filtered_words)
    except Exception as e:
        logging.error(f"Error reading file {readme_path}: {e}")

    most_common_words = [word for word, _ in word_counter.most_common(num_keywords)]
    return most_common_words

# Function to read files and handle errors
def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            logging.info(f"Read file: {file_path} successfully")
            return content
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return ""

# Get the matching patterns
patterns = find_files_and_patterns(clone_dir)

# Path to README.md
readme_path = os.path.join(clone_dir, 'README.md')

# Extract dynamic keywords from the README.md content
dynamic_keywords = extract_keywords_from_readme(readme_path)

# Define the full configuration data
config_data = {
    "project_name": project_name,
    "repo_url": repo_url,
    "commit_id": commit_id,
    "patterns": patterns,
    "yaml_path": "qna.yaml",
    "max_files": 100,
    "max_lines": 2000,
    "keywords": dynamic_keywords,
    "min_sentence_length": 5,
    "min_answers": 5,
    "questions": [
        "What is {project_name}?",
        "How to get started with {project_name}?",
        "What problems is {project_name} aiming to solve?",
        "Who created {project_name}?",
        "How does {project_name} enable community collaboration?",
        "Is {project_name} an open-source project?",
        "What is the tuning method for {project_name}?",
        "What is the mission of {project_name}?",
        "What technologies or programming languages is {project_name} developed in?",
        "What are the key features of {project_name}?",
        "What are the current limitations of {project_name}?",
        "How can contributors improve {project_name}?",
        "What are the future goals for {project_name}?",
        "How is {project_name} maintained and updated?",
        "What are the recommended best practices for using {project_name}?",
        "What are the main challenges faced by {project_name}?"
    ],
    "chat": {
        "enabled": True,
        "model": "deepset/roberta-base-squad2"
    },
    "generate": {
        "enabled": True,
        "model": "deepset/roberta-base-squad2",
        "taxonomy_path": "~/instructlab/taxonomy",
        "taxonomy_base": "~/instructlab/taxonomy"
    },
    "serve": {
        "enabled": True,
        "model_path": "~/instructlab/models/roberta-base-squad2"
    },
    "taxonomy_dir": "~/instructlab/taxonomy",
    "pushgateway_url": "http://your-pushgateway-url:9091",
    "username": "your_username",
    "password": "your_password",
    "model_name": "deepset/roberta-base-squad2",
    "optimize": False,
    "model_list": [
        "deepset/roberta-base-squad2",
        "bert-large-uncased-whole-word-masking-finetuned-squad",
        "distilbert-base-cased-distilled-squad",
        "albert-base-v2",
        "t5-base",
        "ibm/labradorite-13b",
        "ibm/merlinite-7b",
        "ibm/re2g-reranker-trex"
    ]
}

# Write the data to a YAML file
yaml_file = "config.yaml"
with open(yaml_file, 'w') as file:
    yaml.dump(config_data, file, default_flow_style=False)

# Append the available models as comments in the YAML file
with open(yaml_file, 'a') as file:
    file.write("\n# Available models:\n")
    file.write("# - deepset/roberta-base-squad2\n")
    file.write("# - bert-large-uncased-whole-word-masking-finetuned-squad\n")
    file.write("# - distilbert-base-cased-distilled-squad\n")
    file.write("# - albert-base-v2\n")
    file.write("# - t5-base\n")
    file.write("# - ibm/labradorite-13b\n")
    file.write("# - ibm/merlinite-7b\n")
    file.write("# - ibm/re2g-reranker-trex\n")
    file.write("#\n")
    file.write("# To find more models, visit https://huggingface.co/models\n")
    file.write("# https://huggingface.co/models?pipeline_tag=question-answering\n")

print(f"Repository cloned to '{clone_dir}' and '{yaml_file}' generated successfully with dynamic keywords: {dynamic_keywords}.")
