use anyhow::Result;
use url::Url;
use ic_agent::Agent;
use candid::Principal;
use candid::{Encode, Decode};
use axum::{
    routing::{get, post},
    Router,
    Json,
    extract::{State, Path},
    http::{HeaderMap, Request},
    middleware::{self, Next},
    response::{Response, IntoResponse},
};
use std::sync::Arc;
use serde::Serialize;
use std::net::SocketAddr;
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;
use dotenv::dotenv;
use std::io::Write;

mod slack;
use slack::{
    SlackClient, SlackUser, ChatMessage, SlackResponse,
    GitHubConnection, GitHubIssue, AsanaConnection, AsanaTask
};

// const CANISTER_ID: &str = "g7ko2-fyaaa-aaaam-qdlea-cai"; // mainnet
const CANISTER_ID: &str = "54ro3-xaaaa-aaaab-qac2q-cai"; // development

#[derive(Clone)]
struct AppState {
    agent: Arc<Agent>,
    canister_id: Principal,
    slack_client: Arc<SlackClient>,
    api_key: String,
    base_url: String,
}

#[derive(Serialize)]
struct AdminResponse {
    admins: Vec<String>,
}

#[derive(Serialize)]
struct ErrorResponse {
    success: bool,
    data: Option<()>,
    error: String,
}

#[derive(Serialize)]
struct TokenResponse {
    token: String,
    login_url: String,
}

// Add this middleware function
async fn auth_middleware(
    State(state): State<Arc<AppState>>,
    headers: HeaderMap,
    request: Request<axum::body::Body>,
    next: Next,
) -> Result<Response, impl IntoResponse> {
    println!("\n[DEBUG] ====== Auth Middleware ======");
    println!("[DEBUG] Received request to: {}", request.uri());
    std::io::stdout().flush().unwrap();

    // Get the API key from the header
    let api_key = headers
        .get("x-api-key")
        .and_then(|value| value.to_str().ok())
        .ok_or_else(|| {
            println!("[DEBUG] Missing API key");
            std::io::stdout().flush().unwrap();
            Json(ErrorResponse {
                success: false,
                data: None,
                error: "Missing API key".to_string(),
            }).into_response()
        })?;

    // Verify the API key
    if api_key != state.api_key {
        println!("[DEBUG] Invalid API key");
        std::io::stdout().flush().unwrap();
        return Err(Json(ErrorResponse {
            success: false,
            data: None,
            error: "Invalid API key".to_string(),
        }).into_response());
    }

    println!("[DEBUG] Auth successful");
    std::io::stdout().flush().unwrap();

    // If authentication passes, proceed with the request
    Ok(next.run(request).await)
}

// Initializing the agent
pub async fn create_agent(url: Url, use_mainnet: bool) -> Result<Agent> {
    let agent = Agent::builder().with_url(url).build()?;
    if use_mainnet {
        agent.fetch_root_key().await?;
    }
    Ok(agent)
}

#[axum::debug_handler]
async fn get_admins(State(state): State<AppState>) -> Result<Json<AdminResponse>, String> {
    let args = Encode!().map_err(|e| e.to_string())?;
    
    let response = state.agent
        .query(&state.canister_id, "get_admins")
        .with_arg(args)
        .call()
        .await
        .map_err(|e| e.to_string())?;
    
    let admins: Vec<Principal> = Decode!(&response, Vec<Principal>)
        .map_err(|e| e.to_string())?;
    
    Ok(Json(AdminResponse {
        admins: admins.into_iter().map(|p| p.to_string()).collect(),
    }))
}

// Slack endpoints
#[axum::debug_handler]
async fn ensure_slack_user(
    State(state): State<AppState>,
    Path(slack_id): Path<String>,
) -> Json<SlackResponse<()>> {
    match state.slack_client.ensure_user_registered(slack_id).await {
        Ok(response) => Json(response),
        Err(e) => Json(SlackResponse::error(e)),
    }
}

#[axum::debug_handler]
async fn get_slack_user(
    State(state): State<AppState>,
    Path(slack_id): Path<String>,
) -> Json<SlackResponse<Option<SlackUser>>> {
    match state.slack_client.get_user(slack_id).await {
        Ok(response) => Json(response),
        Err(e) => Json(SlackResponse::error(e)),
    }
}

