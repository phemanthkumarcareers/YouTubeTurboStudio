"""
Credential Manager
Manages per-channel and global credentials with strict precedence:
1. Channel-specific secret file (channels/<channel_id>/.env)
2. Global / default environment variables (.env / os.environ)
3. Empty fallback
Provides secret masking for UI display and per-channel YouTube OAuth storage paths.
"""
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import dotenv_values, set_key

BASE_DIR = Path(__file__).resolve().parent.parent
GLOBAL_ENV_PATH = BASE_DIR / ".env"
RUNTIME_DIR = BASE_DIR / "runtime"
CREDENTIALS_DIR = RUNTIME_DIR / "credentials"

# Ensure runtime credentials directory exists
CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

# Standard credential keys supported per channel
MANAGED_KEYS = [
    "gemini_api_key",
    "groq_api_key",
    "openai_api_key",
    "openai_base_url",
    "nano_banana_api_key",
    "pexels_api_key",
    "pixabay_api_key",
    "elevenlabs_api_key",
    "elevenlabs_voice_id",
]

KEY_TO_ENV_NAME = {
    "gemini_api_key": "GEMINI_API_KEY",
    "groq_api_key": "GROQ_API_KEY",
    "openai_api_key": "OPENAI_API_KEY",
    "openai_base_url": "OPENAI_BASE_URL",
    "nano_banana_api_key": "NANO_BANANA_API_KEY",
    "pexels_api_key": "PEXELS_API_KEY",
    "pixabay_api_key": "PIXABAY_API_KEY",
    "elevenlabs_api_key": "ELEVENLABS_API_KEY",
    "elevenlabs_voice_id": "ELEVENLABS_VOICE_ID",
}


def mask_secret(value: Optional[str]) -> str:
    """Mask a secret string for safe UI presentation."""
    if not value or not str(value).strip():
        return ""
    val = str(value).strip()
    if len(val) <= 8:
        return "••••••••"
    return val[:4] + "••••" + val[-4:]


def get_channel_dir(channel_id: str) -> Path:
    """Return directory for a channel."""
    return BASE_DIR / "channels" / channel_id


def get_channel_env_path(channel_id: str) -> Path:
    """Return path to channel-specific .env file."""
    return get_channel_dir(channel_id) / ".env"


def get_channel_credentials_dir(channel_id: str) -> Path:
    """Return runtime directory for channel OAuth and tokens."""
    d = CREDENTIALS_DIR / channel_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_youtube_token_path(channel_id: str) -> Path:
    """
    Return path to channel-specific YouTube OAuth token.
    For 'the-ai-brief-it', migrate existing root token if present.
    """
    chan_token = get_channel_credentials_dir(channel_id) / "youtube_token.pickle"
    root_token = BASE_DIR / "youtube_token.pickle"

    # Auto-migrate legacy root token for the primary channel if not yet in runtime
    if not chan_token.exists() and channel_id == "the-ai-brief-it" and root_token.exists():
        try:
            shutil.copy2(root_token, chan_token)
        except Exception:
            pass

    return chan_token


def get_client_secret_path(channel_id: str) -> Path:
    """
    Return path to channel-specific client_secret.json.
    Strictly uses runtime/credentials/<channel_id>/client_secret.json.
    Root client_secret.json is ONLY used as fallback for 'the-ai-brief-it' legacy migration.
    All other channels require their own dedicated client_secret.json for full OAuth isolation.
    """
    chan_secret = get_channel_credentials_dir(channel_id) / "client_secret.json"
    root_secret = BASE_DIR / "client_secret.json"

    if chan_secret.exists():
        return chan_secret
    if channel_id == "the-ai-brief-it" and root_secret.exists():
        return root_secret
    return chan_secret


def load_channel_credentials(channel_id: str, allow_global_fallback: bool = False) -> Dict[str, str]:
    """
    Load resolved credentials for channel following strict isolation:
    1. channels/<channel_id>/.env (Primary channel-specific source)
    2. Root .env fallback is ONLY used for 'the-ai-brief-it' backwards compatibility,
       or when allow_global_fallback is explicitly True.
    For all other channels ('kids', 'elders', custom channels), keys default to empty strings
    so channels maintain isolated API keys.
    """
    creds = {k: "" for k in KEY_TO_ENV_NAME.keys()}
    channel_env_file = get_channel_env_path(channel_id)
    chan_env_vars = {}
    if channel_env_file.exists():
        try:
            chan_env_vars = dotenv_values(channel_env_file)
        except Exception:
            chan_env_vars = {}

    root_env_vars = {}
    is_primary = (channel_id == "the-ai-brief-it")
    if (allow_global_fallback or is_primary) and GLOBAL_ENV_PATH.exists():
        try:
            root_env_vars = dotenv_values(GLOBAL_ENV_PATH)
        except Exception:
            root_env_vars = {}

    for cfg_key, env_var in KEY_TO_ENV_NAME.items():
        # 1. Channel .env
        val = chan_env_vars.get(env_var)
        if val is not None and str(val).strip():
            creds[cfg_key] = str(val).strip()
            continue

        # 2. Global fallback only if primary channel or explicitly requested
        if allow_global_fallback or is_primary:
            val = root_env_vars.get(env_var)
            if val is not None and str(val).strip():
                creds[cfg_key] = str(val).strip()
                continue
            val = os.getenv(env_var, "")
            if val and str(val).strip():
                creds[cfg_key] = str(val).strip()
                continue

        creds[cfg_key] = ""

    return creds


def save_channel_credentials(channel_id: str, new_creds: Dict[str, Any]) -> bool:
    """
    Save channel-specific credentials to channels/<channel_id>/.env.
    Writes non-masked values. If value is empty string, clears the variable.
    """
    channel_env_file = get_channel_env_path(channel_id)
    channel_env_file.parent.mkdir(parents=True, exist_ok=True)

    if not channel_env_file.exists():
        channel_env_file.touch()

    for cfg_key, val in new_creds.items():
        if cfg_key in KEY_TO_ENV_NAME and val is not None:
            s_val = str(val).strip()
            # Do not save masked placeholder string
            if "••••" in s_val:
                continue
            env_var = KEY_TO_ENV_NAME[cfg_key]
            try:
                set_key(str(channel_env_file), env_var, s_val)
            except Exception:
                pass

    return True


def get_masked_channel_credentials(channel_id: str) -> Dict[str, str]:
    """Return dictionary of credential keys with secrets masked for safe UI display."""
    creds = load_channel_credentials(channel_id)
    return {k: mask_secret(v) for k, v in creds.items()}
