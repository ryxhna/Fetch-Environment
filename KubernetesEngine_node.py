import logging
from google.cloud import container_v1
from google.api_core.exceptions import GoogleAPICallError, NotFound

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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

# Mapping for Disk Type
disk_type_mapping = {
    "pd-standard": "Standard persistent disk",
    "pd-balanced": "Balanced persistent disk",
    "pd-ssd": "SSD persistent disk",
    "regional-ssd": "Regional SSD",
    "local-ssd": "Local SSD",
    "confidential-vm": "Confidential VM",
}

def gkeNodepool(project_id, cluster_name, location):
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
                "Current COS Version": getattr(node_pool.config, "image_version", "N/A"),
                "End of Standard Support": getattr(node_pool.config, "end_of_life_date", "N/A"),
                "End of Extended Support": getattr(node_pool.config, "end_of_extended_support", "N/A"),
                "Image Type": image_type_mapping.get(node_pool.config.image_type, "Unknown"),
                "Machine Type": node_pool.config.machine_type,
                "Boot Disk Size (per node)": node_pool.config.disk_size_gb,
                "Boot Disk Type": disk_type_mapping.get(node_pool.config.disk_type, "Unknown"),
                "Networks": getattr(node_pool.network_config, "network", "N/A"),
                "Subnet": getattr(node_pool.network_config, "subnetwork", "N/A"),
                "Name Pod IP Address Ranges": getattr(node_pool.network_config, "name_pod_ip_ranges", "N/A"),
                "IPv4 Pod IP Address Range": getattr(node_pool.network_config, "pod_ipv4_range", "N/A"),
                "Number of nodes": calculate_total_nodes(node_pool),
                "Autoscaling": "On" if node_pool.autoscaling.enabled else "Off",
                "Node Zones": node_pool.locations if node_pool.locations else [],
                "Maximum Pods per Node": getattr(node_pool.config, "max_pods_constraint", {}).get("max_pods_per_node", "Not available"), 
                "Max Surge": node_pool.upgrade_settings.max_surge if node_pool.upgrade_settings else "N/A",
                "Taints": get_taints(node_pool.config.taints) if node_pool.config else "Not available",
                "GCE Instance Metadata": node_pool.config.metadata if node_pool.config.metadata else {},
            } 
            node_pools_info.append(node_pool_info)

    except NotFound:
        logging.warning(f"No node pools found for cluster: {cluster_name}")
    except GoogleAPICallError as e:
        logging.error(f"Error fetching node pools for cluster {cluster_name}: {e}")

    return node_pools_info

def calculate_total_nodes(node_pool):
    if hasattr(node_pool, "instance_group_urls"):
        total_nodes = len(node_pool.instance_group_urls)
        return f"{total_nodes} total ({1} per zone)"
    elif hasattr(node_pool, "initial_node_count"):
        return f"{node_pool.initial_node_count} total"
    return "Not available"

def get_taints(taints):
    if not taints:
        return "Not available"

    formatted_taints = []
    for taint in taints:
        key_value = f"{taint.key}={taint.value}"  # Only key and value
        formatted_taints.append(key_value)

    return ", ".join(formatted_taints)