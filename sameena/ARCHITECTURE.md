# Sameena AI — General Agent Foundation

Sameena is being expanded from the existing Vexora Tales YouTube controller into a general action-taking assistant.

## Target flow

User -> Sameena chat -> agent planner -> tool/connector -> external service -> result

## Connector strategy

1. Prefer OAuth / official provider authorization.
2. Use browser automation only where an official API/app action is unavailable.
3. Never put provider passwords, OTPs, recovery codes, or API secrets into chat history.
4. Keep irreversible actions behind explicit approval until the action policy is tested.

## First integrations

- YouTube: upload, scheduling, channel status, analytics.
- Browser automation: websites that have no suitable API.
- Google services: Gmail, Drive, Calendar where the user's account authorization permits them.
- Shopify: store/product tasks.
- Instagram/Meta: supported account actions.
- GitHub: code/repository operations.

## Runtime pieces

- Existing Streamlit chat UI: temporary control surface.
- Agent planner/router: natural-language command interpretation.
- Tool adapters: one adapter per provider.
- Credential/config layer: environment variables or a secure secret store; never hard-code secrets.
- Persistent memory/state: database-backed storage for production.
- Scheduler/worker: recurring jobs and long-running tasks.

## Current status

The existing repository already contains a working YouTube-focused Sameena prototype. This branch is the foundation for expanding it without breaking the existing YouTube workflow.
