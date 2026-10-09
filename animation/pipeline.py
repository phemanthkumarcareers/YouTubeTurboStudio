"""
Animation Pipeline — Shared Animation Engine
Full pipeline orchestration for animated video generation (Kids & Elders).
Generates topics, scripts, narration, storyboard scene graphs, composites video
using the shared AnimationRenderer, and validates output with Animation QC.
"""
import os
import time
import threading
from typing import List, Optional, Dict, Any

from config import load_config, OUTPUT_DIR
from core.channel_context import ChannelContext
from core.credential_manager import load_channel_credentials
from core.channel_registry import registry
from core.logger import log_info, log_success, log_warn, log_error, log_stage
from core.state import (
    state,
    update_state,
    reset_pipeline_state,
    set_stage
)
from animation.storyboarder import storyboarder
from animation.renderer import animation_renderer
from animation.qc import animation_qc
from audio.edge_tts_engine import generate_speech

_animation_stop_event = threading.Event()


def stop_animation_pipeline():
    _animation_stop_event.set()


def execute_animation_pipeline(
    channel_context: Optional[ChannelContext] = None,
    steps: Optional[List[str]] = None,
    topic_override: str = "",
    focus_angle: str = "",
    video_type: str = "shorts",
    custom_script: Optional[Dict[str, Any]] = None,
    mode: str = "final"
):
    """
    Executes the shared animation pipeline in a background worker thread.
    """
    if channel_context is None:
        channel_context = registry.get_active_channel()

    if steps is None:
        steps = ["research", "script", "narration", "video"]

    _animation_stop_event.clear()
    reset_pipeline_state(video_type=video_type)
    update_state(current_step="animating")

    def _worker():
        try:
            creds = load_channel_credentials(channel_context.channel_id)
            cfg = channel_context.to_pipeline_config(creds)
            is_kids = ("kid" in channel_context.channel_id.lower())

            # -------------------------------------------------------------
            # STEP 1: TOPIC / RESEARCH
            # -------------------------------------------------------------
            if "research" in steps or "topic" in steps:
                set_stage("research", "running")
                log_stage("RESEARCH", "RUNNING")

                if topic_override:
                    chosen_topic = topic_override
                else:
                    if is_kids:
                        chosen_topic = "The Magical Journey of Raindrops: How Clouds Make Rain"
                    else:
                        chosen_topic = "The Art of Slow Living: What Porch Conversations Taught Me"

                update_state(
                    research_data={
                        "topic": chosen_topic,
                        "angle": focus_angle or "Educational storytelling"
                    }
                )
                log_success(f"[ANIMATION] Active topic: '{chosen_topic}'")
                set_stage("research", "done")

            if _animation_stop_event.is_set():
                return

            # -------------------------------------------------------------
            # STEP 2: SCRIPT GENERATION
            # -------------------------------------------------------------
            script_data = custom_script or {}
            if "script" in steps:
                set_stage("script", "running")
                log_stage("SCRIPT", "RUNNING")

                if not script_data:
                    current_topic = (state.get("research_data") or {}).get("topic") or topic_override or "A Wonderful Day"
                    if is_kids:
                        script_data = {
                            "title": current_topic,
                            "scenes": [
                                {
                                    "scene_id": 1,
                                    "title": "Bright Introduction",
                                    "narration": f"Hello friends! Today we are exploring something amazing: {current_topic}!",
                                    "duration": 4.5,
                                    "bg_style": "vibrant_sky"
                                },
                                {
                                    "scene_id": 2,
                                    "title": "Interactive Wonder",
                                    "narration": "Look closely at the magic unfolding all around us. Isn't that incredible?",
                                    "duration": 5.0,
                                    "bg_style": "playful_park"
                                },
                                {
                                    "scene_id": 3,
                                    "title": "Joyful Lesson",
                                    "narration": "Remember: curiosity is your superpower! Keep exploring, shining bright, and smiling!",
                                    "duration": 4.5,
                                    "bg_style": "starry_space"
                                }
                            ]
                        }
                    else:
                        script_data = {
                            "title": current_topic,
                            "scenes": [
                                {
                                    "scene_id": 1,
                                    "title": "Warm Welcome",
                                    "narration": f"Welcome back. Today let us sit together and reflect upon {current_topic}.",
                                    "duration": 5.5,
                                    "bg_style": "cozy_study"
                                },
                                {
                                    "scene_id": 2,
                                    "title": "Cherished Wisdom",
                                    "narration": "In an ever-rushing world, the gentlest moments often leave the deepest warmth in our hearts.",
                                    "duration": 6.0,
                                    "bg_style": "sunset_porch"
                                },
                                {
                                    "scene_id": 3,
                                    "title": "Parting Reflection",
                                    "narration": "May today bring you quiet peace, a warm cup of tea, and gratitude for the journey.",
                                    "duration": 5.5,
                                    "bg_style": "warm_hearth"
                                }
                            ]
                        }

                if is_kids:
                    from kids.safeguards import kids_safeguards
                    gate_check = kids_safeguards.evaluate(script_data, channel_metadata={"youtube": channel_context.youtube})
                    if gate_check["hard_blocked"]:
                        raise ValueError(f"Kids Safeguards Hard Gate Violation: {gate_check['violations']}")

                update_state(script_data=script_data)
                log_success(f"[ANIMATION] Script created with {len(script_data.get('scenes', []))} scenes.")
                set_stage("script", "done")

            if _animation_stop_event.is_set():
                return

            # -------------------------------------------------------------
            # STEP 3: NARRATION (TTS)
            # -------------------------------------------------------------
            narration_mp3 = ""
            if "narration" in steps:
                set_stage("narration", "running")
                log_stage("NARRATION", "RUNNING")

                full_text = " ".join([sc.get("narration", "") for sc in script_data.get("scenes", [])])
                try:
                    narration_mp3, srt_path = generate_speech(full_text, output_prefix=f"{channel_context.channel_id}_narration")
                    update_state(audio_path=narration_mp3, srt_path=srt_path)
                    log_success(f"[ANIMATION] Narration synthesized: {os.path.basename(narration_mp3)}")
                except Exception as e:
                    log_warn(f"[ANIMATION] Speech synthesis fallback: {e}")
                    narration_mp3 = ""

                set_stage("narration", "done")

            if _animation_stop_event.is_set():
                return

            # -------------------------------------------------------------
            # STEP 4: STORYBOARDING & RENDERING
            # -------------------------------------------------------------
            if "video" in steps:
                set_stage("video", "running")
                log_stage("VIDEO", "RUNNING")

                scene_graph = storyboarder.build_storyboard(
                    script_data=script_data,
                    channel_context=channel_context,
                    video_format=video_type,
                    fps=15 if mode == "preview" else 30
                )
                log_info(f"[ANIMATION] Storyboard generated ({len(scene_graph.scenes)} scenes, total {scene_graph.total_duration:.1f}s)")

                output_filename = f"{channel_context.channel_id}_{video_type}_{int(time.time())}.mp4"
                final_mp4_path = str(OUTPUT_DIR / output_filename)

                animation_renderer.render(
                    scene_graph=scene_graph,
                    output_path=final_mp4_path,
                    mode=mode,
                    narration_audio_path=narration_mp3 if (narration_mp3 and os.path.exists(narration_mp3)) else None
                )

                update_state(video_path=final_mp4_path)
                set_stage("video", "done")

                # -------------------------------------------------------------
                # STEP 5: QUALITY CONTROL (QC)
                # -------------------------------------------------------------
                if is_kids:
                    from kids.qc import kids_qc
                    qc_report = kids_qc.evaluate(
                        scene_graph=scene_graph,
                        video_path=final_mp4_path,
                        script_data=script_data,
                        channel_metadata={"youtube": channel_context.youtube}
                    )
                else:
                    qc_report = animation_qc.evaluate(
                        scene_graph=scene_graph,
                        video_path=final_mp4_path,
                        audio_path=narration_mp3
                    )

                if qc_report.get("passed"):
                    log_success(f"[ANIMATION] QC Passed! Score: {qc_report['score']}/100 (Publish Ready: {qc_report.get('publish_ready', True)})")
                else:
                    log_warn(f"[ANIMATION] QC Warning: Score {qc_report['score']}/100 (Publish Ready: False)")

            update_state(running=False, current_step="done")
            log_success(f"[ANIMATION] Pipeline successfully completed for {channel_context.name}!")

        except Exception as e:
            import traceback
            err = traceback.format_exc()
            log_error(f"[ANIMATION] Pipeline failed: {err}")
            update_state(running=False, error=str(e), current_step="error")
            for s in ("research", "script", "narration", "video"):
                if state["stages"].get(s) == "running":
                    set_stage(s, "error")

    thread = threading.Thread(target=_worker, daemon=True, name=f"anim-pipeline-{channel_context.channel_id}")
    thread.start()
    return thread
