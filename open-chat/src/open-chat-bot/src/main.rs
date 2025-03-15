use axum::{
    body::Bytes,
    extract::State,
    http::StatusCode,
    routing::{get, post},
    Router,
    http::HeaderMap,
};
use dotenv::dotenv;
use oc_bots_sdk::api::command::{CommandHandlerRegistry, CommandResponse};
use oc_bots_sdk::api::definition::{
    BotCommandDefinition, BotCommandParam, BotCommandParamType, BotDefinition, BotPermissions,
    MessagePermission, StringParam, BotCommandOptionChoice,
};
use oc_bots_sdk::oc_api::client_factory::ClientFactory;
use oc_bots_sdk_offchain::env;
use oc_bots_sdk_offchain::AgentRuntime;
use reqwest::Client as ReqwestClient;
use serde::Deserialize;
use std::net::{Ipv4Addr, SocketAddr};
use std::sync::Arc;
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;
use tracing::{info, error};
use tracing_subscriber::fmt::format::FmtSpan;
use serde_json::json;

mod config;

// Structure to hold application state
struct AppState {
    oc_public_key: String,
    commands: CommandHandlerRegistry<AgentRuntime>,
    python_api_url: String,
    http_client: ReqwestClient,
}

// Python API response structure
#[derive(Deserialize, Debug)]
struct PythonBotResponse {
    text: String,
    bot_name: String,
}

// Python API error response
#[derive(Deserialize, Debug)]
struct PythonErrorResponse {
    error: String,
}

// Python API bot info
#[derive(Deserialize, Debug)]
struct BotInfo {
    name: String,
    role: String,
    expertise: String,
}

// Add this struct to deserialize the command data
#[derive(Deserialize, Debug)]
struct CommandRequest {
    jwt: String,
    #[serde(rename = "commandRequest")]
    command_request: serde_json::Value,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load .env file if present
    dotenv().ok();

    // Get config file path from env - if not set, use default
    let config_file_path = std::env::var("CONFIG_FILE").unwrap_or("./config.toml".to_string());

    // Load & parse config
    let config = config::Config::from_file(&config_file_path)?;

    // Setup logging
    tracing_subscriber::fmt()
        .with_max_level(config.log_level)
        .with_span_events(FmtSpan::CLOSE)
        .init();

    info!("Starting OpenChat bot proxy");

    // Build agent for OpenChat communication
    let agent = oc_bots_sdk_offchain::build_agent(config.ic_url.clone(), &config.pem_file).await;

    // Create client factory
    let oc_client_factory = Arc::new(ClientFactory::new(AgentRuntime::new(
        agent.clone(),
        tokio::runtime::Runtime::new().unwrap(),
    )));

    // Create HTTP client for Python API communication
    let http_client = ReqwestClient::new();

    // Fetch available bots from Python API
    let python_api_url = config.python_api_url.clone();
    let bot_info_response = http_client
        .get(format!("{}/api/bot_info", python_api_url))
        .send()
        .await?;
    
    if !bot_info_response.status().is_success() {
        error!("Failed to fetch bot info from Python API: {}", bot_info_response.status());
        return Err("Failed to fetch bot info from Python API".into());
    }

    let bot_info: std::collections::HashMap<String, BotInfo> = bot_info_response.json().await?;
    info!("Fetched info for {} bots from Python API", bot_info.len());

    // Create command registry
    let mut commands = CommandHandlerRegistry::new(oc_client_factory);
    
    // Register the unified ask command
    let ask_handler = BotCommandHandler::new(
        "ask".to_string(),
        "AI Assistant".to_string(),
        python_api_url.clone(),
        http_client.clone(),
    );
    commands = commands.register(ask_handler);

    // Register the unified project command
    let project_handler = BotCommandHandler::new(
        "project".to_string(),
        "Project Assistant".to_string(),
        python_api_url.clone(),
        http_client.clone(),
    );
    commands = commands.register(project_handler);

    // Register the help command
    let help_handler = BotCommandHandler::new(
        "help".to_string(),
        "Help Assistant".to_string(),
        python_api_url.clone(),
        http_client.clone(),
    );
    commands = commands.register(help_handler);

    // Register unified github commands
    let github_handler = BotCommandHandler::new(
        "github".to_string(), 
        "GitHub Assistant".to_string(),
        python_api_url.clone(),
        http_client.clone(),
    );
    commands = commands.register(github_handler);

