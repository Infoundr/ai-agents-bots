from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.web import WebClient
from agent_bots import BOTS
import os
from dotenv import load_dotenv
import ssl
import logging
import sys
from collections import defaultdict
import re
from typing import Dict, Optional
import requests
from urllib.parse import quote

# logging to show detailed information
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

client = WebClient(token=os.environ["SLACK_BOT_TOKEN"], ssl=ssl_context)
app = App(token=os.environ["SLACK_BOT_TOKEN"], client=client)

conversation_histories: Dict[str, Dict] = defaultdict(lambda: {
    "current_bot": None,
    "thread_ts": None,
    "history": []
})


OPENCHAT_API_URL = "http://154.38.174.112:5005"

def call_openchat_api(command: str, args: dict) -> dict:
    """Make a request to the OpenChat API"""
    try:
        response = requests.post(
            f"{OPENCHAT_API_URL}/api/process_command",
            json={"command": command, "args": args}
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error calling OpenChat API: {e}")
        raise Exception(f"Failed to process command: {e}")

def format_openchat_response(response: dict) -> str:
    """Format the OpenChat API response for Slack"""
    if "error" in response:
        return f"❌ Error: {response['error']}"
    
    text = response.get("text", "")
    bot_name = response.get("bot_name", "Assistant")
    return f"*{bot_name}:*\n{text}"

@app.message("")
def handle_messages(message, say, logger):
    try:
        # Skip bot messages and messages that are app mentions (will be handled by app_mention handler)
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
            # Checking for various patterns: "Ask Bot:", "Ask Bot", "@Bot", "Bot:"
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
                        # Clear any previous conversation and set the new bot
                        bot = BOTS[bot_name]
                        response = bot.get_response(question)
                        
                        # Update conversation state
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
        say(f"I encountered an error. Please try asking your question again.", thread_ts=thread_ts)
       
        
@app.event("app_mention")
def handle_app_mention(event, say, logger):
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
            # Check if this message is explicitly asking for a different bot
            is_new_bot_request = False
            for bot_name in BOTS.keys():
                if re.search(rf"(?i)ask\s+{re.escape(bot_name)}|@{re.escape(bot_name)}|^{re.escape(bot_name)}\b", cleaned_text):
                    is_new_bot_request = True
                    break
            
            if not is_new_bot_request:
                try:
                    response = BOTS[current_bot].get_response(cleaned_text)
                    say(f"*{current_bot} says:*\n{response}", thread_ts=thread_ts)
                    return
                except Exception as e:
                    logger.error(f"Error in ongoing conversation: {e}", exc_info=True)
                    return

    # More flexible bot request handling with multiple patterns
    for bot_name in BOTS.keys():
        # Check various patterns: "ask bot:", "ask bot", "@bot", "bot:"
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
                    try:
                        # Clear any previous conversation and set the new bot
                        conversation_histories[conversation_key] = {
                            "current_bot": bot_name,
                            "thread_ts": thread_ts,
                            "history": []
                        }
                        logger.debug(f"Set conversation to use bot: {bot_name}")
                        response = BOTS[bot_name].get_response(question)
                        say(f"*{bot_name} says:*\n{response}", thread_ts=thread_ts)
                        return
                    except Exception as e:
                        logger.error(f"Error processing bot request: {e}", exc_info=True)
                        return

    # Default message for new conversations
    bot_list = ", ".join(BOTS.keys())
    say(f"Hi <@{user_id}>! You can ask any of our experts: {bot_list}\nTry: `Ask {list(BOTS.keys())[0]}: your question`", thread_ts=thread_ts)

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

@app.command("/project")
def handle_project_command(ack, body, respond):
    ack()
    try:
        user_id = body["user_id"]
        text = body.get("text", "").strip()
        
        if not text:
            respond("Usage: `/project connect TOKEN` or `/project list` or `/project create TASK_DESCRIPTION`")
            return
            
        parts = text.split(maxsplit=1)
        action = parts[0].lower()
        params = parts[1] if len(parts) > 1 else ""
        
        command = f"project_{action}"
        args = {
            "user_id": user_id,
            "token": params if action == "connect" else None,
            "description": params if action == "create" else None
        }
        
        response = call_openchat_api(command, args)
        respond(format_openchat_response(response))
        
    except Exception as e:
        logger.error(f"Error handling project command: {e}")
        respond(f"❌ Error: {str(e)}")

@app.command("/github")
def handle_github_command(ack, body, respond):
    ack()
    try:
        user_id = body["user_id"]
        text = body.get("text", "").strip()
        
        if not text:
            respond("Usage: `/github connect TOKEN` or `/github list` or `/github select REPO` or `/github create \"TITLE\" \"DESCRIPTION\"`")
            return
            
        parts = text.split(maxsplit=1)
        action = parts[0].lower()
        params = parts[1] if len(parts) > 1 else ""
        
        command = f"github_{action}"
        args = {
            "user_id": user_id,
            "token": params if action == "connect" else None,
            "repo_name": params if action == "select" else None
        }
        
        # Special handling for issue creation
        if action == "create":
            try:
                title, body = [p.strip('"') for p in params.split('" "')]
                args["title"] = title
                args["body"] = body
            except ValueError:
                respond("For creating issues, use: `/github create \"Issue Title\" \"Issue Description\"`")
                return
        
        response = call_openchat_api(command, args)
        respond(format_openchat_response(response))
        
    except Exception as e:
        logger.error(f"Error handling github command: {e}")
        respond(f"❌ Error: {str(e)}")

@app.command("/help")
def help_command(ack, respond):
    ack()
    help_text = (
        "*Available Commands:*\n\n"
        "*Expert Assistance:*\n"
        "• `Ask [ExpertName]: question` - Ask a question to any of our experts\n"
        "• `/experts` - List all available experts\n\n"
        "*Project Management:*\n"
        "• `/project connect TOKEN` - Connect your Asana account\n"
        "• `/project list` - List your tasks\n"
        "• `/project create DESCRIPTION` - Create a new task\n\n"
        "*GitHub Integration:*\n"
        "• `/github connect TOKEN` - Connect your GitHub account\n"
        "• `/github list` - List your repositories\n"
        "• `/github select REPO` - Select a repository\n"
        "• `/github create \"TITLE\" \"DESCRIPTION\"` - Create an issue\n"
        "• `/github list_issues` - List repository issues\n"
        "• `/github list_prs` - List pull requests"
    )
    respond(help_text)

@app.event("hello")
def handle_hello(say):
    logger.info("Received hello event from Slack - connection confirmed")

if __name__ == "__main__":
    logger.info(f"Starting Slack bot with app token: {os.environ.get('SLACK_APP_TOKEN', '')[:5]}...")
    logger.info(f"Bot token present: {'Yes' if os.environ.get('SLACK_BOT_TOKEN') else 'No'}")
    logger.info(f"Available bots: {', '.join(BOTS.keys())}")
    
    try:
        handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
        logger.info("Starting Socket Mode handler...")
        handler.start()
    except Exception as e:
        logger.error(f"Failed to start Socket Mode handler: {e}", exc_info=True)
