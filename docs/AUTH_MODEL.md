# Ailovanta Auth Model

Ailovanta should not use only wallet login, only GitHub login, or only a social login.

The primary product account should be an Ailovanta account.

## Account types

```text
Ailovanta User
- regular chat/API user
- owns conversations, API keys, usage, billing records

Ailovanta Workspace
- team or company account
- owns members, projects, policies, quotas, billing

Ailovanta Node Operator
- user or company that contributes runtime, storage, bandwidth, or validation capacity
- links runtime nodes, payout profile, reputation, and verification records

Ailovanta Admin
- internal operator role
- manages abuse, model registry, node registry, billing, and incidents
```

## Login methods

### Primary login

```text
Email + passwordless magic code/link
```

Reason:

- works globally
- works for normal users and companies
- avoids password storage risk in the early MVP
- easier than forcing Web3 wallets
- easier than forcing GitHub

### Optional login providers

```text
Google OAuth
GitHub OAuth
Apple Sign In
```

Use these as convenience login methods, not as the core identity system.

### Web3 wallet

```text
Wallet connect / EVM / Solana / other chains
```

Wallet should be linked after account creation.

Do not make wallet the only login method.

Wallet is mainly for:

- node operator payout identity
- contribution proof
- reward ledger
- staking / slashing in later phases
- signed ownership checks

## Best default registration flow

```text
1. User enters email
2. Ailovanta sends magic code/link
3. User signs in
4. System creates personal workspace
5. User can create API key
6. User can optionally link Google/GitHub/wallet
7. User can optionally become node operator
```

## Enterprise flow

```text
1. Admin creates workspace
2. Admin verifies company email domain
3. Admin invites members
4. Members join by email or SSO
5. Workspace sets region, quota, model policy, and billing
6. Enterprise can request dedicated runtime pool
```

## Node operator flow

```text
1. User signs in with Ailovanta account
2. User creates node operator profile
3. User links payout identity or wallet
4. User downloads node client
5. Node registers with node token
6. Node starts reporting capability and heartbeat
7. Reputation grows from verified work
```

## Identity hierarchy

```text
User
  -> Workspaces
      -> Projects
          -> API Keys
          -> Conversations
          -> Runtime policies
          -> Usage records
  -> Node operator profile
      -> Runtime nodes
      -> Reputation
      -> Reward records
      -> Payout identity
```

## What not to do

Do not require GitHub login for normal users.

Do not require wallet login for normal users.

Do not let API keys belong only to a personal user. API keys should belong to a project under a workspace.

Do not mix user login token with node runtime token. A human account token and a machine node token are different things.

Do not put private keys, wallet seed phrases, or payout secrets in the Ailovanta database.

## MVP implementation target

The first useful implementation should support:

```text
users
workspaces
workspace_members
projects
api_keys
sessions
node_operator_profiles
node_tokens
```

MVP login can start with local email-code simulation for development. Production should connect a real email provider later.
