import git
import yaml
import os
import glob
import logging
from transformers import pipeline
from nltk.tokenize import sent_tokenize, blankline_tokenize

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to read the Git repository
def read_git_repo(repo_url, commit_id, patterns, max_files):
    repo_dir = "/tmp/repo"  # Temporary directory to clone the repo
    if os.path.exists(repo_dir):
        os.system(f"rm -rf {repo_dir}")

    logging.info(f"Cloning repository {repo_url}")
    repo = git.Repo.clone_from(repo_url, repo_dir)
    repo.git.checkout(commit_id)
    
    content = {}
    file_count = 0
    for pattern in patterns:
        file_paths = glob.glob(os.path.join(repo_dir, pattern), recursive=True)
        for file_path in file_paths:
            if file_count >= max_files:
                break
            with open(file_path, 'r') as file:
                content[file_path] = file.read()
            file_count += 1
            logging.info(f"Read file: {file_path}")
        if file_count >= max_files:
            break
    
    return content

# Function to extract relevant sections based on keywords
def extract_relevant_sections(text, keywords):
    sections = []
    paragraphs = blankline_tokenize(text)
    for paragraph in paragraphs:
        for keyword in keywords:
            if keyword.lower() in paragraph.lower():
                sections.append(paragraph)
                break
    return sections

# Function to combine relevant sections for better context
def combine_relevant_sections(sections):
    combined_sections = []
    current_section = ""
    for section in sections:
        if len(current_section) + len(section) < 4096:  # Increase token limit for better context
            current_section += " " + section
        else:
            combined_sections.append(current_section.strip())
            current_section = section
    if current_section:
        combined_sections.append(current_section.strip())
    return combined_sections

# Function to generate questions and answers using specified models
def generate_qa_pairs(sections, project_name, min_sentence_length):
    question_answerer = pipeline("question-answering", model="deepset/roberta-base-squad2")

    # Define some initial questions to simulate the process
    questions = [
        f"What is {project_name}?",
        f"How to get started with {project_name}?",
        f"What problems is {project_name} aiming to solve?",
        f"Who created {project_name}?",
        f"How does {project_name} enable community collaboration?",
        f"Is {project_name} an open source project?",
        f"What is the tuning method for {project_name}?",
        f"What is the mission of {project_name}?"
    ]

    seed_examples = []
    for question in questions:
        best_answer = ""
        best_score = 0.0
        for section in sections:
            try:
                answer = question_answerer(question=question, context=section)
                if answer['score'] > best_score and len(answer['answer'].split()) >= min_sentence_length:
                    best_answer = answer['answer']
                    best_score = answer['score']
            except Exception as e:
                logging.error(f"Error processing question '{question}' with context '{section}': {e}")
                continue
        if best_answer.strip() and len(best_answer.split()) >= min_sentence_length:
            seed_examples.append({'question': question, 'answer': best_answer.strip()})
        else:
            logging.warning(f"Skipped question '{question}' due to insufficient answer length.")

    return seed_examples

# Function to generate the YAML file
def generate_yaml(repo_url, commit_id, patterns, yaml_path, project_name, max_files, max_lines, keywords, min_sentence_length, min_answers):
    logging.info("Starting YAML generation process")
    repo_content = read_git_repo(repo_url, commit_id, patterns, max_files)
    combined_content = ""

    for file_path, file_content in repo_content.items():
        lines = file_content.split('\n')
        combined_content += "\n".join(lines[:max_lines]) + "\n"
        if len(combined_content.split('\n')) >= max_lines:
            break

    # Extract relevant sections based on keywords
    relevant_sections = extract_relevant_sections(combined_content, keywords)

    # Combine relevant sections for better context
    combined_sections = combine_relevant_sections(relevant_sections)

    # Generate seed examples from the relevant sections
    seed_examples = generate_qa_pairs(combined_sections, project_name, min_sentence_length)

    # Check if the minimum number of answers is met
    if len(seed_examples) < min_answers:
        logging.error(f"Failed to generate the minimum required number of answers ({min_answers}).")
        raise ValueError(f"Failed to generate the minimum required number of answers ({min_answers}).")

    document_content = {
        'created_by': f'{project_name.lower()}-team',
        'domain': project_name.lower(),
        'seed_examples': seed_examples,
        'task_description': f'Details on {project_name.lower()} community project',
        'document': {
            'repo': repo_url,
            'commit': commit_id,
            'patterns': patterns
        }
    }

    with open(yaml_path, 'w') as yaml_file:
        yaml.dump(document_content, yaml_file, default_flow_style=False)
    
    logging.info(f"YAML file generated at: {yaml_path}")

# Main script
project_name = 'InstructLab'  # Change this to the name of your project
repo_url = 'https://github.com/instructlab/.github'
commit_id = '83d9852ad97c6b27d4b24508f7cfe7ff5dd04d0d'
patterns = ['README.md', '**/*.md', '**/*.txt', '**/*.yaml']
yaml_path = 'qna.yaml'
max_files = 100  # Maximum number of files to read
max_lines = 2000  # Maximum number of lines to read from each file
keywords = ['InstructLab', 'getting started', 'problems', 'created', 'collaboration', 'open source', 'tuning method', 'mission']  # Keywords to search for relevant sections
min_sentence_length = 10  # Minimum number of words in the answer
min_answers = 5  # Minimum number of valid answers required

generate_yaml(repo_url, commit_id, patterns, yaml_path, project_name, max_files, max_lines, keywords, min_sentence_length, min_answers)
