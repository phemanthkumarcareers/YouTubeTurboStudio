"""
Multi-Channel Credentials Isolation & Animation Engine Tests
Verifies:
1. Strict per-channel credential isolation (no key leaking between channels)
2. Dedicated Animation Engine scene plate generation (Kids & Elders)
3. COPPA compliance / Made-for-Kids flag enforcement
4. Multi-channel API endpoints (/api/channels/all-settings, /api/channels/<id>/credentials)
"""
import os
import unittest
from pathlib import Path
from PIL import Image

import app as flask_app
from core.credential_manager import (
    load_channel_credentials,
    save_channel_credentials,
    get_channel_env_path
)
from core.channel_registry import registry
from core.compliance_gate import compliance_gate_mgr
from video.animation_engine import (
    generate_kids_scene,
    generate_elders_scene,
    generate_animated_media_map
)


class TestMultiChannelIsolationAndAnimation(unittest.TestCase):
    def setUp(self):
        self.client = flask_app.app.test_client()

    def test_01_channel_credential_isolation(self):
        """Verifies that non-primary channels default to empty keys and do not leak root .env."""
        kids_creds = load_channel_credentials("kids", allow_global_fallback=False)
        elders_creds = load_channel_credentials("elders", allow_global_fallback=False)

        # Unconfigured keys must strictly be empty string, not copied from root/other channels
        kids_env = get_channel_env_path("kids")
        if not kids_env.exists() or "PEXELS_API_KEY" not in kids_env.read_text():
            self.assertEqual(kids_creds.get("pexels_api_key", ""), "")

        if not kids_env.exists() or "PIXABAY_API_KEY" not in kids_env.read_text():
            self.assertEqual(kids_creds.get("pixabay_api_key", ""), "")

    def test_02_per_channel_credential_save_route(self):
        """Verifies saving credentials for a specific channel updates only that channel."""
        resp = self.client.post("/api/channels/kids/credentials", json={
            "groq_api_key": "test_isolated_kids_key",
            "llm_provider": "groq",
            "gemini_model": "gemini-2.5-flash"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("ok"))

        # Verify kids has this key saved
        creds = load_channel_credentials("kids")
        self.assertEqual(creds.get("groq_api_key"), "test_isolated_kids_key")

        # Verify elders does NOT have this key
        elders_creds = load_channel_credentials("elders")
        self.assertNotEqual(elders_creds.get("groq_api_key"), "test_isolated_kids_key")

        # Clean up test key
        save_channel_credentials("kids", {"groq_api_key": ""})

    def test_03_all_channel_settings_endpoint(self):
        """Verifies /api/channels/all-settings returns all 3 channels with isolated configs."""
        resp = self.client.get("/api/channels/all-settings")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("ok"))
        self.assertIn("channels", data)
        channels = data["channels"]
        self.assertIn("the-ai-brief-it", channels)
        self.assertIn("kids", channels)
        self.assertIn("elders", channels)

        # Check engine types
        self.assertEqual(channels["the-ai-brief-it"]["channel"]["engine"], "media_video")
        self.assertEqual(channels["kids"]["channel"]["engine"], "animation")
        self.assertEqual(channels["elders"]["channel"]["engine"], "animation")

    def test_04_animation_engine_kids_scene_generation(self):
        """Verifies that the Animation Engine generates a valid 1080x1920 cartoon scene plate."""
        out_path = Path("runtime/test_kids_anim.jpg")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists():
            out_path.unlink()

        res_path = generate_kids_scene(
            title="Counting Starry Numbers",
            narration_snippet="One, two, three joyful stars dancing in the sky!",
            W=1080,
            H=1920,
            sec_id=1,
            output_path=str(out_path)
        )
        self.assertTrue(os.path.exists(res_path))
        with Image.open(res_path) as img:
            self.assertEqual(img.size, (1080, 1920))

        if out_path.exists():
            out_path.unlink()

    def test_05_animation_engine_elders_scene_generation(self):
        """Verifies that the Animation Engine generates a valid 1920x1080 storybook scene plate."""
        out_path = Path("runtime/test_elders_anim.jpg")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists():
            out_path.unlink()

        res_path = generate_elders_scene(
            title="The Old Oak Tree",
            narration_snippet="Under the golden branches, years of memory softly whispered.",
            W=1920,
            H=1080,
            sec_id=1,
            output_path=str(out_path)
        )
        self.assertTrue(os.path.exists(res_path))
        with Image.open(res_path) as img:
            self.assertEqual(img.size, (1920, 1080))

        if out_path.exists():
            out_path.unlink()

    def test_06_animation_media_map_generation(self):
        """Verifies generate_animated_media_map builds complete scenes without stock footage."""
        script = {
            "sections": [
                {"id": 1, "title": "Morning Smiles", "narration": "The sunny meadow awakens with joy."},
                {"id": 2, "title": "Rainbow Bridge", "narration": "Colors bridge the sky with happiness."}
            ]
        }
        media_map = generate_animated_media_map(
            script=script,
            channel_id="kids",
            video_type="shorts",
            audience_type="children"
        )
        self.assertIn(1, media_map)
        self.assertIn(2, media_map)
        self.assertTrue(os.path.exists(media_map[1][0]))
        self.assertTrue(os.path.exists(media_map[2][0]))

    def test_07_coppa_kids_safety_gate_enforcement(self):
        """Verifies Kids channel enforces Kids Safety gate."""
        report = compliance_gate_mgr.evaluate_readiness(
            channel_id="kids",
            production_quality_score=95.0,
            originality_score=92.0,
            technical_qc_passed=True,
            compliance_passed=True,
            channel_validation_passed=True,
            asset_provenance_passed=True,
            kids_safety_passed=True,
            educational_accuracy_passed=True,
            is_made_for_kids_valid=True
        )
        self.assertEqual(report["status"], "READY FOR REVIEW")
        self.assertEqual(report["kids_safety"], "PASS")
        self.assertEqual(report["educational_accuracy"], "PASS")

        # Failing kids safety gate blocks readiness
        failing_report = compliance_gate_mgr.evaluate_readiness(
            channel_id="kids",
            production_quality_score=95.0,
            originality_score=92.0,
            kids_safety_passed=False
        )
        self.assertEqual(failing_report["status"], "BLOCKED")
        self.assertEqual(failing_report["kids_safety"], "FAIL")


if __name__ == "__main__":
    unittest.main()
