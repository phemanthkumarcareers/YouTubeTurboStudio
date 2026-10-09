"""
Kids Age Profiles & Content Categories
Defines structured guidelines, pacing rules, and vocabulary constraints
for Toddlers (2-3), Preschoolers (4-5), and Early Elementary (6-8).
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class AgeProfile:
    age_id: str  # "2-3", "4-5", "6-8"
    name: str    # "Toddlers", "Preschool", "Early Elementary"
    min_age: int
    max_age: int
    words_per_minute: int
    max_sentence_length: int
    pacing_seconds_per_scene: float
    tone: str
    allowed_categories: List[str]
    sample_vocabulary: List[str] = field(default_factory=list)


AGE_PROFILES: Dict[str, AgeProfile] = {
    "2-3": AgeProfile(
        age_id="2-3",
        name="Toddlers",
        min_age=2,
        max_age=3,
        words_per_minute=90,
        max_sentence_length=7,
        pacing_seconds_per_scene=5.0,
        tone="Soothing, rhythmic, highly repetitive, cheerful",
        allowed_categories=["colors", "shapes", "numbers_1_to_3", "animal_sounds", "bedtime", "rhymes"],
        sample_vocabulary=["happy", "sun", "star", "red", "blue", "ball", "doggy", "quack", "night", "sleep"]
    ),
    "4-5": AgeProfile(
        age_id="4-5",
        name="Preschool",
        min_age=4,
        max_age=5,
        words_per_minute=115,
        max_sentence_length=12,
        pacing_seconds_per_scene=4.0,
        tone="Joyful, encouraging, musical, exploratory",
        allowed_categories=["alphabet", "phonics", "numbers_1_to_10", "colors_shapes", "stories", "good_habits", "bedtime"],
        sample_vocabulary=["wonder", "friend", "share", "explore", "sparkle", "journey", "curious", "smile"]
    ),
    "6-8": AgeProfile(
        age_id="6-8",
        name="Early Elementary",
        min_age=6,
        max_age=8,
        words_per_minute=135,
        max_sentence_length=16,
        pacing_seconds_per_scene=3.5,
        tone="Engaging, dynamic, educational, STEM-curious, adventure",
        allowed_categories=["science_curiosity", "alphabet_stories", "math_puzzles", "moral_adventures", "bedtime_tales"],
        sample_vocabulary=["discovery", "gravity", "adventure", "invent", "courage", "teamwork", "mystery"]
    )
}


CONTENT_CATEGORIES = [
    "alphabet",
    "phonics",
    "numbers",
    "colors_shapes",
    "animals",
    "good_habits",
    "stories",
    "moral_stories",
    "bedtime_stories",
    "poems_rhymes"
]


def get_age_profile(age_str: Optional[str]) -> AgeProfile:
    """Retrieve profile by age tag (default: '4-5' for preschool)."""
    if not age_str:
        return AGE_PROFILES["4-5"]
    clean = str(age_str).strip()
    if clean in AGE_PROFILES:
        return AGE_PROFILES[clean]
    # Check partial match
    for k, v in AGE_PROFILES.items():
        if k in clean:
            return v
    return AGE_PROFILES["4-5"]
