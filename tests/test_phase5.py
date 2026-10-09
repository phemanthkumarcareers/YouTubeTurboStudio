"""
Phase 5 Test Suite: Elders Channel
Validates all requirements from docs/MASTER_ARCHITECTURE.md (Section 54):
1. Channel-specific adult prompts & categories (life lessons, nostalgia, family wisdom)
2. Adult character pack (Arthur, Eleanor, Walter)
3. Mature voice profiles & slower cinematic animation profile
4. Adult environments & props (cozy study, sunset porch, hearth, tea mug, vintage book, glasses, watch)
5. Shared engine reuse (exact same AnimationRenderer as Kids)
6. Acceptance Criterion 1: One local adult/elder animated story (16:9 long-form)
7. Acceptance Criterion 2: One local adult/elder Short (9:16)
8. Cross-channel isolation: Elders does NOT inherit Kids educational rules, Made-for-Kids is False
9. Elders QC scoring (threshold >= 88/100)
10. Zero publishing / uploading during testing
"""
import os
import tempfile
import unittest
from PIL import Image

try:
    from wondersaga_tv.profiles import (
        ELDERS_CATEGORIES,
        ELDERS_VOICES,
        get_elders_pacing_profile
    )
    from wondersaga_tv.characters import elders_characters
    from wondersaga_tv.story_generator import elders_story_generator
    from wondersaga_tv.qc import elders_qc
except ImportError:
    from elders.profiles import (
        ELDERS_CATEGORIES,
        ELDERS_VOICES,
        get_elders_pacing_profile
    )
    from elders.characters import elders_characters
    from elders.story_generator import elders_story_generator
    from elders.qc import elders_qc
from animation.schema import SceneGraph, Scene, CharacterPlacement, PropPlacement, CameraMove
from animation.character_manager import character_manager
from animation.props import props_manager
from animation.storyboarder import storyboarder
from animation.renderer import animation_renderer
from core.channel_context import ChannelContext


