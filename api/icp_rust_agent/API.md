# ICP Agent API Documentation

This API provides endpoints for interacting with the Internet Computer Protocol (ICP) canister, supporting both Slack and Discord integrations.

## Base URL
```
http://localhost:3000
```

## Quick Examples

### Register a new Slack user
```bash
curl -X POST http://localhost:3000/slack/users/U123456789/register
```

### Get user information
```bash
curl http://localhost:3000/slack/users/U123456789
```

### Store a chat message
```bash
curl -X POST http://localhost:3000/slack/messages/U123456789 \
  -H "Content-Type: application/json" \
  -d '{
    "id": "2vxsx-fae",
    "role": "User",
    "content": "Hello!",
    "question_asked": null,
    "timestamp": 1234567890,
    "bot_name": null
  }'
```

### Get all messages for a user
```bash
curl http://localhost:3000/slack/messages/U123456789
```

### Generate a dashboard token
```bash
curl -X POST http://localhost:3000/slack/token/U123456789
```

## Slack Integration

### User Management

#### Register Slack User
```http
POST /slack/users/:slack_id/register
```

Registers a new Slack user in the system.

**Path Parameters:**
- `slack_id` (string): The Slack user ID

**Example:**
```bash
# Register a new user with ID U123456789
curl -X POST http://localhost:3000/slack/users/U123456789/register
```

**Response:**
```json
{
    "success": true,
    "data": null,
    "error": null
}
```

#### Get Slack User
```http
GET /slack/users/:slack_id
```

Retrieves information about a registered Slack user.

**Path Parameters:**
- `slack_id` (string): The Slack user ID

**Example:**
```bash
# Get information for user U123456789
curl http://localhost:3000/slack/users/U123456789
```

**Response:**
```json
{
    "success": true,
    "data": {
        "slack_id": "U123456789",
        "site_principal": null,
        "display_name": null,
        "team_id": null
    },
    "error": null
}
```

### Message Management

#### Get Chat Messages
```http
GET /slack/messages/:slack_id
```

Retrieves all chat messages for a Slack user.

**Path Parameters:**
- `slack_id` (string): The Slack user ID

**Example:**
```bash
# Get all messages for user U123456789
curl http://localhost:3000/slack/messages/U123456789
```

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": "2vxsx-fae",
            "role": "User",
            "content": "Hello!",
            "question_asked": null,
            "timestamp": 1234567890,
            "bot_name": null
        }
    ],
    "error": null
}
```

#### Store Chat Message
```http
POST /slack/messages/:slack_id
```

Stores a chat message in the system. The message will be associated with the user's principal ID, which is derived from their Slack ID if not already set.

**Path Parameters:**
- `slack_id` (string): The Slack user ID

**Example:**
```bash
# Store a user message
curl -X POST http://localhost:3000/slack/messages/U123456789 \
  -H "Content-Type: application/json" \
  -d '{
    "id": "2vxsx-fae",
    "role": "User",
    "content": "Hello!",
    "question_asked": null,
    "timestamp": 1234567890,
    "bot_name": null
  }'

# Store an assistant message
curl -X POST http://localhost:3000/slack/messages/U123456789 \
  -H "Content-Type: application/json" \
  -d '{
    "id": "2vxsx-fae",
    "role": "Assistant",
    "content": "Hi there! How can I help you today?",
    "question_asked": "Hello!",
    "timestamp": 1234567891,
    "bot_name": "AI Assistant"
  }'
