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

conversation_histories: Dict[str, Dict] = defaultdict(lambda: {
    "current_bot": None,
    "thread_ts": None,
    "history": []
})

@app.message("")
def handle_messages(message, say, logger):
    try:
        if message.get("bot_id") or message.get("subtype") == "bot_message":
            return

        text = message.get("text", "").strip()
        user = message.get("user", "")
        channel = message.get("channel", "")
        thread_ts = message.get("thread_ts") or message.get("ts")
        conversation_key = f"{channel}:{thread_ts}"

        # Direct bot request handling
        for bot_name in BOTS.keys():
            trigger = f"Ask {bot_name}:"
            if text.lower().startswith(trigger.lower()):
                question = text[len(trigger):].strip()
                # using the correct bot
                bot = BOTS[bot_name]
                response = bot.get_response(question)
                
                # Update conversation state
                conversation_histories[conversation_key] = {
                    "current_bot": bot_name,
                    "thread_ts": thread_ts,
                    "history": [(question, response)]
                }
                
                say(f"*{bot_name} says:*\n{response}", thread_ts=thread_ts)
                return

        # Handle ongoing conversations
        if conversation_key in conversation_histories:
            current_bot = conversation_histories[conversation_key]["current_bot"]
            if current_bot:
                response = BOTS[current_bot].get_response(text)
                conversation_histories[conversation_key]["history"].append((text, response))
                say(f"*{current_bot} says:*\n{response}", thread_ts=thread_ts)
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

    # Direct bot request handling
    for bot_name in BOTS.keys():
        trigger = f"ask {bot_name.lower()}:"
        if trigger in cleaned_text.lower():
            try:
                question = cleaned_text.lower().split(trigger)[1].strip()
                if question:
                    conversation_histories[conversation_key] = {
                        "current_bot": bot_name,
                        "thread_ts": thread_ts,
                        "history": []
                    }
                    response = BOTS[bot_name].get_response(question)
                    say(f"*{bot_name} says:*\n{response}", thread_ts=thread_ts)
                    return
            except Exception as e:
                logger.error(f"Error processing bot request: {e}", exc_info=True)
                return

    # Check for ongoing conversation
    if conversation_key in conversation_histories:
        current_bot = conversation_histories[conversation_key]["current_bot"]
        if current_bot:
            try:
                response = BOTS[current_bot].get_response(cleaned_text)
                say(f"*{current_bot} says:*\n{response}", thread_ts=thread_ts)
                return
            except Exception as e:
                logger.error(f"Error in ongoing conversation: {e}", exc_info=True)
                return

    # Default message for new conversations
    if not any(f"ask {bot.lower()}:" in cleaned_text.lower() for bot in BOTS.keys()):
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
