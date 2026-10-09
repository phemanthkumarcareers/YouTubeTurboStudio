"""
Tests for Centralized Fallback Manager and Nano Banana Client
Verifies multi-provider text fallback, visual fallback hierarchies,
and Nano Banana connectivity checks.
"""
import os
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.fallback_manager import (
    _extract_json_payload,
    generate_text_with_fallback,
    acquire_visual_with_fallback,
    synthesize_audio_with_fallback
)
from media.nano_banana_client import (
    test_nano_banana_connection,
    SUPPORTED_NANO_BANANA_MODELS
)


class TestFallbackManager(unittest.TestCase):
    def test_extract_json_payload_clean(self):
        raw = '{"title": "Test Title", "score": 100}'
        parsed = _extract_json_payload(raw)
        self.assertEqual(parsed["title"], "Test Title")
        self.assertEqual(parsed["score"], 100)

    def test_extract_json_payload_fenced(self):
        raw = '```json\n{"status": "ok", "tags": ["space", "universe"]}\n```'
        parsed = _extract_json_payload(raw)
        self.assertEqual(parsed["status"], "ok")
        self.assertEqual(len(parsed["tags"]), 2)

    def test_generate_text_fallback_on_all_empty(self):
        # Empty config forces all LLM providers to fail -> safe template returned
        cfg = {"gemini_api_key": "", "groq_api_key": "", "openai_api_key": ""}
        res = generate_text_with_fallback("Write a script", json_mode=True, custom_config=cfg)
        parsed = json.loads(res)
        self.assertIn("title", parsed)
        self.assertIn("sections", parsed)
        self.assertGreater(len(parsed["sections"]), 0)

    def test_acquire_visual_kids_fallback(self):
        out_dir = Path("output/test_images")
        out_dir.mkdir(parents=True, exist_ok=True)
        paths = acquire_visual_with_fallback(
            query="Sunny meadow with happy bunnies",
            sec_id=1,
            sec_title="A Sunny Day",
            audience_type="kids",
            channel_id="kids",
            output_dir=out_dir
        )
        self.assertGreater(len(paths), 0)
        self.assertTrue(os.path.exists(paths[0]))

    def test_acquire_visual_elders_fallback(self):
        out_dir = Path("output/test_images")
        out_dir.mkdir(parents=True, exist_ok=True)
        paths = acquire_visual_with_fallback(
            query="Golden memories of grandmother's garden",
            sec_id=2,
            sec_title="Treasured Memories",
            audience_type="elders",
            channel_id="elders",
            output_dir=out_dir
        )
        self.assertGreater(len(paths), 0)
        self.assertTrue(os.path.exists(paths[0]))


class TestNanoBananaClient(unittest.TestCase):
    def test_supported_models(self):
        self.assertGreater(len(SUPPORTED_NANO_BANANA_MODELS), 2)
        model_ids = [m["id"] for m in SUPPORTED_NANO_BANANA_MODELS]
        self.assertIn("nano-banana-flux", model_ids)
        self.assertIn("nano-banana-cartoon-v1", model_ids)
        self.assertIn("nano-banana-storybook-v1", model_ids)

    def test_empty_api_key(self):
        ok, msg = test_nano_banana_connection("")
        self.assertFalse(ok)
        self.assertIn("empty", msg.lower())


if __name__ == "__main__":
    unittest.main()
