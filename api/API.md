# Main API Service Documentation

This API service acts as the central hub for all bot interactions, handling requests from Slack, Discord, and OpenChat platforms.

## Base URL
```
http://154.38.174.112:5005
```

## Authentication

Currently, the API doesn't require authentication as it's meant to be used internally by our communication services. However, it's recommended to implement rate limiting and IP whitelisting in production.

## Endpoints

### Health Check
```http
GET /api/health
```

Checks the health status of the API and lists available bots.

**Response:**
```json
{
    "status": "ok",
    "bots_available": ["Benny", "ProjectAssistant", "GitHubAssistant"]
}
```

### Bot Information
```http
GET /api/bot_info
```

Retrieves detailed information about all available bots.

**Response:**
```json
{
    "Benny": {
        "name": "Benny",
        "role": "AI Assistant",
        "expertise": "General knowledge and assistance"
    },
    "ProjectAssistant": {
        "name": "Project Assistant",
        "role": "Project Management",
        "expertise": "Asana integration and task management"
    },
    "GitHubAssistant": {
        "name": "GitHub Assistant",
        "role": "Development",
        "expertise": "GitHub integration and issue management"
    }
}
```

### Process Command
```http
POST /api/process_command
```

Processes commands from any of the communication platforms.

**Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
    "command": "ask_botname",
    "args": {
        "question": "Your question here",
        "user_id": "user123"
    }
}
```

**Supported Commands:**

#### 1. Bot Interaction Commands
- `ask_*` - Ask questions to specific bots
  ```json
  {
      "command": "ask_benny",
      "args": {
          "question": "How do I start a startup?",
          "user_id": "user123"
      }
  }
  ```

#### 2. Project Management Commands
- `project_connect` - Connect Asana account
  ```json
  {
      "command": "project_connect",
      "args": {
          "token": "your_asana_token",
          "user_id": "user123"
      }
  }
  ```

- `project_create_task` - Create new task
  ```json
  {
      "command": "project_create_task",
      "args": {
          "description": "Implement login feature",
          "user_id": "user123"
      }
  }
  ```

- `project_list_tasks` - List existing tasks
  ```json
  {
      "command": "project_list_tasks",
      "args": {
          "user_id": "user123"
      }
  }
  ```

#### 3. GitHub Integration Commands
- `github_connect` - Connect GitHub account
  ```json
  {
      "command": "github_connect",
      "args": {
          "token": "your_github_token",
          "user_id": "user123"
      }
  }
  ```

- `github_list_repos` - List repositories
  ```json
  {
      "command": "github_list_repos",
      "args": {
          "user_id": "user123"
      }
  }
  ```

- `github_select_repo` - Select repository
  ```json
  {
      "command": "github_select_repo",
      "args": {
          "repo_name": "owner/repo",
          "user_id": "user123"
      }
  }
  ```

- `github_list_issues` - List issues
  ```json
  {
      "command": "github_list_issues",
      "args": {
          "state": "open",
          "user_id": "user123"
      }
  }
  ```

- `github_create_issue` - Create new issue
  ```json
  {
      "command": "github_create_issue",
      "args": {
          "title": "Bug fix",
          "body": "Fix the login issue",
          "user_id": "user123"
      }
  }
  ```

- `github_list_prs` - List pull requests
  ```json
  {
      "command": "github_list_prs",
      "args": {
          "state": "open",
          "user_id": "user123"
      }
  }
  ```

**Response Format:**
```json
{
    "text": "Bot response message",
    "bot_name": "Bot Name"
}
```

## Error Handling

All endpoints return responses in the following format:
```json
{
    "error": "Error message if any",
    "bot_name": "Bot Name"
}
```

### Common Error Scenarios:
1. Invalid command format
2. Missing required arguments
3. Invalid user ID
4. Integration connection issues
5. Rate limiting

## Integration with Storage API

The main API service interacts with the Storage API (`http://154.38.174.112:3000`) for:
- Storing user credentials
- Saving chat messages
- Managing integration tokens
- Storing task and issue data

## Development

### Local Development
```bash
# Start the API service
python -m api.main_api
```

### Testing
```bash
# Test health endpoint
curl http://localhost:5005/api/health

# Test bot info endpoint
curl http://localhost:5005/api/bot_info

# Test command processing
curl -X POST http://localhost:5005/api/process_command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "ask_benny",
    "args": {
      "question": "Hello!",
      "user_id": "test123"
    }
  }'
```

## Mainnet Examples

Here's a complete sequence of commands to test the API in production:

```bash
# 1. Check API health
curl http://154.38.174.112:5005/api/health

# 2. Get available bots
curl http://154.38.174.112:5005/api/bot_info

# 3. Ask a question to Benny
curl -X POST http://154.38.174.112:5005/api/process_command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "ask_benny",
    "args": {
      "question": "How do I start a startup?",
      "user_id": "U123456789"
    }
  }'

# 4. Connect Asana account
curl -X POST http://154.38.174.112:5005/api/process_command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "project_connect",
    "args": {
      "token": "your_asana_token",
      "user_id": "U123456789"
    }
  }'

# 5. Create a new task
curl -X POST http://154.38.174.112:5005/api/process_command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "project_create_task",
    "args": {
      "description": "Implement user authentication",
      "user_id": "U123456789"
    }
  }'

# 6. List tasks
curl -X POST http://154.38.174.112:5005/api/process_command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "project_list_tasks",
    "args": {
      "user_id": "U123456789"
    }
  }'

# 7. Connect GitHub account
curl -X POST http://154.38.174.112:5005/api/process_command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "github_connect",
    "args": {
      "token": "your_github_token",
      "user_id": "U123456789"
    }
  }'

# 8. List GitHub repositories
curl -X POST http://154.38.174.112:5005/api/process_command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "github_list_repos",
    "args": {
      "user_id": "U123456789"
    }
  }'

# 9. Select a repository
curl -X POST http://154.38.174.112:5005/api/process_command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "github_select_repo",
    "args": {
      "repo_name": "owner/repo",
      "user_id": "U123456789"
    }
  }'

# 10. Create a GitHub issue
curl -X POST http://154.38.174.112:5005/api/process_command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "github_create_issue",
    "args": {
      "title": "Implement login feature",
      "body": "Add user authentication with JWT",
      "user_id": "U123456789"
    }
  }'

# 11. List GitHub issues
curl -X POST http://154.38.174.112:5005/api/process_command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "github_list_issues",
    "args": {
      "state": "open",
      "user_id": "U123456789"
    }
  }'

# 12. List pull requests
curl -X POST http://154.38.174.112:5005/api/process_command \
  -H "Content-Type: application/json" \
  -d '{
    "command": "github_list_prs",
    "args": {
      "state": "open",
      "user_id": "U123456789"
    }
  }'
```