use candid::{CandidType, Encode, Decode, Principal};
use serde::{Serialize, Deserialize};
use anyhow::Result;
use std::sync::Arc;
use ic_agent::Agent;
use std::io::Write;

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
    // pub fn new(role: MessageRole, content: String, timestamp: u64) -> Self {
    //     Self {
    //         id: Principal::anonymous(),
    //         role,
    //         content,
    //         question_asked: None,
    //         timestamp,
    //         bot_name: None,
    //     }
    // }
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

#[derive(CandidType, Debug)]
pub enum UserIdentifier {
    // Principal(Principal),
    // OpenChatId(String),
    SlackId(String),
    // DiscordId(String),
}

#[derive(Debug, Serialize, Deserialize, CandidType)]
pub struct GitHubConnection {
    pub timestamp: Option<u64>,
    pub token: String,
    pub selected_repo: Option<String>
}

#[derive(Debug, Serialize, Deserialize, CandidType)]
pub enum IssueStatus {
    Open,
    Closed,
}

#[derive(Debug, Serialize, Deserialize, CandidType)]
pub struct GitHubIssue {
    pub id: String,
    pub title: String,
    pub body: String,
    pub repository: String,
    pub created_at: u64,
    #[serde(deserialize_with = "deserialize_status")]
    pub status: IssueStatus,
}

fn deserialize_status<'de, D>(deserializer: D) -> Result<IssueStatus, D::Error>
where
    D: serde::Deserializer<'de>,
{
    let s = String::deserialize(deserializer)?;
    match s.to_lowercase().as_str() {
        "open" => Ok(IssueStatus::Open),
        "closed" => Ok(IssueStatus::Closed),
        _ => Ok(IssueStatus::Open), // Default to Open if status is unknown
    }
}

#[derive(Debug, Serialize, Deserialize, CandidType)]
pub struct AsanaConnection {
    pub token: String,
    pub workspace_id: String,
    pub project_ids: Vec<(String, String)>, // (project_id, project_name)
}

#[derive(Debug, Serialize, Deserialize, CandidType)]
pub struct AsanaTask {
    pub id: String,
    pub title: String,
    pub description: String,
    pub status: String,
    pub created_at: u64,
    pub platform: String,    // "asana" or "github"
    pub platform_id: String, // ID of the task in the respective platform
    pub creator: Principal,
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
        println!("\n[DEBUG] ====== Ensuring User Registration ======");
        println!("[DEBUG] SlackClient: Ensuring user registration for Slack ID: {}", slack_id);
        std::io::stdout().flush().unwrap();

        let args = Encode!(&slack_id)
            .map_err(|e| format!("Failed to encode arguments: {}", e))?;

        match self.agent
            .update(&self.canister_id, "ensure_slack_user")
            .with_arg(args)
            .call_and_wait()
            .await
        {
            Ok(_) => {
                println!("[DEBUG] SlackClient: User registration successful");
                std::io::stdout().flush().unwrap();
                Ok(SlackResponse::success(()))
            },
            Err(e) => {
                println!("[DEBUG] SlackClient: User registration failed: {}", e);
                std::io::stdout().flush().unwrap();
                Ok(SlackResponse::error(format!("Failed to register user: {}", e)))
            },
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
        println!("\n[DEBUG] ====== Chat Message Storage Request ======");
        println!("[DEBUG] SlackClient: Starting to store chat message");
        println!("[DEBUG] SlackClient: Slack ID: {}", slack_id);
        println!("[DEBUG] SlackClient: Message: {:#?}", message);
        std::io::stdout().flush().unwrap();

        // First ensure the user is registered
        match self.ensure_user_registered(slack_id.clone()).await {
            Ok(_) => {
                println!("[DEBUG] SlackClient: User is registered");
                let identifier = UserIdentifier::SlackId(slack_id);
                println!("[DEBUG] SlackClient: Using identifier: {:?}", identifier);
                
                let args = Encode!(&identifier, &message)
                    .map_err(|e| format!("Failed to encode arguments: {}", e))?;
                println!("[DEBUG] SlackClient: Encoded arguments successfully");
                println!("[DEBUG] SlackClient: Canister ID: {:?}", self.canister_id);
                
                match self.agent
                    .update(&self.canister_id, "store_chat_message")
                    .with_arg(args)
                    .call_and_wait()
                    .await
                {
                    Ok(_) => {
                        println!("[DEBUG] SlackClient: Successfully called canister");
                        println!("[DEBUG] ====== Chat Message Storage Complete ======\n");
                        std::io::stdout().flush().unwrap();
                        Ok(SlackResponse::success(()))
                    },
                    Err(e) => {
                        println!("[DEBUG] SlackClient: Error calling canister: {}", e);
                        println!("[DEBUG] ====== Chat Message Storage Failed ======\n");
                        std::io::stdout().flush().unwrap();
                        Ok(SlackResponse::error(format!("Failed to store message: {}", e)))
                    },
                }
            },
            Err(e) => {
                println!("[DEBUG] SlackClient: Failed to register user: {}", e);
                println!("[DEBUG] ====== Chat Message Storage Failed ======\n");
                std::io::stdout().flush().unwrap();
                Ok(SlackResponse::error(format!("Failed to register user: {}", e)))
            },
        }
    }

