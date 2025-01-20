import os
import logging
import pandas as pd
from Runner import LoadProject, CreateFolderOutput
from MemorystoreForRedis import GetRedisMemorystore
from StorageBucket import GetStorageBuckets
from KubernetesEngine_cluster import gkeCluster
from KubernetesEngine_node import gkeNodepool

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# File paths
OUTPUT_FOLDER = "output"
OUTPUT_FILE = os.path.join(OUTPUT_FOLDER, "Asset List 2025.xlsx")

def main():
    """Main runner script to process Redis, Cloud Storage, GKE Clusters, and Node Pools data."""
    logging.info("Starting the data collection process.")

    # Load project list
    projects = LoadProject()
    if not projects:
        logging.error("No projects found in the project list. Exiting.")
        return

    redis_data = []
    storage_data = []
    clusters_data = []
    node_pools_data = []

    # Process each project
    for project_id in projects:
        logging.info(f"Processing project: {project_id}")

        # Fetch Redis data
        redis_instances = GetRedisMemorystore(project_id)
        redis_data.extend(redis_instances)

        # Fetch Storage data
        storage_buckets = GetStorageBuckets(project_id)
        storage_data.extend(storage_buckets)

        # Fetch GKE cluster data
        try:
            clusters = gke_cluster(project_id)
        except KeyError as e:
            logging.error(f"Error processing cluster for project {project_id}: {e}")
            continue  # Continue to the next project if an error occurs
        clusters_data.extend(clusters)

        # Fetch GKE node pool data
        for cluster in clusters:
            try:
                node_pools = gke_nodepool(project_id, cluster["Cluster Name"], cluster["Control Plane Zone"])
            except KeyError as e:
                logging.error(f"Error processing node pool for cluster {cluster['Cluster Name']} in project {project_id}: {e}")
                continue
            node_pools_data.extend(node_pools)

    # Convert data to Pandas DataFrames
    redis_df = pd.DataFrame(redis_data)
    storage_df = pd.DataFrame(storage_data)
    clusters_df = pd.DataFrame(clusters_data)
    node_pools_df = pd.DataFrame(node_pools_data)

    # Save to Excel
    CreateFolderOutput()
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        if not redis_df.empty:
            redis_df.to_excel(writer, sheet_name="Redis Instances", index=False)
        if not storage_df.empty:
            storage_df.to_excel(writer, sheet_name="Storage Buckets", index=False)
        if not clusters_df.empty:
            clusters_df.to_excel(writer, sheet_name="GKE Clusters", index=False)
        if not node_pools_df.empty:
            node_pools_df.to_excel(writer, sheet_name="GKE Node Pools", index=False)

    logging.info(f"Data collection complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
