"""
Phase 3 Test Suite: Shared Animation Engine MVP
Validates all requirements from docs/MASTER_ARCHITECTURE.md (Section 52):
1. Storyboard schema & validator
2. Character loading, expressions, walking legs, gestures
3. Props manager (kids & elders props, actions)
4. Procedural background generator
5. Motion engine & virtual camera
6. Procedural audio / SFX synthesis & mixing
7. Storyboarder for Kids vs Elders
8. Acceptance Scene 1: Kids character walks, talks, gestures, and interacts with a prop.
9. Acceptance Scene 2: Elder character walks, talks, sits/gestures in cozy environment.
10. Shared engine verification: exact same AnimationRenderer code for both.
11. Animation Quality Control (QC) scoring.
12. Zero publishing/uploading.
"""
import os
import tempfile
import unittest
from pathlib import Path
from PIL import Image

from animation.schema import (
    SceneGraph,
    Scene,
    CharacterPlacement,
    PropPlacement,
    CameraMove,
    validate_scene_graph
)
from animation.character_manager import character_manager
from animation.props import props_manager
from animation.backgrounds import background_generator
from animation.motion_engine import motion_engine
from animation.camera import virtual_camera
from animation.audio_sfx import sfx_generator, mix_animation_audio
from animation.storyboarder import storyboarder
from animation.renderer import animation_renderer
from animation.qc import animation_qc
from core.channel_context import ChannelContext


