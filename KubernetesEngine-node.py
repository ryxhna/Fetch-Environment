import os
import logging
import pandas as pd
from google.cloud import container_v1
from google.api_core.exceptions import GoogleAPICallError, NotFound

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Output file
OUTPUT_FOLDER = "output"
OUTPUT_FILE = os.path.join(OUTPUT_FOLDER, "Asset List 2025.xlsx")

def Get-gkeNodepool(project_id, cluster_name, location):
    """Fetch node pool details for a cluster."""
    client = container_v1.ClusterManagerClient()
    node_pools_info = []

    try:
        parent = f"projects/{project_id}/locations/{location}/clusters/{cluster_name}"
        response = client.list_node_pools(parent=parent)

        for node_pool in response.node_pools:
            node_pool_info = {
                "Project ID": project_id,
                "Cluster Name": cluster_name,
                "Nodepool Name": node_pool.name,
                "Node Version": node_pool.version,
                "Current COS Version": node_pool.config.image_version,
                "End of Standard Support": "N/A",  # Add if available
                "End of Extended Support": "N/A",  # Add if available
                "Number of Nodes": node_pool.initial_node_count,
                "Autoscaling": "On" if node_pool.autoscaling.enabled else "Off",
                "Node Zones": node_pool.locations,
                "Image Type": node_pool.config.image_type,
                "Machine Type": node_pool.config.machine_type,
                "Boot Disk Size (per node)": node_pool.config.disk_size_gb,
                "Boot Disk Type": node_pool.config.disk_type,
                "Networks": node_pool.config.network,
                "Subnet": node_pool.config.subnetwork,
                "Name Pod IP Address Ranges": node_pool.pod_ipv4_cidr_blocks,
                "IPv4 Pod IP Address Range": node_pool.config.pod_cidr_overprovisioned,
                "Maximum Pods per Node": node_pool.config.max_pods_per_node,
                "Max Surge": node_pool.upgrade_settings.max_surge,
                "GCE Instance Metadata": node_pool.config.metadata,
            }
            node_pools_info.append(node_pool_info)

    except NotFound:
        logging.warning(f"No node pools found for cluster: {cluster_name}")
    except GoogleAPICallError as e:
        logging.error(f"Error fetching node pools for cluster {cluster_name}: {e}")

    return node_pools_info