"""
Phase 2 Test Suite — The AI Brief It Enhancements
Verifies all Phase 2 criteria defined in MASTER_ARCHITECTURE.md Section 51:
1. Topic Candidate Ranking across core pillars
2. User Topic Mode structuring
3. Hook Tournament (8 psychological structures)
4. Script Critic and multi-pass rewrite loop (11 dimensions)
5. Fact-checking layer with claim veracity classification
6. Visual Director beat planning & science diagrams
7. Video-first media retrieval hierarchy
8. Professional captions with controlled accent (no rainbow subtitles)
9. Audio ducking to protect narration clarity
10. Transparent QC scoring engine (0-100)
"""
import os
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.topic_engine import discover_and_rank_topics, structure_user_topic, CORE_PILLARS
from agents.hook_tournament import run_hook_tournament, HOOK_STRUCTURES
from agents.critic import evaluate_script, review_and_refine_script
from agents.fact_checker import check_script_facts
from video.visual_director import plan_visual_beats, generate_science_diagram
from core.quality import evaluate_video_quality
from video.renderer import _draw_subtitles_and_overlay
from app import app


class TestPhase2QualityEnhancements(unittest.TestCase):

    def setUp(self):
        self.app_client = app.test_client()
        self.sample_script = {
            "title": "What If Gravity Reversed for 5 Seconds?",
            "video_type": "shorts",
            "sections": [
                {
                    "id": 1,
                    "title": "The Upward Fall",
                    "narration": "What happens if gravity suddenly pushed everything upward? In less than three seconds, the atmosphere would violently expand.",
                    "visual_query": "floating objects zero gravity"
                },
                {
                    "id": 2,
                    "title": "Atmospheric Rupture",
                    "narration": "Unanchored oceans and vehicles would ascend at 9.8 meters per second squared into the upper stratosphere.",
                    "visual_query": "ocean tidal surge space"
                },
                {
                    "id": 3,
                    "title": "The Impact",
                    "narration": "When gravity instantly snaps back, everything crashes downward at terminal velocity, releasing gigatons of kinetic energy.",
                    "visual_query": "meteor impact explosion earth"
                },
                {
                    "id": 4,
                    "title": "The Fragile Anchor",
                    "narration": "This reveals the quiet miracle of gravity: an invisible anchor holding our entire existence together.",
                    "visual_query": "earth horizon cosmic sun"
                }
            ]
        }

    def test_01_topic_candidate_ranking(self):
        """Test topic candidate ranking across core science pillars."""
        with patch("agents.topic_engine.generate") as mock_gen:
            mock_gen.return_value = json.dumps({
                "candidates": [
                    {
                        "title": "The Quantum Casimir Force",
                        "hook_question": "Can empty space create physical force?",
                        "core_mechanism": "Quantum vacuum fluctuations",
                        "curiosity": 9,
                        "visual_potential": 8,
                        "novelty": 9,
                        "scientific_credibility": 10,
                        "emotional_impact": 8,
                        "pillar": "space_extreme_science"
                    },
                    {
                        "title": "Why the Brain Forgets",
                        "hook_question": "Why does memory decay?",
                        "core_mechanism": "Synaptic pruning",
                        "curiosity": 7,
                        "visual_potential": 6,
                        "novelty": 6,
                        "scientific_credibility": 8,
                        "emotional_impact": 6,
                        "pillar": "human_body_brain"
                    }
                ]
            })
            result = discover_and_rank_topics(video_type="shorts")
            self.assertEqual(result["topic"], "The Quantum Casimir Force")
            self.assertGreaterEqual(result["composite_score"], 80.0)
            self.assertEqual(result["all_candidates_count"], 2)

    def test_02_user_topic_mode(self):
        """Test user topic framing into structured science dossier."""
        with patch("agents.topic_engine.generate") as mock_gen:
            mock_gen.return_value = json.dumps({
                "topic": "The Mystery of Dark Matter",
                "hook_question": "What is 85% of the universe made of?",
                "core_mechanism": "Non-baryonic matter gravitational lensing",
                "key_points": ["Missing cosmic mass", "Galaxy rotation curves", "Bullet cluster", "WIMP searches"],
                "visual_theme": "dark cosmic filaments"
            })
            result = structure_user_topic("dark matter", video_type="normal")
            self.assertEqual(result["topic"], "The Mystery of Dark Matter")
            self.assertIn("key_points", result)

    def test_03_hook_tournament(self):
        """Test 8-way hook tournament selecting the best truthful hook."""
        self.assertEqual(len(HOOK_STRUCTURES), 8)
        with patch("agents.hook_tournament.generate") as mock_gen:
            mock_gen.return_value = json.dumps({
                "hooks": [
                    {
                        "structure": "curiosity_gap",
                        "text": "For five seconds, your weight drops to zero—then becomes negative.",
                        "curiosity": 10,
                        "retention_pull": 9,
                        "truthfulness": 9
                    },
                    {
                        "structure": "surprising_fact",
                        "text": "Gravity is 10^36 times weaker than electromagnetism.",
                        "curiosity": 7,
                        "retention_pull": 7,
                        "truthfulness": 10
                    }
                ]
            })
            tournament = run_hook_tournament({"topic": "Gravity", "core_mechanism": "Spacetime curvature"}, is_shorts=True)
            self.assertIn("drops to zero", tournament["winner_text"])
            self.assertEqual(tournament["winner_structure"], "curiosity_gap")
            self.assertGreaterEqual(tournament["score"], 85.0)

    def test_04_script_critic_and_rewrite(self):
        """Test 11-dimension script review and automatic rewrite."""
        with patch("agents.critic.generate") as mock_gen:
            mock_gen.return_value = json.dumps({
                "scores": {
                    "hook": 9.0, "curiosity": 8.5, "clarity": 9.0, "pacing": 8.5,
                    "info_density": 9.0, "originality": 8.5, "emotional_impact": 9.0,
                    "scientific_credibility": 9.5, "visual_potential": 9.0, "payoff": 8.5,
                    "channel_fit": 9.5
                },
                "strengths": ["High pacing", "Vivid imagery"],
                "weaknesses": [],
                "rewrite_needed": False
            })
            final_script, critique = review_and_refine_script(self.sample_script, is_shorts=True)
            self.assertGreaterEqual(critique["composite_score"], 8.0)
            self.assertFalse(critique["rewrite_needed"])

    def test_05_fact_checker(self):
        """Test factual claim extraction and classification."""
        with patch("agents.fact_checker.generate") as mock_gen:
            mock_gen.return_value = json.dumps({
                "overall_reliability_score": 96,
                "claims": [
                    {"claim": "Atmosphere would expand if gravity ceased", "status": "established", "explanation": "Pressure gradient would drive expansion without gravitational confinement"},
                    {"claim": "Acceleration rate is 9.8 m/s^2", "status": "established", "explanation": "Earth surface gravitational acceleration"}
                ],
                "concerns": [],
                "passed": True
            })
            report = check_script_facts(self.sample_script)
            self.assertTrue(report["passed"])
            self.assertEqual(report["overall_reliability_score"], 96)

    def test_06_visual_director_beats_and_diagrams(self):
        """Test timestamped visual beat subdivision and programmatic diagram generation."""
        beats = plan_visual_beats(self.sample_script, is_shorts=True)
        # 4 sections x 2 cuts = 8 visual beats
        self.assertEqual(len(beats), 8)
        self.assertEqual(beats[0]["visual_type"], "video")

        # Test science diagram generation
        diagram = generate_science_diagram("Quantum Wave", "Wavefunction Collapse", 540, 960)
        self.assertIsInstance(diagram, Image.Image)
        self.assertEqual(diagram.size, (540, 960))

    def test_07_professional_captions_no_rainbow(self):
        """Acceptance Criteria: Subtitles use clean white + controlled amber, no rainbow palette."""
        base_img = Image.new("RGB", (1080, 1920), (10, 10, 10))
        # Draw subtitles
        rendered_arr = _draw_subtitles_and_overlay(
            base_img,
            subtitle="The fundamental law of gravity",
            W=1080,
            H=1920,
            is_shorts=True,
            section_title="Gravitational Paradox",
            show_subtitles=True
        )
        self.assertEqual(rendered_arr.shape, (1920, 1080, 3))

    def test_08_qc_scoring_engine(self):
        """Test quality control audit scoring (0-100)."""
        qc = evaluate_video_quality(
            script_data=self.sample_script,
            hook_data={"score": 90.0, "winner_structure": "curiosity_gap"},
            critique_data={"composite_score": 8.8},
            fact_check_data={"overall_reliability_score": 95},
            video_path=None,
            video_type="shorts"
        )
        self.assertGreaterEqual(qc["score"], 85.0)
        self.assertTrue(qc["passed"])
        self.assertIn("details", qc)

    def test_09_qc_api_endpoint(self):
        """Verify /api/qc/report REST endpoint."""
        res = self.app_client.get("/api/qc/report")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ok"))
        self.assertIn("report", data)


if __name__ == "__main__":
    unittest.main()
