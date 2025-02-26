from abc import ABC, abstractmethod

class ProjectManagementIntegration(ABC):
    """Base class for all project management tool integrations."""
    
    @abstractmethod
    def authenticate(self):
        """Authenticate with the PM service."""
        pass
    
    @abstractmethod
    def create_task(self, title, description, assignee=None, due_date=None, priority=None):
        """Create a new task/issue/card."""
        pass
    
    @abstractmethod
    def update_task(self, task_id, **kwargs):
        """Update an existing task."""
        pass
    
    @abstractmethod
    def get_task(self, task_id):
        """Get task details."""
        pass
    
    @abstractmethod
    def get_tasks(self, filters=None):
        """Get multiple tasks based on filters."""
        pass
    
    @abstractmethod
    def create_comment(self, task_id, comment):
        """Add a comment to a task."""
        pass
