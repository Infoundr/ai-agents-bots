from flask import Flask, request, jsonify
from agent_bots import BOTS
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

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
