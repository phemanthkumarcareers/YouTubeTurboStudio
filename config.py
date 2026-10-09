"""
YouTube Turbo Studio - Centralized Configuration Manager
Handles settings persistence in config_data.json and .env synchronization.
Provides real-time configuration getters, setters, and credential validation.
"""
import os
import json
import threading
from pathlib import Path
from dotenv import load_dotenv, set_key

BASE_DIR = Path(__file__).resolve().parent

# Load .env file
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

CONFIG_JSON_PATH = BASE_DIR / "config_data.json"
BANNED_TOPICS_PATH = BASE_DIR / "banned_topics.txt"
CLIENT_SECRET_PATH = BASE_DIR / "client_secret.json"
TOKEN_PATH = BASE_DIR / "youtube_token.pickle"
OUTPUT_DIR = BASE_DIR / "output"
RESOURCES_DIR = BASE_DIR / "resources"
SONGS_DIR = RESOURCES_DIR / "songs"
FONTS_DIR = RESOURCES_DIR / "fonts"

# Ensure essential directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "images").mkdir(parents=True, exist_ok=True)
SONGS_DIR.mkdir(parents=True, exist_ok=True)
FONTS_DIR.mkdir(parents=True, exist_ok=True)

_config_lock = threading.RLock()

DEFAULT_CONFIG = {
    # AI Providers & Keys
    "llm_provider": "gemini",  # 'gemini', 'groq', or 'openai'
    "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
    "gemini_model": "gemini-3.8-flash",
    "groq_api_key": os.getenv("GROQ_API_KEY", ""),
    "groq_model": "openai/gpt-oss-120b",
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "openai_base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    "openai_model": "gpt-4o-mini",
    
    # Stock Media & Generative Image Keys
    "nano_banana_api_key": os.getenv("NANO_BANANA_API_KEY", ""),
    "nano_banana_model": "nano-banana-flux",
    "nano_banana_base_url": os.getenv("NANO_BANANA_BASE_URL", "https://api.banana.dev/v1/generate"),
    "pexels_api_key": os.getenv("PEXELS_API_KEY", ""),
    "pixabay_api_key": os.getenv("PIXABAY_API_KEY", ""),
    "video_source": "pexels_images", # 'pexels_images', 'pexels_videos', 'pixabay_images', 'pixabay_videos', 'nano_banana', 'local'
    "local_media_dir": str(RESOURCES_DIR / "media"),

    # Voice / Audio (Multi-Provider: Edge-TTS, ElevenLabs, OpenAI TTS)
    "tts_provider": "edge-tts",  # 'edge-tts', 'elevenlabs', 'openai-tts', 'google-tts'
    "voice_id": "en-US-ChristopherNeural",
    "voice_rate": "+0%",
    "voice_pitch": "+0Hz",
    "elevenlabs_api_key": os.getenv("ELEVENLABS_API_KEY", ""),
    "elevenlabs_voice_id": "21m00Tcm4TlvDq8ikWAM", # Rachel
    "openai_tts_model": "tts-1",
    "openai_tts_voice": "alloy",
    "multi_character_audio": True,
    "music_enabled": True,
    "music_volume": 0.12,

    # Video Render Settings
    "video_type": "normal", # 'normal' (16:9) or 'shorts' (9:16)
    "video_width": 1920,
    "video_height": 1080,
    "video_fps": 30,
    "kb_zoom_start": 1.0,
    "kb_zoom_end": 1.15,
    "overlay_opacity": 0.35,
    "render_preset": "ultrafast",
    "broll_interval": 5.0,
    "broll_xfade": 0.8,
    "subtitle_font": "BeVietnamPro-Bold.ttf",
    "subtitle_size": 42,
    "subtitle_color": "#FFFFFF",
    "subtitle_position": "bottom",
    "subtitles_enabled": True,

    # YouTube Configuration
    "youtube_privacy": "private", # 'private', 'unlisted', 'public'
    "youtube_category_id": "28", # Science & Technology
    "channel_name": "The AI Brief It",
    "channel_description": """Channel niche: Mind-bending science, deep cosmic mysteries, ancient paradoxes,
existential psychology, and theoretical physics.
Tone: Thoughtful, immersive, cinematic, provocative, authoritative yet accessible.
Pacing: Engaging hook in the first 5 seconds, followed by escalating revelation and a memorable conclusion.""",
    "default_tags": ["science", "mystery", "space", "documentary", "physics", "universe", "philosophy"],
    "made_for_kids": False,
    "auto_upload": False
}

YOUTUBE_CATEGORIES = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "19": "Travel & Events",
    "20": "Gaming",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
    "29": "Nonprofits & Activism"
}

