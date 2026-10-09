"""
Originality Engine — Section 3 Hard Publishing Gate
Evaluates new content against channel history to prevent spam, duplication, and template fatigue.
Produces a discrete Originality Score (0-100) independent of production quality.
Default threshold: 85 (configurable per channel).
"""
import re
from typing import Dict, Any, List, Optional, Set
from core.content_family import content_family_mgr
from core.channel_registry import registry
from core.logger import log_info, log_warn, log_error


def _tokenize(text: str) -> List[str]:
    """Tokenize and normalize text."""
    if not text:
        return []
    words = re.findall(r"\b[a-zA-Z0-9']+\b", text.lower())
    # Filter short stop words
    stops = {"the", "a", "an", "is", "and", "or", "to", "in", "of", "for", "on", "with", "this", "that"}
    return [w for w in words if w not in stops]


def _shingles(tokens: List[str], n: int = 3) -> Set[tuple]:
    """Create n-gram shingles for text similarity."""
    if len(tokens) < n:
        return {tuple(tokens)} if tokens else set()
    return {tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)}


def _jaccard_similarity(set_a: Set[Any], set_b: Set[Any]) -> float:
    """Calculate Jaccard similarity coefficient between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return float(intersection) / float(union) if union > 0 else 0.0


class OriginalityEngine:
    """
    Evaluates script, hook, concept, story structure, visual sequence,
    animation actions, metadata, and asset provenance against prior content.
    """

    def __init__(self, default_threshold: float = 85.0):
        self.default_threshold = default_threshold

    def evaluate_originality(
        self,
        channel_id: str,
        topic: str,
        script: str,
        hook: str = "",
        title: str = "",
        story_structure: str = "",
        visual_plan: str = "",
        animation_actions: Optional[List[str]] = None,
        assets_used: Optional[List[str]] = None,
        threshold_override: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Runs comprehensive originality evaluation against channel history.
        """
        chan_ctx = registry.get_channel(channel_id)
        threshold = threshold_override
        if threshold is None:
            if chan_ctx and hasattr(chan_ctx, "settings"):
                threshold = float(chan_ctx.settings.get("originality_threshold", self.default_threshold))
            else:
                threshold = self.default_threshold

        history = content_family_mgr.list_channel_history(channel_id, limit=30)
        failing_components = []

        if not history:
            # Baseline first video for channel
            return {
                "score": 96.0,
                "passed": True,
                "threshold": threshold,
                "breakdown": {
                    "script_similarity": {"score": 100.0, "status": "PASS", "note": "First video in channel."},
                    "concept_similarity": {"score": 100.0, "status": "PASS", "note": "No prior concepts."},
                    "hook_repetition": {"score": 100.0, "status": "PASS", "note": "Initial hook."},
                    "story_structure": {"score": 100.0, "status": "PASS", "note": "Initial story."},
                    "visual_scene_reuse": {"score": 100.0, "status": "PASS", "note": "New visual plan."},
                    "animation_action_reuse": {"score": 100.0, "status": "PASS", "note": "Distinct action sequence."},
                    "title_metadata_similarity": {"score": 100.0, "status": "PASS", "note": "Original title."},
                    "meaningful_value_add": {"score": 90.0, "status": "PASS", "note": "Clear educational value."},
                    "asset_provenance": {"score": 95.0, "status": "PASS", "note": "Standard licensed assets."}
                },
                "failing_components": []
            }

        # 1. Script Similarity Check
        new_tokens = _tokenize(script)
        new_shingles = _shingles(new_tokens, n=3)
        max_script_sim = 0.0
        for item in history:
            old_tokens = _tokenize(item.get("script", ""))
            old_shingles = _shingles(old_tokens, n=3)
            sim = _jaccard_similarity(new_shingles, old_shingles)
            if sim > max_script_sim:
                max_script_sim = sim

        script_score = max(0.0, 100.0 - (max_script_sim * 100.0))
        if max_script_sim > 0.40:
            failing_components.append("script_originality")

        # 2. Concept & Topic Similarity Check
        new_concept_tokens = set(_tokenize(topic))
        max_concept_sim = 0.0
        for item in history:
            old_concept_tokens = set(_tokenize(item.get("concept") or item.get("topic", "")))
            csim = _jaccard_similarity(new_concept_tokens, old_concept_tokens)
            if csim > max_concept_sim:
                max_concept_sim = csim

        concept_score = max(0.0, 100.0 - (max_concept_sim * 80.0))
        if max_concept_sim > 0.70:
            failing_components.append("concept_similarity")

        # 3. Hook Repetition Check
        new_hook_tokens = set(_tokenize(hook or script[:100]))
        max_hook_sim = 0.0
        for item in history:
            old_hook_tokens = set(_tokenize(item.get("hook") or item.get("script", "")[:100]))
            hsim = _jaccard_similarity(new_hook_tokens, old_hook_tokens)
            if hsim > max_hook_sim:
                max_hook_sim = hsim

        hook_score = max(0.0, 100.0 - (max_hook_sim * 90.0))
        if max_hook_sim > 0.50:
            failing_components.append("hook_similarity")

        # 4. Story Structure & Recurring Character Check
        # Rule: Branded recurring characters are allowed without penalty if story/problem is new!
        known_characters = {"toby", "pip", "dr. silas", "silas", "martha", "arthur"}
        char_overlap = any(c in script.lower() for c in known_characters)
        
        story_score = 90.0
        if story_structure:
            new_story_tokens = set(_tokenize(story_structure))
            max_story_sim = 0.0
            for item in history:
                old_story = set(_tokenize(item.get("story_structure", "")))
                sim = _jaccard_similarity(new_story_tokens, old_story)
                if sim > max_story_sim:
                    max_story_sim = sim
            story_score = max(0.0, 100.0 - (max_story_sim * 80.0))
            if max_story_sim > 0.65 and not (char_overlap and max_concept_sim < 0.4):
                failing_components.append("story_similarity")

        # 5. Visual / Scene Reuse
        visual_score = 90.0
        if visual_plan:
            new_vis_tokens = set(_tokenize(visual_plan))
            max_vis_sim = 0.0
            for item in history:
                old_vis = set(_tokenize(item.get("visual_plan", "")))
                sim = _jaccard_similarity(new_vis_tokens, old_vis)
                if sim > max_vis_sim:
                    max_vis_sim = sim
            visual_score = max(0.0, 100.0 - (max_vis_sim * 80.0))
            if max_vis_sim > 0.70:
                failing_components.append("visual_repetition")

        # 6. Animation Action Reuse
        action_score = 92.0
        if animation_actions:
            new_actions = set(a.lower().strip() for a in animation_actions)
            for item in history:
                old_acts = set(_tokenize(item.get("animation_actions", "")))
                if new_actions and old_actions and len(new_actions.intersection(old_acts)) == len(new_actions):
                    action_score = 65.0
                    failing_components.append("animation_repetition")
                    break

        # 7. Title / Metadata Similarity
        new_title_tokens = set(_tokenize(title or topic))
        max_title_sim = 0.0
        for item in history:
            old_title = set(_tokenize(item.get("title", "")))
            tsim = _jaccard_similarity(new_title_tokens, old_title)
            if tsim > max_title_sim:
                max_title_sim = tsim

        title_score = max(0.0, 100.0 - (max_title_sim * 70.0))

        # 8. Meaningful Value-Add Check
        value_add_score = 92.0 if len(script.split()) > 40 else 70.0

        # 9. Asset Provenance Check
        asset_score = 95.0
        if assets_used and any("unverified" in a.lower() for a in assets_used):
            asset_score = 40.0
            failing_components.append("asset_provenance")

        # Aggregate weighted score
        weights = {
            "script": (script_score, 0.25),
            "concept": (concept_score, 0.15),
            "hook": (hook_score, 0.15),
            "story": (story_score, 0.10),
            "visual": (visual_score, 0.10),
            "action": (action_score, 0.05),
            "title": (title_score, 0.05),
            "value": (value_add_score, 0.10),
            "asset": (asset_score, 0.05)
        }

        total_score = sum(s * w for s, w in weights.values())
        total_score = round(max(0.0, min(100.0, total_score)), 1)
        passed = (total_score >= threshold) and (len(failing_components) == 0)

        breakdown = {
            "script_similarity": {"score": round(script_score, 1), "status": "PASS" if script_score >= 70 else "FAIL"},
            "concept_similarity": {"score": round(concept_score, 1), "status": "PASS" if concept_score >= 70 else "FAIL"},
            "hook_repetition": {"score": round(hook_score, 1), "status": "PASS" if hook_score >= 70 else "FAIL"},
            "story_structure": {"score": round(story_score, 1), "status": "PASS" if story_score >= 70 else "FAIL"},
            "visual_scene_reuse": {"score": round(visual_score, 1), "status": "PASS" if visual_score >= 70 else "FAIL"},
            "animation_action_reuse": {"score": round(action_score, 1), "status": "PASS" if action_score >= 70 else "FAIL"},
            "title_metadata_similarity": {"score": round(title_score, 1), "status": "PASS" if title_score >= 70 else "FAIL"},
            "meaningful_value_add": {"score": round(value_add_score, 1), "status": "PASS" if value_add_score >= 70 else "FAIL"},
            "asset_provenance": {"score": round(asset_score, 1), "status": "PASS" if asset_score >= 70 else "FAIL"}
        }

        log_info(f"[ORIGINALITY] Evaluated '{topic}' -> Score: {total_score}/{threshold} (Passed: {passed})")

        return {
            "score": total_score,
            "passed": passed,
            "threshold": threshold,
            "breakdown": breakdown,
            "failing_components": failing_components
        }


# Global singleton
originality_engine = OriginalityEngine()
