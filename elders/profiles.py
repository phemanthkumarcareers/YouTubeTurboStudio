"""
Profiles & Content Categories — Wonder Saga TV
Defines categories, animation pacing rules, and voice profiles
for Wonder Saga TV.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class EldersPacingProfile:
    name: str = "Cinematic Reflective"
    words_per_minute: int = 110
    seconds_per_scene: float = 6.0
    camera_style: str = "slow_zoom_in"  # Gentle, unhurried camera
    gesture_frequency: float = 0.4      # Restrained, dignified gestures
    tone: str = "Calm, empathetic, nostalgic, dignified, and emotionally resonant"


ELDERS_CATEGORIES = [
    "life_lessons",
    "nostalgia",
    "family_stories",
    "inspirational_stories",
    "friendship_stories",
    "village_city_stories",
    "reflective_storytelling"
]

ELDERS_VOICES = {
    "christopher": {
        "id": "en-US-ChristopherNeural",
        "name": "Christopher (Wise Grandfather)",
        "rate": "-4%",
        "pitch": "-2Hz"
    },
    "brian": {
        "id": "en-US-BrianNeural",
        "name": "Brian (Warm Storyteller)",
        "rate": "-3%",
        "pitch": "-1Hz"
    },
    "emma": {
        "id": "en-US-EmmaNeural",
        "name": "Emma (Gentle Matriarch)",
        "rate": "-3%",
        "pitch": "+0Hz"
    }
}


def get_elders_pacing_profile(category: str = "life_lessons") -> EldersPacingProfile:
    """Retrieve pacing profile by category."""
    if category == "nostalgia":
        return EldersPacingProfile(
            name="Nostalgic Reflection",
            words_per_minute=105,
            seconds_per_scene=6.5
        )
    elif category == "bedtime_reflection":
        return EldersPacingProfile(
            name="Quiet Evening",
            words_per_minute=95,
            seconds_per_scene=7.0
        )
    return EldersPacingProfile()
