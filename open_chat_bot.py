from flask import Flask, request, jsonify
from agent_bots import BOTS
import logging
from integrations.manager import IntegrationManager
from integrations.user_credentials import UserCredentialStore
import os
import json
from pathlib import Path
import asana

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Store tokens in a simple file-based system
TOKENS_DIR = Path("tokens")
TOKENS_DIR.mkdir(exist_ok=True)

# Initialize managers
credential_store = UserCredentialStore()

def store_token(user_id: str, token: str):
    """Store Asana token for a user"""
    with open(TOKENS_DIR / f"{user_id}.json", "w") as f:
        json.dump({"token": token}, f)

def get_token(user_id: str) -> str:
    """Get Asana token for a user"""
    try:
        with open(TOKENS_DIR / f"{user_id}.json", "r") as f:
            data = json.load(f)
            return data.get("token")
    except FileNotFoundError:
        return None

def handle_project_command(command, args):
    """Handle project management commands"""
    try:
        # Get user ID from the command context
        user_id = args.get('user_id')
        if not user_id:
            return jsonify({
                "text": "Error: User ID not provided",
                "bot_name": "Project Assistant"
            }), 400

        # Initialize integration manager for this user
        integration_manager = IntegrationManager(user_id=user_id)

        # Handle project_connect command first
        if command == "project_connect":
            token = args.get('token')
            if not token:
                return jsonify({
                    "text": "Error: Please provide your Asana token",
                    "bot_name": "Project Assistant"
                }), 400
                
            # Create Asana client using v5 SDK syntax
            configuration = asana.Configuration()
            configuration.access_token = token
            api_client = asana.ApiClient(configuration)
            
            try:
                # Get workspaces
                workspaces_api = asana.WorkspacesApi(api_client)
                workspaces = list(workspaces_api.get_workspaces({}))
                
                if not workspaces:
                    return jsonify({
                        "text": "Error: No workspaces found in your Asana account.",
                        "bot_name": "Project Assistant"
                    }), 400
                
                # Use the first workspace
                workspace = workspaces[0]
                workspace_gid = workspace['gid']
                
                # Get projects using ProjectsApi
                projects_api = asana.ProjectsApi(api_client)
                projects = list(projects_api.get_projects({'workspace': workspace_gid}))
                
                if not projects:
                    return jsonify({
                        "text": "Error: No projects found in workspace. Please create a project first.",
                        "bot_name": "Project Assistant"
                    }), 400
                
                # Use the first project
                project = projects[0]
                project_gids = {project['name']: project['gid']}
                
                # Store the credentials
                credential_store.store_asana_credentials(
                    user_id,
                    token,
                    workspace_gid,
                    project_gids
                )
                
                return jsonify({
                    "text": f"✅ Successfully connected your Asana account!\n"
                            f"Using workspace: {workspace['name']}\n"
                            f"Using project: {project['name']}",
                    "bot_name": "Project Assistant"
                })
                
            except asana.rest.ApiException as e:
                return jsonify({
                    "text": f"Error connecting to Asana: {str(e)}",
                    "bot_name": "Project Assistant"
                }), 500

        # For other commands, check if user has connected Asana
        asana_creds = credential_store.get_asana_credentials(user_id)
        if not asana_creds:
            return jsonify({
                "text": "⚠️ Please connect your Asana account first using `/project_connect YOUR_ASANA_TOKEN`\n\n"
                        "To get your token:\n"
                        "1. Go to https://app.asana.com/0/developer-console\n"
                        "2. Create a Personal Access Token\n"
                        "3. Copy and use it with the connect command",
                "bot_name": "Project Assistant"
            })

        # Set up integration manager with stored credentials
        integration_manager.setup_user_integrations()
        pm_tool = integration_manager.get_integration("asana")
        
        if command == "project_create_task":
            description = args.get('description', '')
            if not description:
                return jsonify({"error": "No task description provided"}), 400
            
            # Use our existing task creation logic
            result = pm_tool.process_natural_language_request(description)
            
            return jsonify({
                "text": result['response'],
                "bot_name": "Project Assistant"
            })
            
        elif command == "project_list_tasks":
            # Use our existing task listing logic
            tasks = pm_tool.get_tasks()
            
            task_list = "\n".join([f"• {task['title']}" for task in tasks])
            return jsonify({
                "text": f"Your tasks:\n{task_list}",
                "bot_name": "Project Assistant"
            })
            
        else:
            return jsonify({"error": f"Unknown project command: {command}"}), 400
            
    except Exception as e:
        logger.error(f"Project management error: {str(e)}", exc_info=True)
        return jsonify({"error": f"Project management error: {str(e)}"}), 500

@app.route('/api/bot_info', methods=['GET'])
def get_bot_info():
    """Return information about available bots"""
    bot_info = {}
    for name, bot in BOTS.items():
        bot_info[name] = {
            "name": name,
            "role": bot.role,
            "expertise": bot.expertise
        }
    return jsonify(bot_info)

@app.route('/api/process_command', methods=['POST'])
def process_command():
    """Process a command from the Rust proxy"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        command = data.get('command', '')
        args = data.get('args', {})
        
        logger.info(f"Received command: {command} with args: {args}")
        
        # Handle ask commands
        if command.startswith('ask_'):
            bot_name = command.replace('ask_', '').capitalize()
            if bot_name in BOTS:
                question = args.get('question', '')
                if not question:
                    return jsonify({"error": "No question provided"}), 400
                
                logger.info(f"Processing question for {bot_name}: {question}")
                bot = BOTS[bot_name]
                response = bot.get_response(question)
                
                return jsonify({
                    "text": response,
                    "bot_name": bot_name
                })
            else:
                return jsonify({"error": f"Bot {bot_name} not found"}), 404
        elif command.startswith('project_'):
            return handle_project_command(command, args)
        else:
            return jsonify({"error": f"Unknown command: {command}"}), 400
    
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "ok", "bots_available": list(BOTS.keys())})

if __name__ == '__main__':
    port = 5005
    logger.info(f"Starting bot API server on port {port}")
    logger.info(f"Available bots: {', '.join(BOTS.keys())}")
    app.run(host='0.0.0.0', port=port)
