from flask import Flask, request, jsonify
from core.agent_bots import BOTS
import logging
from core.integrations.manager import IntegrationManager
from core.integrations.user_credentials import UserCredentialStore
import os
import json
from pathlib import Path
import asana
from core.integrations.github_integration import GitHubIntegration

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
                            f"Found {len(projects)} projects",
                    "bot_name": "Project Assistant",
                    "metadata": {
                        "workspace_id": workspace_gid,
                        "project_ids": [(p['gid'], p['name']) for p in projects]
                    }
                })
                
            except asana.rest.ApiException as e:
                return jsonify({
                    "text": f"Error connecting to Asana: {str(e)}",
                    "bot_name": "Project Assistant"
                }), 500

        # For other commands, get the token from storage
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
        return jsonify({
            "text": f"Failed to process command: {str(e)}",
            "bot_name": "Project Assistant"
        }), 500

def handle_github_command(command, args):
    """Handle GitHub commands"""
    try:
        user_id = args.get('user_id')
        if not user_id:
            return jsonify({
                "text": "Error: User ID not provided",
                "bot_name": "GitHub Assistant"
            }), 400

        # For list repositories command, we only need the token
        if command == "github_list_repos":
            github_creds = credential_store.get_github_credentials(user_id)
            if not github_creds:
                return jsonify({
                    "text": "⚠️ Please connect your GitHub account first using `/github connect YOUR_TOKEN`\n\n"
                            "To get your token:\n"
                            "1. Go to https://github.com/settings/personal-access-tokens\n"
                            "2. Click on `Generate new token` in the top right section.\n"
                            "3. Set `Repository access` to: All repositories.\n"
                            "4. Under `Repository permissions`: \n"
                            "   - Issues: Set to read & write.\n"
                            "   - Pull requests: Set to read & write.\n"
                            "5. Copy and use it with the connect command",
                    "bot_name": "GitHub Assistant"
                })
            
            github = GitHubIntegration(github_creds['token'])
            repos = github.list_repositories()
            repos_text = "\n".join([f"• {repo['name']}" + 
                                  (f" (Private)" if repo['private'] else "") 
                                  for repo in repos])
            return jsonify({
                "text": f"Your repositories:\n{repos_text}\n\nTo select a repository, use:\n/github select <repository_name>",
                "bot_name": "GitHub Assistant"
            })

        # For selecting a repository
        elif command == "github_select_repo":
            repo_name = args.get('repo_name')
            if not repo_name:
                return jsonify({
                    "text": "Error: Please provide a repository name",
                    "bot_name": "GitHub Assistant"
                }), 400

            github_creds = credential_store.get_github_credentials(user_id)
            if not github_creds:
                return jsonify({
                    "text": "⚠️ Please connect your GitHub account first using `/github connect YOUR_TOKEN`\n\n"
                            "To get your token:\n"
                            "1. Go to https://github.com/settings/personal-access-tokens\n"
                            "2. Click on `Generate new token` in the top right section.\n"
                            "3. Set `Repository access` to: All repositories.\n"
                            "4. Under `Repository permissions`: \n"
                            "   - Issues: Set to read & write.\n"
                            "   - Pull requests: Set to read & write.\n"
                            "5. Copy and use it with the connect command",
                    "bot_name": "GitHub Assistant"
                })

            github = GitHubIntegration(github_creds['token'])
            repo = github.select_repository(repo_name)
            
            # Store the selected repository in credentials
            credential_store.update_github_credentials(user_id, {
                'token': github_creds['token'],
                'selected_repo': repo_name
            })

            return jsonify({
                "text": f"✅ Selected repository: {repo['name']}\n{repo['url']}\n\n"
                        "Next steps:\n"
                        "• To create an issue, use: `/github create \"Issue title\" \"Issue description\"`\n"
                        "• To list available pull requests, use: `/github list_prs`\n"
                        "• To list issues, use: `/github list_issues`",
                "bot_name": "GitHub Assistant"
            })

        elif command == "github_connect":
            token = args.get('token')
            if not token:
                return jsonify({
                    "text": "Error: Please provide your GitHub token",
                    "bot_name": "GitHub Assistant"
                }), 400

            try:
                # Test the connection by getting user info
                github = GitHubIntegration(token)
                user_info = github.test_connection()
                
                # Store credentials
                credential_store.store_github_credentials(user_id, token)
                
                return jsonify({
                    "text": f"✅ Successfully connected GitHub account for {user_info['name']}!\n\n"
                            "Use `/github list` to see your repositories, then\n"
                            "Use `/github select owner/repo` to choose a repository to work with.",
                    "bot_name": "GitHub Assistant"
                })
                
            except Exception as e:
                return jsonify({
                    "text": f"Error connecting to GitHub: {str(e)}",
                    "bot_name": "GitHub Assistant"
                }), 500

        # For other commands, check if user has connected GitHub
        github_creds = credential_store.get_github_credentials(user_id)
        if not github_creds:
            return jsonify({
                "text": "⚠️ Please connect your GitHub account first using `/github connect YOUR_TOKEN`\n\n"
                        "To get your token:\n"
                        "1. Go to https://github.com/settings/personal-access-tokens\n"
                        "2. Click on `Generate new token` in the top right section.\n"
                        "3. Set `Repository access` to: All repositories.\n"
                        "4. Under `Repository permissions`: \n"
                        "   - Issues: Set to read & write.\n"
                        "   - Pull requests: Set to read & write.\n"
                        "5. Copy and use it with the connect command",
                "bot_name": "GitHub Assistant"
            })

        # Initialize GitHub with token and selected repo
        github = GitHubIntegration(
            github_creds['token'], 
            github_creds.get('selected_repo')
        )

        if command == "github_list_issues":
            state = args.get('state', 'open')
            issues = github.list_issues(state)
            issues_text = "\n".join([f"#{i['number']} - {i['title']} ({i['state']})" 
                                   for i in issues])
            return jsonify({
                "text": f"Issues ({state}):\n{issues_text}",
                "bot_name": "GitHub Assistant"
            })

        elif command == "github_create_issue":
            title = args.get('title')
            body = args.get('body', '')
            
            if not title:
                return jsonify({"error": "No issue title provided"}), 400
                
            issue = github.create_issue(title, body)
            return jsonify({
                "text": f"Created issue #{issue['number']}: {issue['title']}\n{issue['url']}",
                "bot_name": "GitHub Assistant"
            })

        elif command == "github_list_prs":
            state = args.get('state', 'open')
            prs = github.list_pull_requests(state)
            prs_text = "\n".join([f"#{pr['number']} - {pr['title']} ({pr['state']})" 
                                 for pr in prs])
            return jsonify({
                "text": f"Pull Requests ({state}):\n{prs_text}",
                "bot_name": "GitHub Assistant"
            })
        
        if command == "github_check_repo":
            selected_repo = github_creds.get('selected_repo')
            if not selected_repo:
                return jsonify({
                    "text": "No repository is currently selected. Use `/github select <repository_name>` to select one.",
                    "bot_name": "GitHub Assistant",
                    "metadata": {
                        "selected_repo": None
                    }
                })
            return jsonify({
                "text": f"Currently connected repository: {selected_repo}",
                "bot_name": "GitHub Assistant",
                "metadata": {
                    "selected_repo": selected_repo
                }
            })
            
    except Exception as e:
        logger.error(f"GitHub command error: {str(e)}", exc_info=True)
        return jsonify({"error": f"GitHub command error: {str(e)}"}), 500

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
        logger.info(f"Received request data: {data}")
        
        if not data:
            logger.error("No data provided")
            return jsonify({"error": "No data provided"}), 400
        
        command = data.get('command', '')
        args = data.get('args', {})
        
        logger.info(f"Processing command: {command} with args: {args}")
        
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
        elif command.startswith('github_'):
            return handle_github_command(command, args)
        else:
            return jsonify({"error": f"Unknown command: {command}"}), 400
    
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "ok", "bots_available": list(BOTS.keys())})

@app.route('/', methods=['GET'])
def root():
    """Root endpoint that redirects to health check"""
    return jsonify({
        "status": "ok", 
        "message": "Bot API server is running", 
        "endpoints": [
            "/api/health",
            "/api/bot_info",
            "/api/process_command"
        ]
    })

if __name__ == '__main__':
    port = 5005
    logger.info(f"Starting bot API server on port {port}")
    logger.info(f"Available bots: {', '.join(BOTS.keys())}")
    app.run(host='0.0.0.0', port=port)
