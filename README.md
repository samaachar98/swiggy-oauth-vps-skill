# swiggy-oauth-vps-skill

Headless-friendly OAuth helper skill for Swiggy MCP on VPS/AWS environments.

This skill is designed for cases where:
- OpenClaw/mcporter runs on a headless server
- OAuth browser callbacks are hard to complete locally
- Access tokens expire and need quick rotation

---

## What this repo contains

- `SKILL.md` — skill instructions for agent usage
- `scripts/swiggy_oauth_manual.py` — PKCE helper script
- `references/token-ops.md` — operational runbook for token rotation

---

## Core flow

1. Generate OAuth URL + PKCE challenge from server
2. Open URL on any device browser (phone/laptop)
3. Paste callback URL (or code) back to script
4. Exchange for tokens immediately

---

## Recommended command (interactive)

```bash
python3 scripts/swiggy_oauth_manual.py interactive --out ~/.swiggy-oauth/latest-token.json
```

Why: authorization codes can expire quickly, so interactive mode reduces delay between login and token exchange.

---

## Other commands

### 1) Two-step init

```bash
python3 scripts/swiggy_oauth_manual.py init
```

### 2) Exchange callback URL/code

```bash
python3 scripts/swiggy_oauth_manual.py exchange \
  --session-file ~/.swiggy-oauth/session-<timestamp>.json \
  --callback-url 'http://127.0.0.1:40701/callback?code=...&state=...'
```

or:

```bash
python3 scripts/swiggy_oauth_manual.py exchange \
  --session-file ~/.swiggy-oauth/session-<timestamp>.json \
  --code '<authorization_code>'
```

---

## Security notes

- Never paste access/refresh tokens in public chats
- Rotate immediately if token leaks
- Prefer AWS SSM/Secrets Manager for storage
- Keep token files `chmod 600`

---

## Token facts

- `expires_in` is in **seconds**
- Example: `432000` = **5 days**
- Refresh token may not always be returned (provider/client policy dependent)

---

## Swiggy MCP endpoints

- `https://mcp.swiggy.com/im`
- `https://mcp.swiggy.com/food`
- `https://mcp.swiggy.com/dineout`

---

## Troubleshooting

- `invalid_grant`: expired/reused code, wrong verifier, redirect URI mismatch
- state mismatch: callback from different auth session
- repeated OAuth prompts in mcporter: client flow/policy may still require full callback auth cache path

---

## License

Use according to your organization/security policy.
