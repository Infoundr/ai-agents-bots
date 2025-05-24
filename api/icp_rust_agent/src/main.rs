use anyhow::Result;
use url::Url;
use ic_agent::Agent;
use candid::Principal;
use candid::{Encode, Decode};
use axum::{
    routing::get,
    Router,
    Json,
    extract::State,
};
use std::sync::Arc;
use serde::{Serialize, Deserialize};
use std::net::SocketAddr;

const CANISTER_ID: &str = "g7ko2-fyaaa-aaaam-qdlea-cai";

#[derive(Clone)]
struct AppState {
    agent: Arc<Agent>,
    canister_id: Principal,
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

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize ICP agent
    let url = Url::parse("https://ic0.app")?;
    let agent = create_agent(url, true).await?;
    let canister_id = Principal::from_text(CANISTER_ID)?;
    
    // Create shared state
    let state = AppState {
        agent: Arc::new(agent),
        canister_id,
    };
    
    // Build our application with a route
    let app = Router::new()
        .route("/admins", get(get_admins))
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