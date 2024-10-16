import git
import yaml
import os
import glob
import logging
from sentence_transformers import SentenceTransformer, util
import argparse
import pandas as pd
import time
from prometheus_client import CollectorRegistry, Gauge, generate_latest, Info
import requests
from requests.auth import HTTPBasicAuth
from nltk.tokenize import sent_tokenize, blankline_tokenize  # Ensure this is imported

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to read the configuration file
def read_config(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

# Function to determine if a file is binary
def is_binary_file(file_path):
    with open(file_path, 'rb') as file:
        chunk = file.read(1024)
    text_characters = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)))
    return bool(chunk.translate(None, text_characters))

# Function to read the Git repository
def read_git_repo(repo_url, commit_id, patterns, max_files):
    repo_dir = "/tmp/repo"
    if os.path.exists(repo_dir):
        os.system(f"rm -rf {repo_dir}")

    logging.info(f"Cloning repository {repo_url}")
    start_time = time.time()
    repo = git.Repo.clone_from(repo_url, repo_dir)
    repo.git.checkout(commit_id)
    clone_time = time.time() - start_time
    
    content = {}
    file_count = 0
    for pattern in patterns:
        file_paths = glob.glob(os.path.join(repo_dir, pattern), recursive=True)
        for file_path in file_paths:
            if os.path.isdir(file_path):
                continue
            if file_count >= max_files:
                break
            if is_binary_file(file_path):
                logging.warning(f"Skipping binary file: {file_path}")
                continue
            start_time = time.time()
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content[file_path] = file.read()
                read_time = time.time() - start_time
                file_count += 1
                logging.info(f"Read file: {file_path} in {read_time:.2f} seconds")
            except UnicodeDecodeError as e:
                logging.error(f"Error reading file {file_path}: {e}")
                continue
        if file_count >= max_files:
            break
    
    return content, clone_time, file_count

# Function to extract relevant sections based on keywords
def extract_relevant_sections(text, keywords):
    sections = []
    paragraphs = blankline_tokenize(text)
    for paragraph in paragraphs:
        for keyword in keywords:
            if keyword.lower() in paragraph.lower():
                sections.append(paragraph)
                break
    logging.info(f"Extracted {len(sections)} relevant sections")
    return sections

# Function to combine relevant sections for better context
def combine_relevant_sections(sections):
    combined_sections = []
    current_section = ""
    for section in sections:
        if len(current_section) + len(section) < 4096:
            current_section += " " + section
        else:
            combined_sections.append(current_section.strip())
            current_section = section
    if current_section:
        combined_sections.append(current_section.strip())
    return combined_sections

# Function to generate questions and answers using specified models
def generate_qa_pairs(sections, project_name, questions, min_sentence_length, model_name):
    model = SentenceTransformer(model_name)
    seed_examples = []
    scores = []
    context = " ".join(sections)

    # Embed the context once
    context_sentences = sent_tokenize(context)
    context_embeddings = model.encode(context_sentences, convert_to_tensor=True)

    for question_template in questions:
        question = question_template.format(project_name=project_name)
        question_embedding = model.encode(question, convert_to_tensor=True)
        
        # Compute cosine similarity between the question and context sentences
        cosine_scores = util.pytorch_cos_sim(question_embedding, context_embeddings)[0]
        best_score, best_idx = cosine_scores.max().item(), cosine_scores.argmax().item()
        
        best_answer = context_sentences[best_idx]
        logging.info(f"Processing question '{question}' with best answer: '{best_answer}' and score: {best_score}")

        if len(best_answer.split()) >= min_sentence_length:
            seed_examples.append({'question': question, 'answer': best_answer.strip()})
            scores.append({'question': question, 'answer': best_answer.strip(), 'score': best_score})
        else:
            logging.warning(f"Skipped question '{question}' due to insufficient answer length. Answer: '{best_answer}', Length: {len(best_answer.split())}")

    return seed_examples, scores

# Function to save scores to CSV
def save_scores_to_csv(scores, model_name):
    df = pd.DataFrame(scores)
    csv_path = f'scores_{model_name.replace("/", "_")}.csv'
    df.to_csv(csv_path, index=False)
    logging.info(f"Scores saved to {csv_path}")

# Function to save metrics to CSV
def save_metrics_to_csv(metrics, metrics_file):
    df = pd.DataFrame([metrics])
    df.to_csv(metrics_file, index=False)
    logging.info(f"Metrics saved to {metrics_file}")

