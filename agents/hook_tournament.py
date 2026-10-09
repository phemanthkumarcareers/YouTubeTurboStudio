"""
Hook Tournament — The AI Brief It
Generates 8-10 hook variants across 8 distinct psychological structures,
scores them, and selects the strongest truthful hook for maximum audience retention.
"""
import json
from typing import Dict, Any, List
from agents.llm_client import generate
from agents.topic_engine import clean_json_response
from core.logger import log_info, log_success

HOOK_STRUCTURES = [
    {"type": "curiosity_gap", "name": "Curiosity Gap", "formula": "Withholding the crucial revelation while highlighting its mind-bending nature"},
    {"type": "surprising_fact", "name": "Surprising Fact", "formula": "Stating an undeniable verified counter-intuitive scientific reality"},
    {"type": "contradiction", "name": "Contradiction", "formula": "Pitting two universally accepted facts against each other to reveal a paradox"},
    {"type": "consequence", "name": "Consequence", "formula": "Revealing the immediate extreme outcome of an invisible physical law"},
    {"type": "challenge", "name": "Challenge", "formula": "Directly daring the viewer's perception of their own senses or reality"},
    {"type": "what_happens_if", "name": "What Happens If", "formula": "Hypothetical escalation of an extreme cosmic or biological scenario"},
    {"type": "misconception", "name": "Misconception", "formula": "Shattering a widespread school textbook belief with modern physics"},
    {"type": "unexpected_comparison", "name": "Unexpected Comparison", "formula": "Juxtaposing an everyday object with an extreme cosmic scale"}
]


def run_hook_tournament(topic_data: Dict[str, Any], is_shorts: bool = False) -> Dict[str, Any]:
    """
    Execute hook tournament:
    1. Generate hooks for all 8 structures
    2. Score on curiosity (0-10), retention_pull (0-10), truthfulness (0-10)
    3. Eliminate misleading clickbait
    4. Select highest scoring truthful hook
    """
    topic = topic_data.get("topic", "Science Phenomenon")
    core_mechanism = topic_data.get("core_mechanism", "")
    key_points = topic_data.get("key_points", [])

    log_info(f"[HOOK TOURNAMENT] Launching 8-way hook tournament for: '{topic}'...")

    prompt = f"""You are the Lead Audience Retention Scientist for 'The AI Brief It'.
Topic: {topic}
Core Scientific Mechanism: {core_mechanism}
Key Points: {json.dumps(key_points)}
Format: {"Shorts (first 3-5 seconds, ultra-punchy, 10-18 words max)" if is_shorts else "Long-form (first 5-10 seconds, cinematic, immersive, 15-28 words max)"}

Generate exactly 8 hook variants, one for EACH of the following psychological structures:
1. Curiosity Gap: Withhold the payoff while revealing its startling reality.
2. Surprising Fact: Verified, jaw-dropping scientific fact.
3. Contradiction: A clash between intuition and physics/biology.
4. Consequence: The catastrophic or bizarre result of a physical law.
5. Challenge: A direct test of the viewer's brain or senses.
6. What-Happens-If: An extreme escalation scenario.
7. Misconception: Overturning a common myth with actual science.
8. Unexpected Comparison: Contrasting an everyday thing with an extreme cosmic scale.

CRITICAL RULES:
- NO generic greetings ("Have you ever wondered", "Hey guys", "In this video").
- NO fake or misleading clickbait. Everything must be factually justifiable.
- Maximum punchiness and spoken rhythm.

Score each hook from 1 to 10 for:
- curiosity (unbearable urge to find out the answer)
- retention_pull (likelihood viewer watches past second 5)
- truthfulness (accuracy with zero false sensationalism)

Return strictly valid JSON:
{{
  "hooks": [
    {{
      "structure": "curiosity_gap",
      "text": "Exact opening words...",
      "curiosity": 9,
      "retention_pull": 9,
      "truthfulness": 10
    }}
  ]
}}
Output ONLY raw JSON."""

    raw = generate(prompt, json_mode=True)
    parsed = clean_json_response(raw)
    hooks = parsed.get("hooks", [])

    if not hooks:
        default_hook = topic_data.get("hook_question", f"What actually happens during {topic}?")
        return {
            "winner_text": default_hook,
            "winner_structure": "curiosity_gap",
            "score": 85.0,
            "all_hooks": []
        }

    # Score each hook: curiosity (40%), retention (40%), truthfulness (20%)
    for h in hooks:
        c = h.get("curiosity", 7)
        r = h.get("retention_pull", 7)
        t = h.get("truthfulness", 8)
        # Heavily penalize untruthful clickbait
        if t < 7:
            h["total_score"] = 0
        else:
            h["total_score"] = round((c * 0.40 + r * 0.40 + t * 0.20) * 10, 1)

    hooks.sort(key=lambda x: x.get("total_score", 0), reverse=True)
    winner = hooks[0]

    log_success(
        f"[HOOK TOURNAMENT] Winner ({winner.get('structure', 'unknown')}): "
        f"\"{winner.get('text', '')}\" (Score: {winner.get('total_score')}/100)"
    )

    return {
        "winner_text": winner.get("text", ""),
        "winner_structure": winner.get("structure", ""),
        "score": winner.get("total_score", 85.0),
        "all_hooks": hooks
    }
