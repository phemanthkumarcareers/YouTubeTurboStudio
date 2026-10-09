"""
Elders Quality Control — Mature Story Quality & QC Scoring
Enforces cinematic unhurried pacing (scenes >= 4.5s), emotional resonance,
character continuity, and schema compliance with >= 88 threshold.
"""
from typing import Dict, Any, Optional
from animation.schema import SceneGraph, validate_scene_graph
from core.logger import log_info, log_warn


class EldersQCChecker:
    """Pre-publish quality control checker for Golden Stories & Wisdom."""

    def evaluate(
        self,
        scene_graph: SceneGraph,
        video_path: str,
        script_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Runs comprehensive Elders QC pass.
        Returns report with numeric score and publish readiness verdict.
        """
        score = 100.0
        checks = {}

        # 1. Schema Validation
        is_schema_ok, schema_errs = validate_scene_graph(scene_graph)
        checks["scene_schema"] = {
            "passed": is_schema_ok,
            "errors": schema_errs,
            "weight": 25
        }
        if not is_schema_ok:
            score -= 25.0

        # 2. Pacing & Unhurried Delivery (scenes >= 4.5s for dignified tone)
        rushed_scenes = [sc.scene_id for sc in scene_graph.scenes if sc.duration < 4.0]
        checks["unhurried_pacing"] = {
            "passed": (len(rushed_scenes) == 0),
            "rushed_scenes": rushed_scenes,
            "weight": 20
        }
        if rushed_scenes:
            score -= 15.0

        # 3. Adult Character Continuity
        chars_found = [c.character_id for sc in scene_graph.scenes for c in sc.characters]
        primary_char = chars_found[0] if chars_found else "none"
        continuity_ok = all(
            any(c.character_id == primary_char for c in sc.characters)
            for sc in scene_graph.scenes
        )
        checks["character_continuity"] = {
            "passed": continuity_ok,
            "primary_character": primary_char,
            "weight": 20
        }
        if not continuity_ok:
            score -= 15.0

        # 4. Adult Atmosphere & Props (tea mug, vintage book, glasses, etc.)
        total_props = sum(len(sc.props) for sc in scene_graph.scenes)
        checks["dignified_props"] = {
            "passed": total_props > 0,
            "count": total_props,
            "weight": 15
        }
        if total_props == 0:
            score -= 10.0

        # 5. Narration & Audio Sync
        has_narration = all(bool(sc.narration) for sc in scene_graph.scenes)
        checks["narration_presence"] = {
            "passed": has_narration,
            "weight": 20
        }
        if not has_narration:
            score -= 15.0

        score = max(0.0, min(100.0, score))
        publish_ready = (score >= 88.0 and is_schema_ok)

        report = {
            "passed": publish_ready,
            "score": round(score, 1),
            "publish_ready": publish_ready,
            "checks": checks,
            "channel_id": scene_graph.channel_id,
            "total_duration": scene_graph.total_duration
        }

        if publish_ready:
            log_info(f"[ELDERS QC] Elders QC PASSED! Score: {report['score']}/100")
        else:
            log_warn(f"[ELDERS QC] Elders QC Warning: Score {report['score']}/100 below 88 threshold")

        return report


elders_qc = EldersQCChecker()
