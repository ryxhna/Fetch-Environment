# Fetching Environment

This program is designed to generate a detailed asset list from various services on Google Cloud Platform (GCP). The services currently supported include:  
- **Google Storage**  
- **Memorystore for Redis**  
- **Kubernetes Engine** *(coming soon)*  

## Features  
- Extract detailed information about resources across multiple GCP services.  
- Generate reports in structured formats like Excel for easier analysis and documentation.  
- Expandable architecture to support additional GCP services in the future.  

## Requirements  

### Prerequisites  
- **Python** 3.8 or later installed on your system.  
- Access to a Google Cloud project with the necessary API permissions enabled.  
  - Google Cloud APIs required:
    - Storage API
    - Memorystore API
    - Kubernetes Engine API *(for future use)*  
- An account that has access to the service to be used in Google Cloud Platform or Service account credentials (JSON key file) with the appropriate role to access the target GCP service.  

### Python Libraries  
Install the required Python libraries using the following commands:  

```bash
pip install pandas openpyxl xlsxwriter
pip install google-api-core google-cloud-monitoring
pip install google-cloud-redis google-cloud-storage google-cloud-container
```