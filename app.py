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


# ── PIPELINE CONTROL ────────────────────────────────────────────────────────

@app.route("/api/generate", methods=["POST"])
def api_generate():
    body = request.get_json(force=True) or {}
    steps = body.get("steps", ["research", "script", "narration", "media", "video", "thumbnail"])
    topic_override = body.get("topic", "").strip()
    focus_angle = body.get("focus_angle", "").strip()
    video_type = body.get("video_type", "normal")
    footage_source = body.get("footage_source")

    st = get_state()
    if st.get("running"):
        return jsonify({"ok": False, "error": "Pipeline is already running."}), 400

    execute_pipeline(
        steps=steps,
        topic_override=topic_override,
        focus_angle=focus_angle,
        video_type=video_type,
        footage_source=footage_source
    )
    return jsonify({"ok": True, "message": "Pipeline initiated"})


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
        "tags": st.get("tags") or (script.get("tags") if script else [])
    })


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
    cfg = load_config()
    banned = load_banned_topics()
    return jsonify({
        "config": cfg,
        "voices": POPULAR_VOICES,
        "categories": YOUTUBE_CATEGORIES,
        "banned_topics": banned
    })


@app.route("/api/settings/save", methods=["POST"])
def api_save_settings():
    body = request.get_json(force=True) or {}
    try:
        updated = save_config(body)
        log_success("Studio configuration saved successfully.")
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
    return jsonify(check_auth_status())


@app.route("/api/youtube/save-secret-json", methods=["POST"])
def api_youtube_save_secret():
    if "file" in request.files:
        f = request.files["file"]
        try:
            data = json.load(f)
            save_client_secret_json(data)
            return jsonify({"ok": True, "message": "Uploaded and saved client_secret.json!"})
        except Exception as e:
            return jsonify({"ok": False, "error": f"Invalid JSON file: {e}"}), 400

    body = request.get_json(force=True) or {}
    raw_json = body.get("raw_json", "").strip()
    if raw_json:
        try:
            data = json.loads(raw_json)
            save_client_secret_json(data)
            return jsonify({"ok": True, "message": "Client secret JSON saved successfully!"})
        except Exception as e:
            return jsonify({"ok": False, "error": f"Invalid JSON syntax: {e}"}), 400

    return jsonify({"ok": False, "error": "No file or JSON data provided."}), 400


@app.route("/api/youtube/save-credentials", methods=["POST"])
def api_youtube_save_credentials():
    body = request.get_json(force=True) or {}
    client_id = body.get("client_id", "").strip()
    client_secret = body.get("client_secret", "").strip()
    if not client_id or not client_secret:
        return jsonify({"ok": False, "error": "Both Client ID and Client Secret are required."}), 400

    if save_client_credentials(client_id, client_secret):
        return jsonify({"ok": True, "message": "Client credentials saved to client_secret.json!"})
    return jsonify({"ok": False, "error": "Failed to save credentials."}), 500


@app.route("/api/youtube/load-secret-path", methods=["POST"])
def api_youtube_load_secret_path():
    body = request.get_json(force=True) or {}
    filepath = body.get("filepath", "").strip()
    if not filepath:
        return jsonify({"ok": False, "error": "No file path provided"}), 400
    ok, msg = load_client_secret_from_path(filepath)
    return jsonify({"ok": ok, "message": msg, "error": None if ok else msg})


@app.route("/api/youtube/authenticate", methods=["POST"])
def api_youtube_authenticate():
    res = run_oauth_flow()
    return jsonify(res)


@app.route("/api/youtube/upload", methods=["POST"])
def api_youtube_upload():
    body = request.get_json(force=True) or {}
    privacy = body.get("privacy", "private")
    category_id = body.get("category_id", "28")
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
    title = custom_title or script.get("title", "Cinematic YouTube Video")
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
                thumb_path=thumb_path
            )
        except Exception as e:
            log_error(f"YouTube upload failed: {e}")
            update_state(error=str(e), uploading=False)

    threading.Thread(target=_upload_async, daemon=True).start()
    return jsonify({"ok": True, "message": "Upload commenced in background."})


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