    // Create app state
    let app_state = AppState {
        oc_public_key: config.oc_public_key,
        commands,
        python_api_url,
        http_client,
    };

    // Create router with endpoints
    let app = Router::new()
        .route("/", get(bot_definition))
        .route("/execute", post(execute_command))
        .route("/execute_command", post(execute_command))
        .layer(CorsLayer::permissive())
        .layer(TraceLayer::new_for_http())
        .with_state(Arc::new(app_state));

    // Start HTTP server
    let socket_addr = SocketAddr::new(Ipv4Addr::UNSPECIFIED.into(), config.port);
    info!("Starting HTTP server on {}", socket_addr);
    
    let listener = tokio::net::TcpListener::bind(socket_addr).await?;
    axum::serve(listener, app.into_make_service()).await?;

    Ok(())
}

// Create a command definition for a bot
fn create_bot_command_definition(bot_name: &str, role: &str) -> BotCommandDefinition {
    BotCommandDefinition {
        name: format!("ask_{}", bot_name.to_lowercase()),
        description: Some(format!("Ask {} ({})", bot_name, role)),
        placeholder: Some(format!("Asking {}...", bot_name)),
        params: vec![BotCommandParam {
            name: "question".to_string(),
            description: Some(format!("The question to ask {}", bot_name)),
            placeholder: Some("Your question".to_string()),
            required: true,
            param_type: BotCommandParamType::StringParam(StringParam {
                min_length: 1,
                max_length: 10000,
                choices: Vec::new(),
                multi_line: true,
            }),
        }],
        permissions: BotPermissions::from_message_permission(MessagePermission::Text),
        default_role: None,
    }
}

// Create project management commands
fn create_project_command_definitions() -> Vec<BotCommandDefinition> {
    vec![
        BotCommandDefinition {
            name: "project_connect".to_string(),
            description: Some("Connect your Asana account".to_string()),
            placeholder: Some("Connecting to Asana...".to_string()),
            params: vec![BotCommandParam {
                name: "token".to_string(),
                description: Some("Your Asana Personal Access Token".to_string()),
                placeholder: Some("Paste your token here".to_string()),
                required: true,
                param_type: BotCommandParamType::StringParam(StringParam {
                    min_length: 1,
                    max_length: 1000,
                    choices: Vec::new(),
                    multi_line: false,
                }),
            }],
            permissions: BotPermissions::from_message_permission(MessagePermission::Text),
            default_role: None,
        },
        BotCommandDefinition {
            name: "project_create_task".to_string(),
            description: Some("Create a new task in Asana".to_string()),
            placeholder: Some("Creating task...".to_string()),
            params: vec![BotCommandParam {
                name: "description".to_string(),
                description: Some("Description of the task".to_string()),
                placeholder: Some("What needs to be done?".to_string()),
                required: true,
                param_type: BotCommandParamType::StringParam(StringParam {
                    min_length: 1,
                    max_length: 10000,
                    choices: Vec::new(),
                    multi_line: true,
                }),
            }],
            permissions: BotPermissions::from_message_permission(MessagePermission::Text),
            default_role: None,
        },
        BotCommandDefinition {
            name: "project_list_tasks".to_string(),
            description: Some("List your Asana tasks".to_string()),
            placeholder: Some("Fetching tasks...".to_string()),
            params: vec![],
            permissions: BotPermissions::from_message_permission(MessagePermission::Text),
            default_role: None,
        },
    ]
}

// Bot definition endpoint
async fn bot_definition(State(state): State<Arc<AppState>>) -> (StatusCode, Bytes) {
    let commands = state.commands.definitions();
    
    let definition = BotDefinition {
        description: "The Genius AI Co-Founder—get expert advice and manage tasks directly in OpenChat".to_string(),
        commands,
        autonomous_config: None,
    };

    (
        StatusCode::OK,
        Bytes::from(serde_json::to_vec(&definition).unwrap()),
    )
}

