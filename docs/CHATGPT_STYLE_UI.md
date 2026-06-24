# ChatGPT-style UI Preview

Status: implemented as the default `/app` experience.

## What changed

The app is now shaped like a real chat product rather than a mixed landing page and demo panel.

```text
Left sidebar: conversations and guest controls
Main area: message stream
Bottom area: sticky composer
Top bar: current status and model context
```

## User-facing behavior

```text
Open /app
See a ChatGPT-style app shell
No login required
No payment required
Guest mode first
Type into the composer
Press Enter to send
Use Shift+Enter for a new line
See Thinking... while the backend responds
See source and context count after response
Load previous conversations from the sidebar
Copy chat
Delete chat
Clear guest data
```

## UI markers

```text
Ailovanta Chat
Message Ailovanta
How can I help?
conversationList
composer
Enter to send
Shift+Enter
Thinking...
Model adapter
Fallback: enabled
```

## Technical notes

The current UI is intentionally a single-file app in `index.html` so it can run with only:

```bash
uvicorn api.main:app --reload
```

No Node.js, no Next.js, and no frontend build step are required for this preview.

## Next UI upgrades

```text
true streaming response
message-level copy button
regenerate response
stop generating
conversation rename
markdown table support
light/dark theme toggle
mobile sidebar drawer
```

## Guardrail

Do not add login, payment, wallet, or access-lock steps before the first chat.
