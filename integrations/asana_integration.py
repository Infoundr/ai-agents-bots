import os
import json
from datetime import datetime
import asana
from asana.rest import ApiException
from dotenv import load_dotenv
from .base import ProjectManagementIntegration

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

class AsanaIntegration(ProjectManagementIntegration):
    def __init__(self, access_token=None, workspace_gid=None):
        self.access_token = access_token or os.environ.get("ASANA_ACCESS_TOKEN")
        self.workspace_gid = workspace_gid or os.environ.get("ASANA_WORKSPACE_GID")
        self.project_gid = os.environ.get("ASANA_PROJECT_ID", os.environ.get("ASANA_PROJECT_GID", ""))
        self.model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
        
        # Set up Asana API client
        self.configuration = None
        self.api_client = None
        self.tasks_api = None
        self.client = None  # For compatibility with previous implementation
        
        # Initialize API clients
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Asana."""
        # Set up using the official Asana SDK
        self.configuration = asana.Configuration()
        self.configuration.access_token = self.access_token
        self.api_client = asana.ApiClient(self.configuration)
        self.tasks_api = asana.TasksApi(self.api_client)
        
        # Remove the old client initialization that's causing the error
        # self.client = asana.Client.access_token(self.access_token)
        
        return self.api_client is not None
        
    @tool
    def create_asana_task(self, task_name, due_on="today", description=None, assignee=None, 
                          dependencies=None, custom_fields=None, subtasks=None):
        """
        Creates a task in Asana with enhanced capabilities
        """
        if due_on == "today":
            due_on = str(datetime.now().date())

        task_body = {
            "data": {
                "name": task_name,
                "due_on": due_on,
                "projects": [self.project_gid]
            }
        }
        
        # Add optional fields if provided
        if description:
            task_body["data"]["notes"] = description
        if assignee:
            task_body["data"]["assignee"] = assignee
        if dependencies:
            task_body["data"]["dependencies"] = dependencies
        if custom_fields:
            task_body["data"]["custom_fields"] = custom_fields

        try:
            # Create main task
            api_response = self.tasks_api.create_task(task_body, {})
            task_gid = api_response['gid']

            # Create subtasks if provided
            if subtasks:
                for subtask_name in subtasks:
                    subtask_body = {
                        "data": {
                            "name": subtask_name,
                            "parent": task_gid,
                            "projects": [self.project_gid]
                        }
                    }
                    self.tasks_api.create_task(subtask_body, {})

            return json.dumps(api_response, indent=2)
        except ApiException as e:
            return f"Exception when calling TasksApi->create_task: {e}"
    
    def create_task(self, title, description, assignee=None, due_date=None, priority=None):
        """Create a new Asana task. (Compatibility method)"""
        result = json.loads(self.create_asana_task(
            task_name=title,
            due_on=due_date or "today",
            description=description,
            assignee=assignee
        ))
        
        return {
            'id': result['gid'],
            'url': f"https://app.asana.com/0/{self.project_gid}/{result['gid']}"
        }
    
    def update_task(self, task_id, **kwargs):
        """Update an existing Asana task."""
        if not self.api_client:
            self.authenticate()
        
        task_data = {"data": {}}
        if 'title' in kwargs:
            task_data["data"]["name"] = kwargs['title']
        if 'description' in kwargs:
            task_data["data"]["notes"] = kwargs['description']
        if 'assignee' in kwargs:
            task_data["data"]["assignee"] = kwargs['assignee']
        if 'due_date' in kwargs:
            task_data["data"]["due_on"] = kwargs['due_date']
        
        try:
            self.tasks_api.update_task(task_id, task_data, {})
            return True
        except ApiException as e:
            raise Exception(f"Error updating Asana task: {e}")
    
    def get_task(self, task_id):
        """Get Asana task details."""
        if not self.api_client:
            self.authenticate()
        
        try:
            task = self.tasks_api.get_task(task_id, {})
            return {
                'id': task['gid'],
                'title': task['name'],
                'description': task.get('notes', ''),
                'status': "Completed" if task.get('completed', False) else "Active",
                'assignee': task.get('assignee', {}).get('name') if task.get('assignee') else None,
                'url': f"https://app.asana.com/0/{self.project_gid}/{task['gid']}"
            }
        except ApiException as e:
            raise Exception(f"Error fetching Asana task: {e}")
    
    def get_tasks(self, filters=None):
        """Get Asana tasks based on filters."""
        if not self.api_client:
            self.authenticate()
        
        try:
            # Build the options parameter
            options = {"project": self.project_gid}
            
            if filters and 'assignee' in filters:
                options["assignee"] = filters['assignee']
            
            tasks_result = self.tasks_api.get_tasks(options)
            tasks = []
            
            # Collect each task's info
            for task in tasks_result:
                task_detail = self.get_task(task['gid'])
                tasks.append(task_detail)
            
            return tasks
        except ApiException as e:
            raise Exception(f"Error fetching Asana tasks: {e}")
    
    def create_comment(self, task_id, comment):
        """Add a comment to an Asana task."""
        if not self.api_client:
            self.authenticate()
        
        try:
            # Create a stories API instance
            stories_api = asana.StoriesApi(self.api_client)
            
            data = {
                "data": {
                    "text": comment
                }
            }
            
            # Use the new API style
            stories_api.create_story_for_task(task_id, data, {})
            return True
        except Exception as e:
            raise Exception(f"Error creating comment: {e}")
    
    def process_natural_language_request(self, text):
        """Process a natural language request to create tasks using LangChain."""
        # Create the initial messages
        messages = [
            SystemMessage(content=f"You are a personal assistant who helps manage tasks in Asana. The current date is: {datetime.now().date()}")
        ]
        
        # Add the user's request
        messages.append(HumanMessage(content=text))
        
        # Define the tools and create LangChain chatbot
        tools = [self.create_asana_task]
        
        if "gpt" in self.model.lower():
            asana_chatbot = ChatOpenAI(model=self.model)
        else:
            asana_chatbot = ChatAnthropic(model=self.model)
            
        asana_chatbot_with_tools = asana_chatbot.bind_tools(tools)
        
        # Function to handle tool calling with recursion
        def prompt_ai(messages, nested_calls=0):
            ai_response = asana_chatbot_with_tools.invoke(messages)
            tool_calls = len(ai_response.tool_calls) > 0
            
            # If the AI decided to invoke a tool
            if tool_calls:
                available_functions = {
                    "create_asana_task": self.create_asana_task
                }
                
                # Add the tool request to messages
                messages.append(ai_response)
                
                # Process each tool call
                for tool_call in ai_response.tool_calls:
                    tool_name = tool_call["name"].lower()
                    selected_tool = available_functions[tool_name]
                    tool_output = selected_tool.invoke(tool_call["args"])
                    messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))
                
                # Call the AI again to get final response
                return prompt_ai(messages, nested_calls + 1)
            
            return ai_response
        
        # Get AI response
        result = prompt_ai(messages)
        
        # Parse the result to extract task information
        task_info = {}
        for msg in messages:
            if isinstance(msg, ToolMessage):
                try:
                    task_data = json.loads(msg.content)
                    task_info = {
                        'id': task_data.get('gid', ''),
                        'title': task_data.get('name', ''),
                        'url': f"https://app.asana.com/0/{self.project_gid}/{task_data.get('gid', '')}"
                    }
                except:
                    pass
        
        return {
            'response': result.content,
            'task': task_info
        }