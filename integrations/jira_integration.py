import os
from jira import JIRA
from .base import ProjectManagementIntegration

class JiraIntegration(ProjectManagementIntegration):
    def __init__(self, url=None, username=None, api_token=None):
        self.url = url or os.environ.get("JIRA_URL")
        self.username = username or os.environ.get("JIRA_USERNAME")
        self.api_token = api_token or os.environ.get("JIRA_API_TOKEN")
        self.client = None
    
    def authenticate(self):
        """Authenticate with Jira."""
        self.client = JIRA(
            server=self.url,
            basic_auth=(self.username, self.api_token)
        )
        return self.client is not None
    
    def create_task(self, title, description, assignee=None, due_date=None, priority=None):
        """Create a new Jira issue."""
        if not self.client:
            self.authenticate()
            
        issue_dict = {
            'project': {'key': os.environ.get("JIRA_PROJECT_KEY")},
            'summary': title,
            'description': description,
            'issuetype': {'name': 'Task'},
        }
        
        if assignee:
            issue_dict['assignee'] = {'name': assignee}
            
        # Add more fields like priority, due date if provided
        
        new_issue = self.client.create_issue(fields=issue_dict)
        return {
            'id': new_issue.key,
            'url': f"{self.url}/browse/{new_issue.key}"
        }
    
    def update_task(self, task_id, **kwargs):
        """Update an existing Jira issue."""
        if not self.client:
            self.authenticate()
            
        issue = self.client.issue(task_id)
        
        fields = {}
        if 'title' in kwargs:
            fields['summary'] = kwargs['title']
        if 'description' in kwargs:
            fields['description'] = kwargs['description']
        if 'assignee' in kwargs:
            fields['assignee'] = {'name': kwargs['assignee']}
            
        if fields:
            issue.update(fields=fields)
            
        return True
    
    def get_task(self, task_id):
        """Get Jira issue details."""
        if not self.client:
            self.authenticate()
            
        issue = self.client.issue(task_id)
        return {
            'id': issue.key,
            'title': issue.fields.summary,
            'description': issue.fields.description,
            'status': issue.fields.status.name,
            'assignee': issue.fields.assignee.displayName if issue.fields.assignee else None,
            'url': f"{self.url}/browse/{issue.key}"
        }
    
    def get_tasks(self, filters=None):
        """Get Jira issues based on filters."""
        if not self.client:
            self.authenticate()
            
        jql = f"project = {os.environ.get('JIRA_PROJECT_KEY')}"
        
        if filters:
            if 'assignee' in filters:
                jql += f" AND assignee = {filters['assignee']}"
            if 'status' in filters:
                jql += f" AND status = '{filters['status']}'"
                
        issues = self.client.search_issues(jql)
        return [{
            'id': issue.key,
            'title': issue.fields.summary,
            'status': issue.fields.status.name,
            'assignee': issue.fields.assignee.displayName if issue.fields.assignee else None,
            'url': f"{self.url}/browse/{issue.key}"
        } for issue in issues]
    
    def create_comment(self, task_id, comment):
        """Add a comment to a Jira issue."""
        if not self.client:
            self.authenticate()
            
        self.client.add_comment(task_id, comment)
        return True
