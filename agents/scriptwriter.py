"""
AI Scriptwriter Agent
Transforms topic research into high-retention cinematic video scripts with visual query cues.
"""
import json
import re
from agents.llm_client import generate
from agents.researcher import clean_json_response
from core.logger import log_info, log_success


def write_script(research: dict, video_type: str = "normal", custom_instructions: str = "") -> dict:
    """
    Generate complete script with section breakdowns and stock footage search queries.
    """
    topic = research.get("topic", "Mysteries of the Universe")
    hook = research.get("hook_question", "")
    key_points = research.get("key_points", [])

    is_shorts = (video_type == "shorts")
    if is_shorts:
        target_duration = "50-60 seconds (135-160 spoken words total across 5 to 6 dynamic, punchy scenes)"
        format_guideline = (
            "YouTube Shorts (fast-paced, high curiosity, punchy, dynamic scene shifts every 8-10 seconds). "
            "Total word count MUST be between 135 and 160 words to ensure exactly 50-60 seconds of narration."
        )
        sections_req = (
            "For Shorts: exactly 5 to 6 sections. Each section narration must be 20 to 30 words (approx 9-11 seconds of speech). "
            "Total across all sections must be 135-160 words."
        )
    else:
        target_duration = "3 to 8 minutes (500-1100 spoken words total across 8 to 14 cinematic, in-depth sections)"
        format_guideline = (
            "Long-form YouTube Documentary / Deep Explainer (3 to 8 minutes, escalating mystery, rich details, scientific and philosophical depth). "
            "Total word count MUST be between 500 and 1100 words."
        )
        sections_req = (
            "For Long-form: 8 to 14 sequential in-depth sections. Each section narration must be 45 to 85 words (approx 20-35 seconds of speech). "
            "Structure: 1. Intriguing Hook, 2. Origin & Paradox, 3-5. Deep Scientific/Historical Mechanics, 6-9. Unsettling Twists & Revelations, 10-12. Philosophical Implications, 13-14. Profound Conclusion."
        )

    log_info(f"Drafting script for '{topic}' ({'Shorts 50-60s' if is_shorts else 'Long-form 3-8 mins'})...")

    prompt = f"""You are an elite YouTube documentary writer whose scripts achieve 70%+ audience retention.
Write a complete, gripping script based on this topic research:

Topic: {topic}
Opening Hook: {hook}
Core Points: {json.dumps(key_points)}
Target Length: {target_duration}
Format: {format_guideline}
Additional User Direction: {custom_instructions if custom_instructions else "None"}

Requirements:
1. "title": Catchy, clickable YouTube title (under 65 characters, high curiosity gap, NO misleading clickbait).
2. "description": 2-3 paragraph YouTube description including hook, key questions, and call to action.
3. "tags": 10-14 relevant SEO tags.
4. "sections": Array of sequential sections.
   {sections_req}
   Each section MUST have:
   - "id": 1, 2, 3...
   - "title": Section header / subtitle (e.g. "The Anomaly", "Event Horizon", "The Unseen Force")
   - "narration": Exact spoken voiceover words. Cinematic, natural speech cadence. No markdown formatting or sound effect cues.
   - "visual_query": 2 to 4 English keywords best suited for searching stock videos/photos on Pexels/Pixabay (e.g. "deep space galaxy", "cyberpunk neural network", "ancient ruins desert", "ocean storm lightning").

Output strictly valid JSON with this structure:
{{
  "title": "Title here",
  "description": "Full description here",
  "tags": ["tag1", "tag2", "tag3"],
  "sections": [
    {{
      "id": 1,
      "title": "The Anomaly",
      "narration": "Exact narration words for this section...",
      "visual_query": "deep space nebula"
    }}
  ]
}}

Do NOT output any markdown backticks, explanations, or commentary. Only the raw JSON object."""

    raw_resp = generate(prompt, json_mode=True)
    script_data = clean_json_response(raw_resp)
    script_data["video_type"] = video_type
    log_success(f"Script created with {len(script_data.get('sections', []))} sections: '{script_data.get('title')}'")
    return script_data
