"""
YouTube OAuth & Channel Authentication Manager
Manages credentials, OAuth2 browser authorization, token persistence, and channel diagnostics
with full multi-channel isolation support.
"""
import os
import json
import pickle
import threading
import time
import shutil
from pathlib import Path
from config import CLIENT_SECRET_PATH, TOKEN_PATH, load_config
from core.credential_manager import get_youtube_token_path, get_client_secret_path
from core.channel_registry import registry
from core.logger import log_info, log_warn, log_success, log_error

# Comprehensive scopes for upload and reading channel details
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

_auth_lock = threading.Lock()
_auth_in_progress = False
_last_refresh_by_channel = {}


def auto_detect_client_secret(channel_id: str = None) -> str | None:
    """Find client_secret.json in channel credentials or standard project locations."""
    if channel_id:
        chan_path = get_client_secret_path(channel_id)
        if chan_path.exists():
            return str(chan_path)

    candidates = [
        CLIENT_SECRET_PATH,
        CLIENT_SECRET_PATH.parent.parent / "client_secret.json",
        CLIENT_SECRET_PATH.parent.parent / "youtube-agentic-ai-studio" / "client_secret.json"
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return None


def load_client_secret_from_path(filepath: str, channel_id: str = None) -> tuple[bool, str]:
    """Load and copy client_secret.json from a custom or default path."""
    p = Path(filepath.strip())
    if not p.exists():
        return False, f"File not found at path: {filepath}"
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "installed" not in data and "web" not in data:
            return False, "Invalid OAuth format (missing 'installed' or 'web' section)"

        # Save to channel credentials directory if channel specified
        cid = channel_id or registry.get_active_channel_id()
        dest_path = get_client_secret_path(cid)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        # Also write to root for backward compatibility if the primary channel
        if cid in ("insightspark-tv", "the-ai-brief-it"):
            with open(CLIENT_SECRET_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        log_success(f"Loaded client_secret.json for '{cid}' from: {filepath}")
        return True, "Loaded and saved client_secret.json successfully!"
    except Exception as e:
        return False, f"Error reading file: {e}"


def check_auth_status(channel_id: str = None) -> dict:
    """
    Check OAuth configuration and token validity for a specific channel.
    Returns channel info if authenticated.
    """
    cid = channel_id or registry.get_active_channel_id()
    token_path = get_youtube_token_path(cid)
    secret_path = get_client_secret_path(cid)

    # If channel secret is missing, try auto-detecting
    if not secret_path.exists():
        detected = auto_detect_client_secret(cid)
        if detected and detected != str(secret_path):
            load_client_secret_from_path(detected, cid)

    has_secret = secret_path.exists()
    has_token = token_path.exists()
    token_valid = False
    token_expired = False
    has_refresh = False
    scopes = []
    channel_info = None

    if has_token:
        try:
            with open(token_path, "rb") as f:
                creds = pickle.load(f)
            token_valid = bool(creds and creds.valid)
            token_expired = bool(creds and creds.expired)
            has_refresh = bool(creds and getattr(creds, "refresh_token", None))
            scopes = list(getattr(creds, "scopes", []))

            now = time.time()
            last_attempt = _last_refresh_by_channel.get(cid, 0)
            if token_expired and has_refresh and (now - last_attempt > 300):
                _last_refresh_by_channel[cid] = now
                from google.auth.transport.requests import Request
                import requests
                sess = requests.Session()
                try:
                    creds.refresh(Request(session=sess))
                    with open(token_path, "wb") as f:
                        pickle.dump(creds, f)
                    if cid in ("insightspark-tv", "the-ai-brief-it"):
                        with open(TOKEN_PATH, "wb") as f:
                            pickle.dump(creds, f)
                    token_valid = True
                    token_expired = False
                except Exception:
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

    detected_path = auto_detect_client_secret(cid)

    return {
        "channel_id": cid,
        "has_client_secret": has_secret,
        "has_token": has_token,
        "token_valid": token_valid,
        "token_expired": token_expired,
        "has_refresh": has_refresh,
        "scopes": scopes,
        "channel": channel_info,
        "default_secret_path": detected_path or str(secret_path)
    }


def save_client_secret_json(secret_data: dict, channel_id: str = None) -> bool:
    """Save client_secret.json to channel credentials directory and root fallback."""
    cid = channel_id or registry.get_active_channel_id()
    dest_path = get_client_secret_path(cid)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(dest_path, "w", encoding="utf-8") as f:
            json.dump(secret_data, f, indent=2)
        if cid in ("insightspark-tv", "the-ai-brief-it"):
            with open(CLIENT_SECRET_PATH, "w", encoding="utf-8") as f:
                json.dump(secret_data, f, indent=2)
        log_success(f"Saved client_secret.json for '{cid}' successfully.")
        return True
    except Exception as e:
        log_error(f"Failed to write client_secret.json: {e}")
        return False


def save_client_credentials(client_id: str, client_secret: str, channel_id: str = None) -> bool:
    """Construct and save standard installed OAuth format for channel."""
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
    return save_client_secret_json(data, channel_id=channel_id)


def run_oauth_flow(port: int = 8095, channel_id: str = None) -> dict:
    """
    Launch interactive Google OAuth flow in user's browser for a specific channel.
    Saves the acquired credentials to that channel's token path.
    """
    global _auth_in_progress
    if _auth_in_progress:
        return {"ok": False, "error": "Authentication is already in progress"}

    cid = channel_id or registry.get_active_channel_id()
    secret_path = get_client_secret_path(cid)

    if not secret_path.exists():
        detected = auto_detect_client_secret(cid)
        if detected:
            load_client_secret_from_path(detected, cid)
            secret_path = get_client_secret_path(cid)
        else:
            return {"ok": False, "error": f"client_secret.json not found for channel '{cid}'"}

    token_path = get_youtube_token_path(cid)
    token_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        return {"ok": False, "error": "google-auth-oauthlib is not installed. Please install requirements."}

    def _auth_worker():
        global _auth_in_progress
        _auth_in_progress = True
        try:
            log_info(f"Starting Google OAuth in browser for channel '{cid}'...")
            flow = InstalledAppFlow.from_client_secrets_file(str(secret_path), YOUTUBE_SCOPES)
            
            # Try designated port, fallback to dynamic available port if needed
            creds = None
            for p in (port, port + 1, port + 2, 0):
                try:
                    creds = flow.run_local_server(port=p, prompt="consent")
                    break
                except Exception as port_err:
                    if p == 0:
                        raise port_err
                    log_warn(f"Port {p} failed for OAuth, trying alternate port: {port_err}")

            if creds:
                with open(token_path, "wb") as f:
                    pickle.dump(creds, f)
                if cid in ("insightspark-tv", "the-ai-brief-it"):
                    with open(TOKEN_PATH, "wb") as f:
                        pickle.dump(creds, f)
                log_success(f"YouTube OAuth authorization completed for '{cid}' and token saved!")
        except Exception as e:
            log_error(f"YouTube OAuth authorization failed for '{cid}': {e}")
        finally:
            _auth_in_progress = False

    t = threading.Thread(target=_auth_worker, daemon=True)
    t.start()
    return {"ok": True, "message": f"OAuth server launched for channel '{cid}'. Complete login in browser window."}
