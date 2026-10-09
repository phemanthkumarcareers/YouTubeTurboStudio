"""
Content Guard & Addendum V1 Acceptance Tests
Covers all 18 Acceptance Tests defined in Section 10 of
Architecture Addendum V1 - Originality / Monetization Guard + Final Long / Shorts / Linked-Shorts Model.
"""
import os
import unittest
from unittest.mock import patch, MagicMock

from core.content_family import (
    content_family_mgr,
    CrossChannelLinkingError,
    ContentFamilyError
)
from core.originality_engine import originality_engine, OriginalityEngine
from core.compliance_gate import (
    compliance_gate_mgr,
    ComplianceGateManager,
    GateBlockedError
)
from core.targeted_regeneration import regeneration_mgr
from core.channel_registry import registry
from youtube.uploader import upload_video_to_youtube
import app as flask_app


class TestContentGuardAndAddendumV1(unittest.TestCase):
    """Verifies all 18 acceptance criteria from Addendum V1."""

    def setUp(self):
        self.client = flask_app.app.test_client()
        self.science_channel = "the-ai-brief-it"
        self.kids_channel = "kids"
        self.elders_channel = "elders"

    # -------------------------------------------------------------------------
    # Test 1: Standalone Short can be generated with no parent relationship and no parent URL
    # -------------------------------------------------------------------------
    def test_01_standalone_short_no_parent_relationship_no_url(self):
        record = content_family_mgr.register_content(
            channel_id=self.science_channel,
            topic="Quantum Entanglement in 60 Seconds",
            content_type="SHORT",
            relationship_type="STANDALONE",
            script="Two particles become inextricably connected regardless of spatial separation.",
            description="Quick dive into entanglement #Physics",
            production_quality_score=92.0,
            originality_score=90.0
        )
        self.assertEqual(record["content_type"], "SHORT")
        self.assertEqual(record["relationship_type"], "STANDALONE")
        self.assertIsNone(record["parent_content_id"])
        self.assertIsNone(record["youtube_url"])

        # Test description remains clean
        final_desc = content_family_mgr.build_short_description(
            base_description=record["description"],
            relationship_type="STANDALONE",
            parent_content_id=None
        )
        self.assertNotIn("http", final_desc)
        self.assertEqual(final_desc, record["description"])

    # -------------------------------------------------------------------------
    # Test 2: Long Video can be generated and stored as an eligible parent
    # -------------------------------------------------------------------------
    def test_02_long_video_stored_as_eligible_parent(self):
        long_record = content_family_mgr.register_content(
            channel_id=self.science_channel,
            topic="Deep Dive: The Cosmic Secrets of Black Holes",
            content_type="LONG",
            relationship_type="PARENT",
            script="Black holes represent the most extreme gravitational phenomena in our universe.",
            description="Comprehensive 8-minute documentary on black holes.",
            production_quality_score=94.0,
            originality_score=92.0
        )
        self.assertEqual(long_record["content_type"], "LONG")
        self.assertEqual(long_record["relationship_type"], "PARENT")
        self.assertEqual(long_record["content_family_id"], long_record["content_id"])

        # Verify it appears in eligible parents
        parents = content_family_mgr.list_eligible_parents(self.science_channel)
        parent_ids = [p["content_id"] for p in parents]
        self.assertIn(long_record["content_id"], parent_ids)

    # -------------------------------------------------------------------------
    # Test 3: Shorts - Link Long Video is disabled when no eligible Long exists
    # -------------------------------------------------------------------------
    def test_03_linked_mode_disabled_when_no_eligible_long(self):
        dummy_channel = "brand-new-channel-without-videos"
        parents = content_family_mgr.list_eligible_parents(dummy_channel)
        self.assertEqual(len(parents), 0)

        # Query API
        resp = self.client.get(f"/api/content-modes/eligible-parents?channel_id={dummy_channel}")
        data = resp.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(len(data["eligible_parents"]), 0)

    # -------------------------------------------------------------------------
    # Test 4: Linked mode becomes enabled when an eligible Long exists
    # -------------------------------------------------------------------------
    def test_04_linked_mode_enabled_when_eligible_long_exists(self):
        # Register a long video for elders channel
        long_elders = content_family_mgr.register_content(
            channel_id=self.elders_channel,
            topic="The Wisdom of Morning Walks",
            content_type="LONG",
            relationship_type="PARENT",
            script="Walking at dawn teaches us presence and stillness.",
            production_quality_score=91.0,
            originality_score=89.0
        )
        parents = content_family_mgr.list_eligible_parents(self.elders_channel)
        self.assertGreaterEqual(len(parents), 1)

        resp = self.client.get(f"/api/content-modes/eligible-parents?channel_id={self.elders_channel}")
        data = resp.get_json()
        self.assertTrue(data["ok"])
        self.assertGreaterEqual(len(data["eligible_parents"]), 1)
        parent_ids = [p["content_id"] for p in data["eligible_parents"]]
        self.assertIn(long_elders["content_id"], parent_ids)

    # -------------------------------------------------------------------------
    # Test 5: Parent dropdown contains only Long videos from the active channel
    # -------------------------------------------------------------------------
    def test_05_parent_dropdown_contains_only_active_channel_long_videos(self):
        # Register long video in Science
        p_sci = content_family_mgr.register_content(
            channel_id=self.science_channel,
            topic="Superconductors Explained",
            content_type="LONG"
        )
        # Register long video in Kids
        p_kids = content_family_mgr.register_content(
            channel_id=self.kids_channel,
            topic="Counting with Toby the Tiger",
            content_type="LONG"
        )

        sci_parents = content_family_mgr.list_eligible_parents(self.science_channel)
        kids_parents = content_family_mgr.list_eligible_parents(self.kids_channel)

        sci_ids = [p["content_id"] for p in sci_parents]
        kids_ids = [p["content_id"] for p in kids_parents]

        self.assertIn(p_sci["content_id"], sci_ids)
        self.assertNotIn(p_kids["content_id"], sci_ids)

        self.assertIn(p_kids["content_id"], kids_ids)
        self.assertNotIn(p_sci["content_id"], kids_ids)

    # -------------------------------------------------------------------------
    # Test 6: Cross-channel parent selection is rejected server-side even if UI is bypassed
    # -------------------------------------------------------------------------
    def test_06_cross_channel_parent_rejected_server_side(self):
        # Create a parent in science channel
        p_sci = content_family_mgr.register_content(
            channel_id=self.science_channel,
            topic="Dark Matter Detection",
            content_type="LONG"
        )

        # Attempt to link a Kids short to the Science parent
        with self.assertRaises(CrossChannelLinkingError):
            content_family_mgr.validate_parent(
                child_channel_id=self.kids_channel,
                parent_content_id=p_sci["content_id"]
            )

        # Test API endpoint rejects cross-channel selection
        resp = self.client.post("/api/content-modes/validate-parent", json={
            "channel_id": self.kids_channel,
            "parent_content_id": p_sci["content_id"]
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["ok"])
        self.assertIn("Cross-channel linking prohibited", data["error"])

    # -------------------------------------------------------------------------
    # Test 7: Linked Short stores parent_content_id and content_family_id
    # -------------------------------------------------------------------------
    def test_07_linked_short_stores_lineage_and_family_id(self):
        parent = content_family_mgr.register_content(
            channel_id=self.science_channel,
            topic="The Great James Webb Telescope Discoveries",
            content_type="LONG"
        )
        linked_short = content_family_mgr.register_content(
            channel_id=self.science_channel,
            topic="Did JWST Break the Big Bang?",
            content_type="SHORT",
            relationship_type="DERIVED",
            parent_content_id=parent["content_id"]
        )
        self.assertEqual(linked_short["parent_content_id"], parent["content_id"])
        self.assertEqual(linked_short["content_family_id"], parent["content_family_id"])
        self.assertEqual(linked_short["relationship_type"], "DERIVED")

    # -------------------------------------------------------------------------
    # Test 8: Published parent URL is automatically inserted into linked Short description
    # -------------------------------------------------------------------------
    def test_08_published_parent_url_inserted_into_linked_short_description(self):
        parent = content_family_mgr.register_content(
            channel_id=self.science_channel,
            topic="Relativity Demystified",
            content_type="LONG"
        )
        # Simulate publishing parent
        content_family_mgr.update_youtube_publish(
            content_id=parent["content_id"],
            youtube_video_id="abc123xyz",
            youtube_url="https://www.youtube.com/watch?v=abc123xyz"
        )

        desc = content_family_mgr.build_short_description(
            base_description="A 45-second explanation of time dilation.",
            relationship_type="DERIVED",
            parent_content_id=parent["content_id"],
            cta_text="Watch the full documentary"
        )
        self.assertIn("Watch the full documentary: https://www.youtube.com/watch?v=abc123xyz", desc)

    # -------------------------------------------------------------------------
    # Test 9: No fake URL is created for an unpublished parent
    # -------------------------------------------------------------------------
    def test_09_no_fake_url_for_unpublished_parent(self):
        parent = content_family_mgr.register_content(
            channel_id=self.science_channel,
            topic="Unpublished Fusion Energy Deep Dive",
            content_type="LONG"
        )
        # Parent is unpublished, so youtube_url is None
        url = content_family_mgr.resolve_parent_url(parent["content_id"])
        self.assertIsNone(url)

        desc = content_family_mgr.build_short_description(
            base_description="Fusion ignition in brief.",
            relationship_type="DERIVED",
            parent_content_id=parent["content_id"]
        )
        self.assertNotIn("http", desc)
        self.assertEqual(desc, "Fusion ignition in brief.")

    # -------------------------------------------------------------------------
    # Test 10: Standalone Short never receives a parent URL
    # -------------------------------------------------------------------------
    def test_10_standalone_short_never_receives_parent_url(self):
        desc = content_family_mgr.build_short_description(
            base_description="Standalone astronomy trivia.",
            relationship_type="STANDALONE",
            parent_content_id=None
        )
        self.assertNotIn("Watch", desc)
        self.assertNotIn("http", desc)
        self.assertEqual(desc, "Standalone astronomy trivia.")

    # -------------------------------------------------------------------------
    # Test 11: Originality failure blocks publishing
    # -------------------------------------------------------------------------
    def test_11_originality_failure_blocks_publishing(self):
        # Low originality score (e.g. 60 vs threshold 85)
        report = compliance_gate_mgr.evaluate_readiness(
            channel_id=self.science_channel,
            production_quality_score=95.0,
            originality_score=60.0
        )
        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["can_publish"])
        self.assertEqual(report["originality"]["status"], "FAIL")

        with self.assertRaises(GateBlockedError):
            compliance_gate_mgr.assert_can_publish(report)

    # -------------------------------------------------------------------------
    # Test 12: Production Quality failure blocks publishing
    # -------------------------------------------------------------------------
    def test_12_production_quality_failure_blocks_publishing(self):
        # Low PQ score (e.g. 75 vs threshold 90)
        report = compliance_gate_mgr.evaluate_readiness(
            channel_id=self.science_channel,
            production_quality_score=75.0,
            originality_score=95.0
        )
        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["can_publish"])
        self.assertEqual(report["production_quality"]["status"], "FAIL")

        with self.assertRaises(GateBlockedError):
            compliance_gate_mgr.assert_can_publish(report)

    # -------------------------------------------------------------------------
    # Test 13: Technical QC failure blocks publishing
    # -------------------------------------------------------------------------
    def test_13_technical_qc_failure_blocks_publishing(self):
        report = compliance_gate_mgr.evaluate_readiness(
            channel_id=self.science_channel,
            production_quality_score=95.0,
            originality_score=92.0,
            technical_qc_passed=False
        )
        self.assertEqual(report["status"], "BLOCKED")
        self.assertFalse(report["can_publish"])
        self.assertEqual(report["technical_qc"], "FAIL")

    # -------------------------------------------------------------------------
    # Test 14: Kids safety/educational failure blocks Kids publishing
    # -------------------------------------------------------------------------
    def test_14_kids_safety_educational_failure_blocks_kids(self):
        # Kids safety failure
        report_safety_fail = compliance_gate_mgr.evaluate_readiness(
            channel_id=self.kids_channel,
            production_quality_score=95.0,
            originality_score=92.0,
            kids_safety_passed=False,
            educational_accuracy_passed=True
        )
        self.assertEqual(report_safety_fail["status"], "BLOCKED")
        self.assertFalse(report_safety_fail["can_publish"])
        self.assertEqual(report_safety_fail["kids_safety"], "FAIL")

        # Educational accuracy failure
        report_edu_fail = compliance_gate_mgr.evaluate_readiness(
            channel_id=self.kids_channel,
            production_quality_score=95.0,
            originality_score=92.0,
            kids_safety_passed=True,
            educational_accuracy_passed=False
        )
        self.assertEqual(report_edu_fail["status"], "BLOCKED")
        self.assertFalse(report_edu_fail["can_publish"])
        self.assertEqual(report_edu_fail["educational_accuracy"], "FAIL")

    # -------------------------------------------------------------------------
    # Test 15: Upload target never overrides failed gates
    # -------------------------------------------------------------------------
    def test_15_upload_target_never_overrides_failed_gates(self):
        failing_report = compliance_gate_mgr.evaluate_readiness(
            channel_id=self.science_channel,
            production_quality_score=70.0,
            originality_score=70.0
        )
        # Attempt to call upload_video_to_youtube with failed report
        with self.assertRaises(GateBlockedError):
            upload_video_to_youtube(
                video_path="dummy_path.mp4",
                title="Test",
                description="Test",
                channel_id=self.science_channel,
                readiness_report=failing_report
            )

    # -------------------------------------------------------------------------
    # Test 16: Targeted regeneration changes only the failed stage where feasible
    # -------------------------------------------------------------------------
    def test_16_targeted_regeneration_isolated_stages(self):
        initial_data = {
            "topic": "Mysteries of the Deep Sea",
            "hook": "Old boring hook",
            "script": "Script body remains the same",
            "video_type": "shorts"
        }
        # 1. Regenerate hook only
        updated_hook = regeneration_mgr.regenerate("hook_similarity", initial_data, self.science_channel)
        self.assertIn("hook", updated_hook)
        self.assertEqual(updated_hook["script"], initial_data["script"])

        # 2. Regenerate captions only
        updated_caps = regeneration_mgr.regenerate("caption", initial_data, self.science_channel)
        self.assertTrue(updated_caps.get("captions_regenerated"))
        self.assertEqual(updated_caps["script"], initial_data["script"])

    # -------------------------------------------------------------------------
    # Test 17: Recurring characters are allowed while near-duplicate stories/templates are detected
    # -------------------------------------------------------------------------
    def test_17_recurring_characters_allowed_but_duplicates_penalized(self):
        test_chan = "recurring-character-test-channel"
        # Episode 1 with Toby the Tiger
        content_family_mgr.register_content(
            channel_id=test_chan,
            topic="Toby Visits the Zoo to Count Monkeys",
            script="Toby the Tiger hops along the trail. He sees one monkey, then two monkeys swinging!",
            story_structure="Introduction to animals then counting beats",
            title="Toby Counts Animals"
        )

        # Episode 2: Same character Toby, but completely NEW story (baking a cake, distinct concept)
        new_story_res = originality_engine.evaluate_originality(
            channel_id=test_chan,
            topic="Toby Bakes a Giant Blueberry Cake",
            script="Toby the Tiger puts on a baker's apron. Flour and sweet blueberries are mixed together into a warm oven.",
            story_structure="Kitchen preparation then baking celebration",
            title="Toby Bakes a Cake"
        )
        self.assertGreaterEqual(new_story_res["score"], 80.0)
        self.assertNotIn("story_similarity", new_story_res["failing_components"])

        # Episode 3: Near-duplicate template of Episode 1 (almost same words and counting beats)
        duplicate_res = originality_engine.evaluate_originality(
            channel_id=test_chan,
            topic="Toby Visits the Park to Count Monkeys",
            script="Toby the Tiger hops along the trail. He sees one monkey, then two monkeys swinging!",
            story_structure="Introduction to animals then counting beats",
            title="Toby Counts Animals Again"
        )
        self.assertLess(duplicate_res["score"], 80.0)
        self.assertIn("script_originality", duplicate_res["failing_components"])

    # -------------------------------------------------------------------------
    # Test 18: All settings remain isolated by channel
    # -------------------------------------------------------------------------
    def test_18_all_settings_remain_isolated_by_channel(self):
        sci = registry.get_channel(self.science_channel)
        kids = registry.get_channel(self.kids_channel)
        elders = registry.get_channel(self.elders_channel)

        self.assertNotEqual(sci.channel_id, kids.channel_id)
        self.assertNotEqual(kids.channel_id, elders.channel_id)

        # Engines are isolated
        self.assertEqual(sci.engine, "media_video")
        self.assertEqual(kids.engine, "animation")
        self.assertEqual(elders.engine, "animation")

        # YouTube made_for_kids configuration is strictly partitioned
        self.assertFalse(sci.youtube.get("made_for_kids", False))
        self.assertTrue(kids.youtube.get("made_for_kids", False))
        self.assertFalse(elders.youtube.get("made_for_kids", False))


if __name__ == "__main__":
    unittest.main()
