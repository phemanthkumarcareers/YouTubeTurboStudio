"""
YouTube Video Uploader
Uploads generated videos and custom thumbnails to YouTube Data API v3 with resumable chunking.
Enforces channel verification prior to upload to prevent cross-channel posting.
"""
import os
import pickle
from typing import Optional, List
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import TOKEN_PATH, CLIENT_SECRET_PATH, load_config
from core.credential_manager import get_youtube_token_path
from core.channel_registry import registry
from core.logger import log_info, log_warn, log_success, log_error
from core.state import update_state
from youtube.channel_verifier import get_channel_youtube_credentials, verify_channel


def get_youtube_service(channel_id: str = None):
    """Return authenticated YouTube API service for a specific channel."""
    cid = channel_id or registry.get_active_channel_id()
    creds = get_channel_youtube_credentials(cid)
    if not creds:
        # Fall back to root token if insightspark-tv / the-ai-brief-it and file exists
        if cid in ("insightspark-tv", "the-ai-brief-it") and TOKEN_PATH.exists():
            with open(TOKEN_PATH, "rb") as f:
                creds = pickle.load(f)

    if not creds:
        raise FileNotFoundError(
            f"No valid YouTube token found for channel '{cid}'. Please authenticate via the YouTube tab."
        )

    if not creds.valid:
        raise PermissionError(
            f"YouTube token for channel '{cid}' is expired or invalid. Please re-authenticate."
        )

    return build("youtube", "v3", credentials=creds)


def upload_video_to_youtube(
    video_path: str,
    title: str,
    description: str,
    tags: Optional[List[str]] = None,
    privacy: str = "private",
    category_id: str = "28",
    publish_at: Optional[str] = None,
    thumb_path: Optional[str] = None,
    channel_id: Optional[str] = None,
    expected_youtube_channel_id: Optional[str] = None,
    made_for_kids: bool = False,
    content_id: Optional[str] = None,
    parent_content_id: Optional[str] = None,
    relationship_type: str = "STANDALONE",
    readiness_report: Optional[dict] = None
) -> str:
    """
    Resumable video upload with progress callback, channel verification,
    and Section 4 / Section 8 compliance & originality gating.
    """
    from core.compliance_gate import compliance_gate_mgr
    from core.content_family import content_family_mgr

    # Enforce hard publishing gate (Upload target never overrides failed gates)
    if readiness_report:
        compliance_gate_mgr.assert_can_publish(readiness_report)
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found at: {video_path}")

    cid = channel_id or registry.get_active_channel_id()
    chan_ctx = registry.get_channel(cid)
    exp_id = expected_youtube_channel_id or (chan_ctx.youtube.get("channel_id") if chan_ctx else "")
    is_kids = made_for_kids or (chan_ctx.youtube.get("made_for_kids", False) if chan_ctx else False)

    # ── SECURITY PRE-UPLOAD CHECK ──────────────────────────────────────
    log_info(f"Verifying YouTube OAuth identity for channel '{cid}' before upload...")
    verified, verif_msg, _ = verify_channel(cid, exp_id)
    if not verified:
        log_error(f"Pre-upload verification failed: {verif_msg}")
        raise PermissionError(f"Upload blocked by channel verifier: {verif_msg}")

    update_state(uploading=True, upload_pct=0, channel_id=cid)
    yt = get_youtube_service(cid)

    # Build short description with parent URL if derived
    description = content_family_mgr.build_short_description(
        base_description=description,
        relationship_type=relationship_type,
        parent_content_id=parent_content_id
    )

    # Append hashtags to description so they show on the YouTube video page
    if tags:
        hashtag_line = " ".join(f"#{t.replace(' ', '')}" for t in tags[:15])
        description = description.rstrip() + "\n\n" + hashtag_line

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags or [],
            "categoryId": str(category_id)
        },
        "status": {
            "privacyStatus": "private" if publish_at else privacy,
            "selfDeclaredMadeForKids": bool(is_kids)
        }
    }
    if publish_at:
        body["status"]["publishAt"] = publish_at

    log_info(f"Initiating YouTube upload for '{title}' (Channel: {cid}, Privacy: {body['status']['privacyStatus']})...")

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=5 * 1024 * 1024  # 5MB chunks
    )

    insert_req = yt.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = insert_req.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            update_state(upload_pct=pct)
            log_info(f"YouTube upload progress: {pct}%")

    video_id = response.get("id")
    yt_url = f"https://www.youtube.com/watch?v={video_id}"
    update_state(upload_pct=100, yt_url=yt_url)
    log_success(f"Video successfully uploaded to YouTube! Watch link: {yt_url}")

    if content_id:
        content_family_mgr.update_youtube_publish(content_id, video_id, yt_url)

    # Set custom thumbnail if available
    if thumb_path and os.path.exists(thumb_path):
        try:
            log_info("Uploading custom thumbnail...")
            yt.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumb_path, mimetype="image/jpeg")
            ).execute()
            log_success("Custom thumbnail uploaded successfully.")
        except Exception as th_err:
            log_warn(f"Failed to set custom thumbnail: {th_err}")

    update_state(uploading=False)
    return yt_url
