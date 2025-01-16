import logging
from google.cloud import redis_v1
from google.api_core.exceptions import GoogleAPICallError, NotFound

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_redis_memorystore(project_id):
    """Fetch Redis instance information for a specific project."""
    client = redis_v1.CloudRedisClient()
    try:
        logging.info(f"Fetching Redis instances for project: {project_id}")
        request = redis_v1.ListInstancesRequest(parent=f"projects/{project_id}/locations/-")
        instances = client.list_instances(request=request)

        if not instances.instances:
            logging.info(f"No Redis instances found for project {project_id}.")
            return []

        redis_info = []
        for instance in instances.instances:
            redis_info.append({
                "Project ID": project_id,
                "Instance ID": instance.name.split('/')[-1],
                "Type": instance.tier,
                "Version": instance.redis_version,
                "Location": instance.location_id,
                "Primary Endpoint": f"{instance.host}:{instance.port}",
                "Read Replica": "Yes" if instance.replica_count > 0 else "No",
                "Read Endpoint": f"{instance.read_endpoint}:{instance.read_endpoint_port}" if instance.read_endpoint else "",
                "Instance Capacity (GB)": instance.memory_size_gb,
                "AUTH": "Enabled" if instance.auth_enabled else "Disabled",
                "TLS": "Enabled" if instance.transit_encryption_mode == "SERVER_AUTHENTICATION" else "Disabled",
                "Labels": ", ".join(f"{k}: {v}" for k, v in instance.labels.items()) if instance.labels else "None"
            })
        logging.info(f"Found {len(redis_info)} Redis instance(s) for project {project_id}.")
        return redis_info

    except NotFound:
        logging.error(f"Project {project_id} not found or Redis API is not enabled.")
        return []
    except GoogleAPICallError as api_error:
        logging.error(f"API error while fetching Redis instances for project {project_id}: {api_error}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error while fetching Redis instances for project {project_id}: {e}")
        return []