```

**Response:**
```json
{
    "success": true,
    "data": null,
    "error": null
}
```

### Token Management

#### Generate Dashboard Token
```http
POST /slack/token/:slack_id
```

Generates a dashboard token for a Slack user.

**Path Parameters:**
- `slack_id` (string): The Slack user ID

**Example:**
```bash
# Generate a token for user U123456789
curl -X POST http://localhost:3000/slack/token/U123456789
```

**Response:**
```json
{
    "success": true,
    "data": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "error": null
}
```

## GitHub Integration

### Connection Management

#### Store GitHub Connection
```http
POST /slack/github/:slack_id/connect
```

Stores a GitHub connection for a Slack user.

**Path Parameters:**
- `slack_id` (string): The Slack user ID

**Request Body:**
```json
{
    "token": "your_github_token",
    "selected_repo": null
}
```

**Example:**
```bash
curl -X POST http://localhost:3000/slack/github/U123456789/connect \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your_github_token",
    "selected_repo": null
  }'
```

**Response:**
```json
{
    "success": true,
    "data": null,
    "error": null
}
```

#### Update Selected Repository
```http
POST /slack/github/:slack_id/repo
```

Updates the selected GitHub repository for a Slack user.

**Path Parameters:**
- `slack_id` (string): The Slack user ID

**Request Body:**
```json
"owner/repo"
```

**Example:**
```bash
curl -X POST http://localhost:3000/slack/github/U123456789/repo \
  -H "Content-Type: application/json" \
  -d '"owner/repo"'
```

**Response:**
```json
{
    "success": true,
    "data": null,
    "error": null
}
```

### Issue Management

#### Store GitHub Issue
```http
POST /slack/github/:slack_id/issues
```

Stores a GitHub issue for a Slack user.

**Path Parameters:**
- `slack_id` (string): The Slack user ID

**Request Body:**
```json
{
    "id": "123",
    "title": "Bug fix",
    "body": "Fix the login issue",
    "repository": "owner/repo",
    "created_at": 1234567890,
    "status": "Open"
}
```

**Example:**
```bash
curl -X POST http://localhost:3000/slack/github/U123456789/issues \
  -H "Content-Type: application/json" \
  -d '{
    "id": "123",
    "title": "Bug fix",
    "body": "Fix the login issue",
    "repository": "owner/repo",
    "created_at": 1234567890,
    "status": "Open"
  }'
```

**Response:**
```json
{
    "success": true,
    "data": null,
    "error": null
}
```

## Project Management (Asana)

### Connection Management

#### Store Asana Connection
```http
POST /slack/asana/:slack_id/connect
```

Stores an Asana connection for a Slack user.

**Path Parameters:**
- `slack_id` (string): The Slack user ID

**Request Body:**
```json
{
    "token": "your_asana_token",
    "workspace_id": "workspace123",
    "project_ids": [
        ["project1", "Project One"],
        ["project2", "Project Two"]
    ]
}
```

**Example:**
```bash
curl -X POST http://localhost:3000/slack/asana/U123456789/connect \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your_asana_token",
    "workspace_id": "workspace123",
    "project_ids": [
        ["project1", "Project One"],
        ["project2", "Project Two"]
    ]
  }'
```

**Response:**
```json
{
    "success": true,
    "data": null,
    "error": null
}
```

### Task Management

#### Store Asana Task
```http
POST /slack/asana/:slack_id/tasks
```

Stores an Asana task for a Slack user.

**Path Parameters:**
- `slack_id` (string): The Slack user ID

**Request Body:**
```json
{
    "id": "task123",
    "status": "active",
    "title": "Implement login feature",
    "creator": "2vxsx-fae",
    "platform_id": "asana_task_123",
    "description": "Implement user authentication",
    "platform": "asana",
    "created_at": 1234567890
}
```

**Example:**
```bash
curl -X POST http://localhost:3000/slack/asana/U123456789/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "id": "task123",
    "status": "active",
    "title": "Implement login feature",
    "creator": "2vxsx-fae",
    "platform_id": "asana_task_123",
    "description": "Implement user authentication",
    "platform": "asana",
    "created_at": 1234567890
  }'
