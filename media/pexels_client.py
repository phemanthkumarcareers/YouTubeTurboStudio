"""
Pexels Stock Media Downloader
Supports both curated high-res photos and HD videos with orientation awareness (portrait for Shorts, landscape for Standard).
"""
import os
import requests
from pathlib import Path
from core.logger import log_info, log_warn, log_success


def test_pexels_key(api_key: str) -> tuple[bool, str]:
    if not api_key or not api_key.strip():
        return False, "Pexels API key is empty."
    headers = {"Authorization": api_key.strip()}
    try:
        r = requests.get("https://api.pexels.com/v1/curated?per_page=1", headers=headers, timeout=8)
        if r.status_code == 200:
            return True, "Pexels API Key is valid and active!"
        elif r.status_code == 401:
            return False, "Invalid API Key (HTTP 401 Unauthorized)."
        else:
            return False, f"Pexels responded with HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def search_photos(query: str, api_key: str, orientation: str = "landscape", count: int = 2) -> list[str]:
    """Search Pexels photos and return list of download URLs."""
    if not api_key:
        return []
    headers = {"Authorization": api_key.strip()}
    params = {
        "query": query,
        "orientation": orientation,  # 'landscape', 'portrait', 'square'
        "per_page": count
    }
    try:
        r = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=12)
        if r.status_code == 200:
            data = r.json()
            photos = data.get("photos", [])
            urls = []
            for p in photos:
                src = p.get("src", {})
                url = src.get("large2x") or src.get("large") or src.get("original")
                if url:
                    urls.append(url)
            return urls
        else:
            log_warn(f"Pexels search '{query}' returned status {r.status_code}")
    except Exception as e:
        log_warn(f"Pexels search failed for '{query}': {e}")
    return []


def search_videos(query: str, api_key: str, orientation: str = "landscape", count: int = 1) -> list[str]:
    """Search Pexels videos and return HD video file URLs."""
    if not api_key:
        return []
    headers = {"Authorization": api_key.strip()}
    params = {
        "query": query,
        "orientation": orientation,
        "per_page": count
    }
    try:
        r = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=12)
        if r.status_code == 200:
            data = r.json()
            videos = data.get("videos", [])
            urls = []
            for v in videos:
                files = v.get("video_files", [])
                # Prefer HD (1080p or 720p)
                hd = next((f["link"] for f in files if f.get("quality") == "hd" and f.get("width", 0) >= 1080), None)
                if not hd:
                    hd = next((f["link"] for f in files if f.get("link")), None)
                if hd:
                    urls.append(hd)
            return urls
    except Exception as e:
        log_warn(f"Pexels video search failed for '{query}': {e}")
    return []


def download_file(url: str, dest_path: str) -> bool:
    try:
        Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(url, stream=True, timeout=25)
        if resp.status_code == 200:
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)
            return True
    except Exception as e:
        log_warn(f"Download failed for {url[:60]}: {e}")
    return False
