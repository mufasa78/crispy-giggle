import os
import json
from google.cloud import secretmanager

def access_secret_version(secret_id, version_id="latest"):
    """Access the secret version."""
    # Create the Secret Manager client
    client = secretmanager.SecretManagerServiceClient()
    
    # Build the resource name of the secret version
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    
    # Access the secret version
    response = client.access_secret_version(name=name)
    
    # Return the decoded payload
    return response.payload.data.decode("UTF-8")

def get_database_url():
    """Get DATABASE_URL from Secret Manager for App Engine."""
    if os.environ.get("GAE_ENV", "") == "standard":
        # In production (App Engine)
        try:
            return access_secret_version("DATABASE_URL")
        except Exception as e:
            print(f"Error accessing secret: {e}")
            # Fallback to local development connection if available
            return os.environ.get("DATABASE_URL", "")
    else:
        # Local development
        return os.environ.get("DATABASE_URL", "")

def get_session_secret():
    """Get SESSION_SECRET from Secret Manager for App Engine."""
    if os.environ.get("GAE_ENV", "") == "standard":
        # In production (App Engine)
        try:
            return access_secret_version("SESSION_SECRET")
        except Exception as e:
            print(f"Error accessing secret: {e}")
            # Fallback to a default secret (not secure for production, just a fallback)
            return os.environ.get("SESSION_SECRET", "dev-secret-key-do-not-use-in-production")
    else:
        # Local development
        return os.environ.get("SESSION_SECRET", "dev-secret-key-for-local-only")
