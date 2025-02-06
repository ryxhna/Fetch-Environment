import json
import logging
from pathlib import Path
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# File paths
OUTPUT_FOLDER = Path("output")
PROJECT_LIST_FILE = [
    Path("project-list/PROD.json"),
    Path("project-list/NON-PROD.json"),
]

def LoadProject():
    all_projects = []
    for file_path in PROJECT_LIST_FILE:
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                projects = data.get("projects", [])
                all_projects.extend(projects)
                logging.info(f"Loaded projects from {file_path}")
        except FileNotFoundError:
            logging.error(f"Project list file not found: {file_path}")
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON in {file_path}: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred with {file_path}: {e}")
    return all_projects

def CreateFolderOutput():
    try:
        OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        logging.info(f"Output folder is ready: {OUTPUT_FOLDER}")
    except OSError as e:
        logging.error(f"Error creating output folder {OUTPUT_FOLDER}: {e}")
