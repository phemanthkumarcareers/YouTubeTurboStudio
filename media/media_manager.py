"""
Unified Media Manager for YouTube Turbo Studio
Coordinates fetching stock images/videos across Pexels, Pixabay, or Local files.
Guarantees visual assets exist for every script section with intelligent fallbacks.
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw
from config import load_config, OUTPUT_DIR
from media.pexels_client import search_photos as pexels_photos, search_videos as pexels_videos, download_file
from media.pixabay_client import search_pixabay_photos, search_pixabay_videos
from core.logger import log_info, log_warn, log_success


def _create_fallback_gradient(dest_path: str, width: int = 1920, height: int = 1080, sec_id: int = 1):
    """Generate high-resolution dark atmospheric gradient image as guaranteed fallback."""
    colors = [
        ((15, 23, 42), (88, 28, 135)),    # Slate to Deep Purple
        ((10, 15, 30), (30, 58, 138)),    # Deep Navy to Blue
        ((20, 20, 30), (13, 148, 136)),   # Dark Charcoal to Teal
        ((24, 24, 27), (180, 83, 9)),     # Dark Gray to Amber
        ((17, 24, 39), (190, 24, 93)),    # Deep Space to Rose
    ]
    c1, c2 = colors[(sec_id - 1) % len(colors)]
    img = Image.new("RGB", (width, height), c1)
    draw = ImageDraw.Draw(img)
    for y in range(height):
        factor = y / height
        r = int(c1[0] * (1 - factor) + c2[0] * factor)
        g = int(c1[1] * (1 - factor) + c2[1] * factor)
        b = int(c1[2] * (1 - factor) + c2[2] * factor)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    img.save(dest_path, "JPEG", quality=90)


from typing import Optional


def fetch_media_for_script(script: dict, video_type: str = "normal", source: Optional[str] = None) -> dict[int, list[str]]:
    """
    Downloads media for each section of the script.
    When source == "nano_banana", generates AI visuals with Nano Banana.
    Returns: {section_id: [path1, path2, ...]}
    """
    cfg = load_config()
    effective_source = source or cfg.get("video_source", "pexels_images")
    pexels_key = cfg.get("pexels_api_key", "").strip()
    pixabay_key = cfg.get("pixabay_api_key", "").strip()

    is_shorts = (video_type == "shorts")
    orientation = "portrait" if is_shorts else "landscape"
    w, h = (1080, 1920) if is_shorts else (1920, 1080)
    target_count = 2 if is_shorts else 1

    img_dir = OUTPUT_DIR / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    result_map = {}
    sections = script.get("sections", [])

    log_info(f"Fetching media assets for {len(sections)} sections (Mode: {effective_source}, Orientation: {orientation})...")

    for sec in sections:
        sec_id = sec.get("id", 1)
        query = sec.get("visual_query", "cinematic nature space")
        sec_paths = []

        log_info(f"   [Section {sec_id}] Searching '{query}'...")

        # 0. Nano Banana AI Generative Visuals
        nano_key = (cfg.get("gemini_api_key") or cfg.get("nano_banana_api_key", "")).strip()
        is_nano_selected = (effective_source == "nano_banana")
        if is_nano_selected:
            try:
                from media.nano_banana_client import generate_image_with_nano_banana
                dest = str(img_dir / f"sec_{sec_id}_nano_banana.jpg")
                sec_text = sec.get("narration") or sec.get("title") or query
                prompt = f"{query}, {sec_text[:80]}, cinematic 4k, photorealistic masterpiece, vivid detail"
                res = generate_image_with_nano_banana(
                    prompt=prompt,
                    width=w,
                    height=h,
                    output_path=dest,
                    api_key=nano_key
                )
                if res and os.path.exists(res):
                    sec_paths.append(res)
            except Exception as e:
                log_warn(f"   [Section {sec_id}] Nano Banana generation error: {e}")

        # 1. Try Pexels
        if not sec_paths and pexels_key:
            if "video" in effective_source:
                urls = pexels_videos(query, pexels_key, orientation=orientation, count=target_count)
            else:
                urls = pexels_photos(query, pexels_key, orientation=orientation, count=target_count)

            for i, u in enumerate(urls):
                ext = ".mp4" if "video" in effective_source else ".jpg"
                dest = str(img_dir / f"sec_{sec_id}_px_{i}{ext}")
                if download_file(u, dest):
                    sec_paths.append(dest)

        # 2. Try Pixabay if Pexels returned nothing or if pixabay configured
        if not sec_paths and pixabay_key:
            if "video" in effective_source:
                urls = search_pixabay_videos(query, pixabay_key, orientation=orientation, count=target_count)
            else:
                urls = search_pixabay_photos(query, pixabay_key, orientation=orientation, count=target_count)

            for i, u in enumerate(urls):
                ext = ".mp4" if "video" in effective_source else ".jpg"
                dest = str(img_dir / f"sec_{sec_id}_pb_{i}{ext}")
                if download_file(u, dest):
                    sec_paths.append(dest)

        # 3. Fallback to existing or synthetic gradient background
        if not sec_paths:
            fallback_file = str(img_dir / f"sec_{sec_id}_fallback.jpg")
            _create_fallback_gradient(fallback_file, width=w, height=h, sec_id=sec_id)
            sec_paths.append(fallback_file)
            log_warn(f"   [Section {sec_id}] No stock media found for '{query}'. Used atmospheric backdrop.")
        else:
            log_success(f"   [Section {sec_id}] Acquired {len(sec_paths)} media item(s).")

        result_map[sec_id] = sec_paths

    return result_map
