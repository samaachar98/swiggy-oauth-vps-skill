---
name: swiggy-oauth-vps
description: Headless-friendly Swiggy MCP OAuth workflow for AWS/VPS environments where the agent has no local browser. Use when Swiggy MCP tools (im/food/dineout) request OAuth repeatedly, token refresh behavior is unclear, or a user needs a manual URL+code exchange flow to mint new access tokens from another device.
---

# Swiggy OAuth VPS

Use this skill to recover or rotate Swiggy MCP tokens from a headless server.

## Quick Workflow

1. Generate OAuth authorize URL + PKCE verifier on VPS.
2. Send URL to user; user authenticates from phone/laptop.
3. User returns callback URL (or `code`) to agent.
4. Exchange code for tokens on VPS.
5. Save token securely and verify MCP access.

## Use Scripted Flow (preferred)

Run either:

```bash
# best for short code TTL (recommended)
python3 scripts/swiggy_oauth_manual.py interactive --out ~/.swiggy-oauth/latest-token.json

# or two-step mode
python3 scripts/swiggy_oauth_manual.py init
```

This prints:
- authorize URL
- `state`
- local `session_file` path

Ask user to open authorize URL and paste back the full callback URL.

Then run:

```bash
python3 scripts/swiggy_oauth_manual.py exchange \
  --session-file <session_file_from_init> \
  --callback-url '<full_callback_url>'
```

Optional (if user pastes code only):

```bash
python3 scripts/swiggy_oauth_manual.py exchange \
  --session-file <session_file_from_init> \
  --code '<authorization_code>'
```

## Security Rules

- Never post access/refresh tokens in public/group chats.
- Rotate immediately if exposed.
- Prefer secret store (AWS SSM/Secrets Manager) over plaintext files.
- Validate `state` before token exchange (script enforces this for callback URL mode).

## Token Expectations

- `expires_in` is seconds. Example: `432000` = 5 days.
- Refresh token may or may not be returned depending on provider/client policy.
- Do not assume non-expiring tokens.

## MCP Integration Notes

- Swiggy endpoints:
  - `https://mcp.swiggy.com/im`
  - `https://mcp.swiggy.com/food`
  - `https://mcp.swiggy.com/dineout`
- If MCP still prompts OAuth after manual token update, provider/client registration policy may require full callback flow through client cache.
- Keep same user/home for OpenClaw + mcporter to preserve auth cache.

## Troubleshooting

- `invalid_grant`: code reused/expired, wrong verifier, or mismatched redirect URI.
- callback timeout: use out-of-band URL+code flow via this script instead of waiting for local loopback callback.
- no refresh token in response: treat as access-token-only lifecycle and schedule proactive re-auth before expiry.

## Resources

- `scripts/swiggy_oauth_manual.py` — generate URL and exchange code for tokens.
- `references/token-ops.md` — operational checklist for rotation and alerts.
