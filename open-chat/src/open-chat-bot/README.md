# Infoundr OpenChat Bot

This project implements an OpenChat bot that provides access to various entrepreneurship experts. The implementation consists of two parts:
1. A Python API that handles the bot logic and responses
2. A Rust proxy that integrates with OpenChat's protocol

## Part 1: Python Bot API

The Python component serves as the backend for our expert bots, handling the actual conversation logic and responses.

### Running the Python API

1. Start the Python bot server:
```bash
python3 open_chat_bot.py
```

2. Test if the API is healthy:
```bash
curl http://localhost:5005/api/health
```

Expected response:
```json 
{
"status": "ok",
"bots_available": ["Benny", "Innocent", "Dean", "Ali", "Sheila", "Felix", "Matt", "Nelly", "Liech", "Steve", "Muoka", "Caleb"]
}
```

3. Test a bot response: 
```bash
curl -X POST http://localhost:5005/api/process_command \
-H "Content-Type: application/json" \
-d '{
"command": "ask_benny",
"args": {
"question": "What is the best way to start a fintech startup?"
}
}'
```

Expected response:
```json
{
"text": "To start a fintech startup, consider the following steps: 1. Define your target market and customer needs. 2. Develop a unique value proposition. 3. Create a business plan. 4. Secure funding or bootstrap with personal savings. 5. Build a minimum viable product. 6. Test and iterate with real users. 7. Launch and market your product. 8. Monitor performance and adapt to market changes.",
"bot_name": "Benny"
}
```

## Part 2: OpenChat Bot Integration

The Rust component acts as a proxy between OpenChat and our Python API, handling the OpenChat protocol and authentication.

### Setting Up the Bot: 
1. Generate the bot identity: 
```bash 
dfx identity new infoundr_identity --storage-mode=plaintext
``` 

2. Export the identity to a PEM file:
```bash 
dfx identity export infoundr_identity > infoundr_identity.pem
``` 

This will create a PEM file containing your bot's private key, which looks like:
```
-----BEGIN EC PRIVATE KEY-----
MHQCAQEEIK1vYf2n4PkLt6sANsPoOmlIIGD6iS5SLvjc9ONIPFa8oAcGBSuBBAAK
oUQDQgAEssRSGHwHiHNfyHWGb7JlWwMsRIADVUPaCU56iVmO3zZ3PgnysVjC7ijd
5pRFUBIeMfCm+yCpYUUtjOGsdLQXCw==
-----END EC PRIVATE KEY-----
```

### Configuring the Bot: 

Create or update your `config.toml` file with the following settings:

1. Set the path to your PEM file:
```toml
pem_file = "./infoundr_identity.pem"
``` 

2. Set the Internet Computer URL:
```toml
ic_url = "http://localhost:8080"
``` 

3. Set the bot's listening port:
```toml
port = 13457
```

4. Set the OpenChat public key. You can get this by running this command in the ``open-chat`` directory:
```bash
dfx canister call user_index public_key '(record { })'
```

Then add it to your config:
```toml
oc_public_key = "-----BEGIN PUBLIC KEY-----\nMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEW1Z0uDeQiWdgxlpsjmAfjPlSKtZT\nT1/7A3xcYeMq3mhUE4PHqLu4D+tdsE5ga+0jyh8PgfsnFBmxNE+F+nr2eg==\n-----END PUBLIC KEY-----\n"
```

5. Set the log level:
```toml
log_level = "INFO"
```

### Running the Bot: 
1. Make sure the Python API is running first (see Part 1)

2. Start the OpenChat bot:
```bash
cargo run
```

### Testing the Bot

1. Check if the bot is running:
```bash
curl http://localhost:13457/
```

You should receive a JSON response containing the bot definition and available commands.

2. The bot should now be ready to be registered with OpenChat using the `/register_bot` command.

## Next Steps

After setting up and testing the bot locally:
1. Register the bot with OpenChat using the `/register_bot` command
2. Test the bot in a development group
3. When ready, submit a proposal to publish the bot publicly

## Troubleshooting

- If the Python API isn't responding, check if it's running on port 5005
- If the Rust proxy fails to start, verify your config.toml settings
- Make sure both the PEM file and OpenChat public key are properly formatted
- Check the logs for any specific error messages

## Architecture
```
OpenChat <-> Rust Proxy (13457) <-> Python API (5005) <-> Bot Logic
``` 

The Rust proxy handles:
- OpenChat protocol compliance
- JWT verification
- Command routing

While the Python API handles:
- Bot logic and responses
- Expert knowledge and conversation





