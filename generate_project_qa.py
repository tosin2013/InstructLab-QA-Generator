import git
import yaml
import os
import glob
import logging
from transformers import pipeline
from nltk.tokenize import sent_tokenize, blankline_tokenize
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to read the configuration file
def read_config(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

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
            if os.path.isdir(file_path):
                continue  # Skip directories
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
def generate_qa_pairs(sections, project_name, questions, min_sentence_length):
    question_answerer = pipeline("question-answering", model="deepset/roberta-base-squad2")

    seed_examples = []
    for question_template in questions:
        question = question_template.format(project_name=project_name)
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
            logging.warning(f"Skipped question '{question}' due to insufficient answer length. Answer: '{best_answer}', Length: {len(best_answer.split())}")

    return seed_examples

# Function to validate taxonomy
def validate_taxonomy():
    result = os.system("ilab diff")
    if result != 0:
        logging.error("Taxonomy validation failed.")
        raise ValueError("Taxonomy validation failed.")
    else:
        logging.info("Taxonomy is valid.")

# Function to generate synthetic data
def generate_synthetic_data():
    logging.info("Generating synthetic data...")
    result = os.system("ilab generate --samples 5")
    if result != 0:
        logging.error("Failed to generate synthetic data.")
        raise ValueError("Failed to generate synthetic data.")
    else:
        logging.info("Synthetic data generation completed.")

# Function to generate the YAML file
def generate_yaml(repo_url, commit_id, patterns, yaml_path, project_name, questions, max_files, max_lines, keywords, min_sentence_length, min_answers):
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
    seed_examples = generate_qa_pairs(combined_sections, project_name, questions, min_sentence_length)

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

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(yaml_path), exist_ok=True)

    with open(yaml_path, 'w') as yaml_file:
        yaml.dump(document_content, yaml_file, default_flow_style=False)
    
    logging.info(f"YAML file generated at: {yaml_path}")

    # Validate taxonomy
    validate_taxonomy()

    # Generate synthetic data
    generate_synthetic_data()

# Main script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate QnA YAML from a Git repository.")
    parser.add_argument('--project_name', type=str, default=os.getenv('PROJECT_NAME', 'InstructLab'), help='Project name')
    parser.add_argument('--repo_url', type=str, default=os.getenv('REPO_URL', 'https://github.com/instructlab/.github'), help='Repository URL')
    parser.add_argument('--commit_id', type=str, default=os.getenv('COMMIT_ID', '83d9852ad97c6b27d4b24508f7cfe7ff5dd04d0d'), help='Commit ID')
    parser.add_argument('--patterns', type=str, default=os.getenv('PATTERNS', 'README.md,**/*.md,**/*.txt,**/*.yaml'), help='File patterns to include')
    parser.add_argument('--yaml_path', type=str, default=os.getenv('YAML_PATH', 'qna.yaml'), help='Path to save the YAML file')
    parser.add_argument('--max_files', type=int, default=int(os.getenv('MAX_FILES', 100)), help='Maximum number of files to read')
    parser.add_argument('--max_lines', type=int, default=int(os.getenv('MAX_LINES', 2000)), help='Maximum number of lines to read from each file')
    parser.add_argument('--keywords', type=str, default=os.getenv('KEYWORDS', 'InstructLab,getting started,problems,created,collaboration,open source,tuning method,mission'), help='Keywords to search for relevant sections')
    parser.add_argument('--min_sentence_length', type=int, default=int(os.getenv('MIN_SENTENCE_LENGTH', 5)), help='Minimum number of words in the answer')
    parser.add_argument('--min_answers', type=int, default=int(os.getenv('MIN_ANSWERS', 5)), help='Minimum number of valid answers required')
    parser.add_argument('--config_path', type=str, default='config_questions.yaml', help='Path to the configuration file with questions')

    args = parser.parse_args()
    
    # Convert comma-separated patterns and keywords to list
    patterns = args.patterns.split(',')
    keywords = args.keywords.split(',')

    # Read questions from config file
    config = read_config(args.config_path)
    questions = config['questions']

    # Define taxonomy path based on project name
    taxonomy_path = os.path.join(os.getenv('TAXONOMY_DIR', '~/instructlab/taxonomy'), 'knowledge', args.project_name.lower(), 'overview', 'qna.yaml')

    generate_yaml(
        repo_url=args.repo_url,
        commit_id=args.commit_id,
        patterns=patterns,
        yaml_path=taxonomy_path,
        project_name=args.project_name,
        questions=questions,
        max_files=args.max_files,
        max_lines=args.max_lines,
        keywords=keywords,
        min_sentence_length=args.min_sentence_length,
        min_answers=args.min_answers
    )
