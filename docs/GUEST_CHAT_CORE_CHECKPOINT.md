# Guest Chat Core Checkpoint

Status: green baseline

This checkpoint locks the current product direction:

```text
Guest mode first.
No required login.
No required payment.
No required wallet.
Open the app and start chatting.
```

## What is now working

```text
/app opens a guest-first chat UI
browser creates guest_id
user can start a chat without login
user can send messages through /ailovanta/v1/chat
conversation_id is saved locally
conversation history is persisted by the backend
conversation list is visible in the UI
user can create a new chat
user can load a previous chat
user can delete a chat
backend uses recent conversation messages for context
Ollama adapter supports chat history messages
fallback does not pretend to be a real model
usage endpoints remain available
reputation endpoints remain available
CI is green for this baseline
```

## Guardrails

Do not reintroduce these into the first-use path:

```text
Login required
Payment required
Wallet required
Access locked
Choose access first
Use paid mode
```

These are intentionally blocked by regression tests.

## Important files

```text
index.html
api/main.py
api/conversation_context.py
api/conversation_store.py
api/ollama_adapter.py
docs/NEXT_STAGE_PRD.md
docs/NEXT_STAGE_CODEX_TASKS.md
docs/AUTH_MODEL.md
docs/PAYMENT_MODEL.md
tests/test_conversation_context.py
tests/test_guest_chat_flow.py
tests/test_frontend_markers.py
tests/test_no_gate_regression.py
```

## Manual verification

Run:

```bash
python validate.py
python -m pytest -q
uvicorn api.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/app
```

Verify:

```text
1. Chat page opens without login.
2. Chat page does not ask for payment.
3. guest_id appears in Guest Session.
4. User can send a message.
5. Response appears.
6. Conversation appears in the conversation list.
7. Refresh page.
8. Conversation can be loaded again.
9. Delete chat removes it from the list.
```

## Next perfection pass

Only after this baseline is stable, improve:

```text
real streaming output
better chat layout spacing
mobile polish
better empty states
conversation title editing
local Ollama connected indicator
export conversation
one-click wipe guest data
```

Do not add login or payment before users prove they want saved identity, sync, API keys, teams, or paid capacity.
