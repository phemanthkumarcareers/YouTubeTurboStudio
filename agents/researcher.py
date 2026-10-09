"""
AI Topic Researcher Agent
Brainstorms viral, trending, high-retention video concepts based on channel niche and focus angles.
"""
import json
import random
import re
from config import load_config, load_banned_topics
from agents.llm_client import generate
from core.logger import log_info, log_warn, log_success

FOCUS_ANGLES = [
    "Theoretical Physics & Time Travel",
    "The Dark Forest Theory & Cosmic Fermi Paradox",
    "Mind-bending Mathematical Paradoxes",
    "Frightening AI Horizons & Technological Singularity",
    "Existential Psychology & Cognitive Biases",
    "The Limits of Human Biology & Immortality",
    "Deep-Sea Cryptogeography & The Ocean Abyss",
    "Cosmic Scale, Black Holes, and False Vacuum Decay",
    "Ancient Civilizations & Erased Human History",
    "Quantum Mechanics & Multiverse Realities",
    "Cutting-edge Biotechnology & Synthetic Life",
    "The Simulation Hypothesis & Computational Reality"
]


def clean_json_response(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n", "", text)
        text = re.sub(r"\n```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try extracting JSON object substring
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise ValueError(f"Could not parse valid JSON from AI response: {text[:200]}")


def research_topic(topic_override: str = "", focus_angle: str = "", video_type: str = "normal") -> dict:
    """
    Generate an engaging research brief for a video tailored to the active channel.
    """
    cfg = load_config()
    channel_name = cfg.get("channel_name", "YouTube Channel")
    channel_desc = cfg.get("channel_description", "")
    channel_niche = cfg.get("channel_niche", "")
    channel_angles = cfg.get("focus_angles") or FOCUS_ANGLES
    banned = load_banned_topics()
    
    if not focus_angle:
        focus_angle = random.choice(channel_angles) if channel_angles else random.choice(FOCUS_ANGLES)

    banned_str = ", ".join(f'"{b}"' for b in banned[:25])

    if topic_override and topic_override.strip():
        log_info(f"Researching custom user topic: '{topic_override}' for '{channel_name}'...")
        prompt = f"""You are a senior YouTube content strategist for '{channel_name}'.
Channel Niche: {channel_niche}
Channel Profile:
{channel_desc}

The user wants a video specifically about: "{topic_override.strip()}"
Format: {"YouTube Shorts (vertical 9:16, punchy 50-60 second viral story)" if video_type == "shorts" else "Long-form YouTube Documentary (16:9 cinematic 3-8 minute deep dive)"}

Analyze this topic and produce a compelling research dossier in valid JSON format:
{{
  "topic": "{topic_override.strip()}",
  "hook_question": "A provocative, irresistible opening question that makes viewers stop scrolling",
  "why_now": "Why this specific topic is fascinating, relevant, or mind-expanding right now",
  "key_points": [
    "Core premise and intriguing setup",
    "Underlying scientific or historical mechanism",
    "Startling counter-intuitive revelation or twist",
    "Broader existential or philosophical implication"
  ],
  "visual_theme": "Suggested visual atmosphere and color palette (e.g. dark cosmic blue, retro cyberpunk, minimalist eerie)"
}}

Output ONLY the JSON object. Do not wrap in markdown or backticks."""
    else:
        log_info(f"Researching trending topic in angle: '{focus_angle}' for '{channel_name}'...")
        prompt = f"""You are a master YouTube content strategist for '{channel_name}'.
Channel Niche: {channel_niche}
Channel Profile:
{channel_desc}

Focus Angle: {focus_angle}
Format: {"YouTube Shorts (vertical 9:16, 50-60 seconds)" if video_type == "shorts" else "Long-form YouTube Documentary (16:9 cinematic 3-8 minutes)"}

DO NOT use any of these banned or recently covered topics:
[{banned_str}]

Develop an original, mind-bending video concept with extraordinary retention potential. Return valid JSON with this exact structure:
{{
  "topic": "Concise, punchy topic title",
  "hook_question": "Irresistible opening hook question that challenges common sense",
  "why_now": "Why this concept is urgent, startling, or deeply compelling",
  "key_points": [
    "Core premise and intriguing setup",
    "Underlying scientific or historical mechanism",
    "Startling counter-intuitive revelation or twist",
    "Broader existential or philosophical implication"
  ],
  "visual_theme": "Visual aesthetic guide (e.g. deep cosmic space, underwater bioluminescence, macro quantum realms)"
}}

Output ONLY the JSON object. Do not wrap in markdown or backticks."""

    raw_resp = generate(prompt, json_mode=True)
    data = clean_json_response(raw_resp)
    log_success(f"Topic selected: '{data.get('topic')}'")
    return data
