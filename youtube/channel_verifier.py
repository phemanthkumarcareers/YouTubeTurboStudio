"""
YouTube Channel Verifier
Validates authenticated YouTube OAuth identity against channel configuration.
Guarantees that a generation job for Channel A cannot upload to Channel B's YouTube account.
"""
import pickle
import time
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import requests

from core.credential_manager import get_youtube_token_path, get_client_secret_path
from core.logger import log_info, log_warn, log_error, log_success

_last_refresh_by_channel: Dict[str, float] = {}


def get_channel_youtube_credentials(channel_id: str):
    """Load and refresh credentials for a specific channel."""
    token_path = get_youtube_token_path(channel_id)
    if not token_path.exists():
        return None

    try:
        with open(token_path, "rb") as f:
            creds = pickle.load(f)
    except Exception as e:
        log_error(f"Failed to unpickle token for channel {channel_id}: {e}")
        return None

    if creds and creds.expired and getattr(creds, "refresh_token", None):
        now = time.time()
        last_attempt = _last_refresh_by_channel.get(channel_id, 0)
        # Avoid rapid repeated refresh attempts
        if now - last_attempt > 60:
            _last_refresh_by_channel[channel_id] = now
            sess = requests.Session()
            try:
                creds.refresh(Request(session=sess))
                with open(token_path, "wb") as f:
                    pickle.dump(creds, f)
                log_info(f"Refreshed YouTube OAuth token for channel '{channel_id}'.")
            except Exception as e:
                log_warn(f"Failed to refresh YouTube token for '{channel_id}': {e}")

    return creds


def get_channel_youtube_info(channel_id: str) -> Dict[str, Any]:
    """
    Query authenticated YouTube channel information for a specific channel.
    Returns status dict including channel details if connected.
    """
    token_path = get_youtube_token_path(channel_id)
    secret_path = get_client_secret_path(channel_id)

    has_token = token_path.exists()
    has_secret = secret_path.exists()
    token_valid = False
    token_expired = False
    has_refresh = False
    channel_info = None

    if has_token:
        creds = get_channel_youtube_credentials(channel_id)
        if creds:
            token_valid = bool(creds.valid)
            token_expired = bool(creds.expired)
            has_refresh = bool(getattr(creds, "refresh_token", None))

            if token_valid:
                try:
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
                    else:
                        channel_info = {
                            "id": "Unknown",
                            "title": "No Channel Found on Account",
                            "subscribers": "0",
                            "custom_url": ""
                        }
                except Exception as e:
                    channel_info = {
                        "id": "Connected",
                        "title": "Authorized Account",
                        "subscribers": "Active",
                        "custom_url": "",
                        "error": str(e)
                    }

    return {
        "channel_id": channel_id,
        "has_client_secret": has_secret,
        "has_token": has_token,
        "token_valid": token_valid,
        "token_expired": token_expired,
        "has_refresh": has_refresh,
        "channel": channel_info,
        "token_path": str(token_path),
        "secret_path": str(secret_path) if has_secret else None
    }


def verify_channel(channel_id: str, expected_youtube_channel_id: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Verify YouTube authentication for a channel before upload.
    Checks:
    1. Channel has a valid token
    2. Authenticated channel matches expected_youtube_channel_id if configured.
    Returns: (is_verified: bool, message: str, channel_info: dict)
    """
    status = get_channel_youtube_info(channel_id)

    if not status.get("has_token"):
        return False, f"Channel '{channel_id}' is not connected to YouTube. Please authenticate in the YouTube tab.", status

    if not status.get("token_valid"):
        return False, f"YouTube OAuth token for '{channel_id}' is expired or invalid. Please re-authenticate.", status

    chan_info = status.get("channel") or {}
    actual_id = chan_info.get("id")

    if expected_youtube_channel_id and expected_youtube_channel_id.strip():
        exp = expected_youtube_channel_id.strip()
        if actual_id and actual_id != exp and actual_id not in ("Connected", "Unknown"):
            err_msg = (
                f"SECURITY ALERT: Channel mismatch! Current OAuth credentials belong to "
                f"YouTube channel '{actual_id}' ({chan_info.get('title')}), but channel configuration "
                f"for '{channel_id}' expects YouTube channel '{exp}'. Upload is blocked to prevent accidental cross-posting."
            )
            log_error(err_msg)
            return False, err_msg, status

    log_success(f"YouTube channel verified for '{channel_id}': {chan_info.get('title', 'Authorized Channel')}")
    return True, f"Verified YouTube identity: {chan_info.get('title', 'Authorized')}", status
