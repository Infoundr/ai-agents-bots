# Infoundr Agent Bots

A modular, multi-bot assistant platform for startups, supporting Open Chat, Slack, and Discord. Each service is organized in its own folder for maintainability and scalability.

## Project Structure

```
ai-agents-bots/
│
├── api/                # Main API service (Flask/FastAPI)
|   ├── icp_rust_agent/ # Rust-based API service for storage and data management
|   |   ├── src/       # Rust source code
|   |   ├── Cargo.toml # Rust dependencies and project configuration
|   |   ├── API.md     # API documentation and specifications
|   |   └── target/    # Build artifacts
│   ├── main_api.py
│   ├── requirements.txt
│   └── tokens/
│
├── open-chat/         # Open Chat service (Rust)
│   ├── src/          # Source code
│   ├── Cargo.toml    # Rust dependencies
│   └── config.toml   # Configuration
│
├── slack/              # Slack integration service
│   ├── slack_bot.py
│   ├── requirements.txt
│   └── slack_installations/
│
├── core/               # Shared logic, bots, integrations
│   ├── agent_bots.py
│   ├── project_management_bot.py
│   ├── connect_asana.py
│   ├── integrations/
│   └── knowledge_bases/
│
├── .env                # Environment variables (not committed)
├── README.md
└── requirements.txt    # (optional: root-level for dev tools)
```

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Infoundr/ai-agents-bots
   cd ai-agents-bots
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install requirements for each service:**
     ```bash
     pip install -r requirements.txt
     ```

4. **Set up environment variables:**
   - Copy `.env.example` to `.env` (if provided), or create a `.env` file in the project root with the variables inside. 

## Running the Services

### 1. **API Service**
From the project root:
```bash
python -m api.main_api
```
- The API will be available at `http://localhost:5005/` 

### 2. **Slack Bot**
From the project root:
```bash
python -m slack.slack_bot
```
- The Slack bot will listen for events and commands as configured.

### 3. **(Optional) Other Integrations**
- Add and run other integrations (e.g., Discord) in their own folders, following the same pattern.

## Adding New Bots or Integrations
- Define new bots in `core/agent_bots.py`.
- Add new integrations in `core/integrations/`.
- Update the relevant service to use the new bot/integration.
