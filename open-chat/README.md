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

## Interacting with the bot: 

1. Register the bot with OpenChat using the `/register_bot` command

2. Add the bot to the group 

You can check out the different steps of doing this in open chat's documentation [here](https://github.com/open-chat-labs/open-chat-bots/blob/main/GETSTARTED.md)

3. Type the ``/help`` command to see the different commands available. 
![help command](./images/help.png)

This is what you'll see in the chat: 
![help command](./images/help-response.png)

Now you can familiarize yourself with the different commands by reading the help response. 

#### Section A: Interacting with the ``Expert Bots``: 

You'll type ``/ask`` command in the chat to interact with the expert bots. 

![ask command](./images/ask.png)

The popup will appear and you can ask questions to the expert bots. This is the format you'll use: 
```bash
Format: [Expert Name] - [Your Question]
```

These are the experts available: 
```bash
• Beniah (Founder of Payd) - Bot Name: Benny
• Innocent Mangothe (Founder of Startinev) - Bot Name: Uncle Startups
• Dean Gichuki (Founder of Quick API) - Bot Name: Dean
• Sheila Waswa (Founder of Chasing Maverick) - Bot Name: Sheila
• Felix Macharia (Founder of KotaniPay) - Bot Name: Felix
```

Example: 
```bash
Benny - What is the best way to start a fintech startup? # This is the question you're asking Benn
Felix - How do I go about building a payment gateway? # This is the question you're asking Felix
```

![ask command response](./images/ask-popup.png)

Then the bot will send the request to the expert, this loading element will appear: 

![ask command response](./images/ask-loading.png)

Once the expert has responded, the bot will send the response back to you: 

![ask command response](./images/ask-response.png)

#### Section B: Interacting with the ``Project Management Bot``: 

You'll type ``/project`` command in the chat to interact with the project management bot. 

![project command](./images/project.png)

The frist step is to connect your asana account to the bot for you to use it. You'll get your asana token from the [developer console](https://app.asana.com/0/developer-console) in Asana 

![asana token](./images/asana-token.png)

You will click on ``Create new token`` and then copy the token. 

![asana token](./images/create-new-token.png)

You will then paste the token in the ``/project`` popup command in the chat. 

![project command](./images/project-connect.png)

You will then get a response in the chat: 

![project command response](./images/project-connected.png)

Now create your first task by typing ``/project`` then ``create [description]``

![project command](./images/project-create.png)

You will get the loading element again. And once your task is created succesfully, you'll get a response in the chat: 

![project command response](./images/project-created.png)

You can now click on the ``here`` link to view your task in your asana account. 

![project command response](./images/task-created.png)

The next step is to check out the tasks that are available on your asana account. You can do this by typing ``/project`` then ``list``

![project command](./images/project-list.png)

You will get the loading element again. And once your task is created succesfully, you'll get a response in the chat: 

![project command response](./images/project-list-response.png)

You can now see the tasks that are available on your asana account. 

#### Section C: Interacting with the ``GitHub Bot``: 

You'll type ``/github`` command in the chat to interact with the GitHub bot. 

![github command](./images/github.png)

You will get a popup to connect your GitHub account to the bot. 

![github command](./images/github-connect.png)

The first step is to create a personal access token from GitHub to connect your account to the bot. 

You can do this by going to your [GitHub account settings](https://github.com/settings/personal-access-tokens) and then generating a token. 

![github command](./images/github-token.png)

Click on ``Generate New Token`` and then once you've added ``Token Name`` and ``Token Description``, allow the following permissions: 
   - In the ``Repository Access``, select ``All Repositories``
   - In the ``Permissions``, select ``Repository Permissions`` and select ``Read and Write`` for all the permissions that you'd like to allow the bot to have. But the main ones are ``Issues`` and ``Pull Requests``.

Once you're done click on ``Generate Token`` and then copy the token, since you won't be able to see it again. 

![github command](./images/github-token.png)

You will then paste the token in the ``/github`` popup command in the chat. 

![github command](./images/github-connect-2.png)

Once you've done this, you'll get a response in the chat: 

![github command response](./images/github-connected.png)

You can start by running the command ``/github list`` to see all the repositories that you have access to. 

![github command](./images/github-list.png)

You will get the loading element again. And once the repositories are listed succesfully, you'll get a response in the chat: 

![github command response](./images/github-list-response.png)

The next step is to connect your repository to the bot. You can do this by typing ``/github select owner/repo``. You can directly copy the owner/repo from the list of repositories. 

![github command](./images/github-select.png)

This is the response you'll get in the chat if the repository is connected succesfully: 

![github command response](./images/github-select-repo.png)

You can now create a new issue by typing ``/github create issue title -- Description``. 

![github command](./images/github-create-issue.png)

You will get the loading element again. And once the issue is created succesfully, you'll get a response in the chat: 

![github command response](./images/github-create-issue-2.png)

You can now see the issue in your repository. 

![github command response](./images/github-create-issue-3.png)

To list issues in your repository, you can type ``/github list issues``. 

![github command](./images/github-list-issues.png)

You will get the loading element again. And once the issues are listed succesfully, you'll get a response in the chat: 

![github command response](./images/github-list-issues-2.png)

And with that you've successfully tested out the ``Infoundr OpenChat Bot``.  






