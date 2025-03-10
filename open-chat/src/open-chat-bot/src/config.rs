use serde::Deserialize;
use std::fs;
use tracing::Level;

#[derive(Deserialize, Debug)]
pub struct Config {
    pub pem_file: String,
    pub ic_url: String,
    pub oc_public_key: String,
    pub port: u16,
    pub python_api_url: String,
    #[serde(with = "LevelDef")]
    pub log_level: Level,
}

#[derive(Deserialize)]
#[serde(remote = "Level")]
enum LevelDef {
    TRACE,
    DEBUG,
    INFO,
    WARN,
    ERROR,
}

impl Config {
    pub fn from_file(path: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let content = fs::read_to_string(path)?;
        let config: Config = toml::from_str(&content)?;
        Ok(config)
    }
} 