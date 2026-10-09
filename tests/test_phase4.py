"""
Phase 4 Test Suite: Kids Channel
Validates all requirements from docs/MASTER_ARCHITECTURE.md (Section 53):
1. Age profiles (2-3, 4-5, 6-8) & content categories
2. Original recurring character packs (Sparky, Pip Bunny, Barnaby Bear, Ollie Owl)
3. Kids Safeguards Hard Gate (inappropriate language, unsafe guidance, franchise protection, phonics correctness)
4. Critical safeguard failure blocking publish readiness
5. Acceptance Criterion 1: One alphabet/number educational video generated locally
6. Acceptance Criterion 2: One story/bedtime video generated locally
7. Acceptance Criterion 3: One vertical Short generated locally
8. Kids-specific QC evaluation (threshold >= 90/100)
9. Zero publishing / uploading during testing
"""
import os
import tempfile
import unittest
from PIL import Image

from kids.profiles import get_age_profile, AGE_PROFILES, CONTENT_CATEGORIES
from kids.safeguards import kids_safeguards
from kids.characters import kids_characters
from kids.story_generator import kids_story_generator
from kids.qc import kids_qc
from animation.schema import SceneGraph, Scene, CharacterPlacement, PropPlacement, CameraMove
from animation.character_manager import character_manager
from animation.props import props_manager
from animation.storyboarder import storyboarder
from animation.renderer import animation_renderer
from core.channel_context import ChannelContext


