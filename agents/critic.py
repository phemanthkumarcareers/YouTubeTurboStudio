"""
Script Critic & Rewrite Agent — The AI Brief It
Evaluates script drafts across 11 retention and scientific criteria.
Triggers targeted automated rewrites if the score falls below threshold (minimum 8.0/10).
"""
import json
import copy
from typing import Dict, Any, Tuple
from agents.llm_client import generate
from agents.topic_engine import clean_json_response
from core.logger import log_info, log_warn, log_success

CRITIC_THRESHOLD = 8.0  # 80/100 threshold for automatic rewrite approval
MAX_REWRITES = 2


def evaluate_script(script_data: Dict[str, Any], is_shorts: bool = False) -> Dict[str, Any]:
    """
    Score script draft across 11 key dimensions (each 1-10):
    1. hook
    2. curiosity
    3. clarity
    4. pacing
    5. information_density
    6. originality
    7. emotional_impact
    8. scientific_credibility
    9. visual_potential
    10. payoff
    11. channel_fit
    """
    title = script_data.get("title", "")
    sections = script_data.get("sections", [])
    full_text = "\n".join(f"[{s.get('title', '')}]: {s.get('narration', '')}" for s in sections)

    log_info(f"[CRITIC] Reviewing script draft: '{title}'...")

    prompt = f"""You are the Executive Editor and Retention Critic for 'The AI Brief It'.
Format: {"Shorts (50-60s fast-paced)" if is_shorts else "Long-form Documentary (3-8 min cinematic)"}
Title: {title}
Script Draft:
{full_text}

Evaluate this script strictly and objectively on a 1.0 to 10.0 scale across these 11 criteria:
1. hook_score: Is the first sentence irresistible? Zero filler?
2. curiosity_score: Does it open and sustain high-tension curiosity gaps?
3. clarity_score: Are complex scientific concepts explained with crystal clear analogies?
4. pacing_score: Are there new beats every few seconds? No dragging or padding?
5. info_density: High signal-to-noise ratio? No empty fluff?
6. originality: Fresh take rather than repeating standard Wikipedia summary?
7. emotional_impact: Sense of awe, mystery, or existential realization?
8. scientific_credibility: Accurate physics/biology? No pseudo-science?
9. visual_potential: Easy to visualize with dramatic stock footage and graphics?
10. payoff_score: Is the conclusion deeply satisfying rather than a rushed generic sign-off?
11. channel_fit: Authoritative, cinematic, thought-provoking?

Return strictly valid JSON:
{{
  "scores": {{
    "hook": 8.5,
    "curiosity": 8.0,
    "clarity": 9.0,
    "pacing": 8.0,
    "info_density": 8.5,
    "originality": 8.0,
    "emotional_impact": 8.5,
    "scientific_credibility": 9.0,
    "visual_potential": 8.5,
    "payoff": 8.0,
    "channel_fit": 9.0
  }},
  "strengths": ["Clear strength 1", "Strength 2"],
  "weaknesses": ["Specific weakness or filler phrase 1", "Weakness 2"],
  "rewrite_needed": false,
  "rewrite_instructions": "Specific guidance for rewrite if score < 8.0"
}}
Output ONLY raw JSON."""

    raw = generate(prompt, json_mode=True)
    critique = clean_json_response(raw)

    scores = critique.get("scores", {})
    if scores:
        vals = [float(v) for v in scores.values() if isinstance(v, (int, float))]
        avg_score = round(sum(vals) / len(vals), 2) if vals else 8.0
    else:
        avg_score = 8.0

    critique["composite_score"] = avg_score
    critique["rewrite_needed"] = (avg_score < CRITIC_THRESHOLD)

    return critique


def rewrite_script_with_feedback(
    script_data: Dict[str, Any],
    critique: Dict[str, Any],
    is_shorts: bool = False
) -> Dict[str, Any]:
    """
    Execute a targeted rewrite of the script addressing the critic's specific feedback.
    """
    weaknesses = critique.get("weaknesses", [])
    instructions = critique.get("rewrite_instructions", "Sharpen the hook, remove filler, and increase scientific punchiness.")

    log_info(f"[CRITIC] Executing automated rewrite based on feedback...")

    prompt = f"""You are the Master Science Scriptwriter for 'The AI Brief It'.
The executive editor reviewed your script draft and requested a rewrite.

Current Script:
{json.dumps(script_data, indent=2)}

Critic Feedback:
Weaknesses Identified: {json.dumps(weaknesses)}
Specific Rewrite Instructions: {instructions}

Format Constraints:
{"Shorts: exactly 5-6 sections, total 135-160 words, punchy cuts, no filler" if is_shorts else "Long-form: 8-14 sections, total 500-1100 words, escalating revelation"}

Rewrite the script to address every single weakness while keeping the same JSON schema:
{{
  "title": "Sharpened Title",
  "description": "YouTube description",
  "tags": ["tag1", "tag2"],
  "sections": [
    {{
      "id": 1,
      "title": "Section Title",
      "narration": "Exact revised narration words...",
      "visual_query": "specific search terms for stock footage"
    }}
  ]
}}
Output ONLY raw JSON."""

    raw = generate(prompt, json_mode=True)
    revised = clean_json_response(raw)
    revised["video_type"] = script_data.get("video_type", "normal")
    return revised


def review_and_refine_script(script_data: Dict[str, Any], is_shorts: bool = False) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Orchestrate the review and automated rewrite loop (maximum 2 iterations).
    Returns (final_script, final_critique_report).
    """
    current_script = copy.deepcopy(script_data)
    history = []

    for iteration in range(MAX_REWRITES + 1):
        critique = evaluate_script(current_script, is_shorts=is_shorts)
        history.append({
            "iteration": iteration + 1,
            "score": critique.get("composite_score"),
            "feedback": critique.get("weaknesses", [])
        })

        if not critique.get("rewrite_needed") or iteration == MAX_REWRITES:
            if critique.get("rewrite_needed"):
                log_warn(f"[CRITIC] Max rewrites reached. Proceeding with best revision (Score: {critique.get('composite_score')}/10).")
            else:
                log_success(f"[CRITIC] Script approved with high retention score: {critique.get('composite_score')}/10!")
            break

        log_warn(
            f"[CRITIC] Draft score {critique.get('composite_score')}/10 is below threshold {CRITIC_THRESHOLD}. "
            f"Rewriting (Pass {iteration + 1}/{MAX_REWRITES})..."
        )
        current_script = rewrite_script_with_feedback(current_script, critique, is_shorts=is_shorts)

    current_script["critic_history"] = history
    current_script["final_critic_score"] = critique.get("composite_score", 8.5)
    return current_script, critique
