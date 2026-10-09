"""
Kids Channel Package — YouTubeTurboStudio
Provides age profiles, safeguards hard gate, recurring characters,
story/educational script generation, and Kids-specific QC.
"""
from kids.profiles import AGE_PROFILES, CONTENT_CATEGORIES, AgeProfile, get_age_profile
from kids.safeguards import KidsSafeguardsGate, kids_safeguards
from kids.characters import KidsCharacterPack, kids_characters
from kids.story_generator import KidsStoryGenerator, kids_story_generator
from kids.qc import KidsQCChecker, kids_qc

__all__ = [
    "AGE_PROFILES",
    "CONTENT_CATEGORIES",
    "AgeProfile",
    "get_age_profile",
    "KidsSafeguardsGate",
    "kids_safeguards",
    "KidsCharacterPack",
    "kids_characters",
    "KidsStoryGenerator",
    "kids_story_generator",
    "KidsQCChecker",
    "kids_qc"
]
