"""
Elders Story & Script Generator
Generates reflective, dignified, unhurried scripts for mature audiences
covering life lessons, nostalgic recollections, and generational wisdom.
Supports both Long-form (16:9) and Shorts (9:16).
"""
from typing import Dict, Any, Optional
from elders.profiles import get_elders_pacing_profile


class EldersStoryGenerator:
    """Generates heartwarming, philosophical narratives for Wonder Saga TV."""

    def generate_story(
        self,
        category: str = "life_lessons",
        topic: str = "",
        character: str = "arthur_storyteller",
        format_type: str = "normal"
    ) -> Dict[str, Any]:
        """
        Generates a multi-scene long-form or short-form narrative.
        format_type: 'normal' (16:9) or 'shorts' (9:16)
        """
        is_shorts = (format_type == "shorts")

        if is_shorts:
            # 2 scenes, punchy yet poetic life reflection (45-55s)
            title = topic or "A Gentle Thought on Rushing Through Life"
            return {
                "title": title,
                "category": category,
                "format": "shorts",
                "character": character,
                "scenes": [
                    {
                        "scene_id": 1,
                        "title": "The Hurried World",
                        "narration": "In youth, we measure life by how quickly we can run. We hurry from one milestone to the next, afraid of falling behind.",
                        "duration": 5.5,
                        "bg_style": "sunset_porch",
                        "character": character,
                        "prop": "pocket_watch"
                    },
                    {
                        "scene_id": 2,
                        "title": "The Quiet Truth",
                        "narration": "With time, you realize the sweetest parts were never at the finish line—they were the gentle conversations held along the way. Slow down today.",
                        "duration": 6.5,
                        "bg_style": "cozy_study",
                        "character": character,
                        "prop": "tea_mug"
                    }
                ]
            }

        # Long-form / Standard Format (16:9)
        if category == "nostalgia":
            title = topic or "The Symphony of the Old Front Porch"
            return {
                "title": title,
                "category": "nostalgia",
                "format": "normal",
                "character": character,
                "scenes": [
                    {
                        "scene_id": 1,
                        "title": "Evening Twilight",
                        "narration": "There was a time when the day didn't end with glowing screens, but with the creak of a wooden rocking chair on the front porch.",
                        "duration": 6.0,
                        "bg_style": "sunset_porch",
                        "character": character,
                        "prop": "vintage_book"
                    },
                    {
                        "scene_id": 2,
                        "title": "Shared Presence",
                        "narration": "Neighbors would stroll past, raising a hand in greeting. We spoke of simple things: the coming rain, the harvest, and the quiet beauty of twilight.",
                        "duration": 6.5,
                        "bg_style": "sunset_porch",
                        "character": character,
                        "prop": "tea_mug"
                    },
                    {
                        "scene_id": 3,
                        "title": "Timeless Wisdom",
                        "narration": "Those quiet hours gave our souls room to breathe. Some traditions deserve to be brought back into our modern lives.",
                        "duration": 6.0,
                        "bg_style": "cozy_study",
                        "character": character,
                        "prop": "pocket_watch"
                    }
                ]
            }

        # Default: Life Lessons / Generational Wisdom
        title = topic or "The Tea Mug and the Art of Patience"
        return {
            "title": title,
            "category": "life_lessons",
            "format": "normal",
            "character": character,
            "scenes": [
                {
                    "scene_id": 1,
                    "title": "The Warm Hearth",
                    "narration": "Good evening, my dear friends. Come in from the chill, sit by the warm fire, and let the rush of the world fade away.",
                    "duration": 5.5,
                    "bg_style": "warm_hearth",
                    "character": character,
                    "prop": "tea_mug"
                },
                {
                    "scene_id": 2,
                    "title": "Lessons of Time",
                    "narration": "A wise teacher once told me: an oak tree does not rush its roots, and true wisdom cannot be hurried by impatience.",
                    "duration": 6.0,
                    "bg_style": "cozy_study",
                    "character": character,
                    "prop": "vintage_book"
                },
                {
                    "scene_id": 3,
                    "title": "Evening Benediction",
                    "narration": "Trust where you are on your journey today. May your evening be filled with peace, gratitude, and a restful heart.",
                    "duration": 6.0,
                    "bg_style": "cozy_study",
                    "character": character,
                    "prop": "reading_glasses"
                }
            ]
        }


elders_story_generator = EldersStoryGenerator()
