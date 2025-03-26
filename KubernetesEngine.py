import logging
import datetime
import json
from google.cloud import container_v1
from google.api_core.exceptions import NotFound
from Runner import LoadProject

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Mapping Image Type
ImageType_mapping = {
    "COS_CONTAINERD": "Container-Optimized OS with containerd (cos_containerd)",
    "UBUNTU": "Ubuntu",
    "UBUNTU_CONTAINERD": "Ubuntu with containerd",
    "CUSTOM_IMAGE": "Custom Image",
    "ML_IMAGE": "Machine Learning Optimized Image",
    "BIG_DATA_IMAGE": "Big Data Optimized Image",
    "LEGACY_IMAGE": "Legacy Image",
}

# Mapping Disk Type
DiskType_mapping = {
    "pd-standard": "Standard persistent disk",
    "pd-balanced": "Balanced persistent disk",
    "pd-ssd": "SSD persistent disk",
    "regional-ssd": "Regional SSD",
    "local-ssd": "Local SSD",
    "confidential-vm": "Confidential VM",
}

def calculate_TotalNodes(node_pool, cluster_client=None, project_id=None, location=None, cluster_name=None):
    # Cek apakah autoscaling aktif
    if hasattr(node_pool, "autoscaling") and node_pool.autoscaling.enabled:
        return f"Min: {node_pool.autoscaling.min_node_count}, Max: {node_pool.autoscaling.max_node_count}"

    # Cek instance_group_urls
    if hasattr(node_pool, "instance_group_urls") and node_pool.instance_group_urls:
        total_nodes = len(node_pool.instance_group_urls)
        return f"{total_nodes} total"

    # Gunakan initial_node_count sebagai fallback
    if hasattr(node_pool, "initial_node_count"):
        return f"{node_pool.initial_node_count} total"

    # Jika parameter cluster_client tersedia, ambil data dari API
    if cluster_client and project_id and location and cluster_name:
        try:
            instance_groups = cluster_client.list_node_pools(
                parent=f"projects/{project_id}/locations/{location}/clusters/{cluster_name}"
            )
            total_nodes = sum(len(np.instance_group_urls) for np in instance_groups.node_pools if hasattr(np, "instance_group_urls"))
            return f"{total_nodes} total (calculated)"
        except Exception as e:
            return f"Error fetching node count: {str(e)}"

    return "Not available"

def getKubernetesEngine(project_id):
    cluster_client = container_v1.ClusterManagerClient()
    results = []

    try:
        clusters_response = cluster_client.list_clusters(parent=f"projects/{project_id}/locations/-")
        for cluster in clusters_response.clusters:
            total_nodes = 0
            cluster_info = {
                "Project ID": project_id,
                "Cluster Name": cluster.name,
                "Mode": "Standard" if cluster.private_cluster_config else "Autopilot",
                "Location Type": "Regional" if cluster.locations and len(cluster.locations) > 1 else "Zonal",
                "Location": cluster.location,
                "Cluster Size": cluster.current_node_count,
                "Cluster Version": cluster.current_master_version,
                # "COS Version": cluster.current_node_version,
                "Private Endpoint": getattr(cluster.private_cluster_config, "private_endpoint", "Not available"),
                "Control Plane Address Range": cluster.private_cluster_config.master_ipv4_cidr_block if cluster.private_cluster_config else "N/A",
                "Cluster Pod IPv4 Range (default)": cluster.cluster_ipv4_cidr,
                "Maximum Pods per Node": getattr(cluster.default_max_pods_constraint, "max_pods_per_node", "Not available"),
                "Network": cluster.network,
                "Subnet": cluster.subnetwork,
                "Autoscaling Profile": getattr(cluster.autoscaling, "profile", "Balanced") if cluster.autoscaling else "Any",
                "Tags": getattr(cluster, "network_tags", []),
                "Labels": cluster.resource_labels
            }

            try:
                node_pools_response = cluster_client.list_node_pools(
                    parent=f"projects/{project_id}/locations/{cluster.location}/clusters/{cluster.name}"
                )
                for node_pool in node_pools_response.node_pools:
                    num_nodes = calculate_TotalNodes(node_pool, cluster_client, project_id, cluster.location, cluster.name)
                    total_nodes += int(num_nodes.split()[0]) if num_nodes.split()[0].isdigit() else 0
                    
                    node_pool_info = {
                        "Node Pool Name": node_pool.name,
                        "Node Version": node_pool.version,
                        "Autoscaling (Min/Max/Total)": calculate_TotalNodes(node_pool, cluster_client, project_id, cluster.location, cluster.name),
                        "Image Type": ImageType_mapping.get(getattr(node_pool.config, "image_type", "Not available"), "Not available"),
                        "Machine Type": getattr(node_pool.config, "machine_type", "Not available"),
                        "Boot Disk Type": DiskType_mapping.get(node_pool.config.disk_type, "Unknown"),
                        "Boot Disk Size (per node)": f"{getattr(node_pool.config, 'disk_size_gb', 'Not available')} GB",
                        "Max Surge": node_pool.upgrade_settings.max_surge if node_pool.upgrade_settings else "N/A",
                        "Autoscaling Status": "On" if node_pool.autoscaling.enabled else "Off",
                        "Taints": getTaints(node_pool.config.taints) if node_pool.config else "Not available",
                        "Node Zones": node_pool.locations if node_pool.locations else [],
                        "GCE Instance Metadata": node_pool.config.metadata if node_pool.config.metadata else {},
                    }
                    combined_info = {key: node_pool_info.get(key, cluster_info.get(key, "Not available")) for key in [
                        "Project ID", "Cluster Name", "Node Pool Name", "Cluster Size", "Mode", 
                        "Location Type", "Location", "Cluster Version", "Node Version", 
                        "Autoscaling Profile", "Autoscaling Status", "Autoscaling (Min/Max/Total)", "Maximum Pods per Node",
                        "Private Endpoint", "Control Plane Address Range", "Cluster Pod IPv4 Range (default)", "Network", "Subnet", 
                        "Max Surge", "Machine Type", "Boot Disk Type", "Boot Disk Size (per node)",
                        "Image Type", "Node Zones", "Tags", "Taints", "Labels", "GCE Instance Metadata",
                    ]}
                    results.append(combined_info)

            except NotFound:
                logging.warning(f"Node pools not found for cluster '{cluster.name}' in project '{project_id}'.")
    except NotFound:
        logging.warning(f"No clusters found for project '{project_id}'.")

    return results

def processProjects():
    projects = LoadProject()
    if not projects:
        logging.error("No projects found. Ensure the JSON file is correctly configured.")
        return []

    all_data = []
    for project_id in projects:
        logging.info(f"Processing project: {project_id}")
        project_data = getKubernetesEngine(project_id)
        all_data.extend(project_data)

    return all_data

def getTaints(taints):
    if not taints:
        return "Not available"
    
    formatted_taints = []
    for taint in taints:
        key_value = f"{taint.key}={taint.value}"  # Hanya key dan value
        formatted_taints.append(key_value)
    
    return ", ".join(formatted_taints)

from kubernetes import client, config