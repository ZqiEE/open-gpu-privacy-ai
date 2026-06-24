# Ailovanta Preview Release Checklist

Goal: make the guest chat MVP safe to share with early users.

## Must stay true

```text
No required login.
No required payment.
No wallet step.
No access lock.
Guest mode first.
```

## Product checks

```text
[ ] /app opens without login.
[ ] User can start typing immediately.
[ ] Send button works.
[ ] Chat response appears.
[ ] Source is shown after response.
[ ] Context message count is shown after response.
[ ] Conversation appears in the list.
[ ] New chat works.
[ ] Load conversation works.
[ ] Delete chat works.
[ ] Copy chat works.
[ ] Clear guest data works.
[ ] Empty conversation list has a clear message.
[ ] API offline state tells the user how to start the API.
```

## Backend checks

```text
[ ] POST /ailovanta/v1/chat works.
[ ] GET /ailovanta/v1/conversations works.
[ ] GET /ailovanta/v1/conversations/{conversation_id}/messages works.
[ ] DELETE /ailovanta/v1/conversations/{conversation_id} works.
[ ] POST /ailovanta/v1/run works.
[ ] POST /v1/chat/completions works.
[ ] GET /reputation/leaderboard works.
[ ] GET /reputation/summary works.
[ ] POST /usage/events works.
[ ] GET /usage/events works.
[ ] GET /usage/summary works.
```

## Quality checks

```text
[ ] python validate.py passes.
[ ] python -m pytest -q passes.
[ ] README matches guest-first direction.
[ ] AUTH_MODEL does not force login.
[ ] PAYMENT_MODEL does not force payment.
[ ] NEXT_STAGE_PRD is still accurate.
[ ] No old access-gate copy is visible.
[ ] No claim says global distributed network is finished.
```

## Manual local run

```bash
python validate.py
python -m pytest -q
uvicorn api.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/app
```

## Release note

Safe public wording:

```text
Ailovanta is a guest-first local MVP for testing persistent AI chat, conversation context, runtime routing primitives, node scheduling, usage records, and reputation endpoints. It does not yet claim a finished global distributed AI network.
```
