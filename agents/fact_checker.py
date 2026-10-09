"""
Fact Checker Agent — InsightSpark TV
Audits science scripts, extracts core factual claims, classifies veracity:
- 'established': Consensus science / peer-reviewed physics/biology
- 'plausible': Well-supported theoretical hypotheses
- 'uncertain': Speculative frontier physics / emerging research
- 'unsupported': Factually incorrect or misleading claims
Provides corrections to ensure authoritative credibility.
"""
import json
from typing import Dict, Any, List, Tuple
from agents.llm_client import generate
from agents.topic_engine import clean_json_response
from core.logger import log_info, log_warn, log_success


def check_script_facts(script_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and verify factual claims across all sections of the script.
    """
    title = script_data.get("title", "")
    sections = script_data.get("sections", [])
    script_text = "\n".join(f"Section {s.get('id')}: {s.get('narration')}" for s in sections)

    log_info(f"[FACT CHECKER] Auditing scientific claims in script: '{title}'...")

    prompt = f"""You are the Chief Scientific Fact Checker for 'InsightSpark TV'.
Audit this script for scientific, cosmological, and biological accuracy:

Script Content:
{script_text}

Instructions:
1. Extract the 4-6 most important factual assertions made in the narration.
2. For each claim, classify its status into exactly ONE of:
   - "established": Solid scientific consensus, experimentally verified law or biology.
   - "plausible": Credible theoretical framework (e.g. string theory concepts, quantum loop gravity, early clinical findings).
   - "uncertain": Speculative, frontier, or contested hypothesis.
   - "unsupported": Erroneous, fabricated study, or pseudo-scientific exaggeration.
3. If any claim is "unsupported" or contains dangerous medical/health misinformation, provide a safe correction.
4. Rate overall scientific reliability from 0 to 100.

Return strictly valid JSON:
{{
  "overall_reliability_score": 95,
  "claims": [
    {{
      "claim": "Brief summary of claim",
      "status": "established",
      "explanation": "Why this is accurate according to modern physics/biology",
      "suggested_correction": null
    }}
  ],
  "concerns": [],
  "passed": true
}}
Output ONLY raw JSON."""

    raw = generate(prompt, json_mode=True)
    report = clean_json_response(raw)

    score = report.get("overall_reliability_score", 90)
    has_unsupported = any(c.get("status") == "unsupported" for c in report.get("claims", []))
    report["passed"] = (score >= 80 and not has_unsupported)

    if report["passed"]:
        log_success(f"[FACT CHECKER] Script passed scientific verification (Score: {score}/100)")
    else:
        log_warn(f"[FACT CHECKER] Script has potential scientific discrepancies (Score: {score}/100)")

    return report