#[axum::debug_handler]
async fn get_slack_messages(
    State(state): State<AppState>,
    Path(slack_id): Path<String>,
) -> Json<SlackResponse<Vec<ChatMessage>>> {
    match state.slack_client.get_messages(slack_id).await {
        Ok(response) => Json(response),
        Err(e) => Json(SlackResponse::error(e)),
    }
}

#[axum::debug_handler]
async fn store_slack_message(
    State(state): State<AppState>,
    Path(slack_id): Path<String>,
    Json(message): Json<ChatMessage>,
) -> Json<SlackResponse<()>> {
    println!("\n[DEBUG] ====== Chat Message Handler ======");
    println!("[DEBUG] Received request to store chat message");
    println!("[DEBUG] Slack ID: {}", slack_id);
    println!("[DEBUG] Message: {:#?}", message);
    std::io::stdout().flush().unwrap();
    
    match state.slack_client.store_chat_message(slack_id, message).await {
        Ok(response) => {
            println!("[DEBUG] Successfully stored chat message");
            println!("[DEBUG] Response: {:?}", response);
            println!("[DEBUG] ====== Chat Message Handler Complete ======\n");
            std::io::stdout().flush().unwrap();
            Json(response)
        },
        Err(e) => {
            println!("[DEBUG] Error storing chat message: {:?}", e);
            println!("[DEBUG] ====== Chat Message Handler Failed ======\n");
            std::io::stdout().flush().unwrap();
            Json(SlackResponse::error(e))
        }
    }
}

#[axum::debug_handler]
async fn generate_slack_token(
    State(state): State<AppState>,
    Path(slack_id): Path<String>,
) -> Json<SlackResponse<TokenResponse>> {
    println!("\n[DEBUG] ====== Token Generation Request ======");
    println!("[DEBUG] Generating token for Slack ID: {}", slack_id);
    
    match state.slack_client.generate_dashboard_token(slack_id).await {
        Ok(response) => {
            if let Some(token) = response.data {
                println!("[DEBUG] Token generated successfully");
                
                // Clone the token before using it
                let token_clone = token.clone();
                
                // Strip the Candid encoding prefix from the token
                let clean_token = if token_clone.starts_with("DIDL\u{0}\u{1}q,") {
                    token_clone.split("DIDL\u{0}\u{1}q,").nth(1).unwrap_or(&token_clone).to_string()
                } else {
                    token_clone
                };
                
                println!("[DEBUG] Clean token: {}", clean_token);
                let login_url = format!("{}/bot-login?token={}", state.base_url.trim_end_matches('/'), clean_token);
                println!("[DEBUG] Generated login URL: {}", login_url);
                println!("[DEBUG] ====== Token Generation Complete ======\n");
                
                Json(SlackResponse::success(TokenResponse {
                    token,
                    login_url,
                }))
            } else {
                println!("[DEBUG] Token generation failed: No token in response");
                println!("[DEBUG] ====== Token Generation Failed ======\n");
                Json(SlackResponse::error("Failed to generate token".to_string()))
            }
        },
        Err(e) => {
            println!("[DEBUG] Token generation error: {}", e);
            println!("[DEBUG] ====== Token Generation Failed ======\n");
            Json(SlackResponse::error(e))
        }
    }
}

// GitHub endpoints
#[axum::debug_handler]
async fn store_github_connection(
    State(state): State<AppState>,
    Path(slack_id): Path<String>,
    Json(connection): Json<GitHubConnection>,
) -> Json<SlackResponse<()>> {
    match state.slack_client.store_github_connection(
        slack_id,
        connection.token,
        connection.selected_repo,
    ).await {
        Ok(response) => Json(response),
        Err(e) => Json(SlackResponse::error(e)),
    }
}

#[axum::debug_handler]
async fn store_github_issue(
    State(state): State<AppState>,
    Path(slack_id): Path<String>,
    Json(issue): Json<GitHubIssue>,
) -> Json<SlackResponse<()>> {
    println!("\n[DEBUG] ====== GitHub Issue Handler ======");
    println!("[DEBUG] Received request to store GitHub issue");
    println!("[DEBUG] Slack ID: {}", slack_id);
    println!("[DEBUG] GitHub Issue: {:#?}", issue);
    std::io::stdout().flush().unwrap();
    
    match state.slack_client.store_github_issue(slack_id, issue).await {
        Ok(response) => {
            println!("[DEBUG] Successfully stored GitHub issue");
            println!("[DEBUG] Response: {:?}", response);
            println!("[DEBUG] ====== GitHub Issue Handler Complete ======\n");
            std::io::stdout().flush().unwrap();
            Json(response)
        },
        Err(e) => {
            println!("[DEBUG] Error storing GitHub issue: {:?}", e);
            println!("[DEBUG] ====== GitHub Issue Handler Failed ======\n");
            std::io::stdout().flush().unwrap();
            Json(SlackResponse::error(e))
        }
    }
}