```

**Response:**
```json
{
    "success": true,
    "data": null,
    "error": null
}
```

## Error Handling

All endpoints return responses in the following format:
```json
{
    "success": boolean,
    "data": any | null,
    "error": string | null
}
```

### Example Error Response
```json
{
    "success": false,
    "data": null,
    "error": "Failed to store message: Invalid message format"
}
```

## Data Types

### MessageRole
```rust
enum MessageRole {
    User,
    Assistant
}
```

### ChatMessage
```rust
struct ChatMessage {
    id: Principal,
    role: MessageRole,
    content: String,
    question_asked: Option<String>,
    timestamp: u64,
    bot_name: Option<String>
}
```

### UserIdentifier
```rust
enum UserIdentifier {
    Principal(Principal),
    OpenChatId(String),
    SlackId(String),
    DiscordId(String)
}
```

### GitHubConnection
```rust
struct GitHubConnection {
    timestamp: u64,
    token: String,
    selected_repo: Option<String>
}
```

### GitHubIssue
```rust
struct GitHubIssue {
    id: String,
    title: String,
    body: String,
    repository: String,
    created_at: u64,
    status: IssueStatus
}

enum IssueStatus {
    Open,
    Closed
}
```

### AsanaConnection
```rust
struct AsanaConnection {
    token: String,
    workspace_id: String,
    project_ids: Vec<(String, String)> // (project_id, project_name)
}
```

### AsanaTask
```rust
struct AsanaTask {
    id: String,
    status: String,
    title: String,
    creator: Principal,
    platform_id: String,
    description: String,
    platform: String,
    created_at: u64
}
```

## Testing the API

Here's a complete sequence of commands to test the API:

```bash
# 1. Register a new user (DO NOT USE - done automatically in the logic, code is only for testing purposes)
curl -X POST http://localhost:3000/slack/users/U123456789/register

# 2. Verify user registration (DO NOT USE - done automatically in the logic, code is only for testing purposes)
curl http://localhost:3000/slack/users/U123456789

# 3. Store a user message
curl -X POST http://localhost:3000/slack/messages/U123456789 \
  -H "Content-Type: application/json" \
  -d '{
    "id": "2vxsx-fae",
    "role": "User",
    "content": "Hello!",
    "question_asked": null,
    "timestamp": 1234567890,
    "bot_name": null
  }'

# 4. Store an assistant response
curl -X POST http://localhost:3000/slack/messages/U123456789 \
  -H "Content-Type: application/json" \
  -d '{
    "id": "2vxsx-fae",
    "role": "Assistant",
    "content": "Hi there! How can I help you today?",
    "question_asked": "Hello!",
    "timestamp": 1234567891,
    "bot_name": "AI Assistant"
  }'

# 5. Retrieve all messages
curl http://localhost:3000/slack/messages/U123456789

# 6. Generate a dashboard token
curl -X POST http://localhost:3000/slack/token/U123456789

# 7. Connect GitHub
curl -X POST http://localhost:3000/slack/github/U123456789/connect \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your_github_token",
    "selected_repo": null
  }'

# 8. Store GitHub issue
curl -X POST http://localhost:3000/slack/github/U123456789/issues \
  -H "Content-Type: application/json" \
  -d '{
    "id": "123",
    "title": "Bug fix",
    "body": "Fix the login issue",
    "repository": "owner/repo",
    "created_at": 1234567890,
    "status": "Open"
  }'

# 9. Connect Asana
curl -X POST http://localhost:3000/slack/asana/U123456789/connect \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your_asana_token",
    "workspace_id": "workspace123",
    "project_ids": [
        ["project1", "Project One"],
        ["project2", "Project Two"]
    ]
  }'

# 10. Store Asana task
curl -X POST http://localhost:3000/slack/asana/U123456789/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "id": "task123",
    "status": "active",
    "title": "Implement login feature",
    "creator": "2vxsx-fae",
    "platform_id": "asana_task_123",
    "description": "Implement user authentication",
    "platform": "asana",
    "created_at": 1234567890
  }'

# 11. Generate dashboard token
curl -X POST http://localhost:3000/slack/token/U123456789
``` 