# Function to push metrics to Prometheus Pushgateway with optional authentication
def push_metrics_to_gateway(metrics, job_name, pushgateway_url, instance, username=None, password=None):
    registry = CollectorRegistry()
    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            gauge = Gauge(key, f'Description of {key}', ['instance'], registry=registry)
            gauge.labels(instance=instance).set(value)
    data = generate_latest(registry)
    
    sanitized_instance = instance.replace("/", "-")
    full_url = f"{pushgateway_url}/metrics/job/{job_name}/instance/{sanitized_instance}"
    
    if username and password:
        response = requests.post(full_url, data=data, auth=HTTPBasicAuth(username, password))
    else:
        response = requests.post(full_url, data=data)
    
    if response.status_code != 200:
        logging.error(f"Failed to push metrics to Pushgateway. URL: {full_url}, Status Code: {response.status_code}, Response: {response.text}")
    else:
        logging.info(f"Metrics successfully pushed to Pushgateway. URL: {full_url}")

# Function to push Q&A metadata to Prometheus Pushgateway with optional authentication
def push_qa_metadata_to_gateway(seed_examples, job_name, pushgateway_url, instance, username=None, password=None):
    registry = CollectorRegistry()
    
    question_count = Gauge('question_count', 'Total number of questions', ['instance'], registry=registry)
    answer_count = Gauge('answer_count', 'Total number of answers', ['instance'], registry=registry)
    longest_answer_length = Gauge('longest_answer_length', 'Length of the longest answer', ['instance'], registry=registry)
    shortest_answer_length = Gauge('shortest_answer_length', 'Length of the shortest answer', ['instance'], registry=registry)
    
    question_count.labels(instance=instance).set(len(seed_examples))
    answer_lengths = [len(example['answer'].split()) for example in seed_examples]
    answer_count.labels(instance=instance).set(len(answer_lengths))
    
    if answer_lengths:
        longest_answer_length.labels(instance=instance).set(max(answer_lengths))
        shortest_answer_length.labels(instance=instance).set(min(answer_lengths))
    
    qa_info = Info('qa_pairs', 'Question and Answer pairs', registry=registry)
    qa_info.info({f'qa_pair_{i}': f"Q: {example['question']} A: {example['answer']}" for i, example in enumerate(seed_examples)})

    data = generate_latest(registry)
    
    sanitized_instance = instance.replace("/", "-")
    full_url = f"{pushgateway_url}/metrics/job/{job_name}/instance/{sanitized_instance}"
    
    if username and password:
        response = requests.post(full_url, data=data, auth=HTTPBasicAuth(username, password))
    else:
        response = requests.post(full_url, data=data)
    
    if response.status_code != 200:
        logging.error(f"Failed to push Q&A metadata to Pushgateway. URL: {full_url}, Status Code: {response.status_code}, Response: {response.text}")
    else:
        logging.info(f"Q&A metadata successfully pushed to Pushgateway. URL: {full_url}")

# Function to save Q&A pairs to a YAML file
def save_qna_to_yaml(seed_examples, model_name):
    yaml_path = f'{model_name.replace("/", "_")}-qna.yml'
    with open(yaml_path, 'w') as file:
        yaml.dump(seed_examples, file, default_flow_style=False)
    logging.info(f"Q&A pairs saved to {yaml_path}")

