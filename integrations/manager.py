# from .jira_integration import JiraIntegration
from .asana_integration import AsanaIntegration
# from .trello_integration import TrelloIntegration

class IntegrationManager:
    """Manages all integrations for the bot."""
    
    def __init__(self):
        self.integrations = {}
        
    def register_integration(self, name, integration):
        """Register a new integration."""
        self.integrations[name] = integration
        
    def get_integration(self, name):
        """Get an integration by name."""
        return self.integrations.get(name)
        
    def setup_default_integrations(self):
        """Set up default integrations from environment variables."""
        # Check if Jira is configured
        import os
        # if os.environ.get("JIRA_URL") and os.environ.get("JIRA_USERNAME") and os.environ.get("JIRA_API_TOKEN"):
        #     self.register_integration("jira", JiraIntegration())
            
        # Check if Asana is configured
        if os.environ.get("ASANA_ACCESS_TOKEN") and os.environ.get("ASANA_WORKSPACE_GID"):
            self.register_integration("asana", AsanaIntegration())
            
        # Check if Trello is configured
        # if os.environ.get("TRELLO_API_KEY") and os.environ.get("TRELLO_TOKEN") and os.environ.get("TRELLO_BOARD_ID"):
        #     self.register_integration("trello", TrelloIntegration())