class TestPhase4KidsChannel(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="phase4_kids_test_")
        self.kids_context = ChannelContext(
            channel_id="kids",
            name="Kids Wonder Lab",
            engine="animation",
            audience={"type": "children", "age_group": "4-5"},
            youtube={"made_for_kids": True}
        )

    def test_01_age_profiles_and_categories(self):
        """Test toddler, preschool, and elementary age profiles & constraints."""
        toddler = get_age_profile("2-3")
        self.assertEqual(toddler.name, "Toddlers")
        self.assertLessEqual(toddler.words_per_minute, 100)
        self.assertIn("bedtime", toddler.allowed_categories)

        preschool = get_age_profile("4-5")
        self.assertEqual(preschool.name, "Preschool")
        self.assertIn("alphabet", preschool.allowed_categories)

        elementary = get_age_profile("6-8")
        self.assertEqual(elementary.name, "Early Elementary")
        self.assertGreater(elementary.words_per_minute, preschool.words_per_minute)

        self.assertIn("alphabet", CONTENT_CATEGORIES)
        self.assertIn("bedtime_stories", CONTENT_CATEGORIES)

    def test_02_original_recurring_characters(self):
        """Test rendering of all 4 original recurring characters."""
        for char_name in ("sparky", "pip_bunny", "barnaby_bear", "ollie_owl"):
            img = character_manager.get_character_frame(
                character_id=char_name,
                style=char_name,
                mouth_open_pct=0.5,
                eye_blink_pct=0.0,
                head_tilt_deg=1.0,
                gesture="wave",
                motion="idle_breathe",
                target_size=(240, 300)
            )
            self.assertIsInstance(img, Image.Image)
            self.assertEqual(img.size, (240, 300))
            self.assertEqual(img.mode, "RGBA")

    def test_03_educational_props(self):
        """Test educational counting & alphabet props."""
        apple_img = props_manager.get_prop_frame("apple", scale=1.0)
        self.assertIsInstance(apple_img, Image.Image)

        balloon_img = props_manager.get_prop_frame("balloon", scale=1.0, time_sec=0.5)
        self.assertIsInstance(balloon_img, Image.Image)

        block_img = props_manager.get_prop_frame("alphabet_block", scale=1.0)
        self.assertIsInstance(block_img, Image.Image)

    def test_04_kids_safeguards_positive_cases(self):
        """Test wholesome educational content passes the safeguards gate."""
        good_script = {
            "title": "Learn Letters: A is for Apple!",
            "scenes": [
                {"narration": "A makes the ah sound! A is for Apple! Crisp, sweet, and bright red!"},
                {"narration": "You are doing wonderful, little friend! Keep smiling!"}
            ]
        }
        res = kids_safeguards.evaluate(good_script, channel_metadata={"youtube": {"made_for_kids": True}})
        self.assertTrue(res["passed"])
        self.assertFalse(res["hard_blocked"])
        self.assertEqual(len(res["violations"]), 0)

    def test_05_kids_safeguards_hard_gate_blocks_violations(self):
        """
        Acceptance Criteria: Critical safeguard failures must block publish readiness.
        Test violent words, franchise characters, dangerous instructions, and alphabet mismatches.
        """
        # 1. Violent / scary language
        bad_words_script = {
            "title": "Scary Monster Knife Fight",
            "scenes": [{"narration": "The terrifying monster will kill and fight with weapons!"}]
        }
        res1 = kids_safeguards.evaluate(bad_words_script)
        self.assertTrue(res1["hard_blocked"])
        self.assertFalse(res1["passed"])
        self.assertTrue(any("Inappropriate or scary language" in v for v in res1["violations"]))

        # 2. Protected Franchise character
        franchise_script = {
            "title": "Adventure with Peppa Pig and Paw Patrol",
            "scenes": [{"narration": "Come play with Peppa Pig and Chase from Paw Patrol!"}]
        }
        res2 = kids_safeguards.evaluate(franchise_script)
        self.assertTrue(res2["hard_blocked"])
        self.assertTrue(any("Protected franchise character" in v for v in res2["violations"]))

        # 3. Dangerous household instruction
        unsafe_script = {
            "title": "Fun Kitchen Game",
            "scenes": [{"narration": "Go touch the stove and play with matches!"}]
        }
        res3 = kids_safeguards.evaluate(unsafe_script)
        self.assertTrue(res3["hard_blocked"])
        self.assertTrue(any("Unsafe instruction" in v for v in res3["violations"]))

        # 4. Educational phonics mismatch (B is for Apple)
        phonics_mismatch = {
            "title": "Alphabet Fun",
            "scenes": [{"narration": "B is for Apple!"}]
        }
        res4 = kids_safeguards.evaluate(phonics_mismatch)
        self.assertTrue(res4["hard_blocked"])
        self.assertTrue(any("Educational mismatch" in v for v in res4["violations"]))

        # 5. Verify QC marks publish_ready = False when hard gate fails
        fake_sg = SceneGraph(title="Blocked Video", channel_id="kids", scenes=[Scene(scene_id=1, duration=3.0)])
        qc_eval = kids_qc.evaluate(fake_sg, "nonexistent.mp4", script_data=bad_words_script)
        self.assertFalse(qc_eval["publish_ready"])
        self.assertFalse(qc_eval["passed"])
        self.assertEqual(qc_eval["score"], 0.0)

    def test_06_acceptance_alphabet_number_educational_video(self):
        """
        Acceptance Criteria 1:
        Generate locally without publishing: one alphabet/number educational video.
        """
        script = kids_story_generator.generate_educational_script(
            category="numbers",
            topic="Count 1, 2, 3 Shiny Stars with Sparky",
            age_group="4-5"
        )
        sg = storyboarder.build_storyboard(
            script_data=script,
            channel_context=self.kids_context,
            video_format="shorts",
            fps=15
        )
        # Scaled resolution for fast test execution
        sg.width = 540
        sg.height = 960

        out_path = os.path.join(self.tmp_dir, "acceptance_counting_video.mp4")
        rendered = animation_renderer.render(
            scene_graph=sg,
            output_path=out_path,
            mode="preview"
        )
        self.assertTrue(os.path.exists(rendered))
        self.assertGreater(os.path.getsize(rendered), 50000)

        # Run Kids QC
        qc_res = kids_qc.evaluate(
            scene_graph=sg,
            video_path=rendered,
            script_data=script,
            channel_metadata={"youtube": {"made_for_kids": True}}
        )
        self.assertTrue(qc_res["passed"])
        self.assertTrue(qc_res["publish_ready"])
        self.assertGreaterEqual(qc_res["score"], 90.0)

    def test_07_acceptance_story_bedtime_video(self):
        """
        Acceptance Criteria 2:
        Generate locally without publishing: one story/bedtime video.
        """
        script = kids_story_generator.generate_bedtime_story(
            character="pip_bunny",
            topic="Pip Bunny's Gentle Starlit Lullaby",
            age_group="2-3"
        )
        sg = storyboarder.build_storyboard(
            script_data=script,
            channel_context=self.kids_context,
            video_format="normal",
            fps=15
        )
        sg.width = 960
        sg.height = 540

        out_path = os.path.join(self.tmp_dir, "acceptance_bedtime_story.mp4")
        rendered = animation_renderer.render(
            scene_graph=sg,
            output_path=out_path,
            mode="preview"
        )
        self.assertTrue(os.path.exists(rendered))
        self.assertGreater(os.path.getsize(rendered), 50000)

        qc_res = kids_qc.evaluate(
            scene_graph=sg,
            video_path=rendered,
            script_data=script,
            channel_metadata={"youtube": {"made_for_kids": True}}
        )
        self.assertTrue(qc_res["passed"])
        self.assertTrue(qc_res["publish_ready"])
        self.assertGreaterEqual(qc_res["score"], 90.0)

    def test_08_acceptance_kids_short(self):
        """
        Acceptance Criteria 3:
        Generate locally without publishing: one vertical Short.
        """
        script = kids_story_generator.generate_kids_short(
            topic="Can You Find the Yellow Star?",
            age_group="4-5"
        )
        sg = storyboarder.build_storyboard(
            script_data=script,
            channel_context=self.kids_context,
            video_format="shorts",
            fps=15
        )
        sg.width = 540
        sg.height = 960

        out_path = os.path.join(self.tmp_dir, "acceptance_kids_short.mp4")
        rendered = animation_renderer.render(
            scene_graph=sg,
            output_path=out_path,
            mode="preview"
        )
        self.assertTrue(os.path.exists(rendered))
        self.assertGreater(os.path.getsize(rendered), 40000)

        qc_res = kids_qc.evaluate(
            scene_graph=sg,
            video_path=rendered,
            script_data=script,
            channel_metadata={"youtube": {"made_for_kids": True}}
        )
        self.assertTrue(qc_res["passed"])
        self.assertTrue(qc_res["publish_ready"])
        self.assertGreaterEqual(qc_res["score"], 90.0)


if __name__ == "__main__":
    unittest.main()
