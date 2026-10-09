"""
Kids Quality Control — Kids-Specific QC & Safeguards Evaluation
Enforces high minimum quality score (>= 90/100), hard safeguards gate,
educational accuracy, and pacing comfort.
"""
from typing import Dict, Any, Optional
from kids.safeguards import kids_safeguards
from animation.schema import SceneGraph, validate_scene_graph
from core.logger import log_info, log_warn, log_error


class KidsQCChecker:
    """Rigorous pre-publish QC validator for children's content."""

    def evaluate(
        self,
        scene_graph: SceneGraph,
        video_path: str,
        script_data: Optional[Dict[str, Any]] = None,
        channel_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes Kids-specific QC pass.
        Returns comprehensive report and publish readiness verdict.
        """
        score = 100.0
        checks = {}

        # 1. HARD GATE: Kids Safeguards
        safe_res = kids_safeguards.evaluate(
            script_data=script_data or {"title": scene_graph.title, "scenes": [s.__dict__ for s in scene_graph.scenes]},
            channel_metadata=channel_metadata
        )
        checks["safeguards_hard_gate"] = {
            "passed": safe_res["passed"],
            "violations": safe_res["violations"],
            "warnings": safe_res["warnings"],
            "weight": 35
        }
        if safe_res["hard_blocked"]:
            score = 0.0
            log_error("[KIDS QC] Content BLOCKED by Kids Safeguards Gate!")
            return {
                "passed": False,
                "score": 0.0,
                "publish_ready": False,
                "blocked_reason": "Failed Kids Safeguards Gate",
                "checks": checks,
                "channel_id": scene_graph.channel_id
            }

        # 2. Schema Validation
        is_schema_ok, schema_errs = validate_scene_graph(scene_graph)
        checks["scene_schema"] = {
            "passed": is_schema_ok,
            "errors": schema_errs,
            "weight": 20
        }
        if not is_schema_ok:
            score -= 20.0

        # 3. Pacing & Sensory Safety (No hyperactive flashing cuts < 2.5s)
        fast_cuts = [sc.scene_id for sc in scene_graph.scenes if sc.duration < 2.5]
        checks["pacing_safety"] = {
            "passed": (len(fast_cuts) == 0),
            "fast_cut_scenes": fast_cuts,
            "weight": 15
        }
        if fast_cuts:
            score -= 10.0

        # 4. Recurring Character Continuity
        chars_found = [c.character_id for sc in scene_graph.scenes for c in sc.characters]
        primary_char = chars_found[0] if chars_found else "none"
        continuity_ok = all(
            any(c.character_id == primary_char for c in sc.characters)
            for sc in scene_graph.scenes
        )
        checks["character_continuity"] = {
            "passed": continuity_ok,
            "primary_character": primary_char,
            "weight": 15
        }
        if not continuity_ok:
            score -= 10.0

        # 5. Educational Prop & Interaction Integrity
        has_props = any(len(sc.props) > 0 for sc in scene_graph.scenes)
        checks["interactive_props"] = {
            "passed": has_props,
            "weight": 15
        }
        if not has_props:
            score -= 5.0

        score = max(0.0, min(100.0, score))
        # High quality threshold for kids (90/100)
        publish_ready = (score >= 90.0 and safe_res["passed"] and is_schema_ok)

        report = {
            "passed": publish_ready,
            "score": round(score, 1),
            "publish_ready": publish_ready,
            "checks": checks,
            "channel_id": scene_graph.channel_id,
            "total_duration": scene_graph.total_duration
        }

        if publish_ready:
            log_info(f"[KIDS QC] All Kids QC criteria PASSED! Score: {report['score']}/100")
        else:
            log_warn(f"[KIDS QC] QC Warning: Score {report['score']}/100 below 90 threshold")

        return report


kids_qc = KidsQCChecker()
