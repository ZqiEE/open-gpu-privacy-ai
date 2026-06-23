# GitHub Auth Setup

Current MVP login method:

```text
GitHub OAuth only
```

## GitHub OAuth app

Create a GitHub OAuth App and set callback URL to:

```text
http://127.0.0.1:8000/auth/github/callback
```

## Environment variables

```bash
export GITHUB_CLIENT_ID="your_client_id"
export GITHUB_CLIENT_SECRET="your_client_secret"
export GITHUB_REDIRECT_URI="http://127.0.0.1:8000/auth/github/callback"
```

Windows PowerShell:

```powershell
$env:GITHUB_CLIENT_ID="your_client_id"
$env:GITHUB_CLIENT_SECRET="your_client_secret"
$env:GITHUB_REDIRECT_URI="http://127.0.0.1:8000/auth/github/callback"
```

## Start API

```bash
uvicorn api.main:app --reload
```

## Login flow

Open:

```text
http://127.0.0.1:8000/auth/github/login
```

The API returns a GitHub login URL. Open that URL, authorize the app, and GitHub will redirect to:

```text
/auth/github/callback
```

The callback returns a local Ailovanta session token.

## Use session

```text
Authorization: Bearer sess_xxx
```

Check current user:

```text
GET /auth/me
```

Logout:

```text
POST /auth/logout
```

## Local database

Auth data is stored in:

```text
runtime_data/auth.sqlite3
```

Tables:

```text
auth_states
users
sessions
```
