"""
Pixabay Stock Media Downloader
Supports searching and downloading stock photos and videos from Pixabay.
"""
import requests
from pathlib import Path
from core.logger import log_info, log_warn


def test_pixabay_key(api_key: str) -> tuple[bool, str]:
    if not api_key or not api_key.strip():
        return False, "Pixabay API key is empty."
    try:
        r = requests.get(f"https://pixabay.com/api/?key={api_key.strip()}&per_page=3", timeout=8)
        if r.status_code == 200:
            data = r.json()
            if "hits" in data:
                return True, "Pixabay API Key is valid and active!"
            return False, f"Pixabay returned unexpected format: {r.text[:80]}"
        elif r.status_code == 400:
            return False, "Invalid API Key or Bad Request."
        else:
            return False, f"Pixabay HTTP {r.status_code}: {r.text[:80]}"
    except Exception as e:
        return False, f"Pixabay connection error: {str(e)}"


def search_pixabay_photos(query: str, api_key: str, orientation: str = "horizontal", count: int = 2) -> list[str]:
    if not api_key:
        return []
    # Pixabay orientation: 'all', 'horizontal', 'vertical'
    pix_orient = "vertical" if orientation == "portrait" else "horizontal"
    try:
        params = {
            "key": api_key.strip(),
            "q": query,
            "image_type": "photo",
            "orientation": pix_orient,
            "per_page": count,
            "safesearch": "true"
        }
        r = requests.get("https://pixabay.com/api/", params=params, timeout=12)
        if r.status_code == 200:
            hits = r.json().get("hits", [])
            urls = []
            for h in hits:
                url = h.get("largeImageURL") or h.get("webformatURL")
                if url:
                    urls.append(url)
            return urls
    except Exception as e:
        log_warn(f"Pixabay photo search error for '{query}': {e}")
    return []


def search_pixabay_videos(query: str, api_key: str, orientation: str = "horizontal", count: int = 1) -> list[str]:
    if not api_key:
        return []
    try:
        params = {
            "key": api_key.strip(),
            "q": query,
            "per_page": count,
            "safesearch": "true"
        }
        r = requests.get("https://pixabay.com/api/videos/", params=params, timeout=12)
        if r.status_code == 200:
            hits = r.json().get("hits", [])
            urls = []
            for h in hits:
                vids = h.get("videos", {})
                large = vids.get("large", {}).get("url") or vids.get("medium", {}).get("url")
                if large:
                    urls.append(large)
            return urls
    except Exception as e:
        log_warn(f"Pixabay video search error for '{query}': {e}")
    return []
