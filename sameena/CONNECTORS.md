# Sameena runtime connector setup

The runtime now separates **planning** from **execution**.

## Security rules
- Never put passwords, OTPs, recovery codes, or access tokens into chat.
- Store secrets in the deployment's encrypted environment/secret manager.
- OAuth is preferred where the provider supports it.
- Irreversible actions (publishing, deleting, sending, charging, etc.) should require confirmation.

## Connector environment variables
- YouTube: `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`
- Shopify: `SHOPIFY_SHOP_DOMAIN`, `SHOPIFY_ACCESS_TOKEN`
- Meta/Instagram: `META_ACCESS_TOKEN`
- Browser service: `BROWSER_AUTOMATION_API_KEY`
- AI: `GEMINI_API_KEY`

The ChatGPT Shopify/Canva connections do **not** automatically expose their credentials to this standalone GitHub application. Sameena needs its own provider authorization/connector when deployed.
