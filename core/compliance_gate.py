"""
Production Quality and Compliance Gates — Section 4 & Section 9
Enforces strict separation between Production Quality and Originality.
READY FOR REVIEW only when all gates pass. Upload target never overrides failed gates.
Produces data for the Internal Readiness Panel (never claiming guaranteed YouTube monetization).
"""
from typing import Dict, Any, Optional
from core.channel_registry import registry
from core.logger import log_info, log_warn, log_error


class GateBlockedError(Exception):
    """Raised when a video fails quality/originality/safety gates and cannot be published."""
    pass


class ComplianceGateManager:
    """Evaluates readiness gates across production quality, originality, and channel compliance."""

    DEFAULT_PQ_THRESHOLD = 90.0
    DEFAULT_ORIG_THRESHOLD = 85.0

    def evaluate_readiness(
        self,
        channel_id: str,
        production_quality_score: float,
        originality_score: float,
        technical_qc_passed: bool = True,
        compliance_passed: bool = True,
        channel_validation_passed: bool = True,
        asset_provenance_passed: bool = True,
        kids_safety_passed: Optional[bool] = None,
        educational_accuracy_passed: Optional[bool] = None,
        is_made_for_kids_valid: Optional[bool] = None,
        pq_threshold_override: Optional[float] = None,
        orig_threshold_override: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluates all gates according to Section 4.
        Returns readiness dictionary and blocks publish if any gate fails.
        """
        chan_ctx = registry.get_channel(channel_id)
        pq_thresh = pq_threshold_override or self.DEFAULT_PQ_THRESHOLD
        orig_thresh = orig_threshold_override or self.DEFAULT_ORIG_THRESHOLD

        if chan_ctx and hasattr(chan_ctx, "settings"):
            pq_thresh = float(chan_ctx.settings.get("production_quality_threshold", pq_thresh))
            orig_thresh = float(chan_ctx.settings.get("originality_threshold", orig_thresh))

        is_kids_channel = (
            channel_id in ("kids", "little-curious-minds") or
            (chan_ctx and chan_ctx.audience.get("type") in ("children", "kids")) or
            (chan_ctx and chan_ctx.youtube.get("made_for_kids", False))
        )

        # 1. Production Quality Gate
        pq_pass = production_quality_score >= pq_thresh

        # 2. Originality Gate
        orig_pass = originality_score >= orig_thresh

        # 3. Technical QC Gate
        tech_pass = bool(technical_qc_passed)

        # 4. Content Compliance Gate
        comp_pass = bool(compliance_passed)

        # 5. Channel-Specific Validation Gate
        chan_pass = bool(channel_validation_passed)

        # 6. Asset Provenance Gate
        asset_pass = bool(asset_provenance_passed)

        # 7. Kids Safety & Educational Gates (if applicable)
        if is_kids_channel:
            kids_safe_str = "PASS" if (kids_safety_passed is True or kids_safety_passed is None) else "FAIL"
            edu_acc_str = "PASS" if (educational_accuracy_passed is True or educational_accuracy_passed is None) else "FAIL"
            mfk_valid = (is_made_for_kids_valid is not False)
        else:
            kids_safe_str = "N/A"
            edu_acc_str = "N/A"
            mfk_valid = True

        kids_passed = (kids_safe_str != "FAIL") and (edu_acc_str != "FAIL") and mfk_valid

        # Overall Status
        all_passed = (
            pq_pass and
            orig_pass and
            tech_pass and
            comp_pass and
            chan_pass and
            asset_pass and
            kids_passed
        )

        status = "READY FOR REVIEW" if all_passed else "BLOCKED"

        failing_reasons = []
        if not pq_pass:
            failing_reasons.append(f"Production Quality {production_quality_score:.1f} < threshold {pq_thresh:.1f}")
        if not orig_pass:
            failing_reasons.append(f"Originality {originality_score:.1f} < threshold {orig_thresh:.1f}")
        if not tech_pass:
            failing_reasons.append("Technical QC failed")
        if not comp_pass:
            failing_reasons.append("Content compliance failed")
        if not chan_pass:
            failing_reasons.append("Channel validation failed")
        if not asset_pass:
            failing_reasons.append("Asset provenance check failed")
        if is_kids_channel:
            if kids_safe_str == "FAIL":
                failing_reasons.append("Kids safety hard gate failed")
            if edu_acc_str == "FAIL":
                failing_reasons.append("Kids educational accuracy check failed")
            if not mfk_valid:
                failing_reasons.append("Made-for-Kids configuration is invalid")

        report = {
            "channel_id": channel_id,
            "status": status,
            "can_publish": all_passed,
            "production_quality": {
                "score": round(production_quality_score, 1),
                "threshold": round(pq_thresh, 1),
                "status": "PASS" if pq_pass else "FAIL"
            },
            "originality": {
                "score": round(originality_score, 1),
                "threshold": round(orig_thresh, 1),
                "status": "PASS" if orig_pass else "FAIL"
            },
            "technical_qc": "PASS" if tech_pass else "FAIL",
            "content_compliance": "PASS" if comp_pass else "FAIL",
            "channel_validation": "PASS" if chan_pass else "FAIL",
            "kids_safety": kids_safe_str,
            "educational_accuracy": edu_acc_str,
            "asset_provenance": "PASS" if asset_pass else "FAIL",
            "failing_reasons": failing_reasons,
            "disclaimer": "Internal readiness gate only. Does not claim guaranteed YouTube monetization."
        }

        if all_passed:
            log_info(f"[READINESS] Channel '{channel_id}' READY FOR REVIEW (PQ: {production_quality_score:.1f}, Orig: {originality_score:.1f}).")
        else:
            log_warn(f"[READINESS] Channel '{channel_id}' BLOCKED: {', '.join(failing_reasons)}")

        return report

    def assert_can_publish(self, readiness_report: Dict[str, Any]):
        """Throws GateBlockedError if readiness status is not READY FOR REVIEW."""
        if not readiness_report.get("can_publish"):
            reasons = "; ".join(readiness_report.get("failing_reasons", ["Failed quality/compliance gates"]))
            raise GateBlockedError(f"Publishing blocked by internal gate: {reasons}")


compliance_gate_mgr = ComplianceGateManager()
