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
import streamlit as st

def setup_authentication():
    """Set up authentication for the application."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_id = None
    
    # For simplicity in development, auto-authenticate with a test user
    # In production, replace this with real authentication
    if not st.session_state.authenticated:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                user_id = authenticate_user(email, password)
                if user_id:
                    st.session_state.authenticated = True
                    st.session_state.user_id = user_id
                    st.experimental_rerun()

def authenticate_user(email, password):
    """
    Authenticate a user with email and password.
    
    Args:
        email (str): User's email address
        password (str): User's password
        
    Returns:
        str: User ID if authentication successful, None otherwise
    """
    # This is a simple example - replace with actual authentication logic
    # For demo purposes only
    if email and password:
        # Simple validation - in reality you would check against a database
        if "@" in email and len(password) >= 6:
            # Generate a simple user_id from the email
            # In a real app, you'd get this from your database
            user_id = str(hash(email) % 10000)
            return user_id
    
    # Authentication failed
    st.error("Invalid email or password")
    return None

class AsanaIntegration(ProjectManagementIntegration):
    def __init__(self, access_token=None, workspace_gid=None, project_gid=None):
        self.access_token = access_token or os.environ.get("ASANA_ACCESS_TOKEN")
        self.workspace_gid = workspace_gid or os.environ.get("ASANA_WORKSPACE_GID")
        # Use the provided project_gid first, fall back to env vars only if not provided
        self.project_gid = project_gid or os.environ.get("ASANA_PROJECT_ID") or os.environ.get("ASANA_PROJECT_GID", "")
        self.model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
        
        # Set up Asana API client
        self.configuration = None
        self.api_client = None
        self.tasks_api = None
        
        # Initialize API clients
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Asana."""
        # Set up using the official Asana SDK
        self.configuration = asana.Configuration()
        self.configuration.access_token = self.access_token
        self.api_client = asana.ApiClient(self.configuration)
        self.tasks_api = asana.TasksApi(self.api_client)
        
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
        print(f"Processing natural language request: {text}")

        # Ensure project_gid is properly set
        if not self.project_gid:
            # Try to get a project from the workspace if we have one
            if self.workspace_gid:
                try:
                    # Create projects API
                    projects_api = asana.ProjectsApi(self.api_client)
                    # Get projects in workspace
                    projects = list(projects_api.get_projects({
                        'workspace': self.workspace_gid,
                        'limit': 1  # Just get the first one
                    }))
                
                    if projects:
                        self.project_gid = projects[0]['gid']
                        print(f"Found and using project: {projects[0]['name']} ({self.project_gid})")
                except Exception as e:
                    print(f"Error finding projects: {e}")
                
        # If still no project_gid, raise error
        if not self.project_gid:
            raise ValueError("Asana project ID is not set. Please specify a project when connecting to Asana.")

        print(f"Using Asana project_gid: {self.project_gid}")

        # Create the initial messages
        messages = [
            SystemMessage(content=f"""You are the Infoundr Task AI Assistant, a helpful assistant specialized in task management for entrepreneurs and startup teams.
    
            You help users create and manage tasks in Asana using natural language. Today's date is {datetime.now().date()}.
    
            When users describe tasks, you should identify key details like:
            - Task name/title
            - Due date
            - Description/details
            - Subtasks (if applicable)
    
            Be friendly, professional, and focused on helping entrepreneurs manage their workloads efficiently.
            """)
        ]

        # Add the user's request
        messages.append(HumanMessage(content=text))
        print(f"Messages after adding user request: {messages}")

        # Create a standalone function that directly calls the Asana API
        @tool
        def create_task(task_name, due_on="today", description=None, assignee=None, 
                 dependencies=None, custom_fields=None, subtasks=None):
            """Creates a task in Asana with enhanced capabilities."""
            if due_on == "today":
                due_on = str(datetime.now().date())

            # Ensure project_gid is properly formatted
            try:
                project_id = str(self.project_gid)
                print(f"Using project ID: {project_id}")
            except Exception as e:
                print(f"Error formatting project ID: {e}")
                raise ValueError(f"Invalid project ID format: {self.project_gid}")

            task_body = {
                "data": {
                    "name": task_name,
                    "due_on": due_on,
                    "projects": [project_id]
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
                # Print the task body being sent to the API for debugging
                print(f"Sending task body to Asana API: {json.dumps(task_body)}")
        
                # Create main task
                api_response = self.tasks_api.create_task(task_body, {})
                task_gid = api_response['gid']
                print(f"Successfully created task with ID: {task_gid}")

                # Create subtasks if provided
                if subtasks:
                    for subtask in subtasks:
                        # Handle both string subtasks and dict subtasks
                        if isinstance(subtask, dict) and 'task_name' in subtask:
                            subtask_name = subtask['task_name']
                        elif isinstance(subtask, str):
                            subtask_name = subtask
                        else:
                            subtask_name = "Subtask"
                    
                        subtask_body = {
                            "data": {
                                "name": subtask_name,
                                "parent": task_gid,
                                "projects": [project_id]
                            }
                        }
                        self.tasks_api.create_task(subtask_body, {})

                return json.dumps(api_response, indent=2)
            except ApiException as e:
                error_detail = str(e)
                print(f"Asana API error: {error_detail}")
                return f"Exception when calling TasksApi->create_task: {error_detail}"
            except Exception as e:
                print(f"Unexpected error creating task: {e}")
                return f"Error creating task: {str(e)}"

        # Define the tools using the wrapper function instead of the class method
        tools = [create_task]
        print(f"Tools: {tools}")

        # Create LangChain chatbot
        if "gpt" in self.model.lower():
            print(f"Using OpenAI model: {self.model}")
            asana_chatbot = ChatOpenAI(model=self.model)
        else:
            print(f"Using Anthropic model: {self.model}")
            asana_chatbot = ChatAnthropic(model=self.model)

        asana_chatbot_with_tools = asana_chatbot.bind_tools(tools)
        print(f"Chatbot with tools: {asana_chatbot_with_tools}")

        # Get AI response with tool usage
        try:
            # First message to get tool calls
            ai_response = asana_chatbot_with_tools.invoke(messages)
            print(f"AI response: {ai_response}")
    
            # Check if there are tool calls
            if ai_response.tool_calls:
                print(f"Tool calls detected: {len(ai_response.tool_calls)}")
        
                # Add the AI's response to the conversation
                messages.append(ai_response)
        
                # Process all tool calls
                for tool_call in ai_response.tool_calls:
                    tool_call_id = tool_call["id"]
                    func_name = tool_call["name"]
                    args = tool_call["args"]
            
                    print(f"Processing tool call: {func_name} with args: {args}")
            
                    # Execute the tool
                    try:
                        tool_result = create_task.invoke(args)
                        print(f"Tool result: {tool_result}")
                
                        # Add tool result to conversation
                        messages.append(ToolMessage(
                            content=tool_result,
                            tool_call_id=tool_call_id,
                        ))
                    except Exception as tool_error:
                        print(f"Error executing tool: {tool_error}")
                        # Add error message as tool response
                        messages.append(ToolMessage(
                            content=f"Error: {str(tool_error)}",
                            tool_call_id=tool_call_id,
                        ))
        
                # Get final response after tool execution
                final_response = asana_chatbot.invoke(messages)
                print(f"Final response: {final_response.content}")
        
                # Parse the task info from the tool results
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
                            break  # Just get the first successful task
                        except:
                            continue
        
                return {
                    'response': final_response.content,
                    'task': task_info
                }
        
            else:
                # No tool calls, just return the response
                return {
                    'response': ai_response.content,
                    'task': {}
                }
        
        except Exception as e:
            print(f"Error in process_natural_language_request: {e}")            
            raise e