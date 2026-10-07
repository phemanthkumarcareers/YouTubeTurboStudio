"""
YouTube Video Uploader
Uploads generated videos and custom thumbnails to YouTube Data API v3 with resumable chunking.
"""
import os
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import TOKEN_PATH, CLIENT_SECRET_PATH, load_config
from core.logger import log_info, log_warn, log_success, log_error
from core.state import update_state


def get_youtube_service():
    """Return authenticated YouTube API service."""
    if not TOKEN_PATH.exists():
        raise FileNotFoundError("youtube_token.pickle does not exist. Please authenticate via the YouTube tab.")

    with open(TOKEN_PATH, "rb") as f:
        creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and getattr(creds, "refresh_token", None):
            from google.auth.transport.requests import Request
            try:
                creds.refresh(Request())
                with open(TOKEN_PATH, "wb") as f:
                    pickle.dump(creds, f)
            except Exception as e:
                raise PermissionError(f"YouTube authentication token expired and could not be refreshed ({e}). Please open the YouTube tab and click 'Connect YouTube Channel' to re-authorize.")
        else:
            raise PermissionError("YouTube token is expired or invalid. Please open the YouTube tab and click 'Connect YouTube Channel' to authorize.")

    return build("youtube", "v3", credentials=creds)


def upload_video_to_youtube(video_path: str, title: str, description: str, tags: list[str] = None,
                            privacy: str = "private", category_id: str = "28",
                            publish_at: str = None, thumb_path: str = None) -> str:
    """
    Resumable video upload with progress callback.
    publish_at: RFC 3339 datetime string (e.g. '2026-10-15T15:00:00Z') or None
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found at: {video_path}")

    update_state(uploading=True, upload_pct=0)
    yt = get_youtube_service()

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
            "selfDeclaredMadeForKids": False
        }
    }
    if publish_at:
        body["status"]["publishAt"] = publish_at

    log_info(f"Initiating YouTube upload for '{title}' (Privacy: {body['status']['privacyStatus']})...")

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
