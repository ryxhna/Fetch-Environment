import json
import logging
from pathlib import Path
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# File paths
PROJECT_LIST_FILE = Path("project-list/NON-PROD.json")
OUTPUT_FOLDER = Path("output")

def LoadProject():
    """Load the list of project IDs from the JSON file."""
    try:
        with open(PROJECT_LIST_FILE, 'r') as file:
            data = json.load(file)
        return data.get("projects", [])
    except FileNotFoundError:
        logging.error(f"Project list file not found: {PROJECT_LIST_FILE}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON in {PROJECT_LIST_FILE}: {e}")
        return []

def CreateFolderOutput():
    """Ensure the output folder exists."""
    try:
        OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        logging.info(f"Output folder is ready: {OUTPUT_FOLDER}")
    except OSError as e:
        logging.error(f"Error creating output folder {OUTPUT_FOLDER}: {e}")
