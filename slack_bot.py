from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_bolt.oauth.oauth_flow import OAuthFlow 
from slack_sdk.web import WebClient
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.installation_store.models.installation import Installation
from agent_bots import BOTS
import os
from dotenv import load_dotenv
import ssl
import logging
import sys
from collections import defaultdict
import re
from typing import Dict, Optional
from flask import Flask, request, redirect
from slack_bolt.adapter.flask import SlackRequestHandler
import datetime

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Validate required environment variables
required_env_vars = ["SLACK_APP_TOKEN", "SLACK_SIGNING_SECRET", "SLACK_CLIENT_ID", "SLACK_CLIENT_SECRET"]
for var in required_env_vars:
    if not os.environ.get(var):
        logger.error(f"Missing environment variable: {var}")
        sys.exit(1)

# SSL context for WebClient
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Initialize installation store
installation_store = FileInstallationStore(base_dir="./slack_installations")

# Configure OAuth settings with expanded scopes
oauth_settings = OAuthSettings(
    client_id=os.environ["SLACK_CLIENT_ID"],
    client_secret=os.environ["SLACK_CLIENT_SECRET"],
    scopes=[
        "app_mentions:read",
        "chat:write",
        "commands",
        "incoming-webhook",
        "channels:history",
        "groups:history",
        "im:history",
        "mpim:history"
    ],
    installation_store=installation_store,
    redirect_uri="https://slack.infoundr.com/slack/oauth_redirect"
)

# Initialize WebClient and App
client = WebClient(ssl=ssl_context)
app = App(
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    installation_store=installation_store,
    oauth_settings=oauth_settings,
    client=client
)

def get_bot_token_for_team(team_id: str) -> Optional[str]:
    try:
        # First try to get the latest installation
        installation = installation_store.find_installation(team_id=team_id)
        
        if not installation:
            logger.warning(f"No installation found for team {team_id}")
            return None
            
        if installation.bot_token:
            # Verify the token is still valid
            try:
                client = WebClient(token=installation.bot_token)
                auth_test = client.auth_test()
                if auth_test["ok"]:
                    logger.debug(f"Found valid bot token for team {team_id}")
                    return installation.bot_token
                else:
                    logger.warning(f"Bot token for team {team_id} is invalid")
            except Exception as e:
                logger.error(f"Error verifying bot token for team {team_id}: {e}")
        
        
        logger.warning(f"No valid bot token found for team {team_id}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving token: {e}", exc_info=True)
        return None

conversation_histories: Dict[str, Dict] = defaultdict(lambda: {
    "current_bot": None,
    "thread_ts": None,
    "history": []
})

