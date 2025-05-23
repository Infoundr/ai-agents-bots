class ProjectManagementIntegration:
    """Base class for all project management integrations."""
    
    def authenticate(self):
        """Authenticate with the project management service."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def create_task(self, title, description, assignee=None, due_date=None, priority=None):
        """Create a new task."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def update_task(self, task_id, **kwargs):
        """Update an existing task."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_task(self, task_id):
        """Get task details."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_tasks(self, filters=None):
        """Get tasks based on filters."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def create_comment(self, task_id, comment):
        """Add a comment to a task."""
        raise NotImplementedError("Subclasses must implement this method")