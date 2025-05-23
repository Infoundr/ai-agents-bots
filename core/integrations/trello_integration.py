import os
from trello import TrelloClient
from .base import ProjectManagementIntegration

class TrelloIntegration(ProjectManagementIntegration):
    def __init__(self, api_key=None, token=None, board_id=None):
        self.api_key = api_key or os.environ.get("TRELLO_API_KEY")
        self.token = token or os.environ.get("TRELLO_TOKEN")
        self.board_id = board_id or os.environ.get("TRELLO_BOARD_ID")
        self.client = None
        self.board = None
    
    def authenticate(self):
        """Authenticate with Trello."""
        self.client = TrelloClient(
            api_key=self.api_key,
            token=self.token
        )
        
        if self.board_id:
            self.board = self.client.get_board(self.board_id)
            
        return self.client is not None
    
    def create_task(self, title, description, assignee=None, due_date=None, priority=None):
        """Create a new Trello card."""
        if not self.client or not self.board:
            self.authenticate()
            
        # Get the first list in the board (usually "To Do")
        lists = self.board.list_lists()
        target_list = lists[0]
        
        card = target_list.add_card(title, description)
        
        if assignee:
            # Find the member by username
            members = self.board.get_members()
            for member in members:
                if member.username == assignee:
                    card.add_member(member)
                    break
                    
        if due_date:
            card.set_due(due_date)
            
        return {
            'id': card.id,
            'url': card.url
        }
    
    def update_task(self, task_id, **kwargs):
        """Update an existing Trello card."""
        if not self.client:
            self.authenticate()
            
        card = self.client.get_card(task_id)
        
        if 'title' in kwargs:
            card.set_name(kwargs['title'])
        if 'description' in kwargs:
            card.set_description(kwargs['description'])
        if 'due_date' in kwargs:
            card.set_due(kwargs['due_date'])
            
        return True
    
    def get_task(self, task_id):
        """Get Trello card details."""
        if not self.client:
            self.authenticate()
            
        card = self.client.get_card(task_id)
        
        return {
            'id': card.id,
            'title': card.name,
            'description': card.description,
            'status': card.list_name,
            'assignee': card.member_names[0] if card.member_names else None,
            'url': card.url
        }
    
    def get_tasks(self, filters=None):
        """Get Trello cards based on filters."""
        if not self.client or not self.board:
            self.authenticate()
            
        cards = self.board.get_cards()
        
        if filters and 'assignee' in filters:
            cards = [card for card in cards if filters['assignee'] in card.member_names]
            
        return [{
            'id': card.id,
            'title': card.name,
            'status': card.list_name,
            'assignee': card.member_names[0] if card.member_names else None,
            'url': card.url
        } for card in cards]
    
    def create_comment(self, task_id, comment):
        """Add a comment to a Trello card."""
        if not self.client:
            self.authenticate()
            
        card = self.client.get_card(task_id)
        card.comment(comment)
        
        return True