@app.message("")
def handle_messages(message, say, logger, client):
    try:
        # Get team_id from message context
        team_id = message.get("team")
        if team_id:
            # Get the bot token for this team
            bot_token = get_bot_token_for_team(team_id)
            if not bot_token:
                # Check if this is a bot message to avoid infinite loops
                if not message.get("bot_id"):
                    say("The app installation appears to be invalid. Please reinstall the app using the /slack/install endpoint.", thread_ts=message.get("ts"))
                return
            # Update the client with the correct token for this request
            client.token = bot_token
        else:
            logger.error("No team_id found in message")
            if not message.get("bot_id"):
                say("Error: Could not identify team. Please reinstall the app.", thread_ts=message.get("ts"))
            return

        # Skip bot messages and messages that are app mentions
        if message.get("bot_id") or message.get("subtype") == "bot_message" or message.get("text", "").startswith("<@"):
            return

        text = message.get("text", "").strip()
        user = message.get("user", "")
        channel = message.get("channel", "")
        thread_ts = message.get("thread_ts") or message.get("ts")
        conversation_key = f"{channel}:{thread_ts}"
        
        logger.debug(f"Processing message: {text}")

        # Handle ongoing conversations first
        if conversation_key in conversation_histories:
            current_bot = conversation_histories[conversation_key]["current_bot"]
            if current_bot:
                logger.debug(f"Found ongoing conversation with {current_bot}")
                # Check if this message is explicitly asking for a different bot
                is_new_bot_request = False
                for bot_name in BOTS.keys():
                    if re.search(rf"(?i)ask\s+{re.escape(bot_name)}|@{re.escape(bot_name)}|^{re.escape(bot_name)}\b", text):
                        is_new_bot_request = True
                        break
                
                if not is_new_bot_request:
                    response = BOTS[current_bot].get_response(text)
                    conversation_histories[conversation_key]["history"].append((text, response))
                    say(f"*{current_bot} says:*\n{response}", thread_ts=thread_ts)
                    return

        # More flexible bot request handling with multiple patterns
        for bot_name in BOTS.keys():
            patterns = [
                re.compile(rf"(?i)^ask\s+{re.escape(bot_name)}:?\s*(.*)", re.IGNORECASE),
                re.compile(rf"(?i)^@{re.escape(bot_name)}:?\s*(.*)", re.IGNORECASE),
                re.compile(rf"(?i)^{re.escape(bot_name)}:?\s*(.*)", re.IGNORECASE)
            ]
            
            for pattern in patterns:
                match = pattern.match(text)
                if match:
                    question = match.group(1).strip()
                    logger.debug(f"Matched bot {bot_name} with question: {question}")
                    if question:
                        bot = BOTS[bot_name]
                        response = bot.get_response(question)
                        
                        conversation_histories[conversation_key] = {
                            "current_bot": bot_name,
                            "thread_ts": thread_ts,
                            "history": [(question, response)]
                        }
                        logger.debug(f"Set conversation to use bot: {bot_name}")
                        
                        say(f"*{bot_name} says:*\n{response}", thread_ts=thread_ts)
                        return

        # Help message for new conversations
        if not thread_ts:
            bot_list = ", ".join(BOTS.keys())
            say(f"Hi <@{user}>! You can ask any of our experts: {bot_list}\nExample: `Ask Benny: How do I structure my startup funding?`")

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        say(f"I encountered an error. Please try asking your question again.", thread_ts=message.get("ts"))

@app.event("app_mention")
def handle_app_mention(event, say, logger, client):
    try:
        # Get team_id from event context
        team_id = event.get("team")
        if team_id:
            # Get the bot token for this team
            bot_token = get_bot_token_for_team(team_id)
            if not bot_token:
                say("Error: Bot token is missing. Please reinstall the app.", thread_ts=event.get("ts"))
                return
            # Update the client with the correct token for this request
            client.token = bot_token
        else:
            logger.error("No team_id found in event")
            say("Error: Could not identify team. Please reinstall the app.", thread_ts=event.get("ts"))
            return

        channel_id = event.get("channel")
        thread_ts = event.get("thread_ts") or event.get("ts")
        conversation_key = f"{channel_id}:{thread_ts}"
        
        text = event.get("text", "")
        user_id = event.get("user")
        cleaned_text = text.split(">", 1)[1].strip() if ">" in text else text
        
        logger.debug(f"Processing app_mention: {cleaned_text}")

        # Check for ongoing conversation first
        if conversation_key in conversation_histories:
            current_bot = conversation_histories[conversation_key]["current_bot"]
            if current_bot:
                logger.debug(f"Found ongoing conversation with {current_bot}")
                is_new_bot_request = False
                for bot_name in BOTS.keys():
                    if re.search(rf"(?i)ask\s+{re.escape(bot_name)}|@{re.escape(bot_name)}|^{re.escape(bot_name)}\b", cleaned_text):
                        is_new_bot_request = True
                        break
                
                if not is_new_bot_request:
                    response = BOTS[current_bot].get_response(cleaned_text)
                    say(f"*{current_bot} says:*\n{response}", thread_ts=thread_ts)
                    return

        # More flexible bot request handling with multiple patterns
        for bot_name in BOTS.keys():
            patterns = [
                re.compile(rf"(?i)ask\s+{re.escape(bot_name)}:?\s*(.*)", re.IGNORECASE),
                re.compile(rf"(?i)@{re.escape(bot_name)}:?\s*(.*)", re.IGNORECASE),
                re.compile(rf"(?i){re.escape(bot_name)}:?\s*(.*)", re.IGNORECASE)
            ]
            
            for pattern in patterns:
                match = pattern.search(cleaned_text)
                if match:
                    question = match.group(1).strip()
                    logger.debug(f"Matched bot {bot_name} with question: {question}")
                    if question:
                        conversation_histories[conversation_key] = {
                            "current_bot": bot_name,
                            "thread_ts": thread_ts,
                            "history": [(question, response)]
                        }
                        logger.debug(f"Set conversation to use bot: {bot_name}")
                        response = BOTS[bot_name].get_response(question)
                        say(f"*{bot_name} says:*\n{response}", thread_ts=thread_ts)
                        return

        # Default message for new conversations
        bot_list = ", ".join(BOTS.keys())
        say(f"Hi <@{user_id}>! You can ask any of our experts: {bot_list}\nTry: `Ask {list(BOTS.keys())[0]}: your question`", thread_ts=thread_ts)

    except Exception as e:
        logger.error(f"Error processing app_mention: {e}", exc_info=True)

