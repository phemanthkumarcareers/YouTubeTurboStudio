"""
Pipeline Orchestrator — Phase 2 Enhanced
Sequences and executes the agentic video generation pipeline with Phase 2 enhancements:
1. Topic Candidate Ranking & User Topic Mode
2. Hook Tournament
3. Science Scriptwriter
4. Critic & Multi-pass Rewrite Loop
5. Scientific Fact-Checking Layer
6. Visual Director Beat Planning
7. Video-First Media Retrieval
8. Narration & Audio Ducking
9. Professional Captions & Ken Burns / Video Rendering
10. Pre- & Post-Render Quality Control (QC) & Transparent Scoring
"""
import os
import json
import threading
from typing import Optional, List, Dict, Any
from config import load_config, OUTPUT_DIR
from core.state import state, update_state, set_stage, reset_pipeline_state
from core.logger import log_info, log_success, log_warn, log_error, log_stage
from core.channel_context import ChannelContext
from core.channel_registry import registry
from core.credential_manager import load_channel_credentials
from agents.topic_engine import discover_and_rank_topics, structure_user_topic
from agents.hook_tournament import run_hook_tournament
from agents.scriptwriter import write_script
from agents.critic import review_and_refine_script
from agents.fact_checker import check_script_facts
from video.visual_director import plan_visual_beats
from audio.edge_tts_engine import generate_speech
from audio.music_manager import mix_voice_and_bgm
from media.media_manager import fetch_media_for_script
from video.renderer import render_video
from video.thumbnail_generator import generate_thumbnail
from core.quality import evaluate_video_quality
from youtube.uploader import upload_video_to_youtube

_stop_event = threading.Event()


def request_stop():
    """Signal running pipeline to cancel."""
    _stop_event.set()
    update_state(stop_requested=True)
    log_warn("Stop requested. Pipeline will halt gracefully after current task.")


def is_stopped() -> bool:
    return _stop_event.is_set()


