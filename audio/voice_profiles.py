"""
Voice Profiles & Multi-Character Voice Management
Supports distinct channel voice profiles, multi-character dialogue mapping
(Kids: Narrator, Character 1, Character 2; Elders: Dignified/Warm; Tech: Authoritative),
and multi-provider voice registries (Edge-TTS, ElevenLabs, OpenAI TTS, Google TTS).
"""
import re
from typing import Dict, Any, List, Optional

SUPPORTED_AUDIO_PROVIDERS = [
    {"id": "edge-tts", "name": "Microsoft Edge-TTS (Free, Ultra-Realistic Neural)", "requires_key": False},
    {"id": "elevenlabs", "name": "ElevenLabs Prime Voice AI (High Fidelity)", "requires_key": True},
    {"id": "openai-tts", "name": "OpenAI TTS (tts-1 / tts-1-hd Natural Speech)", "requires_key": True},
    {"id": "google-tts", "name": "Google Cloud TTS / gTTS", "requires_key": False},
]

PROVIDER_VOICES = {
    "edge-tts": [
        {"id": "en-US-ChristopherNeural", "name": "Christopher (US - Deep, Authoritative Storyteller)", "gender": "Male", "channel_tag": "tech"},
        {"id": "en-US-GuyNeural", "name": "Guy (US - Engaging, Warm Documentary)", "gender": "Male", "channel_tag": "elders"},
        {"id": "en-US-JennyNeural", "name": "Jenny (US - Warm, Clear, Narrative)", "gender": "Female", "channel_tag": "general"},
        {"id": "en-US-AnaNeural", "name": "Ana (US - Gentle, Cheerful Cartoon Kids)", "gender": "Female", "channel_tag": "kids"},
        {"id": "en-US-AriaNeural", "name": "Aria (US - Expressive, Bubbly Character)", "gender": "Female", "channel_tag": "kids"},
        {"id": "en-GB-RyanNeural", "name": "Ryan (UK - Refined, Nostalgic, Dignified)", "gender": "Male", "channel_tag": "elders"},
        {"id": "en-GB-SoniaNeural", "name": "Sonia (UK - Sophisticated, Gentle)", "gender": "Female", "channel_tag": "elders"},
        {"id": "en-IN-PrabhatNeural", "name": "Prabhat (India - Confident, Engaging)", "gender": "Male", "channel_tag": "tech"},
        {"id": "en-IN-NeerjaNeural", "name": "Neerja (India - Friendly, Crisp)", "gender": "Female", "channel_tag": "general"},
    ],
    "openai-tts": [
        {"id": "alloy", "name": "Alloy (Neutral, Balanced, Versatile)", "gender": "Neutral", "channel_tag": "general"},
        {"id": "echo", "name": "Echo (Warm, Rounded, Soft)", "gender": "Male", "channel_tag": "elders"},
        {"id": "fable", "name": "Fable (Expressive, Animated Storybook)", "gender": "Neutral", "channel_tag": "kids"},
        {"id": "onyx", "name": "Onx (Deep, Authoritative, Powerful)", "gender": "Male", "channel_tag": "tech"},
        {"id": "nova", "name": "Nova (Energetic, Cheerful, Bright Kids)", "gender": "Female", "channel_tag": "kids"},
        {"id": "shimmer", "name": "Shimmer (Clear, Warm, Emotional)", "gender": "Female", "channel_tag": "elders"},
    ],
    "elevenlabs": [
        {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel (Calm, Narrative, Clear)", "gender": "Female", "channel_tag": "general"},
        {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi (Friendly, Animated, Story)", "gender": "Female", "channel_tag": "kids"},
        {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella (Bubbly, Playful Character)", "gender": "Female", "channel_tag": "kids"},
        {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni (Warm, Gentle, Deep)", "gender": "Male", "channel_tag": "elders"},
        {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam (Rich, Narrative Storyteller)", "gender": "Male", "channel_tag": "elders"},
        {"id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh (Modern, Tech, Authoritative)", "gender": "Male", "channel_tag": "tech"},
    ]
}

CHANNEL_VOICE_PROFILES = {
    "kids": {
        "channel_id": "kids",
        "description": "Preschool & Children Animation. Multi-character dialogue support with cheerful pacing.",
        "pacing": "+5%",
        "pitch": "+4Hz",
        "roles": {
            "narrator": {
                "name": "Storyteller / Teacher",
                "edge_tts": "en-US-AnaNeural",
                "openai_tts": "nova",
                "elevenlabs": "AZnzlk1XvdvUeBnXmlld",
                "rate": "+0%",
                "pitch": "+2Hz"
            },
            "character_1": {
                "name": "Character 1 (Pip / Bunny / Curious Young)",
                "edge_tts": "en-US-AriaNeural",
                "openai_tts": "fable",
                "elevenlabs": "EXAVITQu4vr4xnSDxMaL",
                "rate": "+6%",
                "pitch": "+6Hz"
            },
            "character_2": {
                "name": "Character 2 (Barnaby / Bear / Gentle Companion)",
                "edge_tts": "en-US-GuyNeural",
                "openai_tts": "alloy",
                "elevenlabs": "ErXwobaYiN019PkySvjV",
                "rate": "-4%",
                "pitch": "-4Hz"
            },
            "character_3": {
                "name": "Character 3 (Professor Owl / Wise Guide)",
                "edge_tts": "en-GB-RyanNeural",
                "openai_tts": "echo",
                "elevenlabs": "pNInz6obpgDQGcFmaJgB",
                "rate": "-2%",
                "pitch": "+0Hz"
            }
        }
    },
    "wondersaga-tv": {
        "channel_id": "wondersaga-tv",
        "description": "Wonder Saga TV. Myth, legendary tales, mysterious phenomena, and inspiring wonders.",
        "pacing": "-5%",
        "pitch": "-1Hz",
        "roles": {
            "narrator": {
                "name": "Narrator (Wonder Storyteller)",
                "edge_tts": "en-GB-RyanNeural",
                "openai_tts": "echo",
                "elevenlabs": "pNInz6obpgDQGcFmaJgB",
                "rate": "-5%",
                "pitch": "-1Hz"
            },
            "character_1": {
                "name": "Character 1 (Warm Narrator)",
                "edge_tts": "en-US-GuyNeural",
                "openai_tts": "onyx",
                "elevenlabs": "ErXwobaYiN019PkySvjV",
                "rate": "-4%",
                "pitch": "-2Hz"
            },
            "character_2": {
                "name": "Character 2 (Tender Matriarch)",
                "edge_tts": "en-GB-SoniaNeural",
                "openai_tts": "shimmer",
                "elevenlabs": "21m00Tcm4TlvDq8ikWAM",
                "rate": "-4%",
                "pitch": "+0Hz"
            }
        }
    },
    "insightspark-tv": {
        "channel_id": "insightspark-tv",
        "description": "Mind-bending science, deep mysteries, and cosmic tech. Authoritative and punchy.",
        "pacing": "+0%",
        "pitch": "+0Hz",
        "roles": {
            "narrator": {
                "name": "Primary Anchor / Storyteller",
                "edge_tts": "en-US-ChristopherNeural",
                "openai_tts": "onyx",
                "elevenlabs": "TxGEqnHWrfWFTfGW9XjX",
                "rate": "+0%",
                "pitch": "+0Hz"
            },
            "character_1": {
                "name": "Analyst / Co-Host",
                "edge_tts": "en-US-JennyNeural",
                "openai_tts": "shimmer",
                "elevenlabs": "21m00Tcm4TlvDq8ikWAM",
                "rate": "+0%",
                "pitch": "+0Hz"
            }
        }
    }
}
# Backward-compatibility aliases
CHANNEL_VOICE_PROFILES["the-ai-brief-it"] = CHANNEL_VOICE_PROFILES["insightspark-tv"]
CHANNEL_VOICE_PROFILES["elders"] = CHANNEL_VOICE_PROFILES["wondersaga-tv"]


def get_channel_voice_profile(channel_id: str) -> dict:
    """Retrieve the voice profile configuration for a given channel."""
    clean_id = (channel_id or "insightspark-tv").lower().strip()
    alias_map = {"the-ai-brief-it": "insightspark-tv", "elders": "wondersaga-tv"}
    resolved = alias_map.get(clean_id, clean_id)
    return CHANNEL_VOICE_PROFILES.get(resolved, CHANNEL_VOICE_PROFILES["insightspark-tv"])


def resolve_speaker_role(speaker_tag: str) -> str:
    """
    Map raw speaker names (e.g., 'Pip', 'Bunny', 'Narrator', 'Character 1', 'Bear')
    to standard profile role keys ('narrator', 'character_1', 'character_2', 'character_3').
    """
    tag = (speaker_tag or "").strip().lower()
    if not tag or "narrator" in tag or "host" in tag or "storyteller" in tag:
        return "narrator"
    
    if any(k in tag for k in ("char 1", "character 1", "bunny", "pip", "kitten", "child", "young")):
        return "character_1"
    elif any(k in tag for k in ("char 2", "character 2", "bear", "barnaby", "grandpa", "elder", "father")):
        return "character_2"
    elif any(k in tag for k in ("char 3", "character 3", "owl", "fox", "teacher", "grandma")):
        return "character_3"
    
    return "character_1"


def get_voice_for_speaker(
    channel_id: str,
    speaker_tag: str,
    provider: str = "edge-tts"
) -> Dict[str, Any]:
    """
    Returns voice configuration (voice ID, rate, pitch) for a speaker in a given channel.
    """
    profile = get_channel_voice_profile(channel_id)
    role_key = resolve_speaker_role(speaker_tag)
    role_cfg = profile.get("roles", {}).get(role_key)
    
    if not role_cfg:
        role_cfg = profile.get("roles", {}).get("narrator", {})

    provider_clean = (provider or "edge-tts").lower().strip()
    if provider_clean == "openai-tts" or provider_clean == "openai":
        voice_id = role_cfg.get("openai_tts", "alloy")
    elif provider_clean == "elevenlabs":
        voice_id = role_cfg.get("elevenlabs", "21m00Tcm4TlvDq8ikWAM")
    else:
        voice_id = role_cfg.get("edge_tts", "en-US-ChristopherNeural")

    return {
        "role": role_key,
        "name": role_cfg.get("name", "Speaker"),
        "voice_id": voice_id,
        "rate": role_cfg.get("rate", profile.get("pacing", "+0%")),
        "pitch": role_cfg.get("pitch", profile.get("pitch", "+0Hz")),
        "provider": provider_clean
    }


def parse_dialogue_line(raw_text: str) -> tuple[str, str]:
    """
    Detects if a script line contains dialogue speaker prefixes, e.g.:
    "Pip: Look at that giant rainbow!" -> ("Pip", "Look at that giant rainbow!")
    "Narrator: Once upon a time..." -> ("Narrator", "Once upon a time...")
    If no speaker prefix is found, defaults to ("Narrator", raw_text).
    """
    if not raw_text:
        return ("Narrator", "")
    match = re.match(r"^([A-Za-z0-9_\s]{2,20})\s*:\s*(.+)$", raw_text.strip(), re.DOTALL)
    if match:
        speaker = match.group(1).strip()
        speech = match.group(2).strip()
        return (speaker, speech)
    return ("Narrator", raw_text.strip())
