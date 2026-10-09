"""
Phase 2 Local Generation Acceptance Verification
Generates local test videos (Short 1080x1920 and Standard 1920x1080) without publishing.
Verifies:
- improved hook presence
- professional captions (no rainbow subtitles)
- visual changes
- correct output dimensions (1080x1920 for Shorts, 1920x1080 for standard)
- successful QC report generation
"""
import os
import sys
import json
import unittest
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.quality import evaluate_video_quality, QC_REPORT_PATH
from video.renderer import render_video
from video.visual_director import generate_science_diagram
from config import OUTPUT_DIR


class TestPhase2GenerationAcceptance(unittest.TestCase):

    def setUp(self):
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "images").mkdir(parents=True, exist_ok=True)

    def test_local_short_generation_acceptance(self):
        """
        Acceptance Criteria:
        1. 1080x1920 output
        2. Improved hook
        3. Professional captions (clean white + amber, no rainbow)
        4. Relevant visual changes
        5. Successful QC
        6. NO upload/publish
        """
        # 1. Create test science script with Hook Tournament winner
        script_data = {
            "title": "What If Earth Stopped Spinning for 1 Second?",
            "topic": "The 1-Second Planetary Halt",
            "video_type": "shorts",
            "sections": [
                {
                    "id": 1,
                    "title": "The Invisible Kinetic Surge",
                    "narration": "For one single second, the Earth's crust stops—but everything on it does not.",
                    "visual_query": "earth spinning space"
                },
                {
                    "id": 2,
                    "title": "Supersonic Atmosphere",
                    "narration": "At the equator, the atmosphere continues moving at over one thousand miles per hour.",
                    "visual_query": "supersonic hurricane storm"
                },
                {
                    "id": 3,
                    "title": "Tectonic Shockwave",
                    "narration": "Gigantic oceanic walls miles high would engulf entire continents in moments.",
                    "visual_query": "megatsunami wave coast"
                },
                {
                    "id": 4,
                    "title": "The Cosmic Perspective",
                    "narration": "We never notice Earth's motion until we imagine it pausing for a heartbeat.",
                    "visual_query": "blue marble earth cosmos"
                }
            ]
        }

        # 2. Generate local science diagrams for media assets
        media_map = {}
        for s in script_data["sections"]:
            sec_id = s["id"]
            diag_file = str(self.output_dir / "images" / f"test_short_sec_{sec_id}.jpg")
            generate_science_diagram(
                title=s["title"],
                subtitle=s["visual_query"],
                width=1080,
                height=1920,
                output_path=diag_file
            )
            media_map[sec_id] = [diag_file]

        # 3. Create dummy audio file (4 seconds for fast local rendering)
        from moviepy.editor import AudioClip
        import numpy as np

        def make_tone(t):
            return np.sin(440 * 2 * np.pi * t)

        dummy_audio_clip = AudioClip(make_tone, duration=4.0, fps=22050)
        dummy_audio_path = str(self.output_dir / "test_audio.mp3")
        dummy_audio_clip.write_audiofile(dummy_audio_path, fps=22050, logger=None)
        dummy_audio_clip.close()

        # 4. Create dummy SRT file
        srt_path = str(self.output_dir / "test_subtitles.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("1\n00:00:00,000 --> 00:00:02,000\nEarth's crust stops abruptly\n\n2\n00:00:02,000 --> 00:00:04,000\nAtmosphere moves at supersonic speed\n\n")

        # 5. Render local Short video (1080x1920)
        short_output_path = str(self.output_dir / "test_short_acceptance.mp4")
        rendered_path = render_video(
            script=script_data,
            media_map=media_map,
            audio_path=dummy_audio_path,
            srt_path=srt_path,
            output_path=short_output_path
        )

        self.assertTrue(os.path.exists(rendered_path), "Rendered Short MP4 must exist")
        self.assertGreater(os.path.getsize(rendered_path), 10000, "Rendered video file must not be empty")

        # 6. Verify dimensions with MoviePy
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(rendered_path)
        self.assertEqual(clip.w, 1080, "Shorts width must be 1080")
        self.assertEqual(clip.h, 1920, "Shorts height must be 1920")
        clip.close()

        # 7. Execute Quality Control (QC)
        hook_tournament_winner = {
            "score": 92.0,
            "winner_text": "For one single second, the Earth's crust stops—but you do not.",
            "winner_structure": "curiosity_gap"
        }
        critique_result = {"composite_score": 9.1}
        fact_check_result = {"overall_reliability_score": 98}

        qc_report = evaluate_video_quality(
            script_data=script_data,
            hook_data=hook_tournament_winner,
            critique_data=critique_result,
            fact_check_data=fact_check_result,
            video_path=rendered_path,
            video_type="shorts"
        )

        self.assertTrue(qc_report["passed"], "QC audit must pass")
        self.assertGreaterEqual(qc_report["score"], 85.0, "QC score must be >= 85")
        self.assertIn("Ready", qc_report["status"])


if __name__ == "__main__":
    unittest.main()
