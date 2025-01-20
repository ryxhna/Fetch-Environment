import logging
from google.cloud import container_v1
from google.api_core.exceptions import GoogleAPICallError, NotFound
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def format_date(date_obj):
    if date_obj:
        return date_obj.strftime('%Y-%m-%d')
    else:
        return "N/A"

# Mapping for Image Type
image_type_mapping = {
    "COS_CONTAINERD": "Container-Optimized OS with containerd (cos_containerd)",
    "UBUNTU": "Ubuntu",
    "UBUNTU_CONTAINERD": "Ubuntu with containerd",
    "CUSTOM_IMAGE": "Custom Image",
    "ML_IMAGE": "Machine Learning Optimized Image",
    "BIG_DATA_IMAGE": "Big Data Optimized Image",
    "LEGACY_IMAGE": "Legacy Image",
}

def gkeCluster(project_id):
    client = container_v1.ClusterManagerClient()
    clusters_info = []

    try:
        parent = f"projects/{project_id}/locations/-"
        response = client.list_clusters(parent=parent)

        for cluster in response.clusters:
            try:
                cluster_info = {
                    "Project ID": project_id,
                    "Cluster Name": cluster.name,
                    "Tier": cluster.resource_labels.get("tier", "N/A"),
                    "Mode": "Private" if cluster.private_cluster_config else "Public",
                    "Location Type": "Regional" if cluster.locations and len(cluster.locations) > 1 else "Zonal",
                    "Control Plane Zone": cluster.location,
                    "Total Size": cluster.current_node_count,
                    "Version Cluster": cluster.current_master_version,
                    "Current COS Version": cluster.current_node_version,
                    "End of Standard Support": format_date(getattr(cluster, 'end_of_life', None)),
                    "End of Extended Support": format_date(getattr(cluster, 'end_of_extended_support', None)),
                    "Maximum Pods per Node": getattr(cluster.default_max_pods_constraint, "max_pods_per_node", "Not available"),
                    "Autoscaling profile": getattr(cluster.autoscaling, "profile", "Not available") if cluster.autoscaling else "Not available",
                    "Private Endpoint": cluster.private_cluster_config.private_endpoint if cluster.private_cluster_config else "N/A",
                    "Control Plane Address Range": cluster.private_cluster_config.master_ipv4_cidr_block if cluster.private_cluster_config else "N/A",
                    "Network": cluster.network,
                    "Subnet": cluster.subnetwork,
                    "Cluster Pod IPv4 Range (default)": cluster.cluster_ipv4_cidr,
                    "HTTP Load Balancing": getattr(cluster, "http_load_balancing", {}).get("enabled", "N/A"),
                    "Gateway API": "Enabled" if hasattr(cluster, "gateway_api_config") and getattr(cluster.gateway_api_config, "enabled", False) else "N/A",
                    "Multi-networking": "Enabled" if hasattr(cluster, "networking_config") and getattr(cluster.networking_config, "multi_networking_enabled", False) else "N/A", 
                    "Binary Authorization": "Enabled" if getattr(cluster.binary_authorization, "enabled", False) else "Disabled",
                    "Secret Manager": "Enabled" if getattr(cluster.secret_manager_config, "enabled", False) else "Disabled",
                    "Legacy Authorization": "Enabled" if getattr(cluster.legacy_abac, "enabled", False) else "Disabled",
                    "Security Posture": "Enabled" if getattr(cluster.security_posture_config, "enabled", False) else "Disabled",
                    "Service Mesh": "Enabled" if hasattr(cluster, "service_mesh") and getattr(cluster.service_mesh, "enabled", False) else "N/A", 
                    "Tags": getattr(cluster, "network_tags", []),
                    "Labels": cluster.resource_labels,
                }
                clusters_info.append(cluster_info)
            except Exception as e:
                logging.error(f"Error processing cluster {cluster.name}: {e}")
                continue

    except NotFound:
        logging.warning(f"No clusters found for project: {project_id}")
    except GoogleAPICallError as e:
        logging.error(f"Error fetching clusters for project {project_id}: {e}")

    return clusters_info

# ... (rest of the code)