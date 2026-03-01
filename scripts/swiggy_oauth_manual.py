#!/usr/bin/env python3
"""
Headless Swiggy OAuth helper.

Commands:
  init         -> create PKCE session + print authorize URL
  exchange     -> exchange callback URL or code for tokens
  interactive  -> run init + wait for callback/code + immediate exchange
"""

import argparse
import base64
import hashlib
import json
import os
import secrets
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

try:
    import requests
except ImportError:
    print("Missing dependency: requests. Install with: pip install -r requirements.txt", file=sys.stderr)
    raise

AUTH_BASE = "https://mcp.swiggy.com/auth"
DEFAULT_CLIENT_ID = "swiggy-mcp"
DEFAULT_SCOPE = "mcp:tools"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:40701/callback"
SESS_DIR = Path.home() / ".swiggy-oauth"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def generate_verifier() -> str:
    return b64url(os.urandom(32))


def challenge_from_verifier(verifier: str) -> str:
    return b64url(hashlib.sha256(verifier.encode()).digest())


def parse_code_from_callback(callback_url: str) -> str:
    parsed = urlparse(callback_url.strip())
    params = parse_qs(parsed.query)
    codes = params.get("code")
    if not codes:
        raise ValueError("No code found in callback URL")
    return codes[0]


def parse_state_from_callback(callback_url: str) -> str:
    parsed = urlparse(callback_url.strip())
    params = parse_qs(parsed.query)
    vals = params.get("state")
    return vals[0] if vals else ""


def cmd_init(args: argparse.Namespace) -> int:
    verifier = generate_verifier()
    challenge = challenge_from_verifier(verifier)
    state = secrets.token_urlsafe(16)

    query = {
        "response_type": "code",
        "client_id": args.client_id,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "redirect_uri": args.redirect_uri,
        "state": state,
        "scope": args.scope,
    }
    auth_url = f"{AUTH_BASE}/authorize?{urlencode(query)}"

    SESS_DIR.mkdir(parents=True, exist_ok=True)
    session = {
        "created_at": int(time.time()),
        "client_id": args.client_id,
        "redirect_uri": args.redirect_uri,
        "scope": args.scope,
        "state": state,
        "code_verifier": verifier,
    }
    session_file = SESS_DIR / f"session-{int(time.time())}.json"
    session_file.write_text(json.dumps(session, indent=2), encoding="utf-8")

    print("=" * 72)
    print("STEP 1: OPEN THIS URL IN ANY BROWSER (PHONE/LAPTOP)")
    print("=" * 72)
    print(auth_url)
    print("\nSTATE:", state)
    print("SESSION_FILE:", session_file)
    print("=" * 72)
    return 0


def load_session(session_file: str) -> dict:
    p = Path(session_file)
    if not p.exists():
        raise FileNotFoundError(f"session file not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def exchange_code(session: dict, code: str) -> dict:
    token_resp = requests.post(
        f"{AUTH_BASE}/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": session["client_id"],
            "redirect_uri": session["redirect_uri"],
            "code_verifier": session["code_verifier"],
        },
        timeout=30,
    )

    if token_resp.status_code != 200:
        raise RuntimeError(f"token exchange failed: {token_resp.status_code} {token_resp.text}")

    tok = token_resp.json()
    return {
        "token_type": tok.get("token_type"),
        "expires_in": tok.get("expires_in"),
        "access_token": tok.get("access_token", ""),
        "refresh_token": tok.get("refresh_token", ""),
        "issued_at": int(time.time()),
    }


def save_or_print_tokens(out: dict, out_path_raw: str) -> None:
    if out_path_raw:
        out_path = Path(out_path_raw)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"saved tokens to {out_path}")
    else:
        print(json.dumps(out, indent=2))


def cmd_exchange(args: argparse.Namespace) -> int:
    try:
        session = load_session(args.session_file)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 2

    code = args.code
    if args.callback_url:
        code = parse_code_from_callback(args.callback_url)
        cb_state = parse_state_from_callback(args.callback_url)
        if cb_state and cb_state != session.get("state"):
            print("state mismatch; aborting", file=sys.stderr)
            return 3

    if not code:
        print("provide --callback-url or --code", file=sys.stderr)
        return 2

    try:
        out = exchange_code(session, code)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 4

    save_or_print_tokens(out, args.out)
    return 0


def cmd_interactive(args: argparse.Namespace) -> int:
    # Run init-like flow and immediately ask for callback/code to reduce code-expiry risk.
    verifier = generate_verifier()
    challenge = challenge_from_verifier(verifier)
    state = secrets.token_urlsafe(16)

    query = {
        "response_type": "code",
        "client_id": args.client_id,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "redirect_uri": args.redirect_uri,
        "state": state,
        "scope": args.scope,
    }
    auth_url = f"{AUTH_BASE}/authorize?{urlencode(query)}"

    session = {
        "created_at": int(time.time()),
        "client_id": args.client_id,
        "redirect_uri": args.redirect_uri,
        "scope": args.scope,
        "state": state,
        "code_verifier": verifier,
    }

    print("=" * 72)
    print("OPEN THIS URL NOW (code may expire quickly):")
    print("=" * 72)
    print(auth_url)
    print("=" * 72)
    print("After login, paste FULL callback URL or just CODE and press Enter:")
    user_input = input("URL/CODE: ").strip()

    code = user_input
    if user_input.startswith("http://") or user_input.startswith("https://"):
        code = parse_code_from_callback(user_input)
        cb_state = parse_state_from_callback(user_input)
        if cb_state and cb_state != state:
            print("state mismatch; aborting", file=sys.stderr)
            return 3

    if not code:
        print("empty code; aborting", file=sys.stderr)
        return 2

    try:
        out = exchange_code(session, code)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 4

    save_or_print_tokens(out, args.out)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Headless Swiggy OAuth helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="generate authorize URL and local PKCE session")
    p_init.add_argument("--client-id", default=DEFAULT_CLIENT_ID)
    p_init.add_argument("--redirect-uri", default=DEFAULT_REDIRECT_URI)
    p_init.add_argument("--scope", default=DEFAULT_SCOPE)
    p_init.set_defaults(func=cmd_init)

    p_ex = sub.add_parser("exchange", help="exchange callback URL/code for tokens")
    p_ex.add_argument("--session-file", required=True)
    p_ex.add_argument("--callback-url", default="")
    p_ex.add_argument("--code", default="")
    p_ex.add_argument("--out", default="")
    p_ex.set_defaults(func=cmd_exchange)

    p_i = sub.add_parser("interactive", help="init + prompt + immediate exchange")
    p_i.add_argument("--client-id", default=DEFAULT_CLIENT_ID)
    p_i.add_argument("--redirect-uri", default=DEFAULT_REDIRECT_URI)
    p_i.add_argument("--scope", default=DEFAULT_SCOPE)
    p_i.add_argument("--out", default="")
    p_i.set_defaults(func=cmd_interactive)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
