import logging
from google.cloud import storage
from google.api_core.exceptions import GoogleAPICallError, NotFound

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def GetStorageBuckets(project_id):
    """Fetch detailed bucket information for a specific project."""
    client = storage.Client(project=project_id)
    try:
        logging.info(f"Fetching storage buckets for project: {project_id}")
        buckets = client.list_buckets()

        bucket_info = []
        for bucket in buckets:
            # Determine public access prevention status
            public_access_prevention = bucket.iam_configuration.public_access_prevention
            if public_access_prevention == "enforced":
                pap_status = "Enabled via bucket setting"
            elif public_access_prevention == "inherited":
                pap_status = "Enabled via org policy inheritance"
            elif public_access_prevention is None:
                pap_status = "Not enabled via bucket setting; org policy status unavailable"
            else:
                pap_status = "Not enabled by org policy or bucket setting"

            # Determine soft delete policy
            soft_delete_policy = "Default 7 Days"
            if bucket.lifecycle_rules:
                for rule in bucket.lifecycle_rules:
                    if rule["action"]["type"] == "Delete":
                        days = rule["condition"].get("age", None)
                        if days:
                            soft_delete_policy = f"Custom {days} Days"
                            break

            # Extract lifecycle rules
            lifecycle_rules = []
            if bucket.lifecycle_rules:
                for rule in bucket.lifecycle_rules:
                    action = rule["action"]["type"]
                    conditions = ", ".join(f"{k}: {v}" for k, v in rule["condition"].items())
                    lifecycle_rules.append(f"{action} -> {conditions}")
            lifecycle_rules_str = "; ".join(lifecycle_rules) if lifecycle_rules else "None"

            # Collect bucket details
            bucket_details = {
                "Project ID": project_id,
                "Bucket Name": bucket.name,
                "Creation Date": bucket.time_created.strftime("%Y-%m-%d"),
                "Last Modified": bucket.updated.strftime("%Y-%m-%d") if bucket.updated else "N/A",
                "Location Type": bucket.location_type,  # Multi-regional, Regional, etc.
                "Location": bucket.location,
                "Storage Class": bucket.storage_class,
                "Hierarchical Namespace": "Enabled" if bucket.iam_configuration.uniform_bucket_level_access_enabled else "Not enabled",
                "Replication": "Enabled" if bucket.iam_configuration.public_access_prevention == "enforced" else "Disabled",
                #"Cross-bucket Replication": ", ".join(bucket.replication_targets) if bucket.replication_targets else "None",
                "Access Control": "Uniform" if bucket.iam_configuration.uniform_bucket_level_access_enabled else "Fine-grained",
                "Public Access Prevention": pap_status,
                "Soft Delete Policy": soft_delete_policy,
                "Object Versioning": "Enabled" if bucket.versioning_enabled else "Disabled",
                #"Bucket Retention Policy": bucket.retention_policy.retention_period if bucket.retention_policy else "None",
                #"Object Retention": bucket.retention_policy.retention_period if bucket.retention_policy else "None",
                "Lifecycle Rules": lifecycle_rules_str,
                "Tags": ", ".join(f"{k}: {v}" for k, v in bucket.labels.items()) if bucket.labels else "None",
                "gsutil URI": f"gs://{bucket.name}",
                "Cloud Console URL": f"https://console.cloud.google.com/storage/browser/{bucket.name}"

            }

            bucket_info.append(bucket_details)

        logging.info(f"Found {len(bucket_info)} bucket(s) for project {project_id}.")
        return bucket_info

    except NotFound:
        logging.error(f"Project {project_id} not found or Storage API is not enabled.")
        return []
    except GoogleAPICallError as api_error:
        logging.error(f"API error while fetching buckets for project {project_id}: {api_error}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error while fetching buckets for project {project_id}: {e}")
        return []