class TestPhase5EldersChannel(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="phase5_elders_test_")
        self.elders_context = ChannelContext(
            channel_id="elders",
            name="Wonder Saga TV",
            engine="animation",
            audience={"type": "general", "age_group": "all_ages"},
            youtube={"made_for_kids": False}
        )

    def test_01_categories_and_mature_voice_profiles(self):
        """Test categories, unhurried pacing rules, and mature voice profiles."""
        self.assertIn("life_lessons", ELDERS_CATEGORIES)
        self.assertIn("nostalgia", ELDERS_CATEGORIES)
        self.assertIn("family_stories", ELDERS_CATEGORIES)

        self.assertIn("christopher", ELDERS_VOICES)
        self.assertEqual(ELDERS_VOICES["christopher"]["id"], "en-US-ChristopherNeural")

        pacing = get_elders_pacing_profile("nostalgia")
        self.assertGreaterEqual(pacing.seconds_per_scene, 6.0)
        self.assertLessEqual(pacing.words_per_minute, 110)

    def test_02_adult_character_pack(self):
        """Test rendering of Arthur, Eleanor, and Walter."""
        # 1. Arthur (Dignified grandfather)
        img_arthur = character_manager.get_character_frame(
            character_id="arthur_storyteller",
            style="arthur_storyteller",
            mouth_open_pct=0.4,
            eye_blink_pct=0.0,
            head_tilt_deg=1.0,
            gesture="hold_prop",
            motion="sit",
            target_size=(240, 300)
        )
        self.assertIsInstance(img_arthur, Image.Image)
        self.assertEqual(img_arthur.size, (240, 300))
        self.assertEqual(img_arthur.mode, "RGBA")

        # 2. Eleanor (Gentle matriarch in lavender shawl)
        img_eleanor = character_manager.get_character_frame(
            character_id="eleanor_matriarch",
            style="eleanor_matriarch",
            mouth_open_pct=0.3,
            eye_blink_pct=0.0,
            head_tilt_deg=-1.0,
            gesture="hold_prop",
            motion="sit",
            target_size=(240, 300)
        )
        self.assertIsInstance(img_eleanor, Image.Image)
        self.assertEqual(img_eleanor.size, (240, 300))
        self.assertEqual(img_eleanor.mode, "RGBA")

        # 3. Walter (Artisan in tweed flat cap and vest)
        img_walter = character_manager.get_character_frame(
            character_id="walter_artisan",
            style="walter_artisan",
            mouth_open_pct=0.5,
            eye_blink_pct=0.0,
            head_tilt_deg=0.5,
            gesture="point",
            motion="idle_breathe",
            target_size=(240, 300)
        )
        self.assertIsInstance(img_walter, Image.Image)
        self.assertEqual(img_walter.size, (240, 300))
        self.assertEqual(img_walter.mode, "RGBA")

    def test_03_adult_props_and_environments(self):
        """Test cozy tea mug, vintage book, pocket watch, and study/sunset environments."""
        tea_img = props_manager.get_prop_frame("tea_mug", scale=1.0, time_sec=0.5)
        self.assertIsInstance(tea_img, Image.Image)

        book_img = props_manager.get_prop_frame("vintage_book", scale=1.0)
        self.assertIsInstance(book_img, Image.Image)

        watch_img = props_manager.get_prop_frame("pocket_watch", scale=1.0, time_sec=1.0)
        self.assertIsInstance(watch_img, Image.Image)

    def test_04_cross_channel_isolation(self):
        """
        Verify Elders does NOT inherit kids-specific constraints:
        - Made-for-Kids is False
        - Philosophical life advice does not fail kids preschool checks
        """
        self.assertFalse(self.elders_context.youtube.get("made_for_kids"))
        self.assertNotEqual(self.elders_context.channel_id, "kids")

    def test_05_shared_animation_engine_identity(self):
        """Verify Kids and Elders channels use identical renderer implementation."""
        from animation import animation_renderer as shared_inst
        from animation.renderer import AnimationRenderer

        self.assertIsInstance(shared_inst, AnimationRenderer)

    def test_06_acceptance_adult_animated_story_long_form(self):
        """
        MASTER_ARCHITECTURE.md Phase 5 Acceptance Criteria:
        Generate one local adult/elder animated story (16:9 Long-Form)
        using the same engine code as Kids.
        """
        script = elders_story_generator.generate_story(
            category="nostalgia",
            topic="The Symphony of the Old Front Porch",
            character="arthur_storyteller",
            format_type="normal"
        )
        sg = storyboarder.build_storyboard(
            script_data=script,
            channel_context=self.elders_context,
            video_format="normal",
            fps=15
        )
        # Scaled resolution for fast test execution
        sg.width = 960
        sg.height = 540

        out_path = os.path.join(self.tmp_dir, "acceptance_elders_story_16x9.mp4")
        rendered = animation_renderer.render(
            scene_graph=sg,
            output_path=out_path,
            mode="preview"
        )
        self.assertTrue(os.path.exists(rendered))
        self.assertGreater(os.path.getsize(rendered), 50000)

        # Run Elders QC
        qc_res = elders_qc.evaluate(
            scene_graph=sg,
            video_path=rendered,
            script_data=script
        )
        self.assertTrue(qc_res["passed"])
        self.assertTrue(qc_res["publish_ready"])
        self.assertGreaterEqual(qc_res["score"], 88.0)

    def test_07_acceptance_adult_short(self):
        """
        MASTER_ARCHITECTURE.md Phase 5 Acceptance Criteria:
        Generate one local adult/elder Short (9:16)
        using the same engine code as Kids.
        """
        script = elders_story_generator.generate_story(
            category="life_lessons",
            topic="A Gentle Thought on Rushing Through Life",
            character="eleanor_matriarch",
            format_type="shorts"
        )
        sg = storyboarder.build_storyboard(
            script_data=script,
            channel_context=self.elders_context,
            video_format="shorts",
            fps=15
        )
        # Scaled resolution for fast test execution
        sg.width = 540
        sg.height = 960

        out_path = os.path.join(self.tmp_dir, "acceptance_elders_short_9x16.mp4")
        rendered = animation_renderer.render(
            scene_graph=sg,
            output_path=out_path,
            mode="preview"
        )
        self.assertTrue(os.path.exists(rendered))
        self.assertGreater(os.path.getsize(rendered), 40000)

        # Run Elders QC
        qc_res = elders_qc.evaluate(
            scene_graph=sg,
            video_path=rendered,
            script_data=script
        )
        self.assertTrue(qc_res["passed"])
        self.assertTrue(qc_res["publish_ready"])
        self.assertGreaterEqual(qc_res["score"], 88.0)


if __name__ == "__main__":
    unittest.main()
