import logging
from google.cloud import container_v1
from google.api_core.exceptions import NotFound
from Runner import LoadProject 

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Mappings for better readability of image types and disk types
ImageType_mapping = {
    "COS_CONTAINERD": "Container-Optimized OS with containerd (cos_containerd)",
    "UBUNTU": "Ubuntu",
    "UBUNTU_CONTAINERD": "Ubuntu with containerd",
    "CUSTOM_IMAGE": "Custom Image",
    "ML_IMAGE": "Machine Learning Optimized Image",
    "BIG_DATA_IMAGE": "Big Data Optimized Image",
    "LEGACY_IMAGE": "Legacy Image",
}

DiskType_mapping = {
    "pd-standard": "Standard persistent disk",
    "pd-balanced": "Balanced persistent disk",
    "pd-ssd": "SSD persistent disk",
    "regional-ssd": "Regional SSD",
    "local-ssd": "Local SSD",
    "confidential-vm": "Confidential VM",
}

def getCluster(project_id):
    cluster_client = container_v1.ClusterManagerClient()
    clusters = []
    try:
        response = cluster_client.list_clusters(parent=f"projects/{project_id}/locations/-")
        for cluster in response.clusters:
            details = {
                "Cluster Name": cluster.name,
                "Version Cluster": cluster.current_master_version,
                "Current COS Version": cluster.current_node_version,
                "Control Plane Address Range": getattr(cluster.private_cluster_config, "master_ipv4_cidr_block", "Not available"),
                "Private Endpoint": getattr(cluster.private_cluster_config, "private_endpoint", "Not available"),
                "Network": cluster.network,
                "Subnet": cluster.subnetwork,
                "Cluster Pod IPv4 Range (default)": getattr(cluster.ip_allocation_policy, "cluster_ipv4_cidr_block", "Not available"),
                "Maximum Pods per Node": getattr(cluster.default_max_pods_constraint, "max_pods_per_node", "Not available"),
                "Total Size": cluster.current_node_count,
                "Labels": cluster.resource_labels,
                "Vertical Pod Autoscaling": "disabled" if getattr(cluster.vertical_pod_autoscaling, "enabled", False) is False else "enabled",
                "Autoscaling Profile": getattr(cluster.autoscaling, "profile", "Balanced") if cluster.autoscaling else "Any",
            }
            clusters.append(details)
    except NotFound:
        logging.warning(f"No clusters found for project '{project_id}'.")
    return clusters

def getNodepool(project_id):
    cluster_client = container_v1.ClusterManagerClient()
    node_pools = []
    try:
        response = cluster_client.list_clusters(parent=f"projects/{project_id}/locations/-")
        for cluster in response.clusters:
            cluster_name = cluster.name
            location = cluster.location
            node_pool_response = cluster_client.list_node_pools(parent=f"projects/{project_id}/locations/{location}/clusters/{cluster_name}")
            for node_pool in node_pool_response.node_pools:
                details = {
                    "Node Pool Name": node_pool.name,
                    "Node Version": node_pool.version,
                    "Number of Nodes": calculate_TotalNodes(node_pool),
                    "Autoscaling": "On" if node_pool.autoscaling.enabled else "Off",
                    "Node Zones": node_pool.locations,
                }
                if hasattr(node_pool, "config"):
                    image_type = getattr(node_pool.config, "image_type", "Not available")
                    disk_type = getattr(node_pool.config, "disk_type", "Not available")
                    details.update({
                        "Image Type": ImageType_mapping.get(image_type, image_type),
                        "Machine Type": getattr(node_pool.config, "machine_type", "Not available"),
                        "Boot Disk Type": DiskType_mapping.get(disk_type, disk_type),
                        "Boot Disk Size (per node)": f"{getattr(node_pool.config, 'disk_size_gb', 'Not available')} GB",
                        "Max Surge": getattr(node_pool.upgrade_settings, "max_surge", "N/A"),
                        "Taints": getTaints(node_pool.config.taints),
                        "GCE Instance Metadata": getattr(node_pool.config, "metadata", "Not available"),
                    })
                node_pools.append(details)
    except NotFound:
        logging.warning(f"No node pools found for project '{project_id}'.")
    return node_pools

def calculate_TotalNodes(node_pool):
    """Calculate the total number of nodes in a node pool."""
    if hasattr(node_pool, "instance_group_urls"):
        return len(node_pool.instance_group_urls)
    elif hasattr(node_pool, "initial_node_count"):
        return node_pool.initial_node_count
    return "Not available"

def getTaints(taints):
    """Format taints for readability."""
    if not taints:
        return "Not available"
    return ", ".join(f"{taint.key}={taint.value}:{taint.effect}" for taint in taints)

def process_projects():
    """Process all projects and retrieve GKE cluster and node pool details."""
    projects = LoadProject()
    if not projects:
        logging.error("No projects found. Ensure the JSON file is correctly configured.")
        return [], []

    all_clusters = []
    all_node_pools = []

    for project_id in projects:
        logging.info(f"Processing project: {project_id}")
        clusters = getCluster(project_id)
        node_pools = getNodepool(project_id)
        all_clusters.extend(clusters)
        all_node_pools.extend(node_pools)

    return all_clusters, all_node_pools
