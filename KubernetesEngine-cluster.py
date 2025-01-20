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

def gkeCluster(project_id):
    """Fetch GKE cluster details for a given project ID."""
    client = container_v1.ClusterManagerClient()
    clusters_info = []

    try:
        parent = f"projects/{project_id}/locations/-"
        response = client.list_clusters(parent=parent)

        for cluster in response.clusters:
            cluster_info = {
                "Project ID": project_id,
                "Cluster Name": cluster.name,
                "Tier": cluster.resource_labels.get("tier", "N/A"),
                "Mode": cluster.cluster_type,
                "Location Type": cluster.location_type,
                "Control Plane Zone": cluster.location,
                "Total Size": cluster.current_node_count,
                "Version": cluster.current_master_version,
                "Current COS Version": cluster.current_node_version,
                "End of Standard Support": cluster.end_of_life.date if cluster.end_of_life else "N/A",
                "End of Extended Support": "N/A",  # Add if available in API
                "Maximum Pods per Node": cluster.max_pods_constraint.max_pods_per_node,
                "Autoscaling Profile": cluster.autoscaling_profile,
                "Private Endpoint": cluster.private_cluster_config.private_endpoint,
                "Control Plane Address Range": cluster.private_cluster_config.master_ipv4_cidr_block,
                "Network": cluster.network,
                "Subnet": cluster.subnetwork,
                "Cluster Pod IPv4 Range (default)": cluster.cluster_ipv4_cidr,
                "HTTP Load Balancing": "Enabled" if cluster.http_load_balancing else "Disabled",
                "Gateway API": "Enabled" if cluster.gateway_api_config.enabled else "Disabled",
                "Multi-networking": "Enabled" if cluster.multi_networking else "Disabled",
                "Binary Authorization": "Enabled" if cluster.binary_authorization.enabled else "Disabled",
                "Secret Manager": "Enabled" if cluster.secret_manager_config.enabled else "Disabled",
                "Legacy Authorization": "Enabled" if cluster.legacy_abac.enabled else "Disabled",
                "Security Posture": "Enabled" if cluster.security_posture.enabled else "Disabled",
                "Service Mesh": "Enabled" if cluster.mesh_certificates else "Disabled",
                "Labels": cluster.resource_labels,
                "Tags": "N/A",  # Add if tags are available
            }
            clusters_info.append(cluster_info)

    except NotFound:
        logging.warning(f"No clusters found for project: {project_id}")
    except GoogleAPICallError as e:
        logging.error(f"Error fetching clusters for project {project_id}: {e}")

    return clusters_infos