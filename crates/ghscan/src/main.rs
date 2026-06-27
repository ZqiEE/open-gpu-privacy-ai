use anyhow::{anyhow, Context, Result};
use clap::Parser;
use reqwest::blocking::Client;
use reqwest::header::{HeaderMap, HeaderValue, ACCEPT, AUTHORIZATION, USER_AGENT};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::thread;
use std::time::Duration;

#[derive(Parser, Debug)]
#[command(author, version, about = "Ailovanta GitHub discovery and sync tool")]
struct Args {
    #[arg(long)]
    token: Option<String>,

    #[arg(long, default_value = "python,typescript,javascript,rust,go")]
    languages: String,

    #[arg(long, default_value = "mit,apache-2.0,bsd-3-clause,bsd-2-clause,isc")]
    licenses: String,

    #[arg(long, default_value_t = 20)]
    min_stars: u32,

    #[arg(long, default_value = "2024-01-01")]
    pushed_after: String,

    #[arg(long, default_value_t = 2)]
    pages_per_query: u32,

    #[arg(long, default_value_t = 50)]
    per_page: u32,

    #[arg(long, default_value = "runtime_data/input_cache")]
    cache_dir: PathBuf,

    #[arg(long, default_value = "runtime_data/input_list.json")]
    out: PathBuf,

    #[arg(long, default_value = "github_public_permissive_v1")]
    rights_id: String,

    #[arg(long, default_value_t = false)]
    no_clone: bool,
}

#[derive(Debug, Deserialize)]
struct SearchResponse {
    items: Vec<RepoItem>,
}

#[derive(Debug, Deserialize)]
struct RepoItem {
    full_name: String,
    clone_url: String,
    html_url: String,
    stargazers_count: u32,
    language: Option<String>,
    fork: bool,
    archived: bool,
    size: u64,
    license: Option<RepoLicense>,
}

#[derive(Debug, Deserialize)]
struct RepoLicense {
    key: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct InputItem {
    repo_id: String,
    repo_url: String,
    rights_id: String,
    status: String,
    local_path: String,
    license: String,
    language: String,
    stars: u32,
}

fn main() -> Result<()> {
    let args = Args::parse();
    let token = args.token.or_else(|| std::env::var("GITHUB_TOKEN").ok());
    let client = build_client(token.as_deref())?;
    fs::create_dir_all(&args.cache_dir)?;

    let languages = split_csv(&args.languages);
    let licenses = split_csv(&args.licenses);
    let mut found: Vec<InputItem> = Vec::new();

    for language in languages {
        for license in &licenses {
            for page in 1..=args.pages_per_query {
                let query = format!(
                    "language:{} license:{} stars:>{} pushed:>{} fork:false archived:false",
                    language, license, args.min_stars, args.pushed_after
                );
                let response = search_page(&client, &query, page, args.per_page)?;
                for repo in response.items {
                    if repo.fork || repo.archived || repo.size > 250_000 {
                        continue;
                    }
                    let license_key = repo.license.map(|l| l.key).unwrap_or_default();
                    if license_key.is_empty() {
                        continue;
                    }
                    let repo_id = safe_name(&repo.full_name);
                    let local_path = args.cache_dir.join(&repo_id);
                    if !args.no_clone {
                        sync_repo(&repo.clone_url, &local_path)?;
                    }
                    found.push(InputItem {
                        repo_id,
                        repo_url: repo.html_url,
                        rights_id: args.rights_id.clone(),
                        status: "active".to_string(),
                        local_path: local_path.to_string_lossy().to_string(),
                        license: license_key,
                        language: repo.language.unwrap_or_else(|| language.clone()),
                        stars: repo.stargazers_count,
                    });
                }
                thread::sleep(Duration::from_millis(1200));
            }
        }
    }

    let merged = merge_existing(&args.out, found)?;
    write_json(&args.out, &merged)?;
    println!(
        "{}",
        serde_json::json!({"ok": true, "items": merged.len(), "out": args.out})
    );
    Ok(())
}

fn build_client(token: Option<&str>) -> Result<Client> {
    let mut headers = HeaderMap::new();
    headers.insert(USER_AGENT, HeaderValue::from_static("ailovanta-ghscan"));
    headers.insert(ACCEPT, HeaderValue::from_static("application/vnd.github+json"));
    if let Some(token) = token {
        let value = format!("Bearer {}", token);
        headers.insert(AUTHORIZATION, HeaderValue::from_str(&value)?);
    }
    Ok(Client::builder().default_headers(headers).build()?)
}

fn search_page(client: &Client, query: &str, page: u32, per_page: u32) -> Result<SearchResponse> {
    let url = format!(
        "https://api.github.com/search/repositories?q={}&sort=stars&order=desc&page={}&per_page={}",
        encode_query(query), page, per_page
    );
    let resp = client.get(url).send()?;
    if !resp.status().is_success() {
        return Err(anyhow!("GitHub search failed: {}", resp.status()));
    }
    Ok(resp.json()?)
}

fn sync_repo(url: &str, target: &Path) -> Result<()> {
    if target.exists() {
        let status = Command::new("git")
            .args(["-C", target.to_str().unwrap_or_default(), "pull", "--ff-only"])
            .status()
            .context("git pull failed to start")?;
        if !status.success() {
            return Err(anyhow!("git pull failed"));
        }
    } else {
        let status = Command::new("git")
            .args(["clone", "--depth", "1", url, target.to_str().unwrap_or_default()])
            .status()
            .context("git clone failed to start")?;
        if !status.success() {
            return Err(anyhow!("git clone failed"));
        }
    }
    Ok(())
}

fn merge_existing(path: &Path, new_items: Vec<InputItem>) -> Result<Vec<InputItem>> {
    let mut items: Vec<InputItem> = if path.exists() {
        serde_json::from_str(&fs::read_to_string(path)?)?
    } else {
        Vec::new()
    };
    for item in new_items {
        if !items.iter().any(|existing| existing.repo_id == item.repo_id) {
            items.push(item);
        }
    }
    Ok(items)
}

fn write_json(path: &Path, items: &[InputItem]) -> Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(path, serde_json::to_string_pretty(items)?)?;
    Ok(())
}

fn split_csv(value: &str) -> Vec<String> {
    value
        .split(',')
        .map(|item| item.trim().to_lowercase())
        .filter(|item| !item.is_empty())
        .collect()
}

fn safe_name(value: &str) -> String {
    value
        .chars()
        .map(|ch| if ch.is_ascii_alphanumeric() { ch } else { '_' })
        .collect::<String>()
        .trim_matches('_')
        .to_string()
}

fn encode_query(value: &str) -> String {
    value
        .bytes()
        .flat_map(|b| match b {
            b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'-' | b'_' | b'.' | b'~' => vec![b as char],
            b' ' => vec!['+'],
            _ => format!("%{:02X}", b).chars().collect(),
        })
        .collect()
}
