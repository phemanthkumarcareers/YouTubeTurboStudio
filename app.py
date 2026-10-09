"""
YouTube Turbo Studio - Web Application Server
Unified Control Center for Agentic AI Video Generation & YouTube Automation.
"""
import os
import sys
import json
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, Response, abort

# Set up module paths
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import (
    load_config, save_config, load_banned_topics, save_banned_topics,
    POPULAR_VOICES, YOUTUBE_CATEGORIES, OUTPUT_DIR, CLIENT_SECRET_PATH
)
from core.state import get_state, update_state
from core.logger import log_stream, log_info, log_warn, log_success, log_error
from core.pipeline import execute_pipeline, request_stop
from agents.llm_client import test_gemini_connection, test_groq_connection, generate
from media.pexels_client import test_pexels_key
from media.pixabay_client import test_pixabay_key
from audio.edge_tts_engine import preview_voice_sample
from video.thumbnail_generator import generate_thumbnail
from youtube.auth import check_auth_status, save_client_secret_json, save_client_credentials, run_oauth_flow, load_client_secret_from_path
from youtube.uploader import upload_video_to_youtube
from youtube.channel_verifier import verify_channel
from core.channel_registry import registry
from core.credential_manager import (
    load_channel_credentials,
    save_channel_credentials,
    get_masked_channel_credentials
)
from core.pipeline_router import route_and_execute

app = Flask(
    __name__,
    template_folder=str(ROOT_DIR / "templates"),
    static_folder=str(ROOT_DIR / "static")
)
app.config["JSON_AS_ASCII"] = False


# ── PAGE ROUTES ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── LOGS & SSE STREAM ───────────────────────────────────────────────────────

@app.route("/api/logs/stream")
def api_logs_stream():
    return Response(log_stream(), mimetype="text/event-stream")


@app.route("/api/status")
def api_status():
    st = get_state()
    st["has_video"] = bool(st.get("video_path") and os.path.exists(st["video_path"]))
    st["has_thumb"] = bool(st.get("thumb_path") and os.path.exists(st["thumb_path"]))
    st["has_script"] = bool(st.get("script_data"))
    return jsonify(st)


# ── CHANNEL MANAGEMENT ──────────────────────────────────────────────────────

@app.route("/api/channels", methods=["GET"])
def api_list_channels():
    channels = registry.list_channels()
    active_id = registry.get_active_channel_id()
    return jsonify({
        "ok": True,
        "channels": channels,
        "active_channel_id": active_id
    })


@app.route("/api/channels/active", methods=["GET"])
def api_get_active_channel():
    chan = registry.get_active_channel()
    masked_creds = get_masked_channel_credentials(chan.channel_id)
    yt_status = check_auth_status(chan.channel_id)
    return jsonify({
        "ok": True,
        "channel": chan.to_dict(),
        "credentials": masked_creds,
        "youtube_status": yt_status
    })


@app.route("/api/channels/select", methods=["POST"])
def api_select_channel():
    body = request.get_json(force=True) or {}
    channel_id = body.get("channel_id", "").strip()
    if not channel_id:
        return jsonify({"ok": False, "error": "channel_id is required"}), 400

    if not registry.set_active_channel_id(channel_id):
        return jsonify({"ok": False, "error": f"Channel '{channel_id}' not found"}), 404

    chan = registry.get_active_channel()
    update_state(channel_id=chan.channel_id)
    log_info(f"Switched active channel to '{chan.name}' ({chan.channel_id})")
    masked_creds = get_masked_channel_credentials(chan.channel_id)
    yt_status = check_auth_status(chan.channel_id)

    return jsonify({
        "ok": True,
        "message": f"Active channel switched to {chan.name}",
        "channel": chan.to_dict(),
        "credentials": masked_creds,
        "youtube_status": yt_status
    })


