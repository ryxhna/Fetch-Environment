import os
import logging
import pandas as pd
from Runner import LoadProject, CreateFolderOutput
from MemorystoreForRedis import GetRedisMemorystore
from StorageBucket import GetStorageBuckets
from KubernetesEngine import getKubernetesEngine, processProjects

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# File paths
OUTPUT_FOLDER = "output"
OUTPUT_FILE = os.path.join(OUTPUT_FOLDER, "Asset List 2025.xlsx")

def main():
    logging.info("Starting the data collection process.")
    projects = LoadProject()
    if not projects:
        logging.error("No projects found in the project list. Exiting.")
        return

    redis_data = []
    storage_data = []
    kubernetes_data = []

    # Process each project
    for project_id in projects:
        logging.info(f"Processing project: {project_id}")

        # Ambil data Redis
        redis_instances = GetRedisMemorystore(project_id)
        redis_data.extend(redis_instances)

        # Ambil data Storage Bucket
        storage_buckets = GetStorageBuckets(project_id)
        storage_data.extend(storage_buckets)

        # Ambil data Kubernetes (Cluster dan Node Pool)
        kubernetes_engine = getKubernetesEngine(project_id)
        kubernetes_data.extend(kubernetes_engine)

    # Convert data to Pandas DataFrames
    redis_df = pd.DataFrame(redis_data)
    storage_df = pd.DataFrame(storage_data)
    kubernetes_df = pd.DataFrame(kubernetes_data)

    # Save to Excel
    CreateFolderOutput()
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        if not redis_df.empty:
            redis_df.to_excel(writer, sheet_name="Redis Instances", index=False)
        if not storage_df.empty:
            storage_df.to_excel(writer, sheet_name="Storage Buckets", index=False)
        if not kubernetes_df.empty:
            kubernetes_df.to_excel(writer, sheet_name="Kubernetes Engine", index=False)

    logging.info(f"Data collection complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