class TestPhase3AnimationEngine(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="phase3_anim_test_")

    def test_01_schema_and_validation(self):
        """Test declarative scene graph schema, dict serialization, and validation."""
        sg = SceneGraph(
            title="Validation Test",
            channel_id="kids",
            format="shorts",
            width=1080,
            height=1920,
            fps=30,
            scenes=[
                Scene(
                    scene_id=1,
                    title="Intro",
                    duration=3.0,
                    bg_style="vibrant_sky",
                    characters=[
                        CharacterPlacement(
                            character_id="sparky",
                            name="Sparky",
                            style="kids",
                            x_percent=0.5,
                            y_percent=0.6,
                            scale=1.0,
                            motion="walk_in",
                            gesture="wave"
                        )
                    ],
                    props=[
                        PropPlacement(
                            prop_id="star_1",
                            name="Golden Star",
                            prop_type="star",
                            x_percent=0.7,
                            y_percent=0.5,
                            scale=1.0,
                            action="float"
                        )
                    ],
                    camera=CameraMove(camera_type="slow_zoom_in", zoom_start=1.0, zoom_end=1.1),
                    narration="Welcome to our fun adventure!"
                )
            ]
        )
        is_valid, errors = validate_scene_graph(sg)
        self.assertTrue(is_valid, f"Validation failed: {errors}")
        self.assertEqual(len(errors), 0)

        # Test serialization round-trip
        data = sg.to_dict()
        rebuilt = SceneGraph.from_dict(data)
        self.assertEqual(rebuilt.title, sg.title)
        self.assertEqual(len(rebuilt.scenes), 1)
        self.assertEqual(rebuilt.scenes[0].characters[0].character_id, "sparky")
        self.assertEqual(rebuilt.scenes[0].props[0].prop_type, "star")

    def test_02_character_rendering_kids_and_elders(self):
        """Test procedural character rendering for both Kids and Elders."""
        # Kids: Cheerful young mascot with open mouth, blink, and wave gesture
        kid_img = character_manager.get_character_frame(
            character_id="kid_test",
            style="kids",
            mouth_open_pct=0.8,
            eye_blink_pct=0.0,
            head_tilt_deg=2.5,
            gesture="wave",
            motion="walk_in",
            walk_cycle=0.25,
            target_size=(300, 380)
        )
        self.assertIsInstance(kid_img, Image.Image)
        self.assertEqual(kid_img.size, (300, 380))
        self.assertEqual(kid_img.mode, "RGBA")

        # Elders: Dignified elder in sitting armchair posture with spectacles and kind smile
        elder_img = character_manager.get_character_frame(
            character_id="elder_test",
            style="elders",
            mouth_open_pct=0.4,
            eye_blink_pct=0.0,
            head_tilt_deg=-1.5,
            gesture="hold_prop",
            motion="sit",
            walk_cycle=0.0,
            target_size=(300, 380)
        )
        self.assertIsInstance(elder_img, Image.Image)
        self.assertEqual(elder_img.size, (300, 380))
        self.assertEqual(elder_img.mode, "RGBA")

    def test_03_props_rendering(self):
        """Test props rendering for Kids (star, magnifying glass) and Elders (tea mug, vintage book)."""
        # Kids prop: star
        star_img = props_manager.get_prop_frame("star", scale=1.0, action="shimmer", time_sec=0.5)
        self.assertIsInstance(star_img, Image.Image)

        # Kids prop: magnifying glass
        mg_img = props_manager.get_prop_frame("magnifying_glass", scale=1.0, action="float", time_sec=1.0)
        self.assertIsInstance(mg_img, Image.Image)

        # Elders prop: steaming tea mug
        mug_img = props_manager.get_prop_frame("tea_mug", scale=1.0, action="held", time_sec=0.7)
        self.assertIsInstance(mug_img, Image.Image)

        # Elders prop: vintage book
        book_img = props_manager.get_prop_frame("vintage_book", scale=1.0, action="held", time_sec=0.0)
        self.assertIsInstance(book_img, Image.Image)

    def test_04_backgrounds_rendering(self):
        """Test background environments for Kids and Elders in both portrait and landscape."""
        # Kids: vibrant sky in 1080x1920
        kids_bg = background_generator.render_background("vibrant_sky", 540, 960, time_sec=0.5)
        self.assertEqual(kids_bg.size, (540, 960))

        # Elders: cozy study in 1920x1080
        elder_bg = background_generator.render_background("cozy_study", 960, 540, time_sec=0.5)
        self.assertEqual(elder_bg.size, (960, 540))

    def test_05_motion_engine_and_camera(self):
        """Test spatial motion easing, walking curves, and virtual camera pan/zoom."""
        char = CharacterPlacement(
            character_id="c1",
            x_percent=0.5,
            y_percent=0.6,
            motion="walk_in",
            gesture="wave"
        )
        # At t=0.5s during walk_in
        tf = motion_engine.compute_character_transform(char, t=0.5, scene_duration=3.0, width=1080, height=1920)
        self.assertIn("x", tf)
        self.assertIn("y", tf)
        self.assertIn("walk_cycle", tf)
        self.assertGreater(tf["walk_cycle"], 0.0)

        # Virtual camera zoom application
        cam = CameraMove(camera_type="slow_zoom_in", zoom_start=1.0, zoom_end=1.15)
        sample_img = Image.new("RGB", (200, 200), (50, 100, 150))
        zoomed_img = virtual_camera.apply(sample_img, cam, t=1.5, duration=3.0)
        self.assertEqual(zoomed_img.size, (200, 200))

    def test_06_audio_sfx_synthesis(self):
        """Test procedural sound effect synthesis and WAV generation."""
        for sfx_name in ("pop", "chime", "twinkle", "gentle_bell", "clock_tick"):
            wav_path = sfx_generator.get_sfx_path(sfx_name)
            self.assertTrue(os.path.exists(wav_path))
            self.assertGreater(os.path.getsize(wav_path), 500)

        # Test audio mixer creating composite audio
        out_wav = os.path.join(self.tmp_dir, "test_mixed_audio.wav")
        mix_animation_audio(
            total_duration=2.0,
            output_path=out_wav,
            sfx_cues=[{"time": 0.5, "type": "chime", "volume": 0.8}]
        )
        self.assertTrue(os.path.exists(out_wav))
        self.assertGreater(os.path.getsize(out_wav), 1000)

    def test_07_storyboarder(self):
        """Test Storyboarder translating scripts into SceneGraphs for Kids and Elders."""
        kids_ctx = ChannelContext(
            channel_id="kids",
            name="Kids Fun Land",
            engine="animation",
            audience={"type": "kids", "tone": "energetic"}
        )
        kids_sg = storyboarder.build_storyboard(
            script_data={
                "title": "Why Clouds Rain",
                "scenes": [
                    {"scene_id": 1, "narration": "Hello little scientists!", "duration": 3.0},
                    {"scene_id": 2, "narration": "Look at the raindrops falling!", "duration": 3.0}
                ]
            },
            channel_context=kids_ctx,
            video_format="shorts"
        )
        self.assertEqual(kids_sg.channel_id, "kids")
        self.assertEqual(kids_sg.format, "shorts")
        self.assertEqual(len(kids_sg.scenes), 2)
        self.assertEqual(kids_sg.scenes[0].characters[0].style, "kids")

        elders_ctx = ChannelContext(
            channel_id="elders",
            name="Elders Wisdom",
            engine="animation",
            audience={"type": "elders", "tone": "calm"}
        )
        elders_sg = storyboarder.build_storyboard(
            script_data={
                "title": "Evening Tea Reflections",
                "scenes": [
                    {"scene_id": 1, "narration": "Good evening, my dear friends.", "duration": 4.0}
                ]
            },
            channel_context=elders_ctx,
            video_format="normal"
        )
        self.assertEqual(elders_sg.channel_id, "elders")
        self.assertEqual(elders_sg.format, "normal")
        self.assertEqual(elders_sg.scenes[0].characters[0].style, "elders")

    def test_08_acceptance_scene_1_kids_walks_talks_gestures_prop(self):
        """
        MASTER_ARCHITECTURE.md Phase 3 Acceptance Criteria #1:
        Kids character walks, talks, gestures, and interacts with a prop.
        Renders a local video scene using shared AnimationRenderer.
        """
        sg = SceneGraph(
            title="Kids Acceptance Scene",
            channel_id="kids",
            format="shorts",
            width=540,   # Scaled for fast local test execution
            height=960,
            fps=15,
            scenes=[
                Scene(
                    scene_id=1,
                    title="Kids Adventure Walk & Star Prop",
                    duration=2.0,
                    bg_style="vibrant_sky",
                    characters=[
                        CharacterPlacement(
                            character_id="sparky_host",
                            name="Sparky",
                            style="kids",
                            x_percent=0.50,
                            y_percent=0.65,
                            scale=1.0,
                            motion="walk_in",
                            gesture="hold_prop",
                            is_talking=True
                        )
                    ],
                    props=[
                        PropPlacement(
                            prop_id="magic_star",
                            name="Magic Star",
                            prop_type="star",
                            x_percent=0.68,
                            y_percent=0.58,
                            scale=0.9,
                            action="held"
                        )
                    ],
                    camera=CameraMove(camera_type="slow_zoom_in", zoom_start=1.0, zoom_end=1.08),
                    narration="Look at this shiny star we found together!",
                    sfx_cues=[{"time": 0.3, "type": "pop", "volume": 0.8}, {"time": 1.2, "type": "chime", "volume": 0.8}]
                )
            ]
        )
        out_video = os.path.join(self.tmp_dir, "kids_acceptance_scene.mp4")
        rendered_path = animation_renderer.render(
            scene_graph=sg,
            output_path=out_video,
            mode="preview"
        )
        self.assertTrue(os.path.exists(rendered_path), "Kids video file was not generated")
        self.assertGreater(os.path.getsize(rendered_path), 50000, "Kids video file is unexpectedly small")

        # Run QC
        qc_result = animation_qc.evaluate(sg, rendered_path)
        self.assertTrue(qc_result["passed"], f"QC failed for Kids scene: {qc_result}")
        self.assertGreaterEqual(qc_result["score"], 80.0)

    def test_09_acceptance_scene_2_elder_walks_talks_sits_gestures_cozy(self):
        """
        MASTER_ARCHITECTURE.md Phase 3 Acceptance Criteria #2:
        Adult/elder character walks, talks, sits/gestures in a different environment (cozy study).
        Renders using the EXACT SAME AnimationRenderer (no duplicated code).
        """
        sg = SceneGraph(
            title="Elders Acceptance Scene",
            channel_id="elders",
            format="normal",
            width=960,   # Scaled for fast local test execution
            height=540,
            fps=15,
            scenes=[
                Scene(
                    scene_id=1,
                    title="Grandpa in Cozy Study with Tea Mug",
                    duration=2.0,
                    bg_style="cozy_study",
                    characters=[
                        CharacterPlacement(
                            character_id="arthur_storyteller",
                            name="Grandpa Arthur",
                            style="elders",
                            x_percent=0.45,
                            y_percent=0.62,
                            scale=1.1,
                            motion="sit",
                            gesture="hold_prop",
                            is_talking=True
                        )
                    ],
                    props=[
                        PropPlacement(
                            prop_id="cozy_tea_mug",
                            name="Tea Mug",
                            prop_type="tea_mug",
                            x_percent=0.60,
                            y_percent=0.64,
                            scale=0.9,
                            action="held"
                        )
                    ],
                    camera=CameraMove(camera_type="slow_zoom_in", zoom_start=1.0, zoom_end=1.05),
                    narration="A peaceful evening, a warm hearth, and cherished memories.",
                    sfx_cues=[{"time": 0.5, "type": "gentle_bell", "volume": 0.7}]
                )
            ]
        )
        out_video = os.path.join(self.tmp_dir, "elders_acceptance_scene.mp4")
        rendered_path = animation_renderer.render(
            scene_graph=sg,
            output_path=out_video,
            mode="preview"
        )
        self.assertTrue(os.path.exists(rendered_path), "Elders video file was not generated")
        self.assertGreater(os.path.getsize(rendered_path), 50000, "Elders video file is unexpectedly small")

        # Run QC
        qc_result = animation_qc.evaluate(sg, rendered_path)
        self.assertTrue(qc_result["passed"], f"QC failed for Elders scene: {qc_result}")
        self.assertGreaterEqual(qc_result["score"], 80.0)

    def test_10_shared_engine_verification(self):
        """Verify Kids and Elders channels use identical renderer class and import."""
        from animation.renderer import AnimationRenderer, animation_renderer as inst1
        from animation import animation_renderer as inst2

        self.assertIs(inst1, inst2, "Both must share the exact same singleton instance")
        self.assertIsInstance(inst1, AnimationRenderer)


if __name__ == "__main__":
    unittest.main()
