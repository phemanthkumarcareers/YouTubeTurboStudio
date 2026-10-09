"""
Elders Channel Package — Golden Stories & Wisdom
Provides profiles, adult character packs, story generation, and Elders QC.
"""
from elders.profiles import (
    ELDERS_CATEGORIES,
    ELDERS_VOICES,
    EldersPacingProfile,
    get_elders_pacing_profile
)
from elders.characters import EldersCharacterPack, elders_characters
from elders.story_generator import EldersStoryGenerator, elders_story_generator
from elders.qc import EldersQCChecker, elders_qc

__all__ = [
    "ELDERS_CATEGORIES",
    "ELDERS_VOICES",
    "EldersPacingProfile",
    "get_elders_pacing_profile",
    "EldersCharacterPack",
    "elders_characters",
    "EldersStoryGenerator",
    "elders_story_generator",
    "EldersQCChecker",
    "elders_qc"
]
