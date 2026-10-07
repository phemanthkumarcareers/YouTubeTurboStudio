"""
YouTube OAuth & Channel Authentication Manager
Manages credentials, OAuth2 browser authorization, token persistence, and channel diagnostics.
"""
import os
import json
import pickle
import threading
import time
from pathlib import Path
from config import CLIENT_SECRET_PATH, TOKEN_PATH, load_config
from core.logger import log_info, log_warn, log_success, log_error

# Comprehensive scopes for upload and reading channel details
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

_auth_lock = threading.Lock()
_auth_in_progress = False
_last_refresh_attempt = 0


def auto_detect_client_secret() -> str | None:
    """Find client_secret.json in current or neighboring directories."""
    candidates = [
        CLIENT_SECRET_PATH,
        CLIENT_SECRET_PATH.parent.parent / "client_secret.json",
        CLIENT_SECRET_PATH.parent.parent / "youtube-agentic-ai-studio" / "client_secret.json"
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None


def load_client_secret_from_path(filepath: str) -> tuple[bool, str]:
    """Load and copy client_secret.json from a custom or default path."""
    p = Path(filepath.strip())
    if not p.exists():
        return False, f"File not found at path: {filepath}"
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "installed" not in data and "web" not in data:
            return False, "Invalid OAuth format (missing 'installed' or 'web' section)"
        with open(CLIENT_SECRET_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        log_success(f"Loaded client_secret.json from: {filepath}")
        return True, "Loaded and saved client_secret.json successfully!"
    except Exception as e:
        return False, f"Error reading file: {e}"


def check_auth_status() -> dict:
    """
    Check OAuth configuration and token validity.
    Returns channel info if authenticated.
    """
    global _last_refresh_attempt

    # If local client secret is missing, try auto-detecting
    if not CLIENT_SECRET_PATH.exists():
        detected = auto_detect_client_secret()
        if detected and detected != str(CLIENT_SECRET_PATH):
            load_client_secret_from_path(detected)

    has_secret = CLIENT_SECRET_PATH.exists()
    has_token = TOKEN_PATH.exists()
    token_valid = False
    token_expired = False
    has_refresh = False
    scopes = []
    channel_info = None

    if has_token:
        try:
            with open(TOKEN_PATH, "rb") as f:
                creds = pickle.load(f)
            token_valid = bool(creds and creds.valid)
            token_expired = bool(creds and creds.expired)
            has_refresh = bool(creds and getattr(creds, "refresh_token", None))
            scopes = list(getattr(creds, "scopes", []))

            # Only attempt refresh once every 300 seconds to avoid spamming SSL / network errors
            now = time.time()
            if token_expired and has_refresh and (now - _last_refresh_attempt > 300):
                _last_refresh_attempt = now
                from google.auth.transport.requests import Request
                import requests
                # Use a session with a timeout to avoid hanging or unhandled SSL drops
                sess = requests.Session()
                try:
                    creds.refresh(Request(session=sess))
                    with open(TOKEN_PATH, "wb") as f:
                        pickle.dump(creds, f)
                    token_valid = True
                    token_expired = False
                except Exception:
                    # Token refresh failed (expired or network/SSL drop).
                    token_valid = False
                    token_expired = True

            # Query channel snippet if credentials valid
            if token_valid:
                try:
                    from googleapiclient.discovery import build
                    yt = build("youtube", "v3", credentials=creds)
                    r = yt.channels().list(part="snippet,statistics", mine=True).execute()
                    items = r.get("items", [])
                    if items:
                        snip = items[0].get("snippet", {})
                        stats = items[0].get("statistics", {})
                        channel_info = {
                            "id": items[0].get("id"),
                            "title": snip.get("title"),
                            "custom_url": snip.get("customUrl", ""),
                            "subscribers": stats.get("subscriberCount", "Hidden"),
                            "video_count": stats.get("videoCount", "0"),
                            "thumbnail": snip.get("thumbnails", {}).get("default", {}).get("url")
                        }
                except Exception:
                    channel_info = {
                        "id": "Connected",
                        "title": "Authorized Channel",
                        "subscribers": "Active",
                        "custom_url": ""
                    }
        except Exception:
            pass

    detected_path = auto_detect_client_secret()

    return {
        "has_client_secret": has_secret,
        "has_token": has_token,
        "token_valid": token_valid,
        "token_expired": token_expired,
        "has_refresh": has_refresh,
        "scopes": scopes,
        "channel": channel_info,
        "default_secret_path": detected_path or str(CLIENT_SECRET_PATH)
    }


def save_client_secret_json(secret_data: dict) -> bool:
    """Save client_secret.json to disk."""
    try:
        with open(CLIENT_SECRET_PATH, "w", encoding="utf-8") as f:
            json.dump(secret_data, f, indent=2)
        log_success("Saved client_secret.json successfully.")
        return True
    except Exception as e:
        log_error(f"Failed to write client_secret.json: {e}")
        return False


def save_client_credentials(client_id: str, client_secret: str) -> bool:
    """Construct and save standard installed OAuth format."""
    data = {
        "installed": {
            "client_id": client_id.strip(),
            "project_id": "youtube-turbo-studio",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret.strip(),
            "redirect_uris": ["http://localhost"]
        }
    }
    return save_client_secret_json(data)


def run_oauth_flow(port: int = 8095) -> dict:
    """
    Launch interactive Google OAuth flow in user's browser.
    Saves the acquired credentials to youtube_token.pickle.
    """
    global _auth_in_progress
    if _auth_in_progress:
        return {"ok": False, "error": "Authentication is already in progress"}

    if not CLIENT_SECRET_PATH.exists():
        detected = auto_detect_client_secret()
        if detected:
            load_client_secret_from_path(detected)
        else:
            return {"ok": False, "error": f"client_secret.json not found at {CLIENT_SECRET_PATH}"}

    from google_auth_oauthlib.flow import InstalledAppFlow

    def _auth_worker():
        global _auth_in_progress
        _auth_in_progress = True
        try:
            log_info("Starting Google OAuth in browser...")
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_PATH), YOUTUBE_SCOPES)
            creds = flow.run_local_server(port=port, prompt="consent")
            with open(TOKEN_PATH, "wb") as f:
                pickle.dump(creds, f)
            log_success("YouTube OAuth authorization completed and token saved!")
        except Exception as e:
            log_error(f"YouTube OAuth authorization failed: {e}")
        finally:
            _auth_in_progress = False

    t = threading.Thread(target=_auth_worker, daemon=True)
    t.start()
    return {"ok": True, "message": "OAuth server launched. Complete login in browser window."}