#[axum::debug_handler]
async fn update_github_repo(
    State(state): State<AppState>,
    Path(slack_id): Path<String>,
    Json(repo_name): Json<String>,
) -> Json<SlackResponse<()>> {
    match state.slack_client.update_github_selected_repo(slack_id, repo_name).await {
        Ok(response) => Json(response),
        Err(e) => Json(SlackResponse::error(e)),
    }
}

// Project Management endpoints
#[axum::debug_handler]
async fn store_asana_connection(
    State(state): State<AppState>,
    Path(slack_id): Path<String>,
    Json(connection): Json<AsanaConnection>,
) -> Json<SlackResponse<()>> {
    match state.slack_client.store_asana_connection(
        slack_id,
        connection.token,
        connection.workspace_id,
        connection.project_ids,
    ).await {
        Ok(response) => Json(response),
        Err(e) => Json(SlackResponse::error(e)),
    }
}

#[axum::debug_handler]
async fn store_asana_task(
    State(state): State<AppState>,
    Path(slack_id): Path<String>,
    Json(task): Json<AsanaTask>,
) -> Json<SlackResponse<()>> {
    println!("\n[DEBUG] ====== Asana Task Handler ======");
    println!("[DEBUG] Received request to store Asana task");
    println!("[DEBUG] Slack ID: {}", slack_id);
    println!("[DEBUG] Asana Task: {:#?}", task);
    
    match state.slack_client.store_asana_task(slack_id, task).await {
        Ok(response) => {
            println!("[DEBUG] Successfully stored Asana task");
            println!("[DEBUG] Response: {:?}", response);
            println!("[DEBUG] ====== Asana Task Handler Complete ======\n");
            Json(response)
        },
        Err(e) => {
            println!("[DEBUG] Error storing Asana task: {:?}", e);
            println!("[DEBUG] ====== Asana Task Handler Failed ======\n");
            Json(SlackResponse::error(e))
        }
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load .env file
    dotenv().ok();
    
    // Initialize ICP agent
    let url = Url::parse("https://ic0.app")?;
    let agent = create_agent(url, true).await?;
    let canister_id = Principal::from_text(CANISTER_ID)?;
    
    // Create Slack client
    let slack_client = Arc::new(SlackClient::new(Arc::new(agent.clone()), canister_id));
    
    // Get API key and base URL from environment variables
    let api_key = std::env::var("API_KEY")
        .expect("API_KEY must be set in .env file");
    let base_url = std::env::var("BASE_URL")
        .unwrap_or_else(|_| "https://6mce5-laaaa-aaaab-qacsq-cai.icp0.io".to_string());

    // Create app state with API key and base URL
    let app_state = AppState {
        agent: Arc::new(agent),
        canister_id,
        slack_client,
        api_key,
        base_url,
    };
    
    // Build our application with routes
    let app = Router::new()
        .route("/admins", get(get_admins))
        .route("/slack/users/:slack_id", get(get_slack_user))
        .route("/slack/users/:slack_id/register", post(ensure_slack_user))
        .route("/slack/messages/:slack_id", get(get_slack_messages).post(store_slack_message))
        .route("/slack/token/:slack_id", post(generate_slack_token))
        .route("/slack/github/:slack_id/connect", post(store_github_connection))
        .route("/slack/github/:slack_id/issues", post(store_github_issue))
        .route("/slack/github/:slack_id/repo", post(update_github_repo))
        .route("/slack/asana/:slack_id/connect", post(store_asana_connection))
        .route("/slack/asana/:slack_id/tasks", post(store_asana_task))
        .route_layer(middleware::from_fn_with_state(
            Arc::new(app_state.clone()),
            auth_middleware,
        ))
        .layer(CorsLayer::permissive())
        .layer(TraceLayer::new_for_http())
        .with_state(app_state);
    
    // Run it with hyper on localhost:3000
    let addr = SocketAddr::from(([0, 0, 0, 0], 3000));
    println!("Starting server on http://{}", addr);
    
    axum::serve(
        tokio::net::TcpListener::bind(addr).await.unwrap(),
        app.into_make_service()
    )
    .await
    .unwrap();
    
    Ok(())
} 