"""
Channel Context
Immutable/Serializable context object holding all channel-specific configuration,
routing, credentials metadata, prompts, voice, and YouTube settings.
Passed explicitly through pipeline components to ensure channel isolation.
"""
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import copy


@dataclass
class ChannelContext:
    channel_id: str
    name: str
    engine: str = "media_video"  # "media_video" or "animation"
    enabled: bool = True
    audience: Dict[str, Any] = field(default_factory=lambda: {
        "type": "general",
        "age_group": "all",
    })
    video: Dict[str, Any] = field(default_factory=lambda: {
        "default_format": "normal",  # "normal" (16:9) or "shorts" (9:16)
        "allow_short": True,
        "allow_long": True,
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "kb_zoom_start": 1.0,
        "kb_zoom_end": 1.15,
        "subtitles_enabled": True,
    })
    credentials: Dict[str, Any] = field(default_factory=lambda: {
        "env_file": "",
        "llm_provider": "gemini",
        "gemini_model": "gemini-2.5-flash",
        "groq_model": "openai/gpt-oss-120b",
        "video_source": "pexels_images",
    })
    youtube: Dict[str, Any] = field(default_factory=lambda: {
        "channel_id": "",  # Expected YouTube Channel ID (e.g. UCxxxxxxxx)
        "oauth_profile": "",
        "privacy": "private",
        "category_id": "28",
        "made_for_kids": False,
        "auto_upload": False,
    })
    pipeline: Dict[str, Any] = field(default_factory=lambda: {
        "auto_topic": True,
        "auto_publish": False,
        "minimum_quality_score": 85,
    })
    prompts: Dict[str, Any] = field(default_factory=lambda: {
        "niche": "",
        "description": "",
        "default_tags": [],
        "banned_topics": [],
        "system_prompt": "",
    })
    voice: Dict[str, Any] = field(default_factory=lambda: {
        "tts_provider": "edge-tts",
        "voice_id": "en-US-ChristopherNeural",
        "voice_rate": "+0%",
        "voice_pitch": "+0Hz",
        "elevenlabs_voice_id": "21m00Tcm4TlvDq8ikWAM",
        "music_enabled": True,
        "music_volume": 0.15,
    })

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to standard dictionary."""
        return copy.deepcopy(asdict(self))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChannelContext":
        """Instantiate ChannelContext from dictionary with safe defaults."""
        d = copy.deepcopy(data)
        return cls(
            channel_id=d.get("channel_id") or d.get("id", "the-ai-brief-it"),
            name=d.get("name", "Default Channel"),
            engine=d.get("engine", "media_video"),
            enabled=d.get("enabled", True),
            audience=d.get("audience", {"type": "general", "age_group": "all"}),
            video=d.get("video", {}),
            credentials=d.get("credentials", {}),
            youtube=d.get("youtube", {}),
            pipeline=d.get("pipeline", {}),
            prompts=d.get("prompts", {}),
            voice=d.get("voice", {}),
        )

    def to_pipeline_config(self, resolved_credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Produce a flat config dictionary compatible with existing pipeline components
        (agents, audio, media, renderer, uploader) while preserving channel context.
        """
        creds = resolved_credentials or {}
        vid = self.video
        yt = self.youtube
        voi = self.voice
        prm = self.prompts
        cred_meta = self.credentials

        return {
            "channel_id": self.channel_id,
            "channel_name": self.name,
            "engine": self.engine,
            # AI Provider & Models
            "llm_provider": cred_meta.get("llm_provider", "gemini"),
            "gemini_api_key": creds.get("gemini_api_key", ""),
            "gemini_model": cred_meta.get("gemini_model", "gemini-2.5-flash"),
            "groq_api_key": creds.get("groq_api_key", ""),
            "groq_model": cred_meta.get("groq_model", "openai/gpt-oss-120b"),
            "openai_api_key": creds.get("openai_api_key", ""),
            "openai_base_url": creds.get("openai_base_url", "https://api.openai.com/v1"),
            "openai_model": cred_meta.get("openai_model", "gpt-4o-mini"),
            # Stock media
            "pexels_api_key": creds.get("pexels_api_key", ""),
            "pixabay_api_key": creds.get("pixabay_api_key", ""),
            "video_source": cred_meta.get("video_source", "pexels_images"),
            # Voice & Audio
            "tts_provider": voi.get("tts_provider", "edge-tts"),
            "voice_id": voi.get("voice_id", "en-US-ChristopherNeural"),
            "voice_rate": voi.get("voice_rate", "+0%"),
            "voice_pitch": voi.get("voice_pitch", "+0Hz"),
            "elevenlabs_api_key": creds.get("elevenlabs_api_key", ""),
            "elevenlabs_voice_id": voi.get("elevenlabs_voice_id", "21m00Tcm4TlvDq8ikWAM"),
            "music_enabled": voi.get("music_enabled", True),
            "music_volume": voi.get("music_volume", 0.15),
            # Video settings
            "video_type": vid.get("default_format", "normal"),
            "video_width": vid.get("width", 1920),
            "video_height": vid.get("height", 1080),
            "video_fps": vid.get("fps", 30),
            "kb_zoom_start": vid.get("kb_zoom_start", 1.0),
            "kb_zoom_end": vid.get("kb_zoom_end", 1.15),
            "subtitles_enabled": vid.get("subtitles_enabled", True),
            "render_preset": vid.get("render_preset", "ultrafast"),
            # YouTube settings
            "youtube_privacy": yt.get("privacy", "private"),
            "youtube_category_id": yt.get("category_id", "28"),
            "made_for_kids": yt.get("made_for_kids", False),
            "auto_upload": yt.get("auto_upload", False),
            "expected_youtube_channel_id": yt.get("channel_id", ""),
            # Channel profile / Prompts
            "channel_description": prm.get("description", ""),
            "channel_niche": prm.get("niche", ""),
            "default_tags": prm.get("default_tags", []),
            "banned_topics": prm.get("banned_topics", []),
        }
