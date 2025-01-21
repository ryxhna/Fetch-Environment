import logging
from google.cloud import container_v1, compute_v1
from google.api_core.exceptions import GoogleAPICallError, NotFound

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Mapping for Image Type
ImageType_mapping = {
    "COS_CONTAINERD": "Container-Optimized OS with containerd (cos_containerd)",
    "UBUNTU": "Ubuntu",
    "UBUNTU_CONTAINERD": "Ubuntu with containerd",
    "CUSTOM_IMAGE": "Custom Image",
    "ML_IMAGE": "Machine Learning Optimized Image",
    "BIG_DATA_IMAGE": "Big Data Optimized Image",
    "LEGACY_IMAGE": "Legacy Image",
}

# Mapping for Disk Type
DiskType_mapping = {
    "pd-standard": "Standard persistent disk",
    "pd-balanced": "Balanced persistent disk",
    "pd-ssd": "SSD persistent disk",
    "regional-ssd": "Regional SSD",
    "local-ssd": "Local SSD",
    "confidential-vm": "Confidential VM",
}

def getNetwork(project_id, subnet):
    try:
        client = compute_v1.SubnetworksClient()
        subnet_info = client.get(project=project_id, region=subnet["region"], subnetwork=subnet["name"])
        return {
            "Primary IPv4 Range": subnet_info.ip_cidr_range,
            "Region": subnet_info.region,
            "Network": subnet_info.network,
        }
    except GoogleAPICallError as e:
        logging.error(f"Error fetching subnet details for {subnet['name']}: {e}")
        return {
            "Primary IPv4 Range": "Error fetching details",
            "Region": subnet.get("region", "Unknown"),
            "Network": "Unknown",
        }

def gkeNodepool(project_id, cluster_name, location):
    client = container_v1.ClusterManagerClient()
    node_pools_info = []

    try:
        parent = f"projects/{project_id}/locations/{location}/clusters/{cluster_name}"
        response = client.list_node_pools(parent=parent)

        for node_pool in response.node_pools:
            network = getattr(node_pool.network_config, "network", "N/A")
            subnet = getattr(node_pool.network_config, "subnetwork", "N/A")

            # Get Subnet details if available
            subnet_info = {}
            if subnet != "N/A":
                subnet_parts = subnet.split("/")  # Extract region and subnet name
                subnet_info = getNetwork(
                    project_id, {"region": subnet_parts[-3], "name": subnet_parts[-1]}
                )

            node_pool_info = {
                "Project ID": project_id,
                "Cluster Name": cluster_name,
                "Nodepool Name": node_pool.name,
                "Node Version": node_pool.version,
                "Image Type": ImageType_mapping.get(node_pool.config.image_type, "Unknown"),
                "Machine Type": node_pool.config.machine_type,
                "Boot Disk Size (per node)": node_pool.config.disk_size_gb,
                "Boot Disk Type": DiskType_mapping.get(node_pool.config.disk_type, "Unknown"),
                "Network": network,
                "Subnet": subnet,
                **subnet_info,
                "Number of nodes": calculate_TotalNodes(node_pool),
                "Autoscaling": "On" if node_pool.autoscaling.enabled else "Off",
                "Node Zones": node_pool.locations if node_pool.locations else [],
                "Maximum Pods per Node": getattr(node_pool.max_pods_constraint, "max_pods_per_node", "Not available"),
                "Max Surge": node_pool.upgrade_settings.max_surge if node_pool.upgrade_settings else "N/A",
                "Taints": getTaints(node_pool.config.taints) if node_pool.config else "Not available",
                "GCE Instance Metadata": node_pool.config.metadata if node_pool.config.metadata else {},
            }
            node_pools_info.append(node_pool_info)

    except NotFound:
        logging.warning(f"No node pools found for cluster: {cluster_name}")
    except GoogleAPICallError as e:
        logging.error(f"Error fetching node pools for cluster {cluster_name}: {e}")

    return node_pools_info

def calculate_TotalNodes(node_pool):
    if hasattr(node_pool, "instance_group_urls"):
        total_nodes = len(node_pool.instance_group_urls)
        return f"{total_nodes} total ({1} per zone)"
    elif hasattr(node_pool, "initial_node_count"):
        return f"{node_pool.initial_node_count} total"
    return "Not available"

def getTaints(taints):
    if not taints:
        return "Not available"

    formatted_taints = []
    for taint in taints:
        key_value = f"{taint.key}={taint.value}" 
        formatted_taints.append(key_value)

    return ", ".join(formatted_taints)
