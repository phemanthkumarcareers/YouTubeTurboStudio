"""
Pipeline Orchestrator
Sequences and executes the agentic video generation pipeline.
Supports step-by-step modular execution or 1-click full automated flow.
"""
import os
import json
import threading
from config import load_config, OUTPUT_DIR
from core.state import state, update_state, set_stage, reset_pipeline_state
from core.logger import log_info, log_success, log_warn, log_error, log_stage
from agents.researcher import research_topic
from agents.scriptwriter import write_script
from audio.edge_tts_engine import generate_speech
from audio.music_manager import mix_voice_and_bgm
from media.media_manager import fetch_media_for_script
from video.renderer import render_video
from video.thumbnail_generator import generate_thumbnail
from youtube.uploader import upload_video_to_youtube

_stop_event = threading.Event()


def request_stop():
    """Signal running pipeline to cancel."""
    _stop_event.set()
    update_state(stop_requested=True)
    log_warn("Stop requested. Pipeline will halt gracefully after current task.")


def is_stopped() -> bool:
    return _stop_event.is_set()


def execute_pipeline(steps: list[str] = None, topic_override: str = "",
                     focus_angle: str = "", video_type: str = "normal",
                     custom_script: dict = None):
    """
    Run pipeline in background thread.
    steps: list like ['research', 'script', 'narration', 'media', 'video', 'thumbnail']
    """
    if steps is None:
        steps = ["research", "script", "narration", "media", "video", "thumbnail"]

    _stop_event.clear()
    reset_pipeline_state(video_type=video_type)

    def _worker():
        try:
            cfg = load_config()
            research_data = state.get("research_data")
            script_data = custom_script or state.get("script_data")

            # ── 1. RESEARCH ────────────────────────────────────────────────
            if "research" in steps:
                if is_stopped(): return
                log_stage("research", "running")
                set_stage("research", "running")
                research_data = research_topic(
                    topic_override=topic_override,
                    focus_angle=focus_angle,
                    video_type=video_type
                )
                update_state(research_data=research_data)
                set_stage("research", "done")
                log_stage("research", "done")

            # ── 2. SCRIPT ──────────────────────────────────────────────────
            if "script" in steps:
                if is_stopped(): return
                log_stage("script", "running")
                set_stage("script", "running")
                if not research_data:
                    research_data = {"topic": topic_override or "Mind-Bending Phenomenon"}
                script_data = write_script(research_data, video_type=video_type)
                update_state(
                    script_data=script_data,
                    description=script_data.get("description", ""),
                    tags=script_data.get("tags", [])
                )
                # Save script to output dir
                with open(OUTPUT_DIR / "script.json", "w", encoding="utf-8") as f:
                    json.dump(script_data, f, indent=2)
                set_stage("script", "done")
                log_stage("script", "done")

            if not script_data:
                # Try loading previous script if steps started from narration
                script_file = OUTPUT_DIR / "script.json"
                if script_file.exists():
                    with open(script_file, "r", encoding="utf-8") as f:
                        script_data = json.load(f)
                else:
                    raise ValueError("Cannot continue: No script available.")

            # ── 3. NARRATION & SRT ─────────────────────────────────────────
            audio_path = state.get("audio_path")
            srt_path = state.get("srt_path")
            if "narration" in steps:
                if is_stopped(): return
                log_stage("narration", "running")
                set_stage("narration", "running")
                # Combine section narrations
                full_narration = " ".join(s.get("narration", "") for s in script_data.get("sections", []))
                raw_voice_mp3, srt_file = generate_speech(full_narration, output_prefix="narration")
                
                # Mix voice with background music
                mixed_audio = mix_voice_and_bgm(raw_voice_mp3, str(OUTPUT_DIR / "audio_track.mp3"))
                update_state(audio_path=mixed_audio, srt_path=srt_file)
                audio_path = mixed_audio
                srt_path = srt_file
                set_stage("narration", "done")
                log_stage("narration", "done")

            # ── 4. MEDIA (IMAGES / VIDEO FOOTAGE) ──────────────────────────
            media_map = {}
            if "media" in steps:
                if is_stopped(): return
                log_stage("media", "running")
                set_stage("media", "running")
                media_map = fetch_media_for_script(script_data, video_type=video_type)
                set_stage("media", "done")
                log_stage("media", "done")

            # ── 5. VIDEO RENDERING ─────────────────────────────────────────
            video_file = None
            if "video" in steps:
                if is_stopped(): return
                log_stage("video", "running")
                set_stage("video", "running")
                if not audio_path or not os.path.exists(audio_path):
                    audio_path = str(OUTPUT_DIR / "audio_track.mp3")
                if not srt_path or not os.path.exists(srt_path):
                    srt_path = str(OUTPUT_DIR / "narration.srt")
                video_file = render_video(
                    script=script_data,
                    media_map=media_map,
                    audio_path=audio_path,
                    srt_path=srt_path,
                    output_path=str(OUTPUT_DIR / "final_video.mp4")
                )
                update_state(video_path=video_file)
                set_stage("video", "done")
                log_stage("video", "done")

            # ── 6. THUMBNAIL ───────────────────────────────────────────────
            if "thumbnail" in steps:
                if is_stopped(): return
                log_stage("thumbnail", "running")
                set_stage("thumbnail", "running")
                # Pick first image
                first_img = None
                for paths in media_map.values():
                    if paths and os.path.exists(paths[0]):
                        first_img = paths[0]
                        break
                thumb_file = generate_thumbnail(script_data, image_path=first_img)
                update_state(thumb_path=thumb_file)
                set_stage("thumbnail", "done")
                log_stage("thumbnail", "done")

            # ── 7. AUTO UPLOAD (IF ENABLED) ────────────────────────────────
            if cfg.get("auto_upload") and video_file and os.path.exists(video_file):
                log_info("Auto-upload enabled in configuration. Commencing YouTube upload...")
                upload_video_to_youtube(
                    video_path=video_file,
                    title=script_data.get("title", "Cinematic Video"),
                    description=state.get("description", script_data.get("description", "")),
                    tags=state.get("tags", script_data.get("tags", [])),
                    privacy=cfg.get("youtube_privacy", "private"),
                    category_id=cfg.get("youtube_category_id", "28"),
                    thumb_path=state.get("thumb_path")
                )

            log_success("Pipeline finished successfully! Video is ready in the Review Studio.")

        except Exception as e:
            err_msg = str(e)
            log_error(f"Pipeline error: {err_msg}")
            update_state(error=err_msg)
            # Mark running stages as error
            for s in state["stages"]:
                if state["stages"][s] == "running":
                    set_stage(s, "error")
        finally:
            update_state(running=False)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread
