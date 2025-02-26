import os
from dotenv import load_dotenv
from .asana_integration import AsanaIntegration
from .user_credentials import UserCredentialStore

class IntegrationManager:
    """Manages all integrations for the bot."""
    
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.integrations = {}
        
    def setup_default_integrations(self):
        """Set up integrations based on environment variables."""
        # Check for Asana configuration
        if os.environ.get("ASANA_ACCESS_TOKEN") and (
            os.environ.get("ASANA_WORKSPACE_GID") or 
            os.environ.get("ASANA_PROJECT_ID") or 
            os.environ.get("ASANA_PROJECT_GID")
        ):
            self.integrations["asana"] = AsanaIntegration(
                access_token=os.environ.get("ASANA_ACCESS_TOKEN"),
                workspace_gid=os.environ.get("ASANA_WORKSPACE_GID"),
                project_gid=os.environ.get("ASANA_PROJECT_ID") or os.environ.get("ASANA_PROJECT_GID")
            )
            
    def setup_user_integrations(self):
        """Set up integrations based on user credentials from database."""
        if not self.user_id:
            return
        
        # Load credentials from session storage
        store = UserCredentialStore()
        asana_creds = store.get_asana_credentials(self.user_id)
        
        if asana_creds:
            # Get the first project ID from the project_gids dict, if available
            project_gid = None
            if asana_creds.get("project_gids") and len(asana_creds["project_gids"]) > 0:
                # Get the first project's ID
                project_gid = list(asana_creds["project_gids"].values())[0]
            
            self.integrations["asana"] = AsanaIntegration(
                access_token=asana_creds["access_token"],
                workspace_gid=asana_creds["workspace_gid"],
                project_gid=project_gid  # Pass the project_gid directly!
            )
            
    def get_integration(self, integration_name):
        """Get a specific integration by name."""
        return self.integrations.get(integration_name)
    # Rest of your methods remain the same