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
    MessagePermission, StringParam,
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
    
    // Register commands for each bot
    for (bot_name, _info) in bot_info.iter() {
        let command_name = format!("ask_{}", bot_name.to_lowercase());
        info!("Registering command: {}", command_name);
        
        // Create command handler for this bot using the new constructor
        let handler = BotCommandHandler::new(
            command_name,
            bot_name.clone(),
            python_api_url.clone(),
            http_client.clone(),
        );
        
        commands = commands.register(handler);
    }

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
    let mut commands = state.commands.definitions();
    commands.extend(create_project_command_definitions());
    
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
        let definition = BotCommandDefinition {
            name: command_name.clone(),
            description: Some(format!("Ask {}", bot_name)),
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
        // Build payload based on command type
        let payload = match self.command_name.as_str() {
            cmd if cmd.starts_with("ask_") => {
                let question: String = context.command.arg("question");
                info!("Executing command {} with question: {}", self.command_name, question);
                
                serde_json::json!({
                    "command": self.command_name,
                    "args": {
                        "question": question,
                        "user_id": context.token
                    }
                })
            },
            "project_connect" => {
                let token: String = context.command.arg("token");
                info!("Executing project_connect with token length: {}", token.len());
                
                serde_json::json!({
                    "command": "project_connect",
                    "args": {
                        "token": token,
                        "user_id": context.token
                    }
                })
            },
            "project_create_task" => {
                let description: String = context.command.arg("description");
                info!("Executing project_create_task with description: {}", description);
                
                serde_json::json!({
                    "command": "project_create_task",
                    "args": {
                        "description": description,
                        "user_id": context.token
                    }
                })
            },
            "project_list_tasks" => {
                info!("Executing project_list_tasks");
                
                serde_json::json!({
                    "command": "project_list_tasks",
                    "args": {
                        "user_id": context.token
                    }
                })
            },
            _ => return Err(format!("Unknown command: {}", self.command_name))
        };

        let response = match self.http_client
            .post(format!("{}/api/process_command", self.python_api_url))
            .json(&payload)
            .send()
            .await {
                Ok(resp) => resp,
                Err(e) => return Err(format!("Failed to call Python API: {}", e)),
            };
        
        // Store the status before moving response
        let status = response.status();
        
        // Try to parse the response
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
    }
}

// Add this function
// fn verify_jwt(jwt: &str, public_key: &str) -> bool {
//     info!("Verifying JWT: {}", jwt);
//     info!("Using public key: {}", public_key);
//     // ... rest of verification
// }