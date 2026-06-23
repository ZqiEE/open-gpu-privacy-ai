from __future__ import annotations

import os
from urllib.parse import urlencode

import httpx

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


class GitHubAuthConfigError(RuntimeError):
    pass


def github_oauth_config() -> dict:
    client_id = os.getenv("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    redirect_uri = os.getenv("GITHUB_REDIRECT_URI", "http://127.0.0.1:8000/auth/github/callback")
    if not client_id:
        raise GitHubAuthConfigError("GITHUB_CLIENT_ID is not configured")
    return {"client_id": client_id, "client_secret": client_secret, "redirect_uri": redirect_uri}


def build_github_login_url(state: str) -> str:
    config = github_oauth_config()
    query = urlencode(
        {
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
            "scope": "read:user user:email",
            "state": state,
        }
    )
    return f"{GITHUB_AUTHORIZE_URL}?{query}"


def exchange_code_for_token(code: str) -> str:
    config = github_oauth_config()
    if not config.get("client_secret"):
        raise GitHubAuthConfigError("GITHUB_CLIENT_SECRET is not configured")
    response = httpx.post(
        GITHUB_TOKEN_URL,
        headers={"Accept": "application/json"},
        data={
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "code": code,
            "redirect_uri": config["redirect_uri"],
        },
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise RuntimeError("GitHub did not return access_token")
    return token


def fetch_github_profile(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"}
    user_response = httpx.get(GITHUB_USER_URL, headers=headers, timeout=15)
    user_response.raise_for_status()
    profile = user_response.json()

    if not profile.get("email"):
        try:
            email_response = httpx.get(GITHUB_EMAILS_URL, headers=headers, timeout=15)
            email_response.raise_for_status()
            for email in email_response.json():
                if email.get("primary") and email.get("verified"):
                    profile["email"] = email.get("email")
                    break
        except Exception:
            profile["email"] = None
    return profile
