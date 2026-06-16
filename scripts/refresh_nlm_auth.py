#!/usr/bin/env python3
"""
Refresh NotebookLM authentication using Playwright with persistent Chrome profile.

Uses a persistent browser profile so the session stays alive between runs.
Also saves storage_state.json (cookies + localStorage) for use by the
Playwright-based NLM client, and auth.json for the notebooklm-mcp-server.

Usage:
    python scripts/refresh_nlm_auth.py                  # Skip if auth < 6 days old
    python scripts/refresh_nlm_auth.py --force          # Always refresh
    python scripts/refresh_nlm_auth.py --setup-keyring  # One-time: store creds in OS keyring

Credential sources (resolved in this order):
    1. OS keyring (preferred — Windows Credential Vault / macOS Keychain / Secret Service)
    2. .env file at project root (legacy — emits a warning, plaintext on disk)
"""
from __future__ import annotations

import getpass
import json
import os
import re
import sys
import time
import subprocess
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────────────

AUTH_CACHE_DIR = Path.home() / ".notebooklm-mcp"
AUTH_JSON_PATH = AUTH_CACHE_DIR / "auth.json"
STORAGE_STATE_PATH = AUTH_CACHE_DIR / "storage_state.json"
PROFILE_DIR = AUTH_CACHE_DIR / "chrome-profile"
ENV_PATH = Path(__file__).parent.parent / ".env"

REQUIRED_COOKIES = ["SID", "HSID", "SSID", "APISID", "SAPISID"]
MAX_AGE_HOURS = 144  # Refresh if older than 6 days (cookies valid ~1 week)
LOGIN_TIMEOUT_S = 300  # Max wait for 2FA / manual steps

NLM_URL = "https://notebooklm.google.com/"

# OS keyring service identifier
KEYRING_SERVICE = "news_notebooklm_nlm"
KEYRING_EMAIL_KEY = "GOOGLE_EMAIL"
KEYRING_PASSWORD_KEY = "GOOGLE_PASSWORD"


# ── Credential helpers ───────────────────────────────────────────────────────

def _load_from_keyring() -> tuple[str, str]:
    """Try to load (email, password) from OS keyring. Returns ('', '') on miss."""
    try:
        import keyring  # type: ignore
    except ImportError:
        return ("", "")
    try:
        email = keyring.get_password(KEYRING_SERVICE, KEYRING_EMAIL_KEY) or ""
        password = keyring.get_password(KEYRING_SERVICE, KEYRING_PASSWORD_KEY) or ""
        return email, password
    except Exception as exc:  # noqa: BLE001
        print(f"  Keyring access error: {exc}")
        return ("", "")


def _load_from_env_file() -> tuple[str, str]:
    """Load (email, password) from .env at project root. Returns ('', '') if absent."""
    if not ENV_PATH.exists():
        return ("", "")
    email = ""
    password = ""
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip().strip('"').strip("'")
            if key.strip() == "GOOGLE_EMAIL":
                email = value
            elif key.strip() == "GOOGLE_PASSWORD":
                password = value
    return email, password


def _load_creds() -> tuple[str, str]:
    """Resolve creds from keyring first, then .env. Warns when .env is used."""
    email, password = _load_from_keyring()
    if email and password:
        return email, password
    email, password = _load_from_env_file()
    if password:
        print(
            "WARNING: Loading GOOGLE_PASSWORD from .env (plaintext on disk).\n"
            "  Migrate to OS keyring with:\n"
            "    python scripts/refresh_nlm_auth.py --setup-keyring\n"
            "  then DELETE the GOOGLE_PASSWORD line from your .env file.\n"
        )
    return email, password


