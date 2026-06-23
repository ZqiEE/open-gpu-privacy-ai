# Ailovanta Payment Model

Ailovanta should separate customer payments from node payouts.

Do not make crypto the primary payment method for normal customers.

## Payment roles

```text
Customer payment
- user pays Ailovanta for chat, API usage, workspace seats, or enterprise runtime

Workspace billing
- company pays for projects, members, quotas, usage, and dedicated runtime pool

Node payout
- Ailovanta pays node operators for verified runtime, storage, bandwidth, or validation work

Reward ledger
- records contribution, proof, score, reputation, and later tokenized rewards
```

## Best customer payment methods

### MVP customer payments

Use normal SaaS payments first:

```text
Card
Apple Pay / Google Pay where supported
Local payment methods where supported
Bank transfer for enterprise invoices
```

This is the fastest path for real users and companies.

### Global billing provider

Ailovanta should start with a mature payment provider instead of building payment rails.

Recommended early choices:

```text
Stripe Billing
Paddle Billing / Merchant of Record option
```

Use Stripe when Ailovanta wants more control over the payment stack.

Use Paddle-style merchant-of-record billing when Ailovanta wants tax and SaaS billing handled by the provider.

## Payment products

```text
Free plan
- limited daily messages
- limited local demo usage

Pro plan
- monthly subscription
- higher message quota
- higher API quota

Developer plan
- usage-based API credits
- project API keys
- runtime route history

Team plan
- workspace members
- shared projects
- team billing

Enterprise plan
- invoice / bank transfer
- custom contract
- region policy
- dedicated runtime pool
- support SLA

Node operator payout
- separate payout profile
- payout identity / wallet link
- node reputation records
```

## What wallet is for

Wallet should not be the default user payment method.

Wallet should be used for:

```text
node operator identity
reward records
contribution proof
future staking / slashing
optional crypto payout
optional ecosystem credits
```

## What wallet is not for

```text
Do not force normal chat users to pay with crypto.
Do not force enterprise users to pay with crypto.
Do not store seed phrases or private keys.
Do not mix wallet identity with human login token.
Do not use a token before the product has real demand.
```

## Best billing architecture

```text
User
  -> Workspace
      -> Project
          -> API Keys
          -> Usage Events
          -> Credits
          -> Invoices
          -> Payment Customer ID

Node Operator
  -> Runtime Nodes
  -> Work Receipts
  -> Reputation
  -> Payout Profile
  -> Reward Records
```

## MVP tables

```text
billing_customers
plans
subscriptions
usage_events
credit_balances
invoices
payment_events
node_payout_profiles
node_reward_records
```

## Revenue model

Ailovanta should support three billing modes:

```text
Subscription
- monthly plan for normal users and small teams

Usage-based credits
- API usage and runtime usage

Enterprise invoice
- custom contract, dedicated runtime pool, region controls
```

## Payment flow

```text
1. User creates Ailovanta account
2. System creates personal workspace
3. User selects plan or buys credits
4. Payment provider handles checkout
5. Webhook confirms payment
6. Ailovanta updates subscription or credit balance
7. API usage consumes quota or credits
8. Invoices and usage events stay attached to workspace/project
```

## Node payout flow

```text
1. Node operator signs in
2. Operator creates payout profile
3. Operator links payout method or wallet
4. Node completes verified work
5. Ailovanta records work receipt
6. Reputation updates
7. Reward balance updates
8. Payout happens on a scheduled cycle
```

## Mobile app rule

If Ailovanta sells digital AI subscriptions inside iOS or Android apps, app store payment rules may apply.

The safest MVP path is:

```text
Web checkout first
Mobile app login second
Enterprise web billing separately
```

## Final principle

Customer payments should be boring and reliable.

Node rewards can be innovative.

```text
Users pay with normal money.
Companies pay by card or invoice.
Nodes earn through verified contribution records.
Wallets are optional identity and payout links, not the default product checkout.
```