def execute_pipeline(
    steps: Optional[List[str]] = None,
    topic_override: str = "",
    focus_angle: str = "",
    video_type: str = "normal",
    custom_script: Optional[Dict[str, Any]] = None,
    channel_context: Optional[ChannelContext] = None
):
    """
    Run pipeline in background thread with explicit ChannelContext and Phase 2 stages.
    """
    if steps is None:
        steps = ["research", "script", "narration", "media", "video", "thumbnail"]

    if channel_context is None:
        channel_context = registry.get_active_channel()

    _stop_event.clear()
    reset_pipeline_state(video_type=video_type)
    update_state(channel_id=channel_context.channel_id)

    def _worker():
        try:
            # Resolve channel-scoped config and credentials
            creds = load_channel_credentials(channel_context.channel_id)
            cfg = channel_context.to_pipeline_config(creds)
            base_cfg = load_config()
            for k, v in base_cfg.items():
                if k not in cfg or cfg[k] is None or cfg[k] == "":
                    cfg[k] = v

            log_info(f"Pipeline started for channel: '{channel_context.name}' (ID: {channel_context.channel_id})")

            research_data = state.get("research_data")
            hook_data = state.get("hook_data")
            script_data = custom_script or state.get("script_data")
            critique_data = state.get("critique_data")
            fact_check_data = state.get("fact_check_data")
            is_shorts = (video_type == "shorts")

            # ── 1. RESEARCH & HOOK TOURNAMENT ──────────────────────────────
            if "research" in steps:
                if is_stopped(): return
                log_stage("research", "running")
                set_stage("research", "running")

                # Topic Mode: User Topic or Candidate Ranking
                if topic_override and topic_override.strip():
                    research_data = structure_user_topic(topic_override, video_type=video_type)
                else:
                    research_data = discover_and_rank_topics(video_type=video_type)

                # Hook Tournament: 8-way psychological hook optimization
                hook_data = run_hook_tournament(research_data, is_shorts=is_shorts)
                research_data["hook_question"] = hook_data.get("winner_text", research_data.get("hook_question"))
                research_data["hook_tournament"] = hook_data

                update_state(research_data=research_data, hook_data=hook_data)
                set_stage("research", "done")
                log_stage("research", "done")

            # ── 2. SCRIPT, CRITIC & FACT-CHECK ─────────────────────────────
            if "script" in steps:
                if is_stopped(): return
                log_stage("script", "running")
                set_stage("script", "running")

                if not research_data:
                    research_data = {"topic": topic_override or "Mind-Bending Phenomenon"}

                # Draft script
                draft_script = write_script(research_data, video_type=video_type)

                # Critic & Rewrite loop (11 criteria, automatic iterations)
                script_data, critique_data = review_and_refine_script(draft_script, is_shorts=is_shorts)

                # Scientific Fact-Checking
                fact_check_data = check_script_facts(script_data)

                # Visual Director planning
                visual_beats = plan_visual_beats(script_data, is_shorts=is_shorts)
                script_data["visual_beats"] = visual_beats

                update_state(
                    script_data=script_data,
                    description=script_data.get("description", ""),
                    tags=script_data.get("tags", []),
                    critique_data=critique_data,
                    fact_check_data=fact_check_data
                )

                # Save script to output dir
                with open(OUTPUT_DIR / "script.json", "w", encoding="utf-8") as f:
                    json.dump(script_data, f, indent=2)

                set_stage("script", "done")
                log_stage("script", "done")

            if not script_data:
                script_file = OUTPUT_DIR / "script.json"
                if script_file.exists():
                    with open(script_file, "r", encoding="utf-8") as f:
                        script_data = json.load(f)
                else:
                    raise ValueError("Cannot continue: No script available.")

            # ── 3. NARRATION, SRT & AUDIO DUCKING ──────────────────────────
            audio_path = state.get("audio_path")
            srt_path = state.get("srt_path")
            if "narration" in steps:
                if is_stopped(): return
                log_stage("narration", "running")
                set_stage("narration", "running")

                full_narration = " ".join(s.get("narration", "") for s in script_data.get("sections", []))
                raw_voice_mp3, srt_file = generate_speech(full_narration, output_prefix="narration")

                # Mix voice with background music + audio ducking
                mixed_audio = mix_voice_and_bgm(raw_voice_mp3, str(OUTPUT_DIR / "audio_track.mp3"))
                update_state(audio_path=mixed_audio, srt_path=srt_file)
                audio_path = mixed_audio
                srt_path = srt_file
                set_stage("narration", "done")
                log_stage("narration", "done")

            # ── 4. MEDIA (VIDEO-FIRST HIERARCHY) ───────────────────────────
            media_map = {}
            if "media" in steps:
                if is_stopped(): return
                log_stage("media", "running")
                set_stage("media", "running")
                media_map = fetch_media_for_script(script_data, video_type=video_type)
                set_stage("media", "done")
                log_stage("media", "done")

            # ── 5. VIDEO RENDERING & PROFESSIONAL CAPTIONS ─────────────────
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

                # Quality Control Audit & Scoring
                qc_report = evaluate_video_quality(
                    script_data=script_data,
                    hook_data=hook_data,
                    critique_data=critique_data,
                    fact_check_data=fact_check_data,
                    video_path=video_file,
                    video_type=video_type
                )
                update_state(video_path=video_file, qc_report=qc_report)
                set_stage("video", "done")
                log_stage("video", "done")

            # ── 6. THUMBNAIL ───────────────────────────────────────────────
            if "thumbnail" in steps:
                if is_stopped(): return
                log_stage("thumbnail", "running")
                set_stage("thumbnail", "running")
                first_img = None
                for paths in media_map.values():
                    if paths and os.path.exists(paths[0]) and not paths[0].endswith(".mp4"):
                        first_img = paths[0]
                        break
                thumb_file = generate_thumbnail(script_data, image_path=first_img)
                update_state(thumb_path=thumb_file)
                set_stage("thumbnail", "done")
                log_stage("thumbnail", "done")

            # ── 7. AUTO UPLOAD (IF ENABLED) ────────────────────────────────
            if cfg.get("auto_upload") and video_file and os.path.exists(video_file):
                log_info(f"Auto-upload enabled for '{channel_context.name}'. Commencing YouTube upload...")
                upload_video_to_youtube(
                    video_path=video_file,
                    title=script_data.get("title", "Cinematic Video"),
                    description=state.get("description", script_data.get("description", "")),
                    tags=state.get("tags", script_data.get("tags", [])),
                    privacy=cfg.get("youtube_privacy", "private"),
                    category_id=cfg.get("youtube_category_id", "28"),
                    thumb_path=state.get("thumb_path"),
                    channel_id=channel_context.channel_id,
                    expected_youtube_channel_id=cfg.get("expected_youtube_channel_id"),
                    made_for_kids=cfg.get("made_for_kids", False)
                )

            log_success(f"Pipeline finished successfully for '{channel_context.name}'! Ready in Review Studio.")

        except Exception as e:
            err_msg = str(e)
            log_error(f"Pipeline error [{channel_context.name}]: {err_msg}")
            update_state(error=err_msg)
            for s in state["stages"]:
                if state["stages"][s] == "running":
                    set_stage(s, "error")
        finally:
            update_state(running=False)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread
