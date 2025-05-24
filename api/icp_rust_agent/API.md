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

## Discord Integration
*Coming soon*

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

## Testing the API

Here's a complete sequence of commands to test the API:

```bash
# 1. Register a new user
curl -X POST http://localhost:3000/slack/users/U123456789/register

# 2. Verify user registration
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
``` 