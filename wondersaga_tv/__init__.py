"""
Channel Package — Wonder Saga TV
Provides profiles, character packs, story generation, and QC.
"""
from wondersaga_tv.profiles import (
    ELDERS_CATEGORIES,
    ELDERS_VOICES,
    EldersPacingProfile,
    get_elders_pacing_profile
)
from wondersaga_tv.characters import EldersCharacterPack, elders_characters
from wondersaga_tv.story_generator import EldersStoryGenerator, elders_story_generator
from wondersaga_tv.qc import EldersQCChecker, elders_qc

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
