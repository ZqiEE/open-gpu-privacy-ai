# UI Validation Contract

Status: active

`validate.py` now validates the app UI as a structural contract instead of relying on fragile copy-only markers.

## Stable product contract

The `/app` HTML must declare these first-use rules on the body element:

```html
<body
  data-app="ailovanta-chat"
  data-guest-mode="true"
  data-login-required="false"
  data-payment-required="false"
  data-wallet-required="false"
>
```

These attributes are the stable contract. Visible copy can change, but these rules must not change without an intentional product decision.

## Required UI regions

The page must keep these `data-region` values:

```text
conversation-sidebar
conversation-list
guest-session
chat-main
status-bar
message-stream
composer-wrap
composer
api-status
```

## Required user actions

The page must keep these `data-action` values:

```text
new-chat
refresh-conversations
reset-guest
clear-guest-data
copy-chat
clear-view
delete-chat
send-message
```

## Required element ids

The page must keep these ids because JavaScript, tests, and product behavior rely on them:

```text
conversationList
guestBox
messages
prompt
send
copyChat
clear
deleteChat
clearGuestData
apiStatus
apiDot
modelLabel
contextLabel
chatStatus
newChat
refreshChats
```

## Why this exists

Before this contract, CI could fail because a visible phrase changed from `guest mode` to another equivalent wording. That was too brittle for product iteration.

Now CI checks structure and product rules:

```text
guest-first remains true
login remains not required
payment remains not required
wallet remains not required
ChatGPT-style shell still has the required regions and actions
frontend still calls the required backend APIs
```

## Rule for future UI edits

You may change wording, spacing, colors, and layout details.

Do not remove or rename `data-*` contract attributes, required ids, required data regions, or required actions unless `validate.py` is intentionally updated in the same commit.
