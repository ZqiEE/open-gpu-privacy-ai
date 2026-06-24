# Codex Task Plan: v1.11.0 Guest Chat Core

Goal: make Ailovanta usable without login or payment, with persistent guest chat and real conversation context.

## Rules

```text
Do not add required login.
Do not add required payment.
Do not add wallet flow.
Do not remove existing tested endpoints.
Do not break pytest.
```

Always run:

```bash
python validate.py
python -m pytest -q
```

## Task 1: Add conversation context builder

Create:

```text
api/conversation_context.py
```

Implement:

```python
build_chat_context(messages: list[dict], latest_prompt: str, max_messages: int = 12) -> list[dict]
```

Requirements:

```text
Use recent conversation messages.
Keep role/content structure.
Avoid duplicating latest prompt.
Limit to max_messages.
Return list suitable for model adapter use.
```

Add tests:

```text
tests/test_conversation_context.py
```

## Task 2: Use history in /ailovanta/v1/chat

Update:

```text
api/main.py
```

In `/ailovanta/v1/chat`:

```text
get or create conversation
store user message
load recent messages
build context
call model adapter with context
store assistant message
return conversation_id, answer, source, runtime_route
```

Do not break:

```text
/reputation/leaderboard
/reputation/summary
/usage/events
/usage/summary
```

## Task 3: Upgrade frontend chat UX

Update:

```text
index.html
```

Add:

```text
conversation list
new chat button
load conversation
delete conversation
send button disabled while sending
clear visible messages
API status message
```

Keep:

```text
No login required
No payment wall
Guest mode first
```

Add tests:

```text
tests/test_frontend_markers.py
```

## Task 4: Guest flow integration tests

Add:

```text
tests/test_guest_chat_flow.py
```

Test:

```text
POST /ailovanta/v1/chat creates conversation
second POST with same conversation_id keeps same conversation
GET messages returns user and assistant messages
DELETE conversation works
usage summary still works
reputation endpoints still work
```

## Task 5: Update validation markers

Update:

```text
validate.py
```

Validate markers:

```text
Guest mode first
No login required
No payment required
/ailovanta/v1/chat
conversation_context
/reputation/leaderboard
/usage/events
```

## Done criteria

```text
python validate.py passes
python -m pytest -q passes
/app opens
Guest chat sends message
conversation history can be loaded
same conversation understands previous messages
no login wall
no payment wall
```