POPULAR_VOICES = [
    {"id": "en-US-ChristopherNeural", "name": "Christopher (US - Deep, Authoritative Storyteller)", "gender": "Male", "lang": "English (US)"},
    {"id": "en-US-GuyNeural", "name": "Guy (US - Engaging, Documentary/Explainer)", "gender": "Male", "lang": "English (US)"},
    {"id": "en-US-JennyNeural", "name": "Jenny (US - Warm, Clear, Narrative)", "gender": "Female", "lang": "English (US)"},
    {"id": "en-US-AriaNeural", "name": "Aria (US - Expressive, Cinematic)", "gender": "Female", "lang": "English (US)"},
    {"id": "en-GB-RyanNeural", "name": "Ryan (UK - Refined, Eloquent)", "gender": "Male", "lang": "English (UK)"},
    {"id": "en-GB-SoniaNeural", "name": "Sonia (UK - Sophisticated, Clear)", "gender": "Female", "lang": "English (UK)"},
    {"id": "en-IN-PrabhatNeural", "name": "Prabhat (India - Confident, Engaging)", "gender": "Male", "lang": "English (India)"},
    {"id": "en-IN-NeerjaNeural", "name": "Neerja (India - Friendly, Crisp)", "gender": "Female", "lang": "English (India)"},
    {"id": "en-AU-WilliamNeural", "name": "William (Australia - Natural, Deep)", "gender": "Male", "lang": "English (AU)"},
    {"id": "es-ES-AlvaroNeural", "name": "Alvaro (Spain - Dynamic, Professional)", "gender": "Male", "lang": "Spanish"},
    {"id": "fr-FR-HenriNeural", "name": "Henri (France - Elegant, Narrative)", "gender": "Male", "lang": "French"},
    {"id": "de-DE-ConradNeural", "name": "Conrad (Germany - Clear, Serious)", "gender": "Male", "lang": "German"},
    {"id": "hi-IN-MadhurNeural", "name": "Madhur (Hindi - Expressive)", "gender": "Male", "lang": "Hindi"}
]


def load_config() -> dict:
    """Load config from config_data.json merged with defaults and .env."""
    with _config_lock:
        cfg = dict(DEFAULT_CONFIG)
        if CONFIG_JSON_PATH.exists():
            try:
                with open(CONFIG_JSON_PATH, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    cfg.update(saved)
            except Exception as e:
                print(f"[Config] Error reading {CONFIG_JSON_PATH}: {e}")
        else:
            try:
                with open(CONFIG_JSON_PATH, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[Config] Error creating {CONFIG_JSON_PATH}: {e}")

        # Ensure env vars are reflected if not in json
        if not cfg.get("gemini_api_key") and os.getenv("GEMINI_API_KEY"):
            cfg["gemini_api_key"] = os.getenv("GEMINI_API_KEY")
        if not cfg.get("groq_api_key") and os.getenv("GROQ_API_KEY"):
            cfg["groq_api_key"] = os.getenv("GROQ_API_KEY")
        if not cfg.get("pexels_api_key") and os.getenv("PEXELS_API_KEY"):
            cfg["pexels_api_key"] = os.getenv("PEXELS_API_KEY")
        if not cfg.get("elevenlabs_api_key") and os.getenv("ELEVENLABS_API_KEY"):
            cfg["elevenlabs_api_key"] = os.getenv("ELEVENLABS_API_KEY")
        if not cfg.get("nano_banana_api_key") and os.getenv("NANO_BANANA_API_KEY"):
            cfg["nano_banana_api_key"] = os.getenv("NANO_BANANA_API_KEY")

        return cfg


def save_config(updates: dict) -> dict:
    """Safely update configuration on disk and in active environment."""
    with _config_lock:
        current = load_config()
        current.update(updates)

        # Write to JSON
        try:
            with open(CONFIG_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Config] Error writing {CONFIG_JSON_PATH}: {e}")

        # Sync critical keys to .env
        env_keys = {
            "gemini_api_key": "GEMINI_API_KEY",
            "groq_api_key": "GROQ_API_KEY",
            "nano_banana_api_key": "NANO_BANANA_API_KEY",
            "pexels_api_key": "PEXELS_API_KEY",
            "pixabay_api_key": "PIXABAY_API_KEY",
            "elevenlabs_api_key": "ELEVENLABS_API_KEY",
            "openai_api_key": "OPENAI_API_KEY",
            "openai_base_url": "OPENAI_BASE_URL",
        }

        if not ENV_PATH.exists():
            ENV_PATH.touch()

        for config_key, env_var in env_keys.items():
            if config_key in updates and updates[config_key] is not None:
                val = str(updates[config_key]).strip()
                os.environ[env_var] = val
                try:
                    set_key(str(ENV_PATH), env_var, val)
                except Exception:
                    pass

        return current


def load_banned_topics() -> list:
    """Read banned topics list from disk."""
    topics = [
        "The Boltzmann Brain",
        "Simulation Theory",
        "Quantum Immortality"
    ]
    if BANNED_TOPICS_PATH.exists():
        try:
            with open(BANNED_TOPICS_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    t = line.strip()
                    if t and not t.startswith("#") and t not in topics:
                        topics.append(t)
        except Exception as e:
            print(f"[Config] Error reading banned topics: {e}")
    return topics


def save_banned_topics(topics: list) -> bool:
    """Write banned topics to banned_topics.txt."""
    try:
        clean = [t.strip() for t in topics if t.strip()]
        with open(BANNED_TOPICS_PATH, "w", encoding="utf-8") as f:
            f.write("# Banned Topics (AI won't research these topics)\n")
            f.write("# One topic per line:\n\n")
            for t in clean:
                f.write(f"{t}\n")
        return True
    except Exception as e:
        print(f"[Config] Error writing banned topics: {e}")
        return False
