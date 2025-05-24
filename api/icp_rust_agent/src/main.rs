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
};
use std::sync::Arc;
use serde::Serialize;
use std::net::SocketAddr;

mod slack;
use slack::{SlackClient, SlackUser, ChatMessage, SlackResponse, MessageRole};

// const CANISTER_ID: &str = "g7ko2-fyaaa-aaaam-qdlea-cai"; // mainnet
const CANISTER_ID: &str = "4dz5m-uyaaa-aaaab-qac6a-cai"; // testnet

#[derive(Clone)]
struct AppState {
    agent: Arc<Agent>,
    canister_id: Principal,
    slack_client: Arc<SlackClient>,
}

#[derive(Serialize)]
struct AdminResponse {
    admins: Vec<String>,
}

// Initializing the agent
pub async fn create_agent(url: Url, use_mainnet: bool) -> Result<Agent> {
    let agent = Agent::builder().with_url(url).build()?;
    if use_mainnet {
        agent.fetch_root_key().await?;
    }
    Ok(agent)
}

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
async fn ensure_slack_user(
    State(state): State<AppState>,
    Path(slack_id): Path<String>,
) -> Json<SlackResponse<()>> {
    match state.slack_client.ensure_user_registered(slack_id).await {
        Ok(response) => Json(response),
        Err(e) => Json(SlackResponse::error(e)),
    }
}

async fn get_slack_user(
    State(state): State<AppState>,
    Path(slack_id): Path<String>,
) -> Json<SlackResponse<Option<SlackUser>>> {
    match state.slack_client.get_user(slack_id).await {
        Ok(response) => Json(response),
        Err(e) => Json(SlackResponse::error(e)),
    }
}

async fn get_slack_messages(
    State(state): State<AppState>,
    Path(slack_id): Path<String>,
) -> Json<SlackResponse<Vec<ChatMessage>>> {
    match state.slack_client.get_messages(slack_id).await {
        Ok(response) => Json(response),
        Err(e) => Json(SlackResponse::error(e)),
    }
}

async fn store_slack_message(
    State(state): State<AppState>,
    Path(slack_id): Path<String>,
    Json(message): Json<ChatMessage>,
) -> Json<SlackResponse<()>> {
    match state.slack_client.store_chat_message(slack_id, message).await {
        Ok(response) => Json(response),
        Err(e) => Json(SlackResponse::error(e)),
    }
}

async fn generate_slack_token(
    State(state): State<AppState>,
    Path(slack_id): Path<String>,
) -> Json<SlackResponse<String>> {
    match state.slack_client.generate_dashboard_token(slack_id).await {
        Ok(response) => Json(response),
        Err(e) => Json(SlackResponse::error(e)),
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize ICP agent
    let url = Url::parse("https://ic0.app")?;
    let agent = create_agent(url, true).await?;
    let canister_id = Principal::from_text(CANISTER_ID)?;
    
    // Create Slack client
    let slack_client = Arc::new(SlackClient::new(Arc::new(agent.clone()), canister_id));
    
    // Create shared state
    let state = AppState {
        agent: Arc::new(agent),
        canister_id,
        slack_client,
    };
    
    // Build our application with routes
    let app = Router::new()
        .route("/admins", get(get_admins))
        .route("/slack/users/:slack_id", get(get_slack_user))
        .route("/slack/users/:slack_id/register", post(ensure_slack_user))
        .route("/slack/messages/:slack_id", get(get_slack_messages).post(store_slack_message))
        .route("/slack/token/:slack_id", post(generate_slack_token))
        .with_state(state);
    
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