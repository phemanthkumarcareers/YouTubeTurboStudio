"""
Kids Story & Educational Script Generator
Generates age-adapted scripts for Alphabet, Numbers, Stories, Bedtime Stories, and Shorts.
Ensures educational clarity, positive emotional reinforcement, and automatic safety validation.
"""
from typing import Dict, Any, Optional
from kids.profiles import get_age_profile, AgeProfile
from kids.safeguards import kids_safeguards
from core.logger import log_info, log_warn


class KidsStoryGenerator:
    """Generates structured educational scripts and stories tailored for children."""

    def generate_educational_script(
        self,
        category: str = "alphabet",
        topic: str = "",
        age_group: str = "4-5"
    ) -> Dict[str, Any]:
        """
        Generates an educational script (alphabet, numbers, colors).
        """
        profile = get_age_profile(age_group)

        if category in ("numbers", "counting"):
            title = topic or "Count with Sparky: 1, 2, 3 Shiny Stars!"
            script = {
                "title": title,
                "category": "numbers",
                "target_number": 3,
                "scenes": [
                    {
                        "scene_id": 1,
                        "title": "Star Number One",
                        "narration": "Hello friends! Look up in the sky! Here comes star number 1! One bright golden star shining for you!",
                        "duration": 4.5,
                        "bg_style": "starry_space",
                        "character": "sparky_host",
                        "prop": "star",
                        "prop_count": 1
                    },
                    {
                        "scene_id": 2,
                        "title": "Star Number Two",
                        "narration": "Twinkle twinkle! Another friend joins! That makes 1, and now 2! Two happy dancing stars!",
                        "duration": 4.5,
                        "bg_style": "starry_space",
                        "character": "sparky_host",
                        "prop": "star",
                        "prop_count": 2
                    },
                    {
                        "scene_id": 3,
                        "title": "Star Number Three",
                        "narration": "And look right there! Star number 3! Let's count together: 1, 2, 3! You did an amazing job!",
                        "duration": 5.0,
                        "bg_style": "starry_space",
                        "character": "sparky_host",
                        "prop": "star",
                        "prop_count": 3
                    }
                ]
            }

        elif category in ("colors", "shapes"):
            title = topic or "Fun with Colors: The Red Shiny Apple"
            script = {
                "title": title,
                "category": "colors",
                "scenes": [
                    {
                        "scene_id": 1,
                        "title": "Bright Red Discovery",
                        "narration": "Welcome explorers! Look what we found in the sunny garden! A beautiful, bright red apple!",
                        "duration": 4.5,
                        "bg_style": "vibrant_sky",
                        "character": "sparky_host",
                        "prop": "apple"
                    },
                    {
                        "scene_id": 2,
                        "title": "Can You Say Red?",
                        "narration": "Can you say red with me? Red! Like a strawberry and a happy fire truck!",
                        "duration": 4.5,
                        "bg_style": "playful_park",
                        "character": "sparky_host",
                        "prop": "apple"
                    },
                    {
                        "scene_id": 3,
                        "title": "Wonderful Job",
                        "narration": "Red is all around us! Keep your eyes open for more colors today! You are fantastic!",
                        "duration": 4.5,
                        "bg_style": "playful_park",
                        "character": "sparky_host",
                        "prop": "balloon"
                    }
                ]
            }

        else:
            # Default: Alphabet / Phonics
            title = topic or "Learn Alphabet: A is for Apple!"
            script = {
                "title": title,
                "category": "alphabet",
                "letter": "A",
                "scenes": [
                    {
                        "scene_id": 1,
                        "title": "Letter A Greeting",
                        "narration": "Hello little learners! Today we meet the very first letter of the alphabet: the letter A!",
                        "duration": 4.5,
                        "bg_style": "chalkboard",
                        "character": "ollie_owl",
                        "prop": "alphabet_block"
                    },
                    {
                        "scene_id": 2,
                        "title": "A is for Apple",
                        "narration": "A makes the sound: ah, ah! A is for Apple! Sweet, crunchy, and bright red!",
                        "duration": 4.5,
                        "bg_style": "vibrant_sky",
                        "character": "ollie_owl",
                        "prop": "apple"
                    },
                    {
                        "scene_id": 3,
                        "title": "Cheering Success",
                        "narration": "You learned the letter A! Give yourself a big clap! You are a brilliant superstar!",
                        "duration": 4.5,
                        "bg_style": "vibrant_sky",
                        "character": "ollie_owl",
                        "prop": "star"
                    }
                ]
            }

        # Validate with safeguards gate
        gate_res = kids_safeguards.evaluate(script)
        if not gate_res["passed"]:
            raise ValueError(f"Generated educational script failed safeguards: {gate_res['violations']}")

        return script

    def generate_bedtime_story(
        self,
        character: str = "pip_bunny",
        topic: str = "",
        age_group: str = "2-3"
    ) -> Dict[str, Any]:
        """
        Generates a calm, gentle bedtime story with soothing pacing.
        """
        title = topic or "Pip Bunny's Gentle Starlit Dream"
        script = {
            "title": title,
            "category": "bedtime_stories",
            "scenes": [
                {
                    "scene_id": 1,
                    "title": "Twilight Falls",
                    "narration": "The golden sun dips softly below the hill. In the cozy green meadow, little Pip Bunny yawns a warm gentle yawn.",
                    "duration": 5.5,
                    "bg_style": "starry_space",
                    "character": "pip_bunny",
                    "prop": "star"
                },
                {
                    "scene_id": 2,
                    "title": "Soft Whispering Breeze",
                    "narration": "The evening breeze whispers through the willow trees. The moon smiles like a cozy lantern in the night sky.",
                    "duration": 5.5,
                    "bg_style": "starry_space",
                    "character": "pip_bunny",
                    "prop": "star"
                },
                {
                    "scene_id": 3,
                    "title": "Sweet Dreams",
                    "narration": "Close your eyes, little dreamer. Sleep warm, sleep safe. Tomorrow brings another joyful day. Goodnight, sweet friend.",
                    "duration": 6.0,
                    "bg_style": "starry_space",
                    "character": "pip_bunny",
                    "prop": "star"
                }
            ]
        }

        gate_res = kids_safeguards.evaluate(script)
        if not gate_res["passed"]:
            raise ValueError(f"Bedtime story failed safeguards: {gate_res['violations']}")

        return script

    def generate_kids_short(
        self,
        topic: str = "Find the Sparkly Star!",
        age_group: str = "4-5"
    ) -> Dict[str, Any]:
        """
        Generates a fast-paced, vertical interactive Short.
        """
        script = {
            "title": topic,
            "category": "educational_shorts",
            "scenes": [
                {
                    "scene_id": 1,
                    "title": "The Quest",
                    "narration": "Can you spot the magical gold star hiding in the sky?",
                    "duration": 3.5,
                    "bg_style": "vibrant_sky",
                    "character": "sparky_host",
                    "prop": "magnifying_glass"
                },
                {
                    "scene_id": 2,
                    "title": "There It Is!",
                    "narration": "Look right up there! Twinkling bright! You found it! High five, superstar!",
                    "duration": 3.5,
                    "bg_style": "starry_space",
                    "character": "sparky_host",
                    "prop": "star"
                }
            ]
        }

        gate_res = kids_safeguards.evaluate(script)
        if not gate_res["passed"]:
            raise ValueError(f"Short failed safeguards: {gate_res['violations']}")

        return script


kids_story_generator = KidsStoryGenerator()
