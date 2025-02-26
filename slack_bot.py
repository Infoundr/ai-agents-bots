from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.web import WebClient
from agent_version1 import BOTS  
import os
from dotenv import load_dotenv
import ssl

load_dotenv()


ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


client = WebClient(token=os.environ["SLACK_BOT_TOKEN"], ssl=ssl_context)


app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    client=client
)

@app.event("message")
def handle_message_events(body, say):
    try:
        print("Received event:", body["event"])
        
        
        if "text" not in body["event"] or "bot_id" in body["event"]:
            return
            
        message = body["event"]["text"]
        user = body["event"]["user"]
        channel_type = body["event"].get("channel_type", "")
        
        print(f"Message from user {user} in channel type {channel_type}: {message}")
        
        # Simple bot selection based on message text i will add feature to select bots based on message content
        selected_bot = "Benny"  # Default
        
        for bot_name in BOTS.keys():
            if f"Ask {bot_name}:" in message:
                selected_bot = bot_name
                message = message.split(f"Ask {bot_name}:", 1)[1].strip()
                break
        
        response = BOTS[selected_bot].get_response(message)
        say(f"*{selected_bot}*: {response}")
    except Exception as e:
        print(f"Error processing message: {e}")

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()