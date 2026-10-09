"""
Channel Registry & Manager
Discovers, validates, and manages multi-channel configurations dynamically.
Reads channels from channels/*/channel.yaml and manages the active channel state.
"""
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import yaml

from core.channel_context import ChannelContext
from core.credential_manager import (
    load_channel_credentials,
    save_channel_credentials,
    get_masked_channel_credentials,
    get_channel_dir,
    RUNTIME_DIR
)

BASE_DIR = Path(__file__).resolve().parent.parent
CHANNELS_DIR = BASE_DIR / "channels"
ACTIVE_CHANNEL_FILE = RUNTIME_DIR / "active_channel.json"

_registry_lock = threading.RLock()


def validate_channel_config(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate that required fields are present in channel configuration."""
    cid = data.get("id") or data.get("channel_id")
    if not cid or not str(cid).strip():
        return False, "Channel ID is required."
    
    clean_id = str(cid).strip().lower()
    if not clean_id.replace("-", "").replace("_", "").isalnum():
        return False, "Channel ID must contain only alphanumeric characters, dashes, or underscores."

    name = data.get("name")
    if not name or not str(name).strip():
        return False, "Channel name is required."

    engine = data.get("engine", "media_video")
    if engine not in ("media_video", "animation"):
        return False, f"Unsupported engine '{engine}'. Must be 'media_video' or 'animation'."

    return True, "Valid configuration"


class ChannelRegistry:
    def __init__(self, channels_dir: Path = CHANNELS_DIR):
        self.channels_dir = channels_dir
        self.channels_dir.mkdir(parents=True, exist_ok=True)
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, ChannelContext] = {}
        self.reload()

    def reload(self):
        """Scan directory and reload all channel configurations."""
        with _registry_lock:
            self._cache.clear()
            if not self.channels_dir.exists():
                return

            for chan_path in self.channels_dir.iterdir():
                if chan_path.is_dir() and chan_path.name != "templates":
                    cfg_file = chan_path / "channel.yaml"
                    if cfg_file.exists():
                        try:
                            with open(cfg_file, "r", encoding="utf-8") as f:
                                data = yaml.safe_load(f) or {}

                            # Load optional prompts.yaml
                            prompts_file = chan_path / "prompts.yaml"
                            if prompts_file.exists():
                                try:
                                    with open(prompts_file, "r", encoding="utf-8") as pf:
                                        p_data = yaml.safe_load(pf) or {}
                                        data.setdefault("prompts", {}).update(p_data)
                                except Exception as e:
                                    print(f"[Registry] Error reading prompts.yaml for {chan_path.name}: {e}")

                            data["channel_id"] = data.get("id", chan_path.name)
                            valid, err = validate_channel_config(data)
                            if valid:
                                self._cache[data["channel_id"]] = ChannelContext.from_dict(data)
                            else:
                                print(f"[Registry] Skipped invalid channel {chan_path.name}: {err}")
                        except Exception as e:
                            print(f"[Registry] Error loading channel {chan_path.name}: {e}")

    def list_channels(self) -> List[Dict[str, Any]]:
        """Return list of channels with overview metadata."""
        with _registry_lock:
            active_id = self.get_active_channel_id()
            res = []
            for cid, ctx in self._cache.items():
                res.append({
                    "channel_id": ctx.channel_id,
                    "name": ctx.name,
                    "engine": ctx.engine,
                    "enabled": ctx.enabled,
                    "is_active": (cid == active_id),
                    "default_format": ctx.video.get("default_format", "normal"),
                    "category_id": ctx.youtube.get("category_id", "28"),
                    "voice_id": ctx.voice.get("voice_id", "en-US-ChristopherNeural"),
                })
            # Ensure the primary channel appears first
            res.sort(key=lambda x: (x["channel_id"] != "the-ai-brief-it", x["name"]))
            return res

    def get_channel(self, channel_id: str) -> Optional[ChannelContext]:
        """Get ChannelContext by ID."""
        with _registry_lock:
            if channel_id not in self._cache:
                self.reload()
            return self._cache.get(channel_id)

    def get_active_channel_id(self) -> str:
        """Get currently active channel ID."""
        with _registry_lock:
            if ACTIVE_CHANNEL_FILE.exists():
                try:
                    with open(ACTIVE_CHANNEL_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        cid = data.get("active_channel_id")
                        if cid and cid in self._cache:
                            return cid
                except Exception:
                    pass

            if "the-ai-brief-it" in self._cache:
                return "the-ai-brief-it"
            if self._cache:
                return next(iter(self._cache.keys()))
            return "the-ai-brief-it"

    def set_active_channel_id(self, channel_id: str) -> bool:
        """Set active channel ID."""
        with _registry_lock:
            if channel_id not in self._cache:
                self.reload()
            if channel_id not in self._cache:
                return False

            try:
                with open(ACTIVE_CHANNEL_FILE, "w", encoding="utf-8") as f:
                    json.dump({"active_channel_id": channel_id}, f, indent=2)
                return True
            except Exception as e:
                print(f"[Registry] Error writing active channel: {e}")
                return False

    def get_active_channel(self) -> ChannelContext:
        """Get ChannelContext for currently active channel."""
        with _registry_lock:
            cid = self.get_active_channel_id()
            chan = self.get_channel(cid)
            if not chan:
                # Return safe fallback if cache is somehow empty
                return ChannelContext(channel_id="the-ai-brief-it", name="The AI Brief It")
            return chan

    def save_channel(self, channel_id: str, updates: Dict[str, Any]) -> ChannelContext:
        """Update and persist channel configuration and credentials."""
        with _registry_lock:
            chan = self.get_channel(channel_id)
            if not chan:
                raise ValueError(f"Channel not found: {channel_id}")

            chan_dir = get_channel_dir(channel_id)
            chan_dir.mkdir(parents=True, exist_ok=True)
            cfg_file = chan_dir / "channel.yaml"

            # Separate credentials / secrets from channel settings
            creds_updates = {}
            for k in list(updates.keys()):
                if k.endswith("_api_key") or k in ("openai_base_url",):
                    creds_updates[k] = updates.pop(k)

            if creds_updates:
                save_channel_credentials(channel_id, creds_updates)

            # Apply structured updates to ChannelContext
            if "name" in updates:
                chan.name = updates["name"]
            if "engine" in updates:
                chan.engine = updates["engine"]
            if "enabled" in updates:
                chan.enabled = bool(updates["enabled"])

            # Nested sections
            for sec in ("audience", "video", "credentials", "youtube", "pipeline", "prompts", "voice"):
                if sec in updates and isinstance(updates[sec], dict):
                    getattr(chan, sec).update(updates[sec])

            # Write updated config to channel.yaml
            chan_data = {
                "id": chan.channel_id,
                "name": chan.name,
                "engine": chan.engine,
                "enabled": chan.enabled,
                "audience": chan.audience,
                "video": chan.video,
                "credentials": chan.credentials,
                "youtube": chan.youtube,
                "pipeline": chan.pipeline,
                "prompts": chan.prompts,
                "voice": chan.voice,
            }

            with open(cfg_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(chan_data, f, default_flow_style=False, sort_keys=False)

            self._cache[channel_id] = chan
            return chan

    def add_channel(self, data: Dict[str, Any]) -> ChannelContext:
        """Add a new channel to registry and create its files."""
        with _registry_lock:
            valid, msg = validate_channel_config(data)
            if not valid:
                raise ValueError(msg)

            cid = (data.get("id") or data.get("channel_id")).strip().lower()
            if cid in self._cache:
                raise ValueError(f"Channel '{cid}' already exists.")

            chan_dir = get_channel_dir(cid)
            chan_dir.mkdir(parents=True, exist_ok=True)

            data["id"] = cid
            data["channel_id"] = cid

            cfg_file = chan_dir / "channel.yaml"
            with open(cfg_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

            ctx = ChannelContext.from_dict(data)
            self._cache[cid] = ctx
            return ctx


# Global singleton registry instance
registry = ChannelRegistry()
