from github.MainClass import Github
import logging

logger = logging.getLogger(__name__)

class GitHubIntegration:
    def __init__(self, token: str, selected_repo_name: str = None):
        self.client = Github(token)
        self.selected_repo = None
        if selected_repo_name:
            self.select_repository(selected_repo_name)
        
    def list_repositories(self):
        """List all accessible repositories"""
        try:
            user = self.client.get_user()
            repos = user.get_repos()
            return [{"name": repo.full_name, 
                    "description": repo.description,
                    "private": repo.private} 
                    for repo in repos]
        except Exception as e:
            logger.error(f"Error listing repositories: {str(e)}")
            raise

    def select_repository(self, repo_name: str):
        """Select a repository to work with"""
        try:
            repo = self.client.get_repo(repo_name)
            self.selected_repo = repo
            return {
                "name": repo.full_name,
                "description": repo.description,
                "url": repo.html_url
            }
        except Exception as e:
            logger.error(f"Error selecting repository: {str(e)}")
            raise

    def get_default_repo(self):
        """Get the currently selected repository"""
        if not self.selected_repo:
            raise Exception("No repository selected. Please select a repository first using /github select <repository_name>")
        return self.selected_repo

    def list_issues(self, state: str = "open"):
        """List issues from the default repository"""
        try:
            # We'll expand this to handle multiple repos later
            repo = self.get_default_repo()
            issues = repo.get_issues(state=state)
            return [{"number": issue.number, 
                    "title": issue.title, 
                    "state": issue.state} 
                    for issue in issues]
        except Exception as e:
            logger.error(f"Error listing issues: {str(e)}")
            raise

    def create_issue(self, title: str, body: str):
        """Create a new issue"""
        try:
            repo = self.get_default_repo()
            issue = repo.create_issue(title=title, body=body)
            return {
                "number": issue.number,
                "title": issue.title,
                "url": issue.html_url
            }
        except Exception as e:
            logger.error(f"Error creating issue: {str(e)}")
            raise

    def list_pull_requests(self, state: str = "open"):
        """List pull requests"""
        try:
            repo = self.get_default_repo()
            pulls = repo.get_pulls(state=state)
            return [{"number": pr.number, 
                    "title": pr.title, 
                    "state": pr.state} 
                    for pr in pulls]
        except Exception as e:
            logger.error(f"Error listing PRs: {str(e)}")
            raise

    def test_connection(self):
        """Test if the GitHub token is valid"""
        try:
            user = self.client.get_user()
            return {
                "login": user.login,
                "name": user.name or user.login
            }
        except Exception as e:
            logger.error(f"Error testing GitHub connection: {str(e)}")
            raise 