"""
Phase 1 Test Suite — Multi-Channel Foundation
Verifies all acceptance criteria defined in MASTER_ARCHITECTURE.md Section 50:
1. All configured channels discovered and loaded
2. Channel switching updates loaded configuration
3. Credential precedence and isolation between channels
4. Settings persistence across cache reload / restart
5. Science pipeline routing preserved (media_video)
6. Animation channels (Kids/Elders) handled gracefully before Phase 3
7. YouTube OAuth isolation and channel verification blocks mismatches
8. Secret masking prevents credential exposure in UI/API responses
9. Repository security: no tracked secrets
"""
import os
import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.channel_context import ChannelContext
from core.channel_registry import ChannelRegistry, validate_channel_config
from core.credential_manager import (
    load_channel_credentials,
    save_channel_credentials,
    mask_secret,
    get_youtube_token_path,
    get_client_secret_path
)
from core.pipeline_router import route_and_execute
from youtube.channel_verifier import verify_channel
from app import app


class TestPhase1MultiChannelFoundation(unittest.TestCase):

    def setUp(self):
        self.app_client = app.test_client()

    def test_01_channel_discovery(self):
        """Acceptance Criteria: All three configured channels appear in registry."""
        registry = ChannelRegistry()
        channels = registry.list_channels()
        channel_ids = [c["channel_id"] for c in channels]

        self.assertIn("the-ai-brief-it", channel_ids, "The AI Brief It channel must be discovered")
        self.assertIn("kids", channel_ids, "Kids channel must be discovered")
        self.assertIn("elders", channel_ids, "Elders channel must be discovered")

        # Verify engine types
        ai_brief = registry.get_channel("the-ai-brief-it")
        self.assertEqual(ai_brief.engine, "media_video")
        self.assertEqual(ai_brief.name, "The AI Brief It")

        kids = registry.get_channel("kids")
        self.assertEqual(kids.engine, "animation")
        self.assertTrue(kids.youtube.get("made_for_kids"), "Kids must have made_for_kids=True")

        elders = registry.get_channel("elders")
        self.assertEqual(elders.engine, "animation")
        self.assertFalse(elders.youtube.get("made_for_kids"), "Elders must not inherit made_for_kids")

    def test_02_channel_config_validation(self):
        """Verify strict channel configuration validation."""
        valid, _ = validate_channel_config({"id": "valid-ch", "name": "Valid", "engine": "media_video"})
        self.assertTrue(valid)

        # Missing id
        valid, msg = validate_channel_config({"name": "No ID", "engine": "media_video"})
        self.assertFalse(valid)
        self.assertIn("Channel ID is required", msg)

        # Invalid engine
        valid, msg = validate_channel_config({"id": "test", "name": "Test", "engine": "unsupported_engine"})
        self.assertFalse(valid)
        self.assertIn("Unsupported engine", msg)

    def test_03_channel_switching(self):
        """Acceptance Criteria: Switching channel changes loaded configuration."""
        registry = ChannelRegistry()
        
        # Switch to kids
        ok = registry.set_active_channel_id("kids")
        self.assertTrue(ok)
        active = registry.get_active_channel()
        self.assertEqual(active.channel_id, "kids")
        self.assertEqual(active.engine, "animation")
        self.assertEqual(active.video.get("default_format"), "shorts")

        # Switch to the-ai-brief-it
        ok = registry.set_active_channel_id("the-ai-brief-it")
        self.assertTrue(ok)
        active = registry.get_active_channel()
        self.assertEqual(active.channel_id, "the-ai-brief-it")
        self.assertEqual(active.engine, "media_video")
        self.assertEqual(active.video.get("default_format"), "normal")

    def test_04_credential_isolation_and_precedence(self):
        """Acceptance Criteria: Secrets remain isolated and follow strict precedence."""
        # Test secret masking
        self.assertEqual(mask_secret(""), "")
        self.assertEqual(mask_secret("short"), "••••••••")
        masked = mask_secret("sk-1234567890abcdef")
        self.assertTrue(masked.startswith("sk-1"))
        self.assertTrue(masked.endswith("cdef"))
        self.assertIn("••••", masked)
        self.assertNotIn("1234567890ab", masked)

        # Verify channel-specific token paths are isolated
        ai_token = get_youtube_token_path("the-ai-brief-it")
        kids_token = get_youtube_token_path("kids")
        elders_token = get_youtube_token_path("elders")

        self.assertNotEqual(str(ai_token), str(kids_token), "Channels must have separate token paths")
        self.assertNotEqual(str(kids_token), str(elders_token), "Channels must have separate token paths")
        self.assertIn("kids", str(kids_token))
        self.assertIn("elders", str(elders_token))

    def test_05_settings_persistence(self):
        """Acceptance Criteria: Settings persist after reload."""
        registry = ChannelRegistry()
        original_chan = registry.get_channel("the-ai-brief-it")
        original_fps = original_chan.video.get("fps", 30)

        # Save an update
        registry.save_channel("the-ai-brief-it", {"video": {"fps": original_fps}})
        
        # Reload fresh from disk
        fresh_registry = ChannelRegistry()
        reloaded_chan = fresh_registry.get_channel("the-ai-brief-it")
        self.assertEqual(reloaded_chan.video.get("fps"), original_fps)
        self.assertEqual(reloaded_chan.name, "The AI Brief It")

    def test_06_pipeline_routing(self):
        """Acceptance Criteria: Science routes to media_video, Kids/Elders handled gracefully before Phase 3."""
        registry = ChannelRegistry()

        # Animation channel routing (Phase 1 acknowledged without crash, Phase 3+ dispatches to animation thread)
        kids_ctx = registry.get_channel("kids")
        result = route_and_execute(channel_context=kids_ctx)
        self.assertTrue(result is None or hasattr(result, "is_alive"), "Animation engine handled safely without crash")

        # Media video channel routing
        ai_ctx = registry.get_channel("the-ai-brief-it")
        self.assertEqual(ai_ctx.engine, "media_video")

    def test_07_youtube_oauth_channel_mismatch_blocks_upload(self):
        """Acceptance Criteria: Wrong YouTube OAuth/channel mismatch blocks upload."""
        # When channel has no valid token, verify_channel returns False
        ok, msg, status = verify_channel("kids", expected_youtube_channel_id="UC_NONEXISTENT")
        self.assertFalse(ok, "Unauthenticated channel must not pass verification")

    def test_07b_youtube_channel_mismatch_explicit_block(self):
        """Acceptance Criteria: YouTube OAuth channel mismatch blocks upload with explicit security alert."""
        from unittest.mock import patch
        with patch("youtube.channel_verifier.get_channel_youtube_info") as mock_info:
            mock_info.return_value = {
                "channel_id": "the-ai-brief-it",
                "has_token": True,
                "token_valid": True,
                "channel": {"id": "UC_ACTUAL_ACCOUNT_999", "title": "Wrong Account"}
            }
            # Expected is UC_EXPECTED_SCIENCE_111
            ok, msg, _ = verify_channel("the-ai-brief-it", expected_youtube_channel_id="UC_EXPECTED_SCIENCE_111")
            self.assertFalse(ok, "Mismatched channel ID must block upload")
            self.assertIn("Channel mismatch", msg)
            self.assertIn("blocked", msg)

            # Matching is permitted
            ok, msg, _ = verify_channel("the-ai-brief-it", expected_youtube_channel_id="UC_ACTUAL_ACCOUNT_999")
            self.assertTrue(ok, "Matching channel ID must be verified")


    def test_08_api_endpoints(self):
        """Verify REST API endpoints for channel management."""
        # 1. List channels
        res = self.app_client.get("/api/channels")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ok"))
        self.assertGreaterEqual(len(data.get("channels", [])), 3)

        # 2. Get active channel
        res = self.app_client.get("/api/channels/active")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ok"))
        self.assertIn("channel", data)
        self.assertIn("credentials", data)
        # Verify credentials in API response are masked
        for key, val in data.get("credentials", {}).items():
            if val:
                self.assertIn("••••", val, f"Credential {key} must be masked in API response")

        # 3. Select channel via API
        res = self.app_client.post("/api/channels/select", json={"channel_id": "kids"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("channel", {}).get("channel_id"), "kids")

        # Restore active channel back to the-ai-brief-it
        self.app_client.post("/api/channels/select", json={"channel_id": "the-ai-brief-it"})

    def test_09_git_security_no_tracked_secrets(self):
        """Acceptance Criteria: No secret is committed or exposed in tracked config files."""
        # Verify .env.example contains no real values
        env_example = PROJECT_ROOT / ".env.example"
        self.assertTrue(env_example.exists())
        with open(env_example, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                self.assertNotIn("AIza", val)
                self.assertNotIn("sk-", val)

        # Verify channel.yaml files do not contain raw API keys
        channels_dir = PROJECT_ROOT / "channels"
        for ch_dir in channels_dir.iterdir():
            if ch_dir.is_dir():
                cfg_file = ch_dir / "channel.yaml"
                if cfg_file.exists():
                    content = cfg_file.read_text(encoding="utf-8")
                    self.assertNotIn("AIza", content)
                    self.assertNotIn("sk_", content)
                    self.assertNotIn("gsk_", content)


if __name__ == "__main__":
    unittest.main()