// Command execution endpoint
async fn execute_command(
    State(state): State<Arc<AppState>>, 
    headers: HeaderMap,
    bytes: Bytes,
) -> (StatusCode, Bytes) {
    info!("=== Command Execution Start ===");
    info!("Headers: {:?}", headers);
    
    // Get JWT from x-oc-jwt header
    let jwt = match headers.get("x-oc-jwt") {
        Some(jwt_header) => {
            match jwt_header.to_str() {
                Ok(jwt) => {
                    info!("Found JWT in x-oc-jwt header");
                    jwt.to_string()
                },
                Err(e) => {
                    error!("Invalid JWT header value: {}", e);
                    return (
                        StatusCode::BAD_REQUEST,
                        Bytes::from("Invalid JWT header value"),
                    );
                }
            }
        },
        None => {
            error!("No JWT found in x-oc-jwt header");
            return (
                StatusCode::BAD_REQUEST,
                Bytes::from("Missing JWT header"),
            );
        }
    };

    info!("JWT length: {}", jwt.len());
    
    // Parse command data from the JWT payload
    let result = state
        .commands
        .execute(&jwt, &state.oc_public_key, env::now())
        .await;
        
    info!("Command execution result: {:?}", result);
    info!("=== Command Execution End ===");
    
    match result {
        CommandResponse::Success(r) => {
            info!("Command executed successfully");
            (StatusCode::OK, Bytes::from(serde_json::to_vec(&r).unwrap()))
        }
        CommandResponse::BadRequest(r) => {
            error!("Bad request: {:?}", r);
            (
                StatusCode::BAD_REQUEST,
                Bytes::from(serde_json::to_vec(&r).unwrap()),
            )
        }
        CommandResponse::InternalError(err) => {
            error!("Internal error: {:?}", err);
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Bytes::from(format!("{err:?}")),
            )
        }
        CommandResponse::TooManyRequests => {
            error!("Too many requests");
            (StatusCode::TOO_MANY_REQUESTS, Bytes::new())
        }
    }
}

// Bot command handler
struct BotCommandHandler {
    command_name: String,
    bot_name: String,
    python_api_url: String,
    http_client: ReqwestClient,
    definition: BotCommandDefinition,
}

impl BotCommandHandler {
    fn new(command_name: String, bot_name: String, python_api_url: String, http_client: ReqwestClient) -> Self {
        let definition = match command_name.as_str() {
            "ask" => BotCommandDefinition {
                name: command_name.clone(),
                description: Some("Ask an AI expert for help: Benny, Felix, or Sheila".to_string()),
                placeholder: Some("Asking expert...".to_string()),
                params: vec![BotCommandParam {
                    name: "message".to_string(),
                    description: Some("Format: [Expert Name] - [Your Question]".to_string()),
                    placeholder: Some("e.g., Benny - How do I validate my startup idea?".to_string()),
                    required: true,
                    param_type: BotCommandParamType::StringParam(StringParam {
                        min_length: 1,
                        max_length: 10000,
                        choices: Vec::new(),
                        multi_line: true,
                    }),
                }],
                permissions: BotPermissions::from_message_permission(MessagePermission::Text),
                default_role: None,
            },
            "project" => BotCommandDefinition {
                name: command_name.clone(),
                description: Some("Manage your Asana projects and tasks".to_string()),
                placeholder: Some("Processing your request...".to_string()),
                params: vec![BotCommandParam {
                    name: "command".to_string(),
                    description: Some(
                        "Available Actions:\n\
                        • connect [token] - Connect your Asana account\n\
                        • list - View your tasks\n\
                        • create [description] - Create a new task\n\n\
                        Example: create Build landing page"
                    .to_string()),
                    placeholder: Some("[action] [parameters]".to_string()),
                    required: true,
                    param_type: BotCommandParamType::StringParam(StringParam {
                        min_length: 1,
                        max_length: 10000,
                        choices: Vec::new(),
                        multi_line: true,
                    }),
                }],
                permissions: BotPermissions::from_message_permission(MessagePermission::Text),
                default_role: None,
            },
            "help" => BotCommandDefinition {
                name: command_name.clone(),
                description: Some("Get help and list of available commands".to_string()),
                placeholder: Some("Processing...".to_string()),
                params: vec![],
                permissions: BotPermissions::from_message_permission(MessagePermission::Text),
                default_role: None,
            },
            "github" => BotCommandDefinition {
                name: command_name.clone(), 
                description: Some("Manage GitHub repositories and issues".to_string()), 
                placeholder: Some("Processing your request...".to_string()),
                params: vec![BotCommandParam {
                    name: "command".to_string(),
                    description: Some("Available commands:\n".to_string() + 
                        "• connect <token> - Connect your GitHub account\n" +
                        "• list - List your repositories\n" +
                        "• select <owner/repo> - Select a repository to work with\n" +
                        "• create \"Issue title\" \"Issue description\" - Create a new issue\n" +
                        "• list_issues [open/closed] - List repository issues\n" +
                        "• list_prs [open/closed] - List pull requests\n" +
                        "• check_repo - Check the currently connected repository"),
                    placeholder: Some("[command] [parameters]".to_string()),
                    required: true, 
                    param_type: BotCommandParamType::StringParam(StringParam {
                        min_length: 1, 
                        max_length: 10000,
                        choices: Vec::new(),
                        multi_line: true,
                    }), 
                }],
                permissions: BotPermissions::from_message_permission(MessagePermission::Text),
                default_role: None,
            },
            _ => BotCommandDefinition {
                name: command_name.clone(),
                description: Some("Unknown command".to_string()),
                placeholder: Some("Unknown command".to_string()),
                params: vec![],
                permissions: BotPermissions::from_message_permission(MessagePermission::Text),
                default_role: None,
            },
        };

        Self {
            command_name,
            bot_name,
            python_api_url,
            http_client,
            definition,
        }
    }
}

