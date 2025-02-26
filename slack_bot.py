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

# Configure logging to show detailed information
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


conversation_histories = defaultdict(dict)


@app.message("")
def handle_messages(message, say, logger):
    try:
        logger.debug(f"Received message: {message}")
        
        
        if message.get("bot_id") or message.get("subtype") == "bot_message":
            logger.debug("Skipping bot message")
        if "text" not in body["event"] or "bot_id" in body["event"]:
            return
            
        text = message.get("text", "").strip()
        user = message.get("user", "")
        channel = message.get("channel", "")
        conversation_key = f"{channel}:{user}"
        
        logger.info(f"Processing message from user {user} in channel {channel}: {text}")
        print(f"Message from user {user} in channel type {channel_type}: {message}")
        
        # Simple bot selection based on message text
        selected_bot = "Benny"  # Default
        
        # Check for expert requests
        for bot_name in BOTS.keys():
            trigger = f"Ask {bot_name}:"
            if text.lower().startswith(trigger.lower()):
                
                question = text[len(trigger):].strip()
                
                
                if question.lower() == "your question":
                    continue
                    
                selected_bot = bot_name
                logger.info(f"Selected bot: {selected_bot}, Processing question: {question}")
                
                # Store conversation state
                conversation_histories[conversation_key] = {
                    "current_bot": selected_bot,
                    "history": []
                }
                
                # Get and send response
                response = BOTS[selected_bot].get_response(question)
                say(f"*{selected_bot} says:*\n{response}")
                return
        
        # Handle ongoing conversations
        if conversation_key in conversation_histories and conversation_histories[conversation_key].get("current_bot"):
            selected_bot = conversation_histories[conversation_key]["current_bot"]
            response = BOTS[selected_bot].get_response(text)
            say(f"*{selected_bot} says:*\n{response}")
            return
            
        # If no trigger found and no ongoing conversation, provide guidance
        bot_list = ", ".join(BOTS.keys())
        say(f"Hi <@{user}>! You can ask any of our experts: {bot_list}\nExample: `Ask Benny: How do I structure my startup funding?`")
        
        # Pass the user ID for task management functionality
        response = BOTS[selected_bot].get_response(message, user_id=user)
        say(f"*{selected_bot}*: {response}")
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        say(f"I encountered an unexpected error. Please try again with your question.")

# Handle direct mentions
@app.event("app_mention")
def handle_app_mention(event, say, logger):
    try:
        logger.debug(f"Received mention event: {event}")
        
        channel_id = event.get("channel")
        user_id = event.get("user")
        conversation_key = f"{channel_id}:{user_id}"
        
        text = event.get("text", "")
        cleaned_text = text.split(">", 1)[1].strip() if ">" in text else text
        
        logger.info(f"App mention from user {user_id}: {cleaned_text}")
        
        # Check if user is in active conversation
        if conversation_key in conversation_histories and conversation_histories[conversation_key].get("current_bot"):
            selected_bot = conversation_histories[conversation_key]["current_bot"]
            
            # Handle conversation control commands
            if cleaned_text.lower() == "end chat":
                conversation_histories[conversation_key]["current_bot"] = None
                say("Chat ended. You can start a new conversation with any expert!")
                return
                
            if cleaned_text.lower().startswith("switch to"):
                new_bot = cleaned_text.lower().replace("switch to", "").strip()
                if new_bot in [b.lower() for b in BOTS.keys()]:
                    selected_bot = [b for b in BOTS.keys() if b.lower() == new_bot][0]
                    conversation_histories[conversation_key]["current_bot"] = selected_bot
                    say(f"Switched to {selected_bot}! How can I help?")
                    return
                    
            response = BOTS[selected_bot].get_response(cleaned_text)
            say(f"*{selected_bot} says:*\n{response}")
            return
            
        # Handle new conversation
        selected_bot = None
        for bot_name in BOTS.keys():
            if bot_name.lower() in cleaned_text.lower():
                selected_bot = bot_name
                parts = cleaned_text.split(bot_name, 1)
                if len(parts) > 1:
                    cleaned_text = parts[1].strip()
                break
                
        if selected_bot:
            conversation_histories[conversation_key] = {
                "current_bot": selected_bot,
                "history": []
            }
            response = BOTS[selected_bot].get_response(cleaned_text)
            say(f"*{selected_bot} says:*\n{response}")
        else:
            bot_list = ", ".join(BOTS.keys())
            say(f"Hi <@{user_id}>! You can ask any of our experts: {bot_list}\nTry: `Ask {list(BOTS.keys())[0]}: your question`")
            
    except Exception as e:
        logger.error(f"Error processing app mention: {e}", exc_info=True)
        say(f"Sorry, I encountered an error: {str(e)}")

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
