use candid::{CandidType, Encode, Decode, Principal};
use serde::{Serialize, Deserialize};
use anyhow::Result;
use std::sync::Arc;
use ic_agent::Agent;

#[derive(Debug, Serialize, Deserialize, CandidType)]
pub struct SlackUser {
    pub slack_id: String,
    pub site_principal: Option<Principal>,
    pub display_name: Option<String>,
    pub team_id: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, CandidType)]
pub enum MessageRole {
    User,
    Assistant,
}

#[derive(Debug, Serialize, Deserialize, CandidType)]
pub struct ChatMessage {
    pub id: Principal,
    pub role: MessageRole,
    pub content: String,
    pub question_asked: Option<String>,
    pub timestamp: u64,
    pub bot_name: Option<String>,
}

impl ChatMessage {
    pub fn new(role: MessageRole, content: String, timestamp: u64) -> Self {
        Self {
            id: Principal::anonymous(),
            role,
            content,
            question_asked: None,
            timestamp,
            bot_name: None,
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SlackResponse<T> {
    pub success: bool,
    pub data: Option<T>,
    pub error: Option<String>,
}

impl<T> SlackResponse<T> {
    pub fn success(data: T) -> Self {
        Self {
            success: true,
            data: Some(data),
            error: None,
        }
    }

    pub fn error(error: String) -> Self {
        Self {
            success: false,
            data: None,
            error: Some(error),
        }
    }
}

#[derive(CandidType)]
pub enum UserIdentifier {
    Principal(Principal),
    OpenChatId(String),
    SlackId(String),
    DiscordId(String),
}

pub struct SlackClient {
    agent: Arc<Agent>,
    canister_id: Principal,
}

impl SlackClient {
    pub fn new(agent: Arc<Agent>, canister_id: Principal) -> Self {
        Self {
            agent,
            canister_id,
        }
    }

    pub async fn ensure_user_registered(&self, slack_id: String) -> Result<SlackResponse<()>, String> {
        let args = Encode!(&slack_id)
            .map_err(|e| format!("Failed to encode arguments: {}", e))?;

        match self.agent
            .update(&self.canister_id, "ensure_slack_user")
            .with_arg(args)
            .call_and_wait()
            .await
        {
            Ok(_) => Ok(SlackResponse::success(())),
            Err(e) => Ok(SlackResponse::error(format!("Failed to register user: {}", e))),
        }
    }

    pub async fn get_user(&self, slack_id: String) -> Result<SlackResponse<Option<SlackUser>>, String> {
        let args = Encode!(&slack_id)
            .map_err(|e| format!("Failed to encode arguments: {}", e))?;

        let response = self.agent
            .query(&self.canister_id, "get_slack_user")
            .with_arg(args)
            .call()
            .await
            .map_err(|e| format!("Failed to get user: {}", e))?;

        let user: Option<SlackUser> = Decode!(&response, Option<SlackUser>)
            .map_err(|e| format!("Failed to decode response: {}", e))?;

        Ok(SlackResponse::success(user))
    }

    pub async fn store_chat_message(&self, slack_id: String, message: ChatMessage) -> Result<SlackResponse<()>, String> {
        let identifier = UserIdentifier::SlackId(slack_id);
        let args = Encode!(&identifier, &message)
            .map_err(|e| format!("Failed to encode arguments: {}", e))?;

        match self.agent
            .update(&self.canister_id, "store_chat_message")
            .with_arg(args)
            .call_and_wait()
            .await
        {
            Ok(_) => Ok(SlackResponse::success(())),
            Err(e) => Ok(SlackResponse::error(format!("Failed to store message: {}", e))),
        }
    }

    pub async fn get_messages(&self, slack_id: String) -> Result<SlackResponse<Vec<ChatMessage>>, String> {
        let args = Encode!(&slack_id)
            .map_err(|e| format!("Failed to encode arguments: {}", e))?;

        let response = self.agent
            .query(&self.canister_id, "get_chat_messages")
            .with_arg(args)
            .call()
            .await
            .map_err(|e| format!("Failed to get messages: {}", e))?;

        let messages: Vec<ChatMessage> = Decode!(&response, Vec<ChatMessage>)
            .map_err(|e| format!("Failed to decode response: {}", e))?;

        Ok(SlackResponse::success(messages))
    }

    pub async fn generate_dashboard_token(&self, slack_id: String) -> Result<SlackResponse<String>, String> {
        let args = Encode!(&slack_id)
            .map_err(|e| format!("Failed to encode arguments: {}", e))?;

        let response = self.agent
            .update(&self.canister_id, "generate_dashboard_token")
            .with_arg(args)
            .call_and_wait()
            .await
            .map_err(|e| format!("Failed to generate token: {}", e))?;

        let token = String::from_utf8(response)
            .map_err(|e| format!("Failed to decode token: {}", e))?;

        Ok(SlackResponse::success(token))
    }
} 