// Bot command handler implementation
#[async_trait::async_trait]
impl oc_bots_sdk::api::command::CommandHandler<AgentRuntime> for BotCommandHandler {
    fn definition(&self) -> &BotCommandDefinition {
        &self.definition
    }

    async fn execute(
        &self,
        context: oc_bots_sdk::types::BotCommandContext,
        oc_client_factory: &ClientFactory<AgentRuntime>,
    ) -> Result<oc_bots_sdk::api::command::SuccessResult, String> {
        let user_id = context.command.initiator.to_string();

        match self.command_name.as_str() {
            "ask" => {
                let message: String = context.command.arg("message");
                info!("Executing ask command with message: {}", message);

                // Parse the expert name and question
                let parts: Vec<&str> = message.splitn(2, '-').collect();
                if parts.len() != 2 {
                    let help_message = oc_client_factory
                        .build(context)
                        .send_text_message(
                            "Please use the format: [Expert Name] - [Your Question]\n\n\
                            Available experts:\n\
                            • Benny - Backend & Business Expert\n\
                            • Felix - Frontend Expert\n\
                            • Dean - DevOps Expert\n\
                            \nExample: `Benny - How do I validate my startup idea?`".to_string()
                        )
                        .execute_then_return_message(|_, _| ());

                    return Ok(oc_bots_sdk::api::command::SuccessResult { message: help_message });
                }

                let expert = parts[0].trim().to_lowercase();
                let question = parts[1].trim();

                // Validate expert name
                let valid_experts = vec!["benny", "felix", "dean"];
                if !valid_experts.contains(&expert.as_str()) {
                    let error_message = oc_client_factory
                        .build(context)
                        .send_text_message(
                            format!("Unknown expert '{}'. Available experts:\n\
                            • Benny - Backend & Business Expert\n\
                            • Felix - Frontend Expert\n\
                            • Dean - DevOps Expert", parts[0].trim())
                        )
                        .execute_then_return_message(|_, _| ());

                    return Ok(oc_bots_sdk::api::command::SuccessResult { message: error_message });
                }

                let payload = serde_json::json!({
                    "command": format!("ask_{}", expert),
                    "args": {
                        "question": question,
                        "user_id": user_id
                    }
                });

                let response = self.http_client
                    .post(format!("{}/api/process_command", self.python_api_url))
                    .json(&payload)
                    .send()
                    .await
                    .map_err(|e| format!("Failed to call Python API: {}", e))?;

                let status = response.status();
                
                if !status.is_success() {
                    match response.json::<PythonErrorResponse>().await {
                        Ok(err) => return Err(err.error),
                        Err(_) => return Err(format!("Python API returned error status: {}", status)),
                    }
                }
                
                let bot_response = match response.json::<PythonBotResponse>().await {
                    Ok(resp) => resp,
                    Err(e) => return Err(format!("Failed to parse Python API response: {}", e)),
                };
                
                let formatted_response = format!("*{}*\n{}", bot_response.bot_name, bot_response.text);
                
                let message = oc_client_factory
                    .build(context)
                    .send_text_message(formatted_response)
                    .execute_then_return_message(|_, _| ());
                
                Ok(oc_bots_sdk::api::command::SuccessResult { message })
            },
            "project" => {
                let command_text: String = context.command.arg("command");
                let parts: Vec<&str> = command_text.splitn(2, ' ').collect();
                
                if parts.is_empty() {
                    return Err("Please specify a project action".to_string());
                }

                let action = parts[0].trim().to_lowercase();
                let params = parts.get(1).map(|s| s.trim()).unwrap_or("");

                // Set processing message based on action
                let processing_message = match action.as_str() {
                    "connect" => "Connecting to Asana...",
                    "list" => "Fetching your tasks...",
                    "create" => "Creating new task...",
                    _ => "Processing project command...",
                };
                info!("{}", processing_message);

                let payload = match action.as_str() {
                    "connect" => serde_json::json!({
                        "command": "project_connect",
                        "args": {
                            "token": params,
                            "user_id": user_id
                        }
                    }),
                    "list" => serde_json::json!({
                        "command": "project_list_tasks",
                        "args": {
                            "user_id": user_id
                        }
                    }),
                    "create" => serde_json::json!({
                        "command": "project_create_task",
                        "args": {
                            "description": params,
                            "user_id": user_id
                        }
                    }),
                    _ => return Err("Unknown project action. Available actions: connect, list, create".to_string()),
                };

                let response = self.http_client
                    .post(format!("{}/api/process_command", self.python_api_url))
                    .json(&payload)
                    .send()
                    .await
                    .map_err(|e| format!("Failed to call Python API: {}", e))?;

                let status = response.status();
                
                if !status.is_success() {
                    match response.json::<PythonErrorResponse>().await {
                        Ok(err) => return Err(err.error),
                        Err(_) => return Err(format!("Python API returned error status: {}", status)),
                    }
                }
                
                let bot_response = match response.json::<PythonBotResponse>().await {
                    Ok(resp) => resp,
                    Err(e) => return Err(format!("Failed to parse Python API response: {}", e)),
                };
                
                let formatted_response = format!("*{}*\n{}", bot_response.bot_name, bot_response.text);
                
                let message = oc_client_factory
                    .build(context)
                    .send_text_message(formatted_response)
                    .execute_then_return_message(|_, _| ());
                
                Ok(oc_bots_sdk::api::command::SuccessResult { message })
            },
            "help" => {
                let help_text = "🤖 **Infoundr: The Genius AI Co-Founder and Assistant**\n\n".to_string() +
                    "I'm your AI-powered assistant that can help with various tasks:\n\n" +
                    
                    "**Ask AI Experts** 📚\n" +
                    "You can ask any question to our AI experts, and they will answer you in a friendly and engaging way.\n" +
                    "`/ask [Expert Name] [Your Question]`\n" +
                    "Available experts:\n\
                    • Beniah (Founder of Payd) - Bot Name: Benny\n\
                    • Innocent Mangothe (Founder of Startinev) - Bot Name: Uncle Startups\n\
                    • Dean Gichuki (Founder of Quick API) - Bot Name: Dean\n\
                    • Sheila Waswa (Founder of Chasing Maverick) - Bot Name: Sheila\n\
                    • Felix Macharia (Founder of KotaniPay) - Bot Name: Felix\n\n" +
                    
                    "**Project Management** 📋\n" +
                    "*Task Management Commands:*\n\
                    1. First, connect your Asana account:\n\
                    `/project connect YOUR_TOKEN` - Get your token from https://app.asana.com/0/developer-console\n\n\
                    2. Create a new task:\n\
                    `/project create Task Name Task Description` - Create a new task in Asana\n\n\
                    3. List your tasks:\n\
                    `/project list` - View your current tasks\n\n" +
                    
                    "**GitHub Integration** 💻\n" +
                    "`/github connect YOUR_TOKEN` - Connect GitHub account\n" +
                    "To connect, you'll need a personal access token. Get it from: https://github.com/settings/personal-access-tokens\n" +
                    "Steps to create a new token:\n\
                    1. Click on 'Generate new token' in the top right section.\n\
                    2. Set 'Repository access' to: All repositories.\n\
                    3. Under 'Repository permissions':\n\
                    - Issues: Set to read & write.\n\
                    - Pull requests: Set to read & write.\n\n" +
                    "`/github list` - List repositories\n" +
                    "`/github select REPO_NAME` - Select repository\n" +
                    "`/github create ISSUE_TITLE ISSUE_DESCRIPTION` - Create issue\n" +
                    "`/github list_issues [open/closed]` - List issues\n" +
                    "`/github list_prs [open/closed]` - List pull requests\n\n" +
                    
                    "For more details on any command, use it with --help\n" +
                    "Example: /github --help";

                let message = oc_client_factory
                    .build(context)
                    .send_text_message(help_text)
                    .execute_then_return_message(|_, _| ());

                Ok(oc_bots_sdk::api::command::SuccessResult { message })
            },
            "github" => {
                let command_text: String = context.command.arg("command");
                let parts: Vec<&str> = command_text.splitn(2, ' ').collect();
                
                if parts.is_empty() {
                    return Err("Please specify a GitHub action".to_string());
                }

                let action = parts[0].trim().to_lowercase();
                let params = parts.get(1).map(|s| s.trim()).unwrap_or("");

                // Set processing message based on action
                let processing_message = match action.as_str() {
                    "connect" => "Connecting to GitHub...",
                    "list" => "Fetching your repositories...",
                    "select" => "Selecting repository...",
                    "create" => "Creating new issue...",
                    "list_issues" => "Fetching issues...",
                    "list_prs" => "Fetching pull requests...",
                    "check_repo" => "Checking connected repository...",
                    _ => "Processing GitHub command...",
                };
                info!("{}", processing_message);

                let payload = match action.as_str() {
                    "connect" => json!({
                        "command": "github_connect",
                        "args": {
                            "token": params,
                            "user_id": user_id
                        }
                    }),
                    "list" => json!({
                        "command": "github_list_repos",
                        "args": {
                            "user_id": user_id
                        }
                    }),
                    "select" => json!({
                        "command": "github_select_repo",
                        "args": {
                            "repo_name": params,
                            "user_id": user_id
                        }
                    }),
                    "create" => {
                        let parts: Vec<&str> = params.splitn(2, '"').collect();
                        if parts.len() < 2 {
                            return Err("Please provide title in quotes: create \"Issue title\" \"Description\"".to_string());
                        }
                        json!({
                            "command": "github_create_issue",
                            "args": {
                                "title": parts[1],
                                "body": parts.get(3).unwrap_or(&""),
                                "user_id": user_id
                            }
                        })
                    },
                    "list_issues" => json!({
                        "command": "github_list_issues",
                        "args": {
                            "state": if params.is_empty() { "open" } else { params },
                            "user_id": user_id
                        }
                    }),
                    "list_prs" => json!({
                        "command": "github_list_prs",
                        "args": {
                            "state": if params.is_empty() { "open" } else { params },
                            "user_id": user_id
                        }
                    }),
                    "check_repo" => json!({
                        "command": "github_check_repo",
                        "args": {
                            "user_id": user_id
                        }
                    }),
                    _ => return Err("Unknown GitHub action. Available actions: connect, list, select, create, list_issues, list_prs".to_string()),
                };

                let response = self.http_client
                    .post(format!("{}/api/process_command", self.python_api_url))
                    .json(&payload)
                    .send()
                    .await
                    .map_err(|e| format!("Failed to call Python API: {}", e))?;

                let status = response.status();
                
                if !status.is_success() {
                    match response.json::<PythonErrorResponse>().await {
                        Ok(err) => return Err(err.error),
                        Err(_) => return Err(format!("Python API returned error status: {}", status)),
                    }
                }
                
                let bot_response = match response.json::<PythonBotResponse>().await {
                    Ok(resp) => resp,
                    Err(e) => return Err(format!("Failed to parse Python API response: {}", e)),
                };
                
                let formatted_response = format!("*{}*\n{}", bot_response.bot_name, bot_response.text);
                
                let message = oc_client_factory
                    .build(context)
                    .send_text_message(formatted_response)
                    .execute_then_return_message(|_, _| ());
                
                Ok(oc_bots_sdk::api::command::SuccessResult { message })
            },
            _ => return Err("Unknown command".to_string()),
        }
    }
}

// Add this function
// fn verify_jwt(jwt: &str, public_key: &str) -> bool {
//     info!("Verifying JWT: {}", jwt);
//     info!("Using public key: {}", public_key);
//     // ... rest of verification
// }