    pub async fn get_messages(&self, slack_id: String) -> Result<SlackResponse<Vec<ChatMessage>>, String> {
        let identifier = UserIdentifier::SlackId(slack_id);
        let args = Encode!(&identifier)
            .map_err(|e| format!("Failed to encode arguments: {}", e))?;

        let response = self.agent
            .query(&self.canister_id, "get_chat_history")
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

    // GitHub Methods
    pub async fn store_github_connection(&self, slack_id: String, token: String, selected_repo: Option<String>) -> Result<SlackResponse<()>, String> {
        // First ensure user is registered
        match self.ensure_user_registered(slack_id.clone()).await {
            Ok(_) => {
                let identifier = UserIdentifier::SlackId(slack_id);
                let args = Encode!(&identifier, &token, &selected_repo)
                    .map_err(|e| format!("Failed to encode arguments: {}", e))?;

                match self.agent
                    .update(&self.canister_id, "store_github_connection")
                    .with_arg(args)
                    .call_and_wait()
                    .await
                {
                    Ok(_) => Ok(SlackResponse::success(())),
                    Err(e) => Ok(SlackResponse::error(format!("Failed to store GitHub connection: {}", e))),
                }
            },
            Err(e) => Ok(SlackResponse::error(format!("Failed to register user: {}", e))),
        }
    }

    pub async fn store_github_issue(&self, slack_id: String, issue: GitHubIssue) -> Result<SlackResponse<()>, String> {
        println!("\n[DEBUG] ====== GitHub Issue Storage Request ======");
        println!("[DEBUG] SlackClient: Starting to store GitHub issue");
        println!("[DEBUG] SlackClient: Slack ID: {}", slack_id);
        println!("[DEBUG] SlackClient: Issue: {:#?}", issue);
        
        // First ensure user is registered
        match self.ensure_user_registered(slack_id.clone()).await {
            Ok(_) => {
                println!("[DEBUG] SlackClient: User is registered");
                let identifier = UserIdentifier::SlackId(slack_id);
                println!("[DEBUG] SlackClient: Using identifier: {:?}", identifier);
                
                let args = Encode!(&identifier, &issue)
                    .map_err(|e| format!("Failed to encode arguments: {}", e))?;
                println!("[DEBUG] SlackClient: Encoded arguments successfully");
                println!("[DEBUG] SlackClient: Canister ID: {:?}", self.canister_id);
                
                match self.agent
                    .update(&self.canister_id, "store_github_issue")
                    .with_arg(args)
                    .call_and_wait()
                    .await
                {
                    Ok(_) => {
                        println!("[DEBUG] SlackClient: Successfully called canister");
                        println!("[DEBUG] ====== GitHub Issue Storage Complete ======\n");
                        Ok(SlackResponse::success(()))
                    },
                    Err(e) => {
                        println!("[DEBUG] SlackClient: Error calling canister: {}", e);
                        println!("[DEBUG] ====== GitHub Issue Storage Failed ======\n");
                        Ok(SlackResponse::error(format!("Failed to store GitHub issue: {}", e)))
                    },
                }
            },
            Err(e) => {
                println!("[DEBUG] SlackClient: Failed to register user: {}", e);
                println!("[DEBUG] ====== GitHub Issue Storage Failed ======\n");
                Ok(SlackResponse::error(format!("Failed to register user: {}", e)))
            },
        }
    }

    pub async fn update_github_selected_repo(&self, slack_id: String, repo_name: String) -> Result<SlackResponse<()>, String> {
        // First ensure user is registered
        match self.ensure_user_registered(slack_id.clone()).await {
            Ok(_) => {
                let identifier = UserIdentifier::SlackId(slack_id);
                let args = Encode!(&identifier, &repo_name)
                    .map_err(|e| format!("Failed to encode arguments: {}", e))?;

                match self.agent
                    .update(&self.canister_id, "update_github_selected_repo")
                    .with_arg(args)
                    .call_and_wait()
                    .await
                {
                    Ok(_) => Ok(SlackResponse::success(())),
                    Err(e) => Ok(SlackResponse::error(format!("Failed to update selected repo: {}", e))),
                }
            },
            Err(e) => Ok(SlackResponse::error(format!("Failed to register user: {}", e))),
        }
    }

    // Project Management Methods
    pub async fn store_asana_connection(&self, slack_id: String, token: String, workspace_id: String, project_ids: Vec<(String, String)>) -> Result<SlackResponse<()>, String> {
        // First ensure user is registered
        match self.ensure_user_registered(slack_id.clone()).await {
            Ok(_) => {
                let identifier = UserIdentifier::SlackId(slack_id);
                let args = Encode!(&identifier, &token, &workspace_id, &project_ids)
                    .map_err(|e| format!("Failed to encode arguments: {}", e))?;

                match self.agent
                    .update(&self.canister_id, "store_asana_connection")
                    .with_arg(args)
                    .call_and_wait()
                    .await
                {
                    Ok(_) => Ok(SlackResponse::success(())),
                    Err(e) => Ok(SlackResponse::error(format!("Failed to store Asana connection: {}", e))),
                }
            },
            Err(e) => Ok(SlackResponse::error(format!("Failed to register user: {}", e))),
        }
    }

    pub async fn store_asana_task(&self, slack_id: String, task: AsanaTask) -> Result<SlackResponse<()>, String> {
        println!("\n[DEBUG] ====== Asana Task Storage Request ======");
        println!("[DEBUG] SlackClient: Starting to store Asana task");
        println!("[DEBUG] SlackClient: Slack ID: {}", slack_id);
        println!("[DEBUG] SlackClient: Task: {:#?}", task);
        
        // First ensure user is registered
        match self.ensure_user_registered(slack_id.clone()).await {
            Ok(_) => {
                println!("[DEBUG] SlackClient: User is registered");
                let identifier = UserIdentifier::SlackId(slack_id);
                println!("[DEBUG] SlackClient: Using identifier: {:?}", identifier);
                
                let args = Encode!(&identifier, &task)
                    .map_err(|e| format!("Failed to encode arguments: {}", e))?;
                println!("[DEBUG] SlackClient: Encoded arguments successfully");
                println!("[DEBUG] SlackClient: Canister ID: {:?}", self.canister_id);
                
                match self.agent
                    .update(&self.canister_id, "store_asana_task")
                    .with_arg(args)
                    .call_and_wait()
                    .await
                {
                    Ok(_) => {
                        println!("[DEBUG] SlackClient: Successfully called canister");
                        println!("[DEBUG] ====== Asana Task Storage Complete ======\n");
                        Ok(SlackResponse::success(()))
                    },
                    Err(e) => {
                        println!("[DEBUG] SlackClient: Error calling canister: {}", e);
                        println!("[DEBUG] ====== Asana Task Storage Failed ======\n");
                        Ok(SlackResponse::error(format!("Failed to store Asana task: {}", e)))
                    },
                }
            },
            Err(e) => {
                println!("[DEBUG] SlackClient: Failed to register user: {}", e);
                println!("[DEBUG] ====== Asana Task Storage Failed ======\n");
                Ok(SlackResponse::error(format!("Failed to register user: {}", e)))
            },
        }
    }
} 