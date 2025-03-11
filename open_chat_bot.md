python3 open_chat_bot.py

INFO - Starting bot API server on port 5005
INFO - Available bots: Benny, Innocent, Dean, Ali, ...
 * Serving Flask app '...'
 * Debug mode: off
 * Running on http://0.0.0.0:5005

curl http://localhost:5005/api/health

{
    "status": "ok",
    "bots_available": ["Benny", "Innocent", "Dean", "Ali", "Sheila", "Felix", "Matt", "Nelly", "Liech", "Steve", "Muoka", "Caleb"]
}

Bot information: 
curl http://localhost:5005/api/bot_info

{
    "Benny": {
        "name": "Benny",
        "role": "Financial Decision Making Expert from Payd",
        "expertise": "fintech strategies, payment solutions, financial planning for startups"
    },
    "Innocent": {
        "name": "Innocent",
        "role": "Business Strategy Expert from Startinev",
        "expertise": "startup scaling, business growth, leadership development"
    },
    ...
}

Process command: 
curl -X POST http://localhost:5005/api/process_command -d '{"bot_name": "Benny", "command": "What is the best way to start a fintech startup?"}'

{
    "text": "To start a fintech startup, consider the following steps: 1. Define your target market and customer needs. 2. Develop a unique value proposition. 3. Create a business plan. 4. Secure funding or bootstrap with personal savings. 5. Build a minimum viable product. 6. Test and iterate with real users. 7. Launch and market your product. 8. Monitor performance and adapt to market changes.",
    "bot_name": "Benny"
}



