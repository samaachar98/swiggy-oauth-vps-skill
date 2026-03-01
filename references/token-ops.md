# Token Ops Checklist (Swiggy MCP)

## Rotation

1. Run `python3 scripts/swiggy_oauth_manual.py init`.
2. Open printed URL on any available browser device.
3. Paste callback URL back to operator.
4. Exchange with `exchange` command and save output to secure path.
5. Update runtime secret/env used by OpenClaw/mcporter.
6. Verify with a harmless MCP tool/list call.

## Expiry Handling

- Compute `expiry_at = issued_at + expires_in`.
- Alert at T-24h and T-6h.
- Re-auth before expiry if no refresh token exists.

## Security

- Never paste tokens in chat.
- Revoke/rotate immediately if exposed.
- Store secrets in AWS SSM/Secrets Manager when possible.
- Restrict file permissions: `chmod 600`.
