"""
Topic Engine — The AI Brief It
Implements Topic Candidate Ranking and User Topic Mode.
Core Pillars:
1. Human body and brain
2. Space and extreme science
3. Future science and technology
"""
import json
import random
import re
from typing import Dict, Any, List, Optional
from config import load_banned_topics
from agents.llm_client import generate
from core.logger import log_info, log_warn, log_success

CORE_PILLARS = [
    {
        "id": "human_body_brain",
        "name": "Human Body and Brain",
        "themes": [
            "Neuroscience anomalies and consciousness paradoxes",
            "Extreme human physiology under limits of survival",
            "Hidden biological clocks and sensory illusions",
            "Memory distortion, dreams, and brain regeneration"
        ]
    },
    {
        "id": "space_extreme_science",
        "name": "Space and Extreme Science",
        "themes": [
            "Black hole interiors, event horizons, and time dilation",
            "Strange matter, false vacuum decay, and quantum gravity",
            "Cosmic radiation, dark energy, and the fate of the universe",
            "Extreme planetary conditions and rogue planets"
        ]
    },
    {
        "id": "future_science_tech",
        "name": "Future Science and Technology",
        "themes": [
            "Synthetic biology, CRISPR, and genetic immortality",
            "Artificial Superintelligence and consciousness emergence",
            "Fusion energy, antimatter drives, and interstellar travel",
            "Quantum computing paradoxes and simulated universes"
        ]
    }
]


def clean_json_response(raw: str) -> dict:
    """Extract and parse clean JSON from AI output."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n", "", text)
        text = re.sub(r"\n```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        m_arr = re.search(r"\[.*\]", text, re.DOTALL)
        if m_arr:
            return json.loads(m_arr.group(0))
        raise ValueError(f"Could not parse valid JSON from AI response: {text[:200]}")


def discover_and_rank_topics(
    video_type: str = "normal",
    preferred_pillar: Optional[str] = None,
    candidate_count: int = 15
) -> Dict[str, Any]:
    """
    Automatic Topic Mode:
    1. Generates 15-20 diverse candidates across core science pillars
    2. Scores candidates across 6 criteria (curiosity, visual potential, novelty, credibility, impact, channel fit)
    3. Selects the top-ranked candidate and returns full research dossier
    """
    banned = load_banned_topics()
    banned_str = ", ".join(f'"{b}"' for b in banned[:30])

    pillar = None
    if preferred_pillar:
        pillar = next((p for p in CORE_PILLARS if p["id"] == preferred_pillar), None)
    if not pillar:
        pillar = random.choice(CORE_PILLARS)

    log_info(f"[TOPIC ENGINE] Brainstorming {candidate_count} candidates in pillar: '{pillar['name']}'...")

    prompt = f"""You are the Lead Science Content Director for 'The AI Brief It' (mind-blowing science & future technology).
Pillar: {pillar['name']}
Focus Themes: {json.dumps(pillar['themes'])}
Format: {"YouTube Shorts (9:16 vertical, 50-60s punchy)" if video_type == "shorts" else "Long-form Documentary (16:9 cinematic, 3-8m)"}

DO NOT use any of these banned or saturated topics:
[{banned_str}]

Brainstorm exactly {candidate_count} distinct science video concepts. For each concept, assign scores from 1 to 10 for:
- curiosity (unresolved question that sparks intense interest)
- visual_potential (ability to illustrate with stunning space, microscopic, or tech footage)
- novelty (fresh angle, avoiding common generic science clichés)
- scientific_credibility (backed by real physics, biology, or peer-reviewed science)
- emotional_impact (sense of awe, existential wonder, or suspense)

Return strictly valid JSON:
{{
  "candidates": [
    {{
      "title": "Title under 65 chars",
      "hook_question": "Provocative question",
      "core_mechanism": "Underlying science in 1 sentence",
      "curiosity": 9,
      "visual_potential": 9,
      "novelty": 8,
      "scientific_credibility": 9,
      "emotional_impact": 8,
      "pillar": "{pillar['id']}"
    }}
  ]
}}
Output ONLY raw JSON."""

    raw = generate(prompt, json_mode=True)
    parsed = clean_json_response(raw)
    candidates = parsed.get("candidates", [])

    if not candidates:
        raise ValueError("Topic generator returned 0 candidates")

    # Score and rank candidates
    scored = []
    for c in candidates:
        # Weighted score: curiosity (25%), visual (25%), novelty (20%), credibility (15%), impact (15%)
        total = (
            c.get("curiosity", 5) * 0.25 +
            c.get("visual_potential", 5) * 0.25 +
            c.get("novelty", 5) * 0.20 +
            c.get("scientific_credibility", 5) * 0.15 +
            c.get("emotional_impact", 5) * 0.15
        ) * 10
        c["composite_score"] = round(total, 1)
        scored.append(c)

    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    winner = scored[0]

    log_success(f"[TOPIC ENGINE] Winner selected: '{winner['title']}' (Score: {winner['composite_score']}/100)")

    return {
        "topic": winner["title"],
        "hook_question": winner["hook_question"],
        "core_mechanism": winner["core_mechanism"],
        "pillar": winner.get("pillar", pillar["id"]),
        "composite_score": winner["composite_score"],
        "all_candidates_count": len(candidates),
        "key_points": [
            f"Core premise: {winner['title']}",
            f"Underlying scientific mechanism: {winner['core_mechanism']}",
            f"Counter-intuitive twist or revelation in {pillar['name']}",
            "Broader existential implication for humanity and the cosmos"
        ],
        "visual_theme": "cinematic dark science, deep contrast, microscopic and cosmic scale"
    }


def structure_user_topic(user_topic: str, video_type: str = "normal") -> Dict[str, Any]:
    """
    User Topic Mode:
    Takes user prompt/topic and frames it into an authoritative science documentary angle.
    """
    log_info(f"[TOPIC ENGINE] Structuring user-provided topic: '{user_topic}'...")

    prompt = f"""You are the Science Strategist for 'The AI Brief It'.
A user requested a video on this topic: "{user_topic.strip()}"
Format: {"YouTube Shorts (9:16 vertical, 50-60s)" if video_type == "shorts" else "Long-form Documentary (16:9 cinematic, 3-8m)"}

Transform this into a viral, factually grounded science video brief.
Return strictly valid JSON:
{{
  "topic": "Refined clickable YouTube Title (<65 chars, provocative, truthful)",
  "hook_question": "Irresistible opening question challenging intuition",
  "core_mechanism": "The exact scientific phenomenon or mechanism at play",
  "key_points": [
    "Compelling setup and immediate hook",
    "Detailed scientific mechanism or physical law",
    "Mind-bending twist, exception, or extreme manifestation",
    "Profound takeaway or future scientific horizon"
  ],
  "visual_theme": "Visual treatment recommendation"
}}
Output ONLY raw JSON."""

    raw = generate(prompt, json_mode=True)
    data = clean_json_response(raw)
    data["composite_score"] = 92.0
    log_success(f"[TOPIC ENGINE] User topic structured: '{data.get('topic')}'")
    return data