@app.command("/hello")
def hello_command(ack, body, respond):
    ack()
    user_id = body["user_id"]
    respond(f"Hello, <@{user_id}>! I'm your AI entrepreneurship assistant.")

@app.command("/experts")
def list_bots(ack, respond):
    ack()
    bot_list = "\n".join([f"• *{name}*: {bot.role}" for name, bot in BOTS.items()])
    respond(f"Available expert bots:\n{bot_list}\n\nTo ask a bot, use: `Ask [BotName]: your question`")

@app.event("hello")
def handle_hello(say):
    logger.info("Received hello event from Slack - connection confirmed")

flask_app = Flask(__name__)
flask_app.config['JSON_AS_ASCII'] = False
handler = SlackRequestHandler(app)

@flask_app.route("/slack/install", methods=["GET"])
def install():
    try:
        # Generate a random state parameter
        state = os.urandom(16).hex()
        
        # Generate Slack OAuth URL
        oauth_url = (
            "https://slack.com/oauth/v2/authorize?"
            f"client_id={os.environ['SLACK_CLIENT_ID']}&"
            f"scope={','.join(oauth_settings.scopes)}&"
            f"redirect_uri={oauth_settings.redirect_uri}&"
            f"state={state}"  
        )
        
        return f"""
        <html>
            <head>
                <title>Install Infoundr Bot</title>
                <style>
                    body {{ 
                        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background-color: #f8f9fa;
                    }}
                    .container {{
                        text-align: center;
                        padding: 2rem;
                        background: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    h1 {{
                        color: #1d1c1d;
                        margin-bottom: 2rem;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Install Infoundr Bot</h1>
                    <a href="{oauth_url}"><img 
                        alt="Add to Slack" 
                        height="40" 
                        width="139" 
                        src="https://platform.slack-edge.com/img/add_to_slack.png" /></a>
                </div>
            </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error building authorization URL: {e}", exc_info=True)
        return "Error generating installation link. Please try again later.", 500

@flask_app.route("/slack/oauth_redirect", methods=["GET"])
def oauth_redirect():
    if "error" in request.args:
        logger.error(f"OAuth error: {request.args['error']}")
        return f"Error: {request.args['error']}"
    
    # Verify state parameter
    if "state" not in request.args:
        return "Invalid OAuth flow - missing state parameter", 400
        
    if "code" in request.args:
        try:
            client = WebClient()
            oauth_response = client.oauth_v2_access(
                client_id=os.environ["SLACK_CLIENT_ID"],
                client_secret=os.environ["SLACK_CLIENT_SECRET"],
                code=request.args["code"],
                redirect_uri=oauth_settings.redirect_uri
            ).data  

            logger.debug(f"OAuth response received: {oauth_response}")
            
            # Add this before creating the Installation object
            logger.debug(f"Enterprise info: {oauth_response.get('enterprise')}")
            logger.debug(f"Team info: {oauth_response.get('team')}")
            logger.debug(f"Auth user info: {oauth_response.get('authed_user')}")

            # Convert OAuth response to Installation - safely handle None values
            enterprise = oauth_response.get("enterprise")
            enterprise_id = enterprise.get("id") if enterprise else None
            
            installation = Installation(
                app_id=oauth_response.get("app_id"),
                enterprise_id=enterprise_id,
                team_id=oauth_response["team"]["id"],
                team_name=oauth_response["team"].get("name", ""),
                user_id=oauth_response["authed_user"]["id"],
                bot_token=oauth_response["access_token"],
                bot_id=oauth_response["bot_user_id"],
                bot_user_id=oauth_response["bot_user_id"],
                bot_scopes=oauth_settings.scopes,
                user_token=oauth_response.get("authed_user", {}).get("access_token"),
                installed_at=datetime.datetime.now().timestamp()
            )
            
            # Save the installation
            logger.debug(f"Saving installation for team: {installation.team_id}")
            installation_store.save(installation)
            
            return """
            <html>
                <head>
                    <style>
                        body { 
                            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            margin: 0;
                            background-color: #f8f9fa;
                        }
                        .container {
                            text-align: center;
                            padding: 2rem;
                            background: white;
                            border-radius: 8px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Installation Successful! 🎉</h1>
                        <p>You can now close this window and start using the bot.</p>
                    </div>
                </body>
            </html>
            """
            
        except Exception as e:
            logger.error(f"OAuth installation error: {e}", exc_info=True)
            return """
            <html>
                <head>
                    <style>
                        body { 
                            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            margin: 0;
                            background-color: #fff0f0;
                        }
                        .container {
                            text-align: center;
                            padding: 2rem;
                            background: white;
                            border-radius: 8px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        }
                        .error { color: #dc3545; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1 class="error">Installation Failed</h1>
                        <p>There was an error during installation. Please try again or contact support.</p>
                        <p class="error">Error: {str(e)}</p>
                    </div>
                </body>
            </html>
            """, 500
        
    return "Installation failed! Missing authorization code.", 400

@flask_app.route("/", methods=["GET"])
def index():
    """
    Handler for the root URL path.
    Redirects to the installation page or provides basic info about the bot.
    """
    return """
    <html>
        <head>
            <title>Infoundr Bot</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background-color: #f8f9fa;
                }
                .container {
                    text-align: center;
                    padding: 2rem;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    max-width: 600px;
                }
                h1 {
                    color: #1d1c1d;
                    margin-bottom: 1.5rem;
                }
                .button {
                    display: inline-block;
                    background-color: #4A154B;
                    color: white;
                    padding: 12px 24px;
                    border-radius: 4px;
                    text-decoration: none;
                    margin-top: 1rem;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to Infoundr Bot</h1>
                <p>An AI-powered assistant for entrepreneurs and startups.</p>
                <a href="/slack/install" class="button">Install on Slack</a>
            </div>
        </body>
    </html>
    """

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    # Handle URL verification challenge
    if request.json and request.json.get("type") == "url_verification":
        logger.info("Handling URL verification challenge")
        return {
            "challenge": request.json["challenge"]
        }
    
    try:
        # Handle other events through the SlackRequestHandler
        return handler.handle(request)
    except Exception as e:
        logger.error(f"Error handling event: {e}", exc_info=True)
        return {"error": "Internal server error"}, 500

@flask_app.route("/slack/logo.png")
def serve_logo():
    return '', 404  

if __name__ == "__main__":
    ngrok_url = "https://slack.infoundr.com/slack/oauth_redirect"
    logger.info(f"Starting Slack bot server on port 3000...")
    logger.info(f"Public URL: {ngrok_url}")
    
    # Create installations directory if it doesn't exist
    os.makedirs("./slack_installations", exist_ok=True)
    
    flask_app.run(host='0.0.0.0', port=3000, debug=True)