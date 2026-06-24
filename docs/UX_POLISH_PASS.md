# Guest Chat UX Polish Pass

Status: next refinement pass after green baseline

The green baseline is working. This pass improves the user experience without adding login, payment, wallet, or any first-use barrier.

## Product rules

```text
Do not require login.
Do not require payment.
Do not require wallet.
Do not block first chat.
Do not make users understand infrastructure before chatting.
```

## P0 polish items

### 1. Better empty states

Current conversation list should not feel broken when empty.

Expected empty state:

```text
No conversations yet. Start a new guest chat.
```

Expected API-offline state:

```text
Could not load conversations. Start the API with:
uvicorn api.main:app --reload
```

### 2. Clear API status

The guest panel should make local runtime state obvious:

```text
API online
API offline
Fallback mode
Ollama connected later
```

### 3. Export conversation

Add a user-facing action:

```text
Export chat
```

Minimum acceptable behavior:

```text
fetch /ailovanta/v1/conversations/{conversation_id}/messages
render plain text
let the browser download or copy it
```

### 4. Clear guest data

Add a user-facing action:

```text
Clear guest data
```

Minimum acceptable behavior:

```text
remove local guest_id
remove local conversation_id
clear visible messages
refresh conversation list
show a fresh guest session
```

Server-side deletion of every old conversation can be added later. The first safe version can clear local browser state only.

### 5. Better sending state

While sending:

```text
button disabled
button text = Sending...
status = Sending...
```

After response:

```text
show source
show context_messages_used
refresh conversation list
```

## P1 polish items

```text
conversation title editing
mobile spacing pass
keyboard shortcut hints
copy message button
streaming output
local model connected indicator
```

## Regression checks

Keep these tests or equivalent checks:

```text
No login required
No payment required
Guest mode first
conversationList
/ailovanta/v1/chat
context_messages_used
```

Do not bring back:

```text
Choose access first
Access: locked
Use paid mode
Login required
Payment required
```

## Done criteria

```text
python validate.py passes
python -m pytest -q passes
/app opens
user can chat without login
history can be loaded
conversation can be removed
no login or payment wall appears
```
