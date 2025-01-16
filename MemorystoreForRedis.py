import logging
from google.cloud import redis_v1, monitoring_v3
from google.api_core.exceptions import GoogleAPICallError, NotFound

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_redis_metrics(project_id, instance_id, location):
    """Fetch metrics for a specific Redis instance using Cloud Monitoring API."""
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{project_id}"
    
    metrics = {
        "network_bytes": "redis.googleapis.com/redis/network/bytes",
        "calls": "redis.googleapis.com/redis/calls",
        "used_memory": "redis.googleapis.com/redis/memory/usage"
    }
    
    metric_values = {}
    for metric_name, metric_type in metrics.items():
        try:
            interval = monitoring_v3.TimeInterval()
            interval.end_time.seconds = int(time.time())
            interval.start_time.seconds = interval.end_time.seconds - 3600  # Last hour

            aggregation = monitoring_v3.Aggregation()
            aggregation.alignment_period.seconds = 3600
            aggregation.per_series_aligner = monitoring_v3.Aggregation.Aligner.ALIGN_SUM

            results = client.list_time_series(
                request={
                    "name": project_name,
                    "filter": f'metric.type="{metric_type}" AND resource.label.instance_id="{instance_id}" AND resource.label.location="{location}"',
                    "interval": interval,
                    "aggregation": aggregation,
                }
            )
            for result in results:
                metric_values[metric_name] = result.points[0].value.int64_value if result.points else "N/A"
        except Exception as e:
            logging.error(f"Error fetching metric {metric_name} for {instance_id}: {e}")
            metric_values[metric_name] = "N/A"
    return metric_values

def GetRedisMemorystore(project_id):
    """Fetch detailed Redis instance information for a specific project."""
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
            metrics = get_redis_metrics(project_id, instance.name.split('/')[-1], instance.location_id)

            redis_info.append({
                "Project ID": project_id,
                "Instance ID": instance.name.split('/')[-1],
                "Type": instance.tier.name,
                "Version": instance.redis_version,
                "Location": instance.location_id,
                "Status": instance.state.name,
                "Calls": metrics.get("calls", "N/A"),
                "Used Memory": metrics.get("used_memory", "N/A"),
                "Network Bytes": metrics.get("network_bytes", "N/A"),
                "Primary Endpoint": f"{instance.host}:{instance.port}",
                "Read Endpoint": f"{instance.read_endpoint}:{instance.read_endpoint_port}" if instance.read_endpoint else "",
                "IP Range": instance.authorized_network if instance.authorized_network else "N/A",
                "Connection Mode": instance.connect_mode.name,
                "Authorized Network": instance.authorized_network if instance.authorized_network else "N/A",
                "Read Replica": "Yes" if instance.replica_count > 0 else "No",
                "Replica Count": instance.replica_count,
                "Instance Capacity": instance.memory_size_gb,
                "Max Memory": f"{instance.memory_size_gb} GB",
                "RDB Snapshot": "On" if instance.persistence_iam_identity else "Off",
                "Labels": ", ".join(f"{k}: {v}" for k, v in instance.labels.items()) if instance.labels else "None",
                "AUTH": "Enabled" if instance.auth_enabled else "Disabled",
                "In-transit Encryption": "Enabled" if instance.transit_encryption_mode.name == "SERVER_AUTHENTICATION" else "Disabled",
                "CMEK": instance.persistence_iam_identity if instance.persistence_iam_identity else "Disabled"
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

# Example usage
if __name__ == "__main__":
    project_id = "your-project-id"
    redis_data = GetRedisMemorystore(project_id)
    for data in redis_data:
        print(data)
