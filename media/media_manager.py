"""
Unified Media Manager for YouTube Turbo Studio — Phase 2 Enhanced
Implements Video-First Retrieval Hierarchy:
1. Relevant Pexels HD video
2. Relevant Pexels high-res photo with intelligent motion
3. Programmatic science diagram / HUD graphic
4. Branded atmospheric fallback gradient
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw
from config import load_config, OUTPUT_DIR
from media.pexels_client import search_photos as pexels_photos, search_videos as pexels_videos, download_file
from media.pixabay_client import search_pixabay_photos, search_pixabay_videos
from video.visual_director import generate_science_diagram
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


def fetch_media_for_script(script: dict, video_type: str = "normal") -> dict[int, list[str]]:
    """
    Downloads media for each section of the script following the Video-First hierarchy:
    Pexels video -> Pexels photo -> Pixabay video -> Pixabay photo -> Science diagram -> Gradient.
    """
    cfg = load_config()
    source = cfg.get("video_source", "pexels_videos")
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

    log_info(f"[MEDIA] Fetching assets for {len(sections)} sections (Video-First Hierarchy, {orientation})...")

    for sec in sections:
        sec_id = sec.get("id", 1)
        query = sec.get("visual_query", "deep space galaxy")
        sec_title = sec.get("title", f"Section {sec_id}")
        sec_paths = []

        log_info(f"   [Section {sec_id}] Searching '{query}'...")

        # ── 1. Video-First: Query Pexels HD Videos ──
        if pexels_key:
            try:
                vid_urls = pexels_videos(query, pexels_key, orientation=orientation, count=target_count)
                for i, u in enumerate(vid_urls):
                    dest = str(img_dir / f"sec_{sec_id}_px_vid_{i}.mp4")
                    if download_file(u, dest):
                        sec_paths.append(dest)
            except Exception as e:
                log_warn(f"   [Section {sec_id}] Pexels video query failed: {e}")

        # ── 2. Photo Fallback: Query Pexels Photos if no video acquired ──
        if not sec_paths and pexels_key:
            try:
                photo_urls = pexels_photos(query, pexels_key, orientation=orientation, count=target_count)
                for i, u in enumerate(photo_urls):
                    dest = str(img_dir / f"sec_{sec_id}_px_img_{i}.jpg")
                    if download_file(u, dest):
                        sec_paths.append(dest)
            except Exception as e:
                log_warn(f"   [Section {sec_id}] Pexels photo query failed: {e}")

        # ── 3. Pixabay Videos & Photos Fallback ──
        if not sec_paths and pixabay_key:
            try:
                urls = search_pixabay_videos(query, pixabay_key, orientation=orientation, count=target_count)
                if not urls:
                    urls = search_pixabay_photos(query, pixabay_key, orientation=orientation, count=target_count)
                for i, u in enumerate(urls):
                    ext = ".mp4" if ".mp4" in u else ".jpg"
                    dest = str(img_dir / f"sec_{sec_id}_pb_{i}{ext}")
                    if download_file(u, dest):
                        sec_paths.append(dest)
            except Exception as e:
                log_warn(f"   [Section {sec_id}] Pixabay query failed: {e}")

        # ── 4. Programmatic Science Diagram Fallback ──
        if not sec_paths:
            diagram_file = str(img_dir / f"sec_{sec_id}_diagram.jpg")
            try:
                generate_science_diagram(
                    title=sec_title,
                    subtitle=query,
                    width=w,
                    height=h,
                    output_path=diagram_file
                )
                sec_paths.append(diagram_file)
                log_info(f"   [Section {sec_id}] Generated high-tech science diagram.")
            except Exception as e:
                log_warn(f"   [Section {sec_id}] Diagram generation error: {e}")

        # ── 5. Guaranteed Atmospheric Gradient Fallback ──
        if not sec_paths:
            fallback_file = str(img_dir / f"sec_{sec_id}_fallback.jpg")
            _create_fallback_gradient(fallback_file, width=w, height=h, sec_id=sec_id)
            sec_paths.append(fallback_file)
            log_warn(f"   [Section {sec_id}] Used atmospheric backdrop.")
        else:
            log_success(f"   [Section {sec_id}] Acquired {len(sec_paths)} media asset(s).")

        result_map[sec_id] = sec_paths

    return result_map
