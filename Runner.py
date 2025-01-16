import json
import os
import logging
import pandas as pd
from get_redis_memorystore import get_redis_memorystore
from get_bucket_storage import get_bucket_storage

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def load_project_ids(json_file):
    """Load project IDs from a JSON file."""
    try:
        with open(json_file, 'r') as file:
            data = json.load(file)
            return data.get("projects", [])
    except FileNotFoundError:
        logging.error(f"JSON file '{json_file}' not found.")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON file '{json_file}': {e}")
        return []

def save_to_excel(output_path, redis_data, bucket_data):
    """Save Redis and bucket data to an Excel file."""
    try:
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # Redis data sheet
            if redis_data:
                redis_df = pd.DataFrame(redis_data)
                redis_df.to_excel(writer, index=False, sheet_name='Redis Instances')
                logging.info("Redis data written to Excel.")

            # Bucket data sheet
            if bucket_data:
                bucket_df = pd.DataFrame(bucket_data)
                bucket_df.to_excel(writer, index=False, sheet_name='Bucket Storage')
                logging.info("Bucket data written to Excel.")
        logging.info(f"Data saved to Excel file: {output_path}")
    except Exception as e:
        logging.error(f"Error saving data to Excel: {e}")

def main():
    # Define paths
    json_file = "project/NON-PROD.json"
    output_folder = "output"
    output_file = os.path.join(output_folder, "Asset List 2025.xlsx")

    # Ensure output directory exists
    os.makedirs(output_folder, exist_ok=True)

    # Load project IDs
    project_ids = load_project_ids(json_file)
    if not project_ids:
        logging.error("No project IDs found. Exiting.")
        return

    # Collect data
    all_redis_data = []
    all_bucket_data = []

    for project_id in project_ids:
        logging.info(f"Processing project: {project_id}")
        redis_data = get_redis_memorystore(project_id)
        bucket_data = get_bucket_storage(project_id)

        all_redis_data.extend(redis_data)
        all_bucket_data.extend(bucket_data)

    # Save data to Excel
    save_to_excel(output_file, all_redis_data, all_bucket_data)

if __name__ == "__main__":
    main()
