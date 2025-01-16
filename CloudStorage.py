import logging
from google.cloud import storage
from google.api_core.exceptions import GoogleAPICallError, NotFound

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_bucket_storage(project_id):
    """Fetch bucket information for a specific project."""
    client = storage.Client(project=project_id)
    try:
        logging.info(f"Fetching buckets for project: {project_id}")
        buckets = list(client.list_buckets())

        if not buckets:
            logging.info(f"No buckets found for project {project_id}.")
            return []

        bucket_data = []
        for bucket in buckets:
            bucket_info = {
                "Name": bucket.name,
                "Created": bucket.time_created.isoformat() if bucket.time_created else None,
                "Updated": bucket.updated.isoformat() if bucket.updated else None,
                "Hierarchical Namespace": bucket.hns_enabled,
                "Location Type": bucket.location_type,
                "Location": bucket.location,
                "Replication": bucket.replication_config,
                "Cross-Bucket Replication": bucket.rpo,
                "Default Storage Class": bucket.storage_class,
                "Requester Pays": bucket.requester_pays,
                "Tags": bucket.labels,
                "Labels": bucket.labels,
                "Cloud Console URL": f"https://console.cloud.google.com/storage/browser/{bucket.name}",
                "gsutil URI": f"gs://{bucket.name}",
                "Access Control": bucket.iam_configuration.uniform_bucket_level_access_enabled,
                "Public Access Prevention": bucket.iam_configuration.public_access_prevention,
                "Public Access Status": "Public" if bucket.acl.loaded else "Private",
                "Soft Delete Policy": bucket.retention_policy.locked if bucket.retention_policy else None,
                "Object Versioning": bucket.versioning_enabled,
                "Bucket Retention Policy": bucket.retention_policy.retention_period if bucket.retention_policy else None,
                "Object Retention": bucket.retention_policy.retention_period if bucket.retention_policy else None,
                "Encryption Type": bucket.default_kms_key_name,
                "Lifecycle Rules": bucket.lifecycle_rules,
            }
            bucket_data.append(bucket_info)

        logging.info(f"Found {len(bucket_data)} bucket(s) for project {project_id}.")
        return bucket_data

    except NotFound:
        logging.error(f"Project {project_id} not found or Storage API is not enabled.")
        return []
    except GoogleAPICallError as api_error:
        logging.error(f"API error while fetching buckets for project {project_id}: {api_error}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error while fetching buckets for project {project_id}: {e}")
        return []