# Function to generate the YAML file
def generate_yaml(repo_url, commit_id, patterns, yaml_path, project_name, questions, max_files, max_lines, keywords, min_sentence_length, min_answers, taxonomy_dir, model_name, save_scores, pushgateway_url, enable_prometheus, username, password, job_name):
    logging.info(f"Starting YAML generation process with model: {model_name}")
    
    metrics = {
        'repo_url': repo_url,
        'commit_id': commit_id,
        'model_name': model_name,
        'start_time': time.time(),
    }

    repo_content, clone_time, file_count = read_git_repo(repo_url, commit_id, patterns, max_files)
    metrics.update({
        'clone_time': clone_time,
        'file_count': file_count,
    })
    
    combined_content = ""

    start_time = time.time()
    for file_path, file_content in repo_content.items():
        lines = file_content.split('\n')
        combined_content += "\n".join(lines[:max_lines]) + "\n"
        if len(combined_content.split('\n')) >= max_lines:
            break
    metrics['file_read_time'] = time.time() - start_time

    start_time = time.time()
    relevant_sections = extract_relevant_sections(combined_content, keywords)
    metrics['section_extraction_time'] = time.time() - start_time
    metrics['relevant_section_count'] = len(relevant_sections)

    combined_sections = combine_relevant_sections(relevant_sections)

    start_time = time.time()
    seed_examples, scores = generate_qa_pairs(combined_sections, project_name, questions, min_sentence_length, model_name)
    metrics['qa_generation_time'] = time.time() - start_time
    metrics['qa_count'] = len(seed_examples)

    if not seed_examples:
        scores.append("failed")

    if len(seed_examples) < min_answers:
        logging.error(f"Failed to generate the minimum required number of answers ({min_answers}).")
        raise ValueError(f"Failed to generate the minimum required number of answers ({min_answers}).")

    logging.info(f"Printing out the results of each answer and question using model: {model_name}")
    for seed_example in seed_examples:
        question = seed_example['question']
        answer = seed_example['answer']
        color = '\033[92m' if len(answer.split()) >= min_sentence_length else '\033[91m'
        end_color = '\033[0m'
        print(f"{color}Question: {question}\nAnswer: {answer}{end_color}\n")

    if save_scores:
        save_scores_to_csv(scores, model_name)

    save_qna_to_yaml(seed_examples, model_name)

    metrics['end_time'] = time.time()
    metrics['total_time'] = metrics['end_time'] - metrics['start_time']
    
    metrics_file = f'metrics_{model_name.replace("/", "_")}.csv'
    save_metrics_to_csv(metrics, metrics_file)

    if enable_prometheus and pushgateway_url:
        push_metrics_to_gateway(metrics, job_name=job_name, pushgateway_url=pushgateway_url, instance=model_name, username=username, password=password)
        push_qa_metadata_to_gateway(seed_examples, job_name=job_name, pushgateway_url=pushgateway_url, instance=model_name, username=username, password=password)

# Main script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate QnA YAML from a Git repository.")
    parser.add_argument('--config_path', type=str, default='config.yaml', help='Path to the configuration file')
    parser.add_argument('--save_scores', action='store_true', help='Flag to save the scores of the models')
    parser.add_argument('--pushgateway_url', type=str, help='URL of the Prometheus Pushgateway')
    parser.add_argument('--enable_prometheus', action='store_true', help='Flag to enable Prometheus metrics')
    parser.add_argument('--username', type=str, help='Username for Prometheus Pushgateway authentication')
    parser.add_argument('--password', type=str, help='Password for Prometheus Pushgateway authentication')

    args = parser.parse_args()

    config = read_config(args.config_path)

    project_name = config['project_name']
    repo_url = config['repo_url']
    commit_id = config['commit_id']
    patterns = config['patterns']
    yaml_path = config['yaml_path']
    max_files = config['max_files']
    max_lines = config['max_lines']
    keywords = config['keywords']
    min_sentence_length = config['min_sentence_length']
    min_answers = config['min_answers']
    questions = config['questions']
    taxonomy_dir = config['taxonomy_dir']
    model_list = config.get('model_list', [config['model_name']])
    pushgateway_url = config.get('pushgateway_url', args.pushgateway_url)
    enable_prometheus = args.enable_prometheus
    username = args.username
    password = args.password
    job_name = project_name

    if config.get('optimize', False):
        for model in model_list:
            logging.info(f"Running optimization with model: {model}")
            try:
                generate_yaml(
                    repo_url=repo_url,
                    commit_id=commit_id,
                    patterns=patterns,
                    yaml_path=yaml_path,
                    project_name=project_name,
                    questions=questions,
                    max_files=max_files,
                    max_lines=max_lines,
                    keywords=keywords,
                    min_sentence_length=min_sentence_length,
                    min_answers=min_answers,
                    taxonomy_dir=taxonomy_dir,
                    model_name=model,
                    save_scores=args.save_scores,
                    pushgateway_url=pushgateway_url,
                    enable_prometheus=enable_prometheus,
                    username=username,
                    password=password,
                    job_name=job_name
                )
            except Exception as e:
                logging.error(f"Error with model {model}: {e}")
                continue
    else:
        generate_yaml(
            repo_url=repo_url,
            commit_id=commit_id,
            patterns=patterns,
            yaml_path=yaml_path,
            project_name=project_name,
            questions=questions,
            max_files=max_files,
            max_lines=max_lines,
            keywords=keywords,
            min_sentence_length=min_sentence_length,
            min_answers=min_answers,
            taxonomy_dir=taxonomy_dir,
            model_name=model_list[0],
            save_scores=args.save_scores,
            pushgateway_url=pushgateway_url,
            enable_prometheus=enable_prometheus,
            username=username,
            password=password,
            job_name=job_name
        )