def _setup_keyring_interactive() -> None:
    """One-time helper: prompt for credentials and store them in the OS keyring."""
    try:
        import keyring  # type: ignore
    except ImportError:
        print("ERROR: 'keyring' package not installed. Run: pip install keyring")
        sys.exit(1)

    backend_name = keyring.get_keyring().__class__.__name__
    print("Setting up OS-level credential storage for NotebookLM auth.")
    print(f"  Service ID:      {KEYRING_SERVICE}")
    print(f"  Keyring backend: {backend_name}")
    print()

    # Pre-fill suggestion from current source if available.
    current_email, _ = _load_from_keyring()
    if not current_email:
        current_email, _ = _load_from_env_file()

    suffix = f" [{current_email}]" if current_email else ""
    email_input = input(f"Google email{suffix}: ").strip()
    email = email_input or current_email
    if not email:
        print("ERROR: email is required.")
        sys.exit(1)

    password = getpass.getpass("Google password (or app-password if 2FA): ").strip()
    if not password:
        print("ERROR: password is required.")
        sys.exit(1)

    keyring.set_password(KEYRING_SERVICE, KEYRING_EMAIL_KEY, email)
    keyring.set_password(KEYRING_SERVICE, KEYRING_PASSWORD_KEY, password)
    print()
    print(f"OK — credentials stored in {backend_name} under service '{KEYRING_SERVICE}'.")
    print()
    print("Next steps:")
    print(f"  1. Open {ENV_PATH} and DELETE the GOOGLE_PASSWORD line.")
    print("     (You may keep GOOGLE_EMAIL if you want; it's not sensitive.)")
    print("  2. Run `python scripts/refresh_nlm_auth.py --force` to verify the new flow.")
    print("  3. (Recommended) rotate the old Google password at")
    print("     https://myaccount.google.com/security since it sat in plaintext.")


def _is_auth_fresh() -> bool:
    """Return True if auth.json is recent enough to skip refresh."""
    if not AUTH_JSON_PATH.exists():
        return False
    try:
        data = json.loads(AUTH_JSON_PATH.read_text(encoding="utf-8"))
        age_hours = (time.time() - data.get("extracted_at", 0)) / 3600
        if age_hours < MAX_AGE_HOURS:
            print(f"Auth is fresh ({age_hours:.1f}h old). Skipping refresh.")
            return True
    except Exception:
        pass
    return False


def _save_auth(cookies_dict: dict[str, str], csrf_token: str = "", session_id: str = "") -> None:
    AUTH_CACHE_DIR.mkdir(exist_ok=True)
    data = {
        "cookies": cookies_dict,
        "csrf_token": csrf_token,
        "session_id": session_id,
        "extracted_at": time.time(),
    }
    AUTH_JSON_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Saved auth to {AUTH_JSON_PATH}")


def _extract_google_cookies(context) -> dict[str, str]:
    """Extract all cookies for google.com domains."""
    all_cookies = context.cookies()
    return {
        c["name"]: c["value"]
        for c in all_cookies
        if "google" in c.get("domain", "").lower()
    }


def _validate(cookies_dict: dict[str, str]) -> bool:
    missing = [k for k in REQUIRED_COOKIES if k not in cookies_dict]
    if missing:
        print(f"WARNING: missing cookies: {missing}")
        return False
    print(f"All required cookies present: {REQUIRED_COOKIES}")
    return True


# ── Login flow ────────────────────────────────────────────────────────────────

def _do_google_login(page, email: str, password: str) -> None:
    """Fill Google sign-in form. Waits for manual 2FA if needed."""
    print("Filling Google sign-in form...")

    # Email step
    try:
        page.wait_for_selector('input[type="email"], input#identifierId', timeout=8000)
        page.fill('input[type="email"], input#identifierId', email)
        for selector in ('#identifierNext button', '#identifierNext', '[data-identifier-next]',
                         'button:has-text("Next")'):
            try:
                page.click(selector, timeout=3000)
                break
            except Exception:
                continue
    except Exception as e:
        print(f"  Email step error: {e}")

    # Password step
    try:
        page.wait_for_selector('input[type="password"]:visible', timeout=10000)
        page.wait_for_timeout(500)
        page.fill('input[type="password"]:visible', password)
        for selector in ('#passwordNext button', '#passwordNext',
                         'button:has-text("Next")', 'button:has-text("Sign in")'):
            try:
                page.click(selector, timeout=3000)
                break
            except Exception:
                continue
        print("  Password submitted.")
    except Exception as e:
        print(f"  Password step error: {e}")

    print("  Waiting for login to complete (complete any 2FA prompts in the browser)...")


# ── Main flow ─────────────────────────────────────────────────────────────────

