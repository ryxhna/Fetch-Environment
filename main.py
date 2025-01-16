import os
import logging
import pandas as pd
from Runner import LoadProject, CreateFolderOutput
from MemorystoreForRedis import GetRedisMemorystore
from CloudStorage import get_bucket_storage

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# File paths
OUTPUT_FOLDER = "output"
OUTPUT_FILE = os.path.join(OUTPUT_FOLDER, "Asset List 2025.xlsx")

def main():
    """Main runner script to process Redis and Cloud Storage data."""
    logging.info("Starting the data collection process.")
    
    # Load project list
    projects = LoadProject()
    if not projects:
        logging.error("No projects found in the project list. Exiting.")
        return

    redis_data = []
    storage_data = []

    # Process each project
    for project_id in projects:
        logging.info(f"Processing project: {project_id}")
        
        # Fetch Redis data
        redis_instances = GetRedisMemorystore(project_id)
        redis_data.extend(redis_instances)
        
        # Fetch Storage data
        storage_buckets = get_bucket_storage(project_id)
        storage_data.extend(storage_buckets)

    # Convert data to Pandas DataFrames
    redis_df = pd.DataFrame(redis_data)
    storage_df = pd.DataFrame(storage_data)

    # Save to Excel
    create_output_folder()
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        if not redis_df.empty:
            redis_df.to_excel(writer, sheet_name="Redis Instances", index=False)
        else:
            logging.info("No Redis data to save.")
        
        if not storage_df.empty:
            storage_df.to_excel(writer, sheet_name="Storage Buckets", index=False)
        else:
            logging.info("No Storage data to save.")

    logging.info(f"Data collection complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