@app.route("/api/channels/save", methods=["POST"])
def api_save_channel():
    body = request.get_json(force=True) or {}
    channel_id = body.get("channel_id") or registry.get_active_channel_id()
    try:
        updated_chan = registry.save_channel(channel_id, body)
        if channel_id == registry.get_active_channel_id():
            flat_cfg = updated_chan.to_pipeline_config(load_channel_credentials(channel_id))
            save_config(flat_cfg)
        log_success(f"Channel '{updated_chan.name}' configuration saved successfully.")
        return jsonify({
            "ok": True,
            "channel": updated_chan.to_dict(),
            "credentials": get_masked_channel_credentials(channel_id)
        })
    except Exception as e:
        log_error(f"Failed to save channel {channel_id}: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/channels/add", methods=["POST"])
def api_add_channel():
    body = request.get_json(force=True) or {}
    try:
        new_chan = registry.add_channel(body)
        log_success(f"Added new channel: '{new_chan.name}' ({new_chan.channel_id})")
        return jsonify({"ok": True, "channel": new_chan.to_dict()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


# ── PIPELINE CONTROL ────────────────────────────────────────────────────────

@app.route("/api/generate", methods=["POST"])
def api_generate():
    body = request.get_json(force=True) or {}
    steps = body.get("steps", ["research", "script", "narration", "media", "video", "thumbnail"])
    topic_override = body.get("topic", "").strip()
    focus_angle = body.get("focus_angle", "").strip()
    video_type = body.get("video_type", "normal")
    channel_id = body.get("channel_id") or registry.get_active_channel_id()

    content_mode = body.get("content_mode", "shorts" if video_type == "shorts" else "long").lower()
    parent_content_id = body.get("parent_content_id")
    if content_mode == "shorts_linked":
        if not parent_content_id:
            return jsonify({"ok": False, "error": "Linked Shorts mode requires selecting a parent Long video."}), 400
        from core.content_family import content_family_mgr, CrossChannelLinkingError
        try:
            valid, err, parent = content_family_mgr.validate_parent(channel_id, parent_content_id)
            if not valid:
                return jsonify({"ok": False, "error": err}), 400
        except CrossChannelLinkingError as cce:
            return jsonify({"ok": False, "error": str(cce)}), 400
        video_type = "shorts"
    elif content_mode == "shorts":
        video_type = "shorts"
    elif content_mode == "long":
        video_type = "normal"

    st = get_state()
    if st.get("running"):
        return jsonify({"ok": False, "error": "Pipeline is already running."}), 400

    chan_ctx = registry.get_channel(channel_id)
    if not chan_ctx:
        return jsonify({"ok": False, "error": f"Channel '{channel_id}' not found"}), 404

    route_and_execute(
        channel_context=chan_ctx,
        steps=steps,
        topic_override=topic_override,
        focus_angle=focus_angle,
        video_type=video_type
    )
    return jsonify({"ok": True, "message": f"Pipeline initiated for {chan_ctx.name}", "channel_id": channel_id})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    request_stop()
    return jsonify({"ok": True, "message": "Stop requested"})


# ── MEDIA STREAMING ─────────────────────────────────────────────────────────

@app.route("/api/media/video")
def serve_video():
    p = OUTPUT_DIR / "final_video.mp4"
    if p.exists():
        return send_file(str(p), mimetype="video/mp4")
    abort(404)


@app.route("/api/media/thumbnail")
def serve_thumbnail():
    p = OUTPUT_DIR / "thumbnail.jpg"
    if p.exists():
        return send_file(str(p), mimetype="image/jpeg")
    abort(404)


@app.route("/api/media/audio")
def serve_audio():
    p = OUTPUT_DIR / "audio_track.mp3"
    if not p.exists():
        p = OUTPUT_DIR / "narration.mp3"
    if p.exists():
        return send_file(str(p), mimetype="audio/mpeg")
    abort(404)


@app.route("/api/preview/voice", methods=["POST"])
def api_preview_voice():
    body = request.get_json(force=True) or {}
    voice_id = body.get("voice_id", "en-US-JennyNeural")
    try:
        sample_file = preview_voice_sample(voice_id)
        return send_file(sample_file, mimetype="audio/mpeg")
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ── SCRIPT & REVIEW ─────────────────────────────────────────────────────────

@app.route("/api/script", methods=["GET"])
def api_get_script():
    st = get_state()
    script = st.get("script_data")
    if not script:
        p = OUTPUT_DIR / "script.json"
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                script = json.load(f)
    return jsonify({
        "script": script,
        "description": st.get("description") or (script.get("description") if script else ""),
        "tags": st.get("tags") or (script.get("tags") if script else []),
        "hook_tournament": st.get("hook_data"),
        "critique": st.get("critique_data"),
        "fact_check": st.get("fact_check_data")
    })


@app.route("/api/qc/report", methods=["GET"])
def api_get_qc_report():
    st = get_state()
    qc = st.get("qc_report")
    if not qc:
        p = OUTPUT_DIR / "qc_report.json"
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    qc = json.load(f)
            except Exception:
                pass
    if not qc:
        qc = {
            "score": 0,
            "status": "Pending",
            "passed": False,
            "details": ["No video evaluated yet."]
        }
    return jsonify({"ok": True, "report": qc})


@app.route("/api/script/save", methods=["POST"])
def api_save_script():
    body = request.get_json(force=True) or {}
    title = body.get("title")
    description = body.get("description")
    tags = body.get("tags")

    st = get_state()
    script = st.get("script_data") or {}
    if title:
        script["title"] = title
    if description:
        script["description"] = description
        update_state(description=description)
    if tags is not None:
        script["tags"] = tags
        update_state(tags=tags)

    update_state(script_data=script)
    with open(OUTPUT_DIR / "script.json", "w", encoding="utf-8") as f:
        json.dump(script, f, indent=2)

    return jsonify({"ok": True})


@app.route("/api/script/regenerate-description", methods=["POST"])
def api_regenerate_description():
    st = get_state()
    script = st.get("script_data") or {}
    title = script.get("title", "Video")
    prompt = f"""Write an engaging, high-converting YouTube description for this video:
Title: {title}
Tags: {json.dumps(script.get('tags', []))}

Requirements:
- Strong curiosity opening hook
- 3 key bullet points on what viewers will discover
- Call to action to subscribe, like, and comment
- Include hashtags at the very end
Return ONLY the description text."""
    try:
        new_desc = generate(prompt)
        update_state(description=new_desc)
        return jsonify({"ok": True, "description": new_desc})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/script/regenerate-thumbnail", methods=["POST"])
def api_regenerate_thumbnail():
    body = request.get_json(force=True) or {}
    st = get_state()
    script = st.get("script_data") or {}
    if "title" in body and body["title"]:
        script["title"] = body["title"]

    try:
        # Check if an existing image can be used
        img_dir = OUTPUT_DIR / "images"
        sample_img = next((str(p) for p in img_dir.glob("*.jpg")), None)
        thumb_path = generate_thumbnail(script, image_path=sample_img)
        update_state(thumb_path=thumb_path)
        return jsonify({"ok": True, "timestamp": int(os.path.getmtime(thumb_path))})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ── CONFIGURATION & API KEYS ────────────────────────────────────────────────

@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    chan = registry.get_active_channel()
    creds = load_channel_credentials(chan.channel_id)
    cfg = chan.to_pipeline_config(creds)
    # Merge with base config for backwards compatibility
    global_cfg = load_config()
    for k, v in global_cfg.items():
        if k not in cfg or cfg[k] is None or cfg[k] == "":
            cfg[k] = v

    banned = chan.prompts.get("banned_topics") or load_banned_topics()
    return jsonify({
        "config": cfg,
        "active_channel": chan.to_dict(),
        "masked_credentials": get_masked_channel_credentials(chan.channel_id),
        "voices": POPULAR_VOICES,
        "categories": YOUTUBE_CATEGORIES,
        "banned_topics": banned
    })


@app.route("/api/settings/save", methods=["POST"])
def api_save_settings():
    body = request.get_json(force=True) or {}
    try:
        active_id = registry.get_active_channel_id()
        registry.save_channel(active_id, body)
        updated = save_config(body)
        log_success(f"Studio configuration saved successfully for '{active_id}'.")
        return jsonify({"ok": True, "config": updated})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/settings/test-gemini", methods=["POST"])
def api_test_gemini():
    body = request.get_json(force=True) or {}
    key = body.get("gemini_api_key", "")
    model = body.get("gemini_model", "gemini-2.5-flash")
    ok, msg = test_gemini_connection(key, model)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/settings/test-groq", methods=["POST"])
def api_test_groq():
    body = request.get_json(force=True) or {}
    key = body.get("groq_api_key", "")
    model = body.get("groq_model", "llama-3.3-70b-versatile")
    ok, msg = test_groq_connection(key, model)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/settings/test-pexels", methods=["POST"])
def api_test_pexels():
    body = request.get_json(force=True) or {}
    key = body.get("pexels_api_key", "")
    ok, msg = test_pexels_key(key)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/settings/test-pixabay", methods=["POST"])
def api_test_pixabay():
    body = request.get_json(force=True) or {}
    key = body.get("pixabay_api_key", "")
    ok, msg = test_pixabay_key(key)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/settings/banned-topics", methods=["POST"])
def api_save_banned_topics():
    body = request.get_json(force=True) or {}
    topics = body.get("topics", [])
    if save_banned_topics(topics):
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Could not save banned topics"}), 500


# ── YOUTUBE INTEGRATION & OAUTH ─────────────────────────────────────────────

@app.route("/api/youtube/status", methods=["GET"])
def api_youtube_status():
    cid = request.args.get("channel_id") or registry.get_active_channel_id()
    return jsonify(check_auth_status(channel_id=cid))


@app.route("/api/youtube/save-secret-json", methods=["POST"])
def api_youtube_save_secret():
    cid = request.form.get("channel_id") or registry.get_active_channel_id()
    if "file" in request.files:
        f = request.files["file"]
        try:
            data = json.load(f)
            save_client_secret_json(data, channel_id=cid)
            return jsonify({"ok": True, "message": f"Uploaded and saved client_secret.json for '{cid}'!"})
        except Exception as e:
            return jsonify({"ok": False, "error": f"Invalid JSON file: {e}"}), 400

    body = request.get_json(force=True) or {}
    cid = body.get("channel_id") or cid
    raw_json = body.get("raw_json", "").strip()
    if raw_json:
        try:
            data = json.loads(raw_json)
            save_client_secret_json(data, channel_id=cid)
            return jsonify({"ok": True, "message": f"Client secret JSON saved for '{cid}'!"})
        except Exception as e:
            return jsonify({"ok": False, "error": f"Invalid JSON syntax: {e}"}), 400

    return jsonify({"ok": False, "error": "No file or JSON data provided."}), 400


@app.route("/api/youtube/save-credentials", methods=["POST"])
def api_youtube_save_credentials():
    body = request.get_json(force=True) or {}
    cid = body.get("channel_id") or registry.get_active_channel_id()
    client_id = body.get("client_id", "").strip()
    client_secret = body.get("client_secret", "").strip()
    if not client_id or not client_secret:
        return jsonify({"ok": False, "error": "Both Client ID and Client Secret are required."}), 400

    if save_client_credentials(client_id, client_secret, channel_id=cid):
        return jsonify({"ok": True, "message": f"Client credentials saved for '{cid}'!"})
    return jsonify({"ok": False, "error": "Failed to save credentials."}), 500


@app.route("/api/youtube/load-secret-path", methods=["POST"])
def api_youtube_load_secret_path():
    body = request.get_json(force=True) or {}
    cid = body.get("channel_id") or registry.get_active_channel_id()
    filepath = body.get("filepath", "").strip()
    if not filepath:
        return jsonify({"ok": False, "error": "No file path provided"}), 400
    ok, msg = load_client_secret_from_path(filepath, channel_id=cid)
    return jsonify({"ok": ok, "message": msg, "error": None if ok else msg})


@app.route("/api/youtube/authenticate", methods=["POST"])
def api_youtube_authenticate():
    body = request.get_json(silent=True) or {}
    cid = body.get("channel_id") or registry.get_active_channel_id()
    res = run_oauth_flow(channel_id=cid)
    return jsonify(res)


@app.route("/api/youtube/upload", methods=["POST"])
def api_youtube_upload():
    body = request.get_json(force=True) or {}
    cid = body.get("channel_id") or registry.get_active_channel_id()
    chan_ctx = registry.get_channel(cid)
    if not chan_ctx:
        return jsonify({"ok": False, "error": f"Channel '{cid}' not found"}), 404

    # Pre-upload verification check
    exp_id = chan_ctx.youtube.get("channel_id", "")
    verified, verif_msg, _ = verify_channel(cid, exp_id)
    if not verified:
        log_error(f"YouTube upload rejected: {verif_msg}")
        return jsonify({"ok": False, "error": verif_msg}), 400

    privacy = body.get("privacy", chan_ctx.youtube.get("privacy", "private"))
    category_id = body.get("category_id", chan_ctx.youtube.get("category_id", "28"))
    publish_at = body.get("publish_at")
    custom_title = body.get("title")
    custom_desc = body.get("description")

    st = get_state()
    video_path = st.get("video_path")
    if not video_path or not os.path.exists(video_path):
        video_path = str(OUTPUT_DIR / "final_video.mp4")
    if not os.path.exists(video_path):
        return jsonify({"ok": False, "error": "No video file found to upload."}), 400

    script = st.get("script_data") or {}
    title = custom_title or script.get("title", f"Cinematic Video - {chan_ctx.name}")
    description = custom_desc or st.get("description") or script.get("description", "")
    tags = st.get("tags") or script.get("tags", [])
    thumb_path = st.get("thumb_path") or str(OUTPUT_DIR / "thumbnail.jpg")

    def _upload_async():
        try:
            upload_video_to_youtube(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags,
                privacy=privacy,
                category_id=category_id,
                publish_at=publish_at if publish_at else None,
                thumb_path=thumb_path,
                channel_id=cid,
                expected_youtube_channel_id=exp_id,
                made_for_kids=chan_ctx.youtube.get("made_for_kids", False)
            )
        except Exception as e:
            log_error(f"YouTube upload failed: {e}")
            update_state(error=str(e), uploading=False)

    threading.Thread(target=_upload_async, daemon=True).start()
    return jsonify({"ok": True, "message": f"Upload commenced for {chan_ctx.name} in background."})


# ── PHASE 6: AUTOMATION, SCHEDULING & ANALYTICS ROUTES ─────────────────────

@app.route("/api/jobs", methods=["GET", "POST"])
def api_jobs():
    from automation.job_queue import job_queue
    if request.method == "POST":
        body = request.get_json(force=True) or {}
        cid = body.get("channel_id") or registry.get_active_channel().channel_id
        topic = body.get("topic", "")
        vtype = body.get("video_type", "shorts")
        meta = body.get("metadata", {})
        if meta.get("relationship_type") == "DERIVED" or meta.get("parent_content_id"):
            parent_id = meta.get("parent_content_id")
            from core.content_family import content_family_mgr, CrossChannelLinkingError
            try:
                valid, msg, _ = content_family_mgr.validate_parent(cid, parent_id)
                if not valid:
                    return jsonify({"ok": False, "error": msg}), 400
            except CrossChannelLinkingError as cce:
                return jsonify({"ok": False, "error": str(cce)}), 400

        job = job_queue.enqueue(channel_id=cid, topic=topic, video_type=vtype, metadata=meta)
        return jsonify({"ok": True, "job": job.to_dict()})

    cid = request.args.get("channel_id")
    status = request.args.get("status")
    limit = int(request.args.get("limit", 50))
    jobs = job_queue.list_jobs(channel_id=cid, status=status, limit=limit)
    return jsonify({"ok": True, "jobs": [j.to_dict() for j in jobs]})


@app.route("/api/jobs/<job_id>", methods=["GET"])
def api_get_job(job_id):
    from automation.job_queue import job_queue
    job = job_queue.get_job(job_id)
    if not job:
        return jsonify({"ok": False, "error": "Job not found."}), 404
    return jsonify({"ok": True, "job": job.to_dict()})


@app.route("/api/jobs/<job_id>/retry", methods=["POST"])
def api_retry_job(job_id):
    from automation.job_queue import job_queue
    job = job_queue.retry_job(job_id)
    if not job:
        return jsonify({"ok": False, "error": "Job not found."}), 404
    return jsonify({"ok": True, "job": job.to_dict()})


@app.route("/api/jobs/<job_id>/cancel", methods=["POST"])
def api_cancel_job(job_id):
    from automation.job_queue import job_queue
    ok = job_queue.cancel_job(job_id)
    return jsonify({"ok": ok})


@app.route("/api/review-queue", methods=["GET"])
def api_review_queue():
    from automation.review_queue import review_queue
    cid = request.args.get("channel_id")
    pending = review_queue.list_pending(channel_id=cid)
    return jsonify({"ok": True, "review_queue": pending})


@app.route("/api/review-queue/<job_id>/approve", methods=["POST"])
def api_review_approve(job_id):
    from automation.review_queue import review_queue
    body = request.get_json(force=True) or {}
    notes = body.get("notes", "")
    ok = review_queue.approve(job_id, notes=notes)
    return jsonify({"ok": ok})


@app.route("/api/review-queue/<job_id>/reject", methods=["POST"])
def api_review_reject(job_id):
    from automation.review_queue import review_queue
    body = request.get_json(force=True) or {}
    notes = body.get("notes", "")
    ok = review_queue.reject(job_id, notes=notes)
    return jsonify({"ok": ok})


@app.route("/api/schedules", methods=["GET", "POST"])
def api_schedules():
    from automation.scheduler import auto_scheduler
    if request.method == "POST":
        body = request.get_json(force=True) or {}
        cid = body.get("channel_id") or registry.get_active_channel().channel_id
        enabled = bool(body.get("enabled", True))
        interval = float(body.get("interval_hours", 24.0))
        cron_expr = body.get("cron_expression", "0 10 * * *")
        vtype = body.get("video_type", "shorts")
        sched = auto_scheduler.configure_schedule(
            channel_id=cid, enabled=enabled, interval_hours=interval,
            cron_expression=cron_expr, video_type=vtype
        )
        return jsonify({"ok": True, "schedule": sched})

    cid = request.args.get("channel_id")
    if cid:
        sched = auto_scheduler.get_schedule(cid)
        return jsonify({"ok": True, "schedule": sched})
    schedules = auto_scheduler.list_schedules()
    return jsonify({"ok": True, "schedules": schedules})


@app.route("/api/schedules/trigger", methods=["POST"])
def api_schedules_trigger():
    from automation.scheduler import auto_scheduler
    body = request.get_json(force=True) or {}
    cid = body.get("channel_id") or registry.get_active_channel().channel_id
    job = auto_scheduler.trigger_scheduled_run(cid)
    return jsonify({"ok": True, "job": job.to_dict()})


@app.route("/api/analytics", methods=["GET", "POST"])
def api_analytics():
    from automation.analytics import analytics_manager
    if request.method == "POST":
        body = request.get_json(force=True) or {}
        rowid = analytics_manager.ingest_metrics(
            channel_id=body.get("channel_id"),
            video_id=body.get("video_id"),
            title=body.get("title", ""),
            format_type=body.get("format", "shorts"),
            views=int(body.get("views", 0)),
            likes=int(body.get("likes", 0)),
            comments=int(body.get("comments", 0)),
            watch_time_hours=float(body.get("watch_time_hours", 0.0)),
            avg_view_duration_sec=float(body.get("avg_view_duration_sec", 0.0)),
            avg_view_pct=float(body.get("avg_view_pct", 0.0)),
            subscribers_gained=int(body.get("subscribers_gained", 0))
        )
        return jsonify({"ok": True, "id": rowid})

    cid = request.args.get("channel_id") or registry.get_active_channel().channel_id
    summary = analytics_manager.get_channel_summary(cid)
    metrics = analytics_manager.get_channel_metrics(cid, limit=25)
    return jsonify({"ok": True, "summary": summary, "metrics": metrics})


@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    from automation.dashboard import dashboard_service
    cid = request.args.get("channel_id") or registry.get_active_channel().channel_id
    data = dashboard_service.get_channel_dashboard(cid)
    return jsonify({"ok": True, "dashboard": data})


@app.route("/api/learning-loop", methods=["GET"])
def api_learning_loop():
    from automation.learning_loop import learning_loop
    cid = request.args.get("channel_id") or registry.get_active_channel().channel_id
    strategy = learning_loop.get_strategy_recommendation(cid)
    return jsonify({"ok": True, "strategy": strategy})


# ── CONTENT GUARD: CONTENT MODES, ORIGINALITY & READINESS ROUTES ────────────

@app.route("/api/content-modes/eligible-parents", methods=["GET"])
def api_eligible_parents():
    from core.content_family import content_family_mgr
    cid = request.args.get("channel_id") or registry.get_active_channel_id()
    parents = content_family_mgr.list_eligible_parents(cid)
    return jsonify({"ok": True, "channel_id": cid, "eligible_parents": parents})


@app.route("/api/content-modes/validate-parent", methods=["POST"])
def api_validate_parent():
    from core.content_family import content_family_mgr, CrossChannelLinkingError
    body = request.get_json(force=True) or {}
    cid = body.get("channel_id") or registry.get_active_channel_id()
    parent_id = body.get("parent_content_id")
    try:
        valid, msg, parent = content_family_mgr.validate_parent(cid, parent_id)
        return jsonify({"ok": valid, "valid": valid, "message": msg, "parent": parent})
    except CrossChannelLinkingError as e:
        return jsonify({"ok": False, "valid": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "valid": False, "error": str(e)}), 400


@app.route("/api/readiness/<content_id>", methods=["GET"])
def api_get_readiness(content_id):
    from core.content_family import content_family_mgr
    from core.compliance_gate import compliance_gate_mgr
    rec = content_family_mgr.get_content(content_id)
    if not rec:
        return jsonify({"ok": False, "error": "Content record not found."}), 404
    report = compliance_gate_mgr.evaluate_readiness(
        channel_id=rec["channel_id"],
        production_quality_score=rec["production_quality_score"],
        originality_score=rec["originality_score"],
        technical_qc_passed=(rec["technical_qc_result"] == "PASS"),
        compliance_passed=(rec["compliance_result"] == "PASS"),
        channel_validation_passed=(rec["channel_validator_result"] == "PASS"),
        asset_provenance_passed=(rec["asset_provenance_result"] == "PASS"),
        kids_safety_passed=True if rec["kids_safety_result"] == "PASS" else (False if rec["kids_safety_result"] == "FAIL" else None),
        educational_accuracy_passed=True if rec["educational_accuracy_result"] == "PASS" else (False if rec["educational_accuracy_result"] == "FAIL" else None)
    )
    return jsonify({"ok": True, "readiness": report, "content": rec})


@app.route("/api/originality/evaluate", methods=["POST"])
def api_evaluate_originality():
    from core.originality_engine import originality_engine
    body = request.get_json(force=True) or {}
    cid = body.get("channel_id") or registry.get_active_channel_id()
    res = originality_engine.evaluate_originality(
        channel_id=cid,
        topic=body.get("topic", ""),
        script=body.get("script", ""),
        hook=body.get("hook", ""),
        title=body.get("title", ""),
        story_structure=body.get("story_structure", ""),
        visual_plan=body.get("visual_plan", "")
    )
    return jsonify({"ok": True, "report": res})


@app.route("/api/regenerate-stage", methods=["POST"])
def api_regenerate_stage():
    from core.targeted_regeneration import regeneration_mgr
    body = request.get_json(force=True) or {}
    comp = body.get("component", "hook_similarity")
    cid = body.get("channel_id") or registry.get_active_channel_id()
    data = body.get("data", {})
    updated = regeneration_mgr.regenerate(comp, data, cid)
    return jsonify({"ok": True, "component": comp, "updated_data": updated})


# ── ENTRY POINT ─────────────────────────────────────────────────────────────

def start_server(port=7860):
    import webbrowser
    print(f"\n=======================================================")
    print(f"[*] YouTube Turbo Studio is starting!")
    print(f"    URL: http://localhost:{port}")
    print(f"=======================================================\n")
    threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)


if __name__ == "__main__":
    start_server()
