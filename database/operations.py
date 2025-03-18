from .models import User, MessageHistory, AsanaConnection, GitHubConnection, AsanaTask, GitHubIssue
from .db import get_session
from datetime import datetime

class DatabaseOperations:
    def __init__(self):
        self.session = get_session()

    def get_or_create_user(self, user_id: str) -> User:
        user = self.session.query(User).filter_by(id=user_id).first()
        if not user:
            user = User(id=user_id)
            self.session.add(user)
            self.session.commit()
        return user

    def store_message_history(self, user_id: str, bot_name: str, message: str, response: str):
        history = MessageHistory(
            user_id=user_id,
            bot_name=bot_name,
            message=message,
            response=response
        )
        self.session.add(history)
        self.session.commit()

    def store_asana_credentials(self, user_id: str, token: str, workspace_gid: str, project_gids: dict):
        connection = self.session.query(AsanaConnection).filter_by(user_id=user_id).first()
        if connection:
            connection.token = token
            connection.workspace_gid = workspace_gid
            connection.project_gids = project_gids
            connection.updated_at = datetime.utcnow()
        else:
            connection = AsanaConnection(
                user_id=user_id,
                token=token,
                workspace_gid=workspace_gid,
                project_gids=project_gids
            )
            self.session.add(connection)
        self.session.commit()

    def get_asana_credentials(self, user_id: str):
        connection = self.session.query(AsanaConnection).filter_by(user_id=user_id).first()
        if connection:
            return {
                'token': connection.token,
                'workspace_gid': connection.workspace_gid,
                'project_gids': connection.project_gids
            }
        return None

    def store_github_credentials(self, user_id: str, token: str, selected_repo: str = None):
        connection = self.session.query(GitHubConnection).filter_by(user_id=user_id).first()
        if connection:
            connection.token = token
            if selected_repo:
                connection.selected_repo = selected_repo
            connection.updated_at = datetime.utcnow()
        else:
            connection = GitHubConnection(
                user_id=user_id,
                token=token,
                selected_repo=selected_repo
            )
            self.session.add(connection)
        self.session.commit()

    def get_github_credentials(self, user_id: str):
        connection = self.session.query(GitHubConnection).filter_by(user_id=user_id).first()
        if connection:
            return {
                'token': connection.token,
                'selected_repo': connection.selected_repo
            }
        return None

    def store_asana_task(self, connection_id: int, task_gid: str, title: str, description: str):
        task = AsanaTask(
            connection_id=connection_id,
            task_gid=task_gid,
            title=title,
            description=description
        )
        self.session.add(task)
        self.session.commit()

    def store_github_issue(self, connection_id: int, issue_number: int, title: str, body: str, state: str):
        issue = GitHubIssue(
            connection_id=connection_id,
            issue_number=issue_number,
            title=title,
            body=body,
            state=state
        )
        self.session.add(issue)
        self.session.commit()

    def close(self):
        self.session.close() 