def refresh_auth() -> None:
    email, password = _load_creds()

    if not email or not password:
        print("ERROR: No NotebookLM credentials found.")
        print("  Preferred:  python scripts/refresh_nlm_auth.py --setup-keyring")
        print(f"  Fallback:   set GOOGLE_EMAIL/GOOGLE_PASSWORD in {ENV_PATH}")
        sys.exit(1)

    print(f"Starting NLM auth refresh for: {email}")
    print("A browser window will open. Complete any 2FA prompts if required.")

    AUTH_CACHE_DIR.mkdir(exist_ok=True)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=300,
            args=["--no-sandbox", "--disable-gpu", "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        try:
            # 1. Go to NotebookLM — if session is cached in profile, we're done
            print("Navigating to NotebookLM...")
            page.goto(NLM_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)

            # 2. If redirected to Google login, sign in
            if "accounts.google.com" in page.url:
                print("Login required — signing in...")
                _do_google_login(page, email, password)

                # 3. Wait for successful login
                deadline = time.time() + LOGIN_TIMEOUT_S
                while time.time() < deadline:
                    current = page.url
                    if current.startswith("https://notebooklm.google.com"):
                        print(f"  Reached NotebookLM ({current[:80]})")
                        break
                    
                    # Take screenshot and scan for 2-digit numbers
                    try:
                        screenshot_path = Path(__file__).resolve().parent.parent / "google_2fa_screenshot.png"
                        page.screenshot(path=str(screenshot_path))
                    except Exception:
                        pass
                    
                    try:
                        # Fast evaluation of 2-digit numbers in divs, spans, or blockquotes
                        js_code = """
                        () => {
                            let results = [];
                            let els = document.querySelectorAll('div, span, blockquote');
                            for (let el of els) {
                                let txt = el.innerText ? el.innerText.trim() : '';
                                if (/^\\d{2}$/.test(txt)) {
                                    results.push(txt);
                                }
                            }
                            return Array.from(new Set(results));
                        }
                        """
                        numbers = page.evaluate(js_code)
                        if numbers:
                            print(f"  [2FA Info] Found 2-digit numbers on screen: {', '.join(numbers)}")
                    except Exception:
                        pass

                    # Auto-skip optional onboarding/recovery setups
                    try:
                        for text_val in ["Not now", "Bỏ qua", "Not right now", "Bỏ qua lúc này", "Bỏ qua thiết lập"]:
                            for selector in [f'button:has-text("{text_val}")', f'span:has-text("{text_val}")']:
                                locator = page.locator(selector).first
                                if locator.is_visible():
                                    print(f"  [2FA Info] Auto-clicking onboarding skip button: {text_val}")
                                    locator.click()
                                    page.wait_for_timeout(1000)
                    except Exception:
                        pass

                    remaining = int(deadline - time.time())
                    if remaining % 10 == 0:
                        print(f"  Waiting for login / 2FA... {remaining}s remaining")
                    page.wait_for_timeout(2000)
                else:
                    print("ERROR: Timed out waiting for NotebookLM after login.")
                    context.close()
                    sys.exit(1)
            else:
                print(f"Session already active ({page.url[:80]})")

            # Navigate to NLM root if we landed elsewhere
            if not page.url.startswith("https://notebooklm.google.com"):
                print("Navigating to NotebookLM root...")
                page.goto(NLM_URL, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)
                if not page.url.startswith("https://notebooklm.google.com"):
                    print(f"ERROR: Still not on NotebookLM. URL: {page.url}")
                    context.close()
                    sys.exit(1)

            # 4. Wait for page to fully render
            page.wait_for_timeout(4000)

            # 5. Extract CSRF token and session ID
            html = page.content()
            csrf_match = re.search(r'"SNlM0e":"([^"]+)"', html)
            sid_match = re.search(r'"FdrFJe":"([^"]+)"', html)
            csrf_token = csrf_match.group(1) if csrf_match else ""
            session_id = sid_match.group(1) if sid_match else ""

            if csrf_token:
                print(f"CSRF token extracted ({len(csrf_token)} chars).")
            else:
                print("WARNING: CSRF token not found in page HTML.")

            if session_id:
                print(f"Session ID extracted ({len(session_id)} chars).")

            # 6. Save full storage state (cookies + localStorage + sessionStorage)
            context.storage_state(path=str(STORAGE_STATE_PATH))
            print(f"Storage state saved to {STORAGE_STATE_PATH}")

            # 7. Save cookies in auth.json format for notebooklm-mcp-server
            cookies_dict = _extract_google_cookies(context)
            print(f"Extracted {len(cookies_dict)} Google cookies.")
            _validate(cookies_dict)
            _save_auth(cookies_dict, csrf_token=csrf_token, session_id=session_id)
            print("Auth refresh complete! Session valid for ~1 week.")

        finally:
            context.close()
            browser.close()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--setup-keyring" in sys.argv:
        _setup_keyring_interactive()
        sys.exit(0)

    force = "--force" in sys.argv

    if force:
        print("--force flag set. Refreshing regardless of age.")
        refresh_auth()
    elif _is_auth_fresh():
        sys.exit(0)
    else:
        print("Auth is stale or missing. Refreshing...")
        refresh